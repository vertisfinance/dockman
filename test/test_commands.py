import os

from click.testing import CliRunner

import dockman
from dockman import dockman as commands
from dockman.docker import SafeDocker
from dockman.context import Context


def path(relpath):
    """Returns path relative to the current file."""
    return os.path.join(os.path.dirname(__file__), relpath)


def test_ps():
    container_ids = '944afe740314\n2fb996a8e981\n2ba796be766d\nfc05dd6c5e9c\n'
    container_info = open(path('inspect1.json'), 'r')
    dockman.DOCKER = SafeDocker(_output=[container_ids, container_info])
    dockman.CONTEXT = Context(path='src', config={})
    runner = CliRunner()
    result = runner.invoke(commands.ps)
    out = result.output
    # print out
    assert out == ('-------------------------------------------\n'
                   'src.postgres  running  5432 -> 0.0.0.0:5432\n'
                   '                       1112 -> 0.0.0.0:1111\n'
                   'src.shared    running  \n'
                   '-------------------------------------------\n')
