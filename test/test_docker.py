import pytest

from dockman.docker import SafeDocker


class TestException(Exception):
    pass


def test_safe_docker():
    """
    First test if the SafeDocker class works correctly.
    """
    docker = SafeDocker(command=['test'], _output=TestException())

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
    docker = SafeDocker(_output=TestException())
    assert docker.getstate('somecontainer') is None

    docker = SafeDocker(_output='false')
    assert docker.getstate('somecontainer') is False

    docker = SafeDocker(_output='true')
    assert docker.getstate('somecontainer') is True


def test_run():
    docker = SafeDocker()
    docker.run('image', daemon=True, interactive=False,
               remove=False, name='', volumes_from=[], volumes={},
               ports={}, links={}, env={}, cmd=[])
    assert docker._cmd == ['docker', 'run', '-d', 'image']

    docker.run('image', daemon=False, interactive=True,
               remove=True, name='name', volumes_from=['a', 'b'],
               volumes={'x': 'y'}, ports={1: 1},
               links={'l': 'l'}, env={'ev': 'ev'}, cmd=['do', 'it'])
    assert docker._cmd == ['docker', 'run', '-it', '--rm', '--name', 'name',
                           '--volumes-from', 'a',
                           '--volumes-from', 'b',
                           '-v', 'x:y', '-p', '1:1',
                           '--link', 'l:l', '-e', 'ev=ev', 'image',
                           'do', 'it']


def test_start_stop_remove():
    docker = SafeDocker()
    docker.start('x')
    assert docker._cmd == ['docker', 'start', 'x']
    docker.stop('x')
    assert docker._cmd == ['docker', 'stop', 'x']
    docker.remove('x')
    assert docker._cmd == ['docker', 'rm', 'x']


def test_container_ids():
    ids = ['a', 'b', 'c']
    docker = SafeDocker(_output='\n'.join(ids))
    assert docker.container_ids == ids
