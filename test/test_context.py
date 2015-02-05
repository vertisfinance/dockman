import os

import pytest

from dockman import context


cwd = os.path.dirname(__file__)
cwd1 = os.path.join(cwd, 'a')
cwd2 = os.path.join(cwd1, 'b')


def test_read_config():
    with pytest.raises(context.NoConfigException):
        context.Context(config_filename='dockman.yaml')

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test1.yaml',
                        path=cwd2)

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test2.yaml',
                        path=cwd1)

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test3.yaml',
                        path=cwd)

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test4.yaml',
                        path=cwd)

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test5.yaml',
                        path=cwd)

    ctx = context.Context(config_filename='test6.yaml',
                          path=cwd)

    assert ctx.containers.keys() == ['a', 'b']
