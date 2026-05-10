# Healthcheck My Server
Healthcheck service to monitor the server uptime.
It notifies when the server is unreachable and when it starts up.

## Table of Contents
- [Installation](#installation)
- [Authors](#authors)
- [License](#license)

## Requirements
- Python3
- systemd
- [Healthcheck](#https://healthchecks.io)

## Installation
1. Clone and enter the repository.
```
git clone https://github.com/ozneroL541/healthcheck-myserver.git \
&& cd healthcheck-myserver
```
2. Create a `.env` file like this:
```
HC_UUID="AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"
SLEEP_MINUTES=30
REQUEST_TIMEOUT=10
```
3. Install the Healthcheck service
```
sudo make install
```
4. Start the service or reboot the server.
```
sudo systemctl start healthcheck.service
```

## Authors
- @ozneroL541 Lorenzo Radice

## License
Copyright (C) 2026  Lorenzo Radice

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
