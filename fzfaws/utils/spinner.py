"""contains the class to init a spinner

Using python multi thread to achieve a spinner
during wait operation for aws
"""
import sys
import time
import threading


class Spinner(threading.Thread):
    """create a spinner in command line async

    Attributes:
        pattern: string, defualt='|/-\\'
        message: string, message to display, default='loading..'
        speed: number, spin speed in seconds
    """

    instances = []  # type: list

    def __init__(self, pattern=None, message=None, speed=None):
        # type: (str, str, int) -> None
        """construtor of spinner

        Args:
            pattern: string, spinner spin pattern
            message: string, spinner loading message
            speed: number, spin speed in seconds
        """
        if message is None:
            message = "loading.."
        if speed is None:
            speed = 0.1
        if pattern is None:
            pattern = "|/-\\"
        super().__init__(target=self._spin)
        self.message = message  # type: str
        self.speed = speed  # type: float
        self.pattern = pattern  # type: str
        self._stopevent = threading.Event()  # type: threading.Event
        self.__class__.instances.append(self)

    def stop(self):
        """stop the spinner"""
        self._stopevent.set()
        self.join()

    def _spin(self):
        """spin the spinner"""
        while not self._stopevent.is_set():
            for cursor in self.pattern:
                sys.stdout.write("%s %s" % (cursor, self.message))
                sys.stdout.flush()
                time.sleep(self.speed)
                sys.stdout.write("\033[2K\033[1G")

    def execute_with_spinner(self, action, **kwargs):
        # type: (Callable, str, **kwargs) -> Any
        """used for basic fetching information from boto3 with spinner

        :param action: function to execute
        :type action: Callable
        """
        try:
            self.start()
            response = action(**kwargs)
            self.stop()
            return response
        except:
            Spinner.clear_spinner()
            raise

    @classmethod
    def clear_spinner(cls):
        for spinner in cls.instances:
            spinner.stop()
