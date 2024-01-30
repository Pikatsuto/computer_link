from audio import AudioServices


class Main:
    def __init__(self, audio_config_path="audio_config.json", video_config_path="video_config.json"):
        """
        Initialize the main class
        :param audio_config_path:
        :param video_config_path:
        """

        self.audio_config_path = audio_config_path
        self.video_config_path = video_config_path

        # start program
        self.run()

    def run(self):
        """
        Run the main class
        :return: None
        """

        # run audio config
        audio_services = AudioServices(self.audio_config_path)
        audio_services.run_all()

        # run video config
        # video_services = VideoServices(self.video_config_path)
        # video_services.run_all()


if __name__ == '__main__':
    Main()
