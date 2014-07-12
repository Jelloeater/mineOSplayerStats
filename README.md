# mineOSHeartBeat
A small application to detect if a Mincraft server(s) running on MineOS is down, and automatically restart it/them.

Can monitor all present servers, a single server, or be run interactively.

## Usage
For help just run with -h

### Example

#### Single server w/ e-mail alerts
	python mineos_monitor.py -c
	python mineos_monitor.py -e -s ServerNameInMineOS 

## Dependency's
MineOS (http://minecraft.codeemo.com)
Keyring (https://bitbucket.org/kang/python-keyring-lib) (included)