Name:           openpulsar
Version:        0.1.1
Release:        1%{?dist}
Summary:        Configuration utility for Pulsar wired gaming mice

License:        GPL-3.0-or-later
URL:            https://github.com/Andalrick/OpenPulsar
Source0:        %{url}/archive/refs/tags/v%{version}/%{name}-%{version}.tar.gz

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
%license LICENSE
%doc README.md CHANGELOG.md
%{_bindir}/openpulsar
%{_bindir}/openpulsar-cli
%{_datadir}/applications/io.github.andalrick.OpenPulsar.desktop
%{_metainfodir}/io.github.andalrick.OpenPulsar.metainfo.xml
%{_datadir}/icons/hicolor/scalable/apps/io.github.andalrick.OpenPulsar.svg
%{_udevrulesdir}/70-openpulsar.rules

%changelog
* Wed Jul 15 2026 Andalrick <andalrick@outlook.com> - 0.1.1-1
- Refine DPI and keyboard command controls

* Sat Jul 11 2026 Andalrick <andalrick@outlook.com> - 0.1.0-1
- Initial RPM packaging
