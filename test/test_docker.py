import pytest

from . import SafeDocker


class TestException(Exception):
    pass


def test_safe_docker():
    """
    First test if the SafeDocker class works correctly.
    """
    docker = SafeDocker(command=['test'], _exception=TestException())

    # must raise the exception
    with pytest.raises(TestException):
        docker.execute([])

    # must remember the command
    assert docker._cmd == ['test']

    docker = SafeDocker(command=['test'], _output='test_output')
    assert docker.execute(['1', '2']) == 'test_output'
    assert docker._cmd == ['test', '1', '2']

    docker.execute_interactive(['foo'])
    assert docker._cmd == ['test', 'foo']


def test_getstate():
    docker = SafeDocker(_exception=TestException())
    assert docker.getstate('somecontainer') is None

    docker = SafeDocker(_output='false')
    assert docker.getstate('somecontainer') is False

    docker = SafeDocker(_output='true')
    assert docker.getstate('somecontainer') is True
