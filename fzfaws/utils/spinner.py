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

    def __init__(self, pattern=None, message=None, speed=None):
        """construtor of spinner

        Args:
            pattern: string, spinner spin pattern
            message: string, spinner loading message
            speed: number, spin speed in seconds
        """
        super().__init__(target=self._spin)
        self._stopevent = threading.Event()
        self.pattern = pattern if pattern else '|/-\\'
        self.message = message if message else 'loading..'
        self.speed = speed if speed else 0.1

    def stop(self):
        """stop the spinner"""
        self._stopevent.set()

    def _spin(self):
        """spin the spinner"""
        while not self._stopevent.isSet():
            for cursor in self.pattern:
                sys.stdout.write('%s %s' % (cursor, self.message))
                sys.stdout.flush()
                time.sleep(self.speed)
                sys.stdout.write('\033[2K\033[1G')
