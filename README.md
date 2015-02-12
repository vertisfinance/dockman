[![Build Status](https://travis-ci.org/vertisfinance/dockman.svg?branch=master)](https://travis-ci.org/vertisfinance/dockman)
[![codecov.io](https://codecov.io/github/vertisfinance/dockman/coverage.svg?branch=master)](https://codecov.io/github/vertisfinance/dockman?branch=master)
# dockman
Docker container management for development and production.
Define your `docker run` parameters in a `yaml` file and use `dockman run <container>`. Create different named groups of related containers (ex. `dev`, `test` and `prod`) and boot them with `dockman up <dev>`. Dependent containers will be created and started in both cases. Use `-i` to get a console: `dockman run -i postgres bash`.

# yaml reference
```yaml
containers:  # define containers here
    shared:
        image: vertis/shared  # the image to use... :)

    view:
        image: vertis/shared
        volumes:  # host binded volumes
            ~/container_shared: /home/myvertis/container_shared
            # your home directory will be substituted
            # also ., .. can be used, will be relative to the project
            # directory (the dir of this yaml file)
        volumes_from:  # just as in docker
            - shared
        icmd: shell  # this command will be used in "interactive mode" (-i)

    postgres:
        image: vertis/postgres
        volumes_from:
            - shared
        env:  # environment variables
            DB_PASSWORD:  # if nothing here, the current value will be used
        ports:
            5432: 5432  # host binded ports (only this format allowed now)
        cmd: start  # the command to run in "daemon mode"

    django-runserver:
        image: vertis/django
        volumes_from:
            - shared
        env:
            MYVERTIS_ENV:
            EMAIL_USER:
            EMAIL_PASSWORD:
            DJANGO_SECRET_KEY:
            DB_PASSWORD:
            PYTHONUNBUFFERED: true
        volumes:
            ~/src: /home/myvertis/src
        links:  # links as with docker
            postgres: db
        ports:
            80: 8000

    nginx:
        image: vertis/nginx-uwsgi
        volumes_from:
            - shared
        ports:
            80: 8080

    uwsgi:
        image: vertis/uwsgi
        volumes_from:
            - shared
        env:
            MYVERTIS_ENV:
            EMAIL_USER:
            EMAIL_PASSWORD:
            DJANGO_SECRET_KEY:
            DB_PASSWORD:
        volumes:
            ~/src: /home/myvertis/src
        links:
            postgres: db

groups:  # your groups comes here
    dev:
        - shared
        - postgres
        - django-runserver

    test:
        - shared
        - postgres
        - uwsgi
        - nginx
```