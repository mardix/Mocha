
At root of `/app` directory contains `config.py`. This is where most of the
configuration reside

Mocha uses class-based configuration

By default it is expecting a config class `Dev`, but can be change by setting
a environment variable: `env=prod` or `env=stage`