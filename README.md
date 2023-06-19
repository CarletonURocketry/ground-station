# CUInSpace Telemetry Server

This software is a command line tool for retrieving UART data via serial from the CUInSpace
[ground station board](ground-station-board) and parsing it into readable data which is served via websocket for the
[ground-station-ui](ground-station-ui) live telemetry dashboard.

## Quick Start
Before starting, ensure you have Python 3.11+ installed and the CP210x driver for the homemade ground-station board UART
connection. This is not necessary if using the PICTail Daughter Board.

- Download the latest release
- Navigate to the project directory from the terminal
- Run `pip install -r requirements.txt`
- Run `py main.py -h` for a list of commands

Note that the ground station device should be connected before starting the telemetry server in order to receive an
accurate list of available serial ports.

## Further Reading
Please see the [GitHub Wiki](wiki) for further documentation on how to set up and run the telemetry server.

## Contribution
To contribute to this project, please view the contribution guidelines in the project's GitHub Wiki. Note that
contributions are currently limited to *Carleton University students or CUInSpace members*.

### Authors
- Samuel Dewan
- Thomas Selwyn
- Matteo Golin
- Arsalan Syed

<!--Links-->
[ground-station-board]: https://github.com/CarletonURocketry/avionics-hardware/pull/18
[ground-station-ui]: https://github.com/CarletonURocketry/ground-station-ui
[wiki]: https://github.com/CarletonURocketry/ground-station/wiki
