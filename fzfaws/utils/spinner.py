"""This module contains the class to create a cli spinner.

The spinner class is utilising the threading to achieve
a spinner.
"""
from contextlib import contextmanager
import os
import sys
import threading
import time
from typing import Iterator, Optional


class Spinner(threading.Thread):
    """Create a spinner in the command line.

    Using python threading to achieve the spinner.
    After the operation finish, call spinner.stop()
    to stop and remove the spinner.

    It also comes with a context manager that could be
    used easier.

    Example:
        with Spinner.spin(message="hello"):
            long_running_task()
        print('finished')

    All the arguments are optional, if nothing is found, the spiner
    will attempt to read the ENV (user config) before proceeding.

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
        """Construct a spiner."""
        if message is None:
            message = str(os.getenv("FZFAWS_SPINNER_MESSAGE", "loading ..."))
        if speed is None:
            speed = float(os.getenv("FZFAWS_SPINNER_SPEED", "0.1"))
        if pattern is None:
            pattern = str(os.getenv("FZFAWS_SPINNER_PATTERN", "|/-\\"))
        super().__init__(target=self._spin)
        self.message: str = message
        self.speed: float = speed
        self.pattern: str = pattern
        self._stopevent = threading.Event()
        self.__class__.instances.append(self)

    def stop(self) -> None:
        """Stop the spinner."""
        self._stopevent.set()
        self.join()

    def _spin(self) -> None:
        """Spin the spinner."""
        while not self._stopevent.is_set():
            for cursor in self.pattern:
                sys.stdout.write("%s %s" % (cursor, self.message))
                sys.stdout.flush()
                time.sleep(self.speed)
                sys.stdout.write("\033[2K\033[1G")

    @classmethod
    def clear_spinner(cls) -> None:
        """Clean up all spinner instance."""
        for spinner in cls.instances:
            if spinner.is_alive():
                spinner.stop()
        cls.instances[:] = []

    @classmethod
    @contextmanager
    def spin(
        cls,
        pattern: Optional[str] = None,
        message: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> Iterator[None]:
        """Context manager to handle spinner start and exit.

        :param pattern: pattern to display during spin
        :type pattern: str, optional
        :param message: message to display during spin
        :type message: str, optional
        :param speed: speed to spin
        :type speed: float, optional
        """
        try:
            spinner = cls(pattern=pattern, message=message, speed=speed)
            spinner.start()
            yield
            spinner.stop()
        except:
            cls.clear_spinner()
            raise
