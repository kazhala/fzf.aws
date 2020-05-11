"""contains the class to init a spinner

Using python multi thread to achieve a spinner
during wait operation for aws
"""
import sys
import time
import threading
from typing import Any, Callable, Optional


class Spinner(threading.Thread):
    """create a spinner in command line async

    :param pattern: pattern to display during spin
    :type pattern: str, optional
    :param message: message to display during spin
    :type message: str, optional
    :param speed: speed to spin
    :type speed: float, optional
    """

    instances: list = []

    def __init__(
        self,
        pattern: Optional[str] = None,
        message: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> None:
        """construtor of spinner
        """
        if message is None:
            message = "loading.."
        if speed is None:
            speed = 0.1
        if pattern is None:
            pattern = "|/-\\"
        super().__init__(target=self._spin)
        self.message: str = message
        self.speed: float = speed
        self.pattern: str = pattern
        self._stopevent = threading.Event()
        self.__class__.instances.append(self)

    def stop(self) -> None:
        """stop the spinner
        """
        self._stopevent.set()
        self.join()

    def _spin(self) -> None:
        """spin the spinner
        """
        while not self._stopevent.is_set():
            for cursor in self.pattern:
                sys.stdout.write("%s %s" % (cursor, self.message))
                sys.stdout.flush()
                time.sleep(self.speed)
                sys.stdout.write("\033[2K\033[1G")

    def execute_with_spinner(self, action: Callable, **kwargs) -> Any:
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
    def clear_spinner(cls) -> None:
        for spinner in cls.instances:
            if spinner.isAlive():
                spinner.stop()
        cls.instances[:] = []
