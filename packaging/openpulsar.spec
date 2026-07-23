Name:           openpulsar
Version:        0.1.7
Release:        1%{?dist}
Summary:        Configuration utility for Pulsar wired gaming mice

License:        GPL-3.0-or-later
URL:            https://github.com/Andalrick/OpenPulsar
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-pytest
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib

Requires:       python3dist(pyside6)
Requires:       python3dist(pyusb)
Requires:       python3dist(hidapi)
Requires:       udev

%description
OpenPulsar is an open-source configuration utility for Pulsar wired gaming
mice on Linux. It supports profiles, DPI stages, polling rate, debounce,
sensor options, button remapping and RGB settings on supported devices.

%prep
%autosetup -n OpenPulsar-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files openpulsar

install -Dpm0644 packaging/io.github.andalrick.OpenPulsar.desktop \
  %{buildroot}%{_datadir}/applications/io.github.andalrick.OpenPulsar.desktop
install -Dpm0644 packaging/io.github.andalrick.OpenPulsar.metainfo.xml \
  %{buildroot}%{_metainfodir}/io.github.andalrick.OpenPulsar.metainfo.xml
install -Dpm0644 packaging/70-openpulsar.rules \
  %{buildroot}%{_udevrulesdir}/70-openpulsar.rules
install -Dpm0644 src/openpulsar/assets/icons/Icon_OpenPulsar.svg \
  %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/io.github.andalrick.OpenPulsar.svg

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/io.github.andalrick.OpenPulsar.desktop
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/io.github.andalrick.OpenPulsar.metainfo.xml
%pytest -q

%files -f %{pyproject_files}
%license LICENSE THIRD-PARTY-NOTICES.md
%doc README.md CHANGELOG.md
%{_bindir}/openpulsar
%{_bindir}/openpulsar-cli
%{_datadir}/applications/io.github.andalrick.OpenPulsar.desktop
%{_metainfodir}/io.github.andalrick.OpenPulsar.metainfo.xml
%{_datadir}/icons/hicolor/scalable/apps/io.github.andalrick.OpenPulsar.svg
%{_udevrulesdir}/70-openpulsar.rules

%changelog
* Thu Jul 23 2026 Andalrick <andalrick@outlook.com> - 0.1.7-1
- Finalize main-window layout, profile ribbon geometry and panel radii
- Add consistent painted help controls and align the header help button
- Replace generic notifications with native OpenPulsar dialogs
- Integrate the persistent-mode prompt into the keyboard-command panel

* Sun Jul 19 2026 Andalrick <andalrick@outlook.com> - 0.1.6-1
- Make DPI-stage rows fully clickable with hardware-confirmed activation
- Add hover feedback to DPI LED selectors and restore remove-button hover
- Correct DPI panel spacing, alignment and hidden-row behavior

* Sat Jul 18 2026 Andalrick <andalrick@outlook.com> - 0.1.5-1
- Add direct DPI value keyboard commands and integrated shortcut conflict handling
- Prevent multiple shortcut capture controls from listening simultaneously
- Unify keyboard-command pills, DPI/RGB indicators and LED mode styling

* Fri Jul 17 2026 Andalrick <andalrick@outlook.com> - 0.1.4-1
- Add required upstream MIT notices and complete the visual consistency pass

* Thu Jul 16 2026 Andalrick <andalrick@outlook.com> - 0.1.3-1
- Improve the About experience and unify interface styling

* Thu Jul 16 2026 Andalrick <andalrick@outlook.com> - 0.1.2-1
- Refine command selector focus and category behavior

* Wed Jul 15 2026 Andalrick <andalrick@outlook.com> - 0.1.1-1
- Refine DPI and keyboard command controls

* Sat Jul 11 2026 Andalrick <andalrick@outlook.com> - 0.1.0-1
- Initial RPM packaging
