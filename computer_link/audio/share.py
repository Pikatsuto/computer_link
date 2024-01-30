import os
import socket
import pyaudio
import threading
import time
import signal
from termcolor import colored


class AudioShare:
    def __init__(
        self,
        input_device_name=None,
        output_device_name=None,
        host="0.0.0.0",
        connect="0.0.0.0",
        port=452,
    ):
        """
        Initialize the share audio server
        :param input_device_name:
        :param output_device_name:
        :param host:
        :param port:
        """

        # listening information
        self.host = host
        self.connect = connect
        self.port = port

        # device / pyaudio instance
        self.pyaudio = pyaudio.PyAudio()
        self.input_device_info, self.output_device_info = self.show_devices(input_device_name, output_device_name)

        # audio information
        self.chunk = 3072
        self.channels = 1
        self.rate = 96000

        self.input_index = int(self.input_device_info["index"])
        self.output_index = int(self.output_device_info["index"])

        self.format = pyaudio.paInt16

        # stream / player instance
        self.stream = self.pyaudio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            frames_per_buffer=self.chunk,
            input=True,
            input_device_index=self.input_index,
        )
        self.player = self.pyaudio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            frames_per_buffer=self.chunk,
            output=True,
            output_device_index=self.output_index,
        )

        # continue condition
        self.non_stop = True

        # create socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # set kill process
        signal.signal(signal.SIGABRT, self.stop_all)

    def show_devices(
        self,
        input_device_name,
        output_device_name
    ):
        """
        Show all devices and return selected devices
        :param input_device_name:
        :param output_device_name:
        :return: input_device_info, output_device_info
        """
        already_show = []

        input_device_info = self.pyaudio.get_device_info_by_index(0)
        output_device_info = self.pyaudio.get_device_info_by_index(0)

        # clear console
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

        # print header
        print(f"\nindex"
              f"\t{colored('(', 'magenta')}{colored('input', 'red')}"
              f"\t{colored('output', 'green')}{colored(')', 'magenta')}"
              f"\tname ({colored('selected', 'blue')})")
        print("______________________________________________________________")

        # loop on all devices
        i = 0
        loop_while = True
        while loop_while:
            try:
                card = self.pyaudio.get_device_info_by_index(i)

                # if device already show close loop
                for device in already_show:
                    if card['name'] == device['name']:
                        loop_while = False
                # else add device to already show
                already_show.append(card)

                # if loop continue
                if loop_while:
                    # set selected device
                    if card['name'] == input_device_name:
                        input_device_info = card
                    if card['name'] == output_device_name:
                        output_device_info = card

                    message = f"{card['index']}:\t{card['maxInputChannels']}\t{card['maxOutputChannels']}\t"

                    # set color
                    if card['name'] == input_device_name:
                        message += colored(card['name'], 'blue')
                    elif card['name'] == output_device_name:
                        message += colored(card['name'], 'blue')
                    elif card['maxInputChannels'] > 0 and card['maxOutputChannels'] > 0:
                        message += colored(card['name'], 'magenta')
                    elif card['maxInputChannels'] > 0:
                        message += colored(card['name'], 'red')
                    elif card['maxOutputChannels'] > 0:
                        message += colored(card['name'], 'green')
                    else:
                        message += colored(card['name'], 'yellow')

                    # print separator
                    print(message)
                    print("______________________________________________________________")
                    i += 1

            # if no more device
            except OSError:
                loop_while = False

        print("")
        return input_device_info, output_device_info

    def share_thread(self):
        """
        Share audio thread
        :return: None
        """

        # catch error for clean exit
        try:
            print_if_error = True
            await_connection = True

            # open stream socket
            while self.non_stop and await_connection:
                try:
                    # bind socket
                    self.server_socket.bind((
                        self.host,
                        self.port)
                    )
                    self.server_socket.listen(1)
                    print(colored(f"Listening on {self.server_socket.getsockname()}", "blue"))
                    await_connection = False

                # if port already in use
                except OSError:
                    if print_if_error:
                        print("Port already in use")
                        print_if_error = False
                    time.sleep(5)

            # launch server
            print_if_error = False
            while self.non_stop:
                try:
                    # accept connection
                    connection, address = self.server_socket.accept()

                    # stream audio
                    if connection:
                        print(colored(f"Connection from {address}", "green"))
                        print_if_error = True
                        while self.non_stop:
                            connection.sendall(
                                self.stream.read(self.chunk)
                            )

                # if connection closed
                except (OSError, ConnectionResetError):
                    if print_if_error:
                        print(colored("Connection server closed", "red"))
                        print_if_error = False

        # if all error
        except Exception as error:
            self.stop_all(error=f"{error}on audio share thread")

    def listen_thread(self):
        """
        Listen audio thread
        :return: None
        """

        # catch error for clean exit
        try:
            print_if_error = False
            while self.non_stop:
                try:
                    # connect to stream
                    self.client_socket = socket.socket(
                        socket.AF_INET,
                        socket.SOCK_STREAM
                    )
                    self.client_socket.connect((
                        self.connect,
                        self.port)
                    )

                    # read audio stream
                    if self.client_socket:
                        print(colored(f"Connected to {self.client_socket.getpeername()}", "green"))
                        print_if_error = True

                        data = True
                        while self.non_stop and data:
                            data = self.client_socket.recv(self.chunk)
                            self.player.write(data)

                        # if connection closed
                        if not data:
                            raise ConnectionResetError()

                # if connection closed
                except (OSError, ConnectionResetError):
                    if print_if_error:
                        print(colored("Connection client closed", "red"))
                        print_if_error = False

        # if all error
        except Exception as error:
            self.stop_all(error=f"{error}on audio client thread")

    def stop_all(
        self,
        signum=None,
        frame=None,
        error=""
    ):
        """
        Kill all audio server
        :return: None
        """

        # print signal
        message = "Closing process"
        if error:
            message = f"Crashed {error}"
        if signum:
            message = f"killing process with signal{signum}"
        print(colored(message, "light_red"))

        # kill all threads
        self.non_stop = False
        self.client_socket.close()
        self.server_socket.close()
        self.stream.stop_stream()
        self.pyaudio.terminate()

        exit(0)

    def run(
        self,
        listen=True,
        share=True
    ):
        """
        Run audio server on listen audio
        :return: None
        """

        # run server threads
        time.sleep(1.5)
        if share:
            threading.Thread(
                target=self.share_thread
            ).start()

        # run client threads
        time.sleep(1.5)
        if listen:
            threading.Thread(
                target=self.listen_thread
            ).start()
