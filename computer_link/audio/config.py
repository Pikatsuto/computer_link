import json
import os
import pyaudio
from .share import AudioShare


class AudioServiceConfig:
    def __init__(self, config_path="audio_config.json"):
        """
        Initialize the share audio server
        :param config_path
        """

        self.service_list = []
        self.config = {}

        # load config
        if os.path.exists(config_path):
            with open(config_path) as f:
                self.config = json.load(f)

        # get device 0 name
        p = pyaudio.PyAudio()
        default_device = p.get_device_info_by_index(0)["name"]

        # check if config is defined
        if not self.config:
            # create default config
            self.config = {
                "service": [
                    {
                        "host": "0.0.0.0",
                        "connect": "0.0.0.0",
                        "port": 452,

                        "input_device_name": default_device,
                        "output_device_name": default_device,

                        "share": True,
                        "listen": True,
                    }
                ],
            }

            # write this
            with open(config_path, "w+") as f:
                json.dump(self.config, f, indent=2)

    def run_all(self):
        """
        Run all share and listen audio server
        :return: None
        """

        for service in self.config["service"]:
            # create share
            share = AudioShare(
                host=service["host"],
                connect=service["connect"],
                port=service["port"],
                input_device_name=service["input_device_name"],
                output_device_name=service["output_device_name"],
            )

            # run share
            share.run(
                share=service["share"],
                listen=service["listen"],
            )
            self.service_list.append(share)

        return self.service_list
