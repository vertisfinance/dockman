[![Build Status](https://travis-ci.org/vertisfinance/dockman.svg?branch=master)](https://travis-ci.org/vertisfinance/dockman)
[![Coverage Status](https://coveralls.io/repos/vertisfinance/dockman/badge.svg?branch=master)](https://coveralls.io/r/vertisfinance/dockman?branch=master)
# dockman
Docker container management for development and production.
Define your `docker run` parameters in a `yaml` file and use `dockman run container`. Create different named groups
of related containers (ex. `dev`, `test` and `prod`) and boot them with `dockman up dev`. Dependent containers will
be created and started in both cases. Use `-i` to get a console: `dockman run -i postgres bash`.
