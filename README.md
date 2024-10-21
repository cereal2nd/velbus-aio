![CI](https://github.com/Cereal2nd/velbus-aio/actions/workflows/main.yml/badge.svg)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Cereal2nd/velbus-aio/master.svg)](https://results.pre-commit.ci/latest/github/Cereal2nd/velbus-aio/master)

> This project requires financial support, but it is free for you to use. You can join those helping to keep the lights on at:
>
> [<img src="https://raw.githubusercontent.com/Cereal2nd/hassio-velbusd/refs/heads/main/images/bmc-button.svg" width=150 height=40 style="margin: 5px"/>](https://buymeacoffee.com/cereal2nd) [<img src="https://raw.githubusercontent.com/Cereal2nd/hassio-velbusd/refs/heads/main/images/github-sponsors-button.svg" width=150 height=40 style="margin: 5px"/>](https://github.com/sponsors/Cereal2nd/)

# velbus-aio

Velbus Asyncio, a library to support the [Velbus](https://www.velbus.eu/) home automation system.

This Lib is a rewrite in python3 with asyncio of the [python-velbus](https://github.com/thomasdelaet/python-velbus/) module.
Part of the code from the above lib is reused.
Its also build on top of the [openHab velbus protocol description](https://github.com/StefCoene/moduleprotocol).

The latest version of the library is published as a python package on [pypi](https://pypi.org/project/velbus-aio/)

# Supported connections:

| Type               | Example                          | Description                                                                                                           |
| ------------------ | -------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| serial             | /dev/ttyACME0                    | a serial device                                                                                                       |
| (tcp://)ip:port    | 192.168.1.9:1234                 | An ip address + tcp port combination, used in combination with any velbus => tcp gateway, the tcp:// part is optional |
| tls://ip:port      | tls://192.168.1.9:12345          | A connection to [Signum](https://www.velbus.eu/products/view/?id=458140)                                              |
| tls://auth@ip:port | tls://iauthKey@192.168.1.9:12345 | A connection to [Signum](https://www.velbus.eu/products/view/?id=458140) with uthentication                           |

# Development

See the [contributing](https://github.com/Cereal2nd/velbus-aio/blob/master/CONTRIBUTING.md) guidelines.
