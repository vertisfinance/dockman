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
    assert out == ('-------------------------------------------\n'
                   'Showing containers in project "src"\n'
                   '-------------------------------------------\n'
                   'src.postgres  running  5432 -> 0.0.0.0:5432\n'
                   '                       1112 -> 0.0.0.0:1111\n'
                   'src.shared    running  \n'
                   '-------------------------------------------\n')


def test_logs():
    container_ids = '944afe740314\n2fb996a8e981\n2ba796be766d\nfc05dd6c5e9c\n'
    container_info = open(path('inspect1.json'), 'r')

    docker_output = [container_ids, container_info]
    dockman.DOCKER = SafeDocker(_output=docker_output,
                                _popenout_filename=path('logs_02_'),
                                _log_max_iter=10)
    dockman.CONTEXT = Context(path='src', config={})

    runner = CliRunner()
    result = runner.invoke(commands.logs)
    out = result.output
    out = out.split('\n')
    assert len(out) == 6 + 2  # 2 new lines at the end
    assert 'src.postgres: 02_src.postgres_1' in out
    assert 'src.postgres: 02_src.postgres_2' in out
    assert 'src.postgres: 02_src.postgres_3' in out
    assert 'src.shared: 02_src.shared_1' in out
    assert 'src.shared: 02_src.shared_2' in out
    assert 'src.shared: 02_src.shared_3' in out
