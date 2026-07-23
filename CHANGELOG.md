# Changelog

All notable changes to OpenPulsar will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

## [0.1.7] - 2026-07-19

### Changed

- Made complete DPI-stage rows clickable while keeping hardware-confirmed activation behavior.
- Harmonized DPI and LED panel margins, spacing and active-state styling.
- Improved the visual consistency of DPI, RGB gain and keyboard-command controls.

### Fixed

- Added clear hover feedback to clickable DPI LED color indicators.
- Restored the red hover state of DPI-stage remove buttons.
- Removed the selectable empty DPI row below the last configured stage.
- Corrected the horizontal and vertical alignment of DPI-stage controls.

## [0.1.5] - 2026-07-18

### Added

- Added the `Set DPI` keyboard command with the shared DPI value control.
- Added an integrated conflict card for resolving duplicate keyboard shortcuts without a system dialog.

### Changed

- Unified keyboard-command controls around a shared pill-size grid.
- Reused the DPI color indicator design for RGB gain controls.
- Made the LED mode indicator follow the same active and inactive styling as brightness and pulsation controls.

### Fixed

- Prevented multiple keyboard shortcut controls from listening at the same time.
- Restored the previous shortcut when shortcut capture is cancelled.

## [0.1.4] - 2026-07-17

### Added

- Added complete MIT copyright and license notices for `pulsar-mouse-linux` and `python-pulsar-mouse-tool`.
- Added explicit upstream acknowledgements to the README, About panel and derived source files.
- Added a dedicated RGB gain icon to the LED panel header.

### Changed

- Included third-party notices in Python packages and RPM installations.
- Unified typography, hover text colors, toggle states and control shadows throughout the interface.
- Matched sensor subpanel corner radii to the control-pill radius.

### Fixed

- Made active brightness and pulsation controls visually distinct from inactive controls.
- Ensured keyboard-command and mouse-button text uses the shared blue hover state.

## [0.1.3] - 2026-07-16

### Added

- Added a first-run OpenPulsar presentation with GitHub and Discord links.
- Added project background, acknowledgements and community participation guidance to the About panel.

### Changed

- Redesigned and repositioned the About panel to integrate with the main interface.
- Unified border widths, corner radii and active-state styling throughout the application.

### Fixed

- Kept composite-control borders visible when their buttons are highlighted.
- Kept the About trigger visibly active while the panel is open.

## [0.1.2] - 2026-07-16

### Changed

- Kept at least one category expanded in categorized mouse-button action menus.

### Fixed

- Removed persistent focus outlines that could highlight two keyboard command selectors at once.

## [0.1.1] - 2026-07-15

### Added

- Public repository metadata and contribution workflow.
- Direct keyboard shortcuts for selecting available DPI stages.

### Changed

- Grouped keyboard commands into DPI adjustment, DPI stages and profile categories.
- Limited direct DPI-stage choices to the stages available in the active profile.
- Unified action-menu sizing, alignment and selection styling across mouse buttons and keyboard commands.
- Corrected the supported mouse name from Pulsar Xlite V3 Wired to Pulsar Xlite Wired.

### Fixed

- Removed the unwanted shadow from DPI color indicators.
- Prevented keyboard command menus from flickering, clipping or appearing below command rows.

## [0.1.0] - 2026-07-11

### Added

- Support for Pulsar Xlite Wired.
- Support for Pulsar X2 Wired.
- Support for Pulsar X2H Wired with a provisional product ID pending hardware confirmation.
- Support for Pulsar X2A Wired.
- Five onboard profiles.
- DPI-stage configuration and active-stage selection.
- Polling rate, debounce and lift-off-distance controls.
- Motion Sync, Angle Snap and Ripple Control.
- Mouse-button remapping and keyboard commands.
- RGB LED controls on supported devices.
- Profile import and export.
- System-tray controls.
- English, French, German and Spanish translations.
