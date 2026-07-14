<p align="center">
  <img src="src/openpulsar/assets/icons/Icon_OpenPulsar.svg" alt="OpenPulsar" width="96">
</p>

<h1 align="center">OpenPulsar</h1>

<p align="center"><strong>Open-source configuration utility for Pulsar wired gaming mice on Linux.</strong></p>

<p align="center">
  <a href="https://github.com/Andalrick/OpenPulsar/actions/workflows/tests.yml"><img alt="Tests" src="https://github.com/Andalrick/OpenPulsar/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="License: GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg"></a>
  <img alt="Python 3.12+" src="https://img.shields.io/badge/Python-3.12%2B-blue.svg">
  <img alt="Linux" src="https://img.shields.io/badge/Platform-Linux-lightgrey.svg">
  <a href="https://discord.gg/VghxVFVUUQ"><img alt="Discord" src="https://img.shields.io/badge/Discord-Join%20the%20community-5865F2?logo=discord&logoColor=white"></a>
</p>

<p align="center">
  <img src="docs/screenshots/openpulsar-main.png" alt="OpenPulsar main window" width="760">
</p>

## Features

- Five onboard profiles
- DPI stages and active DPI selection
- Polling rate, debounce and lift-off distance
- Motion Sync, Angle Snap and Ripple Control
- Mouse-button remapping and keyboard commands
- RGB LED controls on supported devices
- Profile import and export
- System-tray controls for profiles and DPI stages
- English, French, German and Spanish interface translations

## Supported devices

| Device | USB PID | Status |
|---|---:|:---:|
| Pulsar Xlite V3 Wired — Medium | `0x1401` | ✅ |
| Pulsar X2 Wired | `0x1402` | ⚠️ Provisional PID |
| Pulsar X2H Wired | `0x1403` | ✅ |
| Pulsar X2A Wired | `0x1404` | ✅ |

All currently supported devices use Pulsar vendor ID `0x3710` and the Sonix Gen1 wired protocol.

## Installation

Packaged installation instructions will be added with the first binary release. Until then, OpenPulsar can be run from source.

### Run from source

Requirements:

- Linux
- Python 3.12 or newer
- access to the mouse HID interface

```bash
git clone https://github.com/Andalrick/OpenPulsar.git
cd OpenPulsar

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

openpulsar
```

The temporary development launcher remains available as:

```bash
./run.sh
```

## Tests

Install the test dependencies and run the hardware-free test suite:

```bash
python -m pip install -e '.[test]'
pytest
```

The GUI smoke tests are skipped automatically when Qt cannot initialize. Real-device validation remains manual.

## Contributing

Bug reports, tested device information and code contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

For compatibility questions, hardware testing and protocol research, join the [OpenPulsar Discord community](https://discord.gg/VghxVFVUUQ).

## Disclaimer

OpenPulsar is an independent community project. It is not affiliated with, endorsed by or sponsored by Pulsar Gaming Gears.

## License

OpenPulsar is licensed under the [GNU General Public License v3.0 or later](LICENSE).
