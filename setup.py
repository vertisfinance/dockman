# during development install it with
#     pip install --editable .

from setuptools import setup


setup(
    name='dockman',
    version='0.1',
    packages=['dockman'],
    install_requires=[
        'click >= 2.4',
        'PyYAML >= 3.11'
    ],
    entry_points={
        "console_scripts": ['dockman = dockman.dockman:main']
    }
)
