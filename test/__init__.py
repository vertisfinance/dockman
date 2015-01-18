import sys
import os

sys.path.insert(0, os.path.abspath('..'))

from dockman import docker


class SafeDocker(docker.Docker):
    """
    Will not call subprocess, just remember the arguments.
    """
    def __init__(self, *args, **kwargs):
        self._cmd = None
        self._exception = None
        self._output = None

        if '_exception' in kwargs:
            self._exception = kwargs.pop('_exception')
        if '_output' in kwargs:
            self._output = kwargs.pop('_output')

        super(SafeDocker, self).__init__(*args, **kwargs)

    def execute(self, params):
        print '----', self.command, params
        self._cmd = self.command + params

        if self._exception:
            raise self._exception
        else:
            return self._output

    def execute_interactive(self, params):
        self._cmd = self.command + params
