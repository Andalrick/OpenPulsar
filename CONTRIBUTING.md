# Contributing to OpenPulsar

Thank you for helping improve OpenPulsar.

## Before opening an issue

- Search existing issues first.
- Use the appropriate issue form.
- Include your distribution, desktop environment, display protocol (X11 or Wayland), Python version and mouse model.
- For hardware problems, include the USB vendor/product IDs from `lsusb` and the exact firmware version shown by OpenPulsar.
- Never publish captures containing secrets or unrelated USB traffic.

## Development setup

```bash
git clone https://github.com/Andalrick/OpenPulsar.git
cd OpenPulsar
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
pytest
```

## Pull requests

- Keep each pull request focused on one change.
- Add or update tests when changing behavior.
- Do not add support for a device based only on an assumed USB product ID.
- Document reverse-engineered protocol behavior and the evidence supporting it.
- Keep hardware-specific capabilities in `src/openpulsar/devices/` and shared protocol logic in `src/openpulsar/protocol/`.
- Ensure `pytest` passes before submitting.

## Device support contributions

A useful device-support report should include:

- exact retail model and size;
- USB vendor ID and product ID;
- firmware version;
- supported profile count and DPI-stage count;
- confirmed controls and any unsupported controls;
- captures or reproducible observations when protocol changes are required.

By contributing, you agree that your contribution may be distributed under the project license, GPL-3.0-or-later.
