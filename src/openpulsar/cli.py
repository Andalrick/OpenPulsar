import argparse
import subprocess
from contextlib import contextmanager

from openpulsar.devices.registry import find_supported_device
from openpulsar.logging_utils import configure_logging
from openpulsar.devices.pulsar import PulsarXliteV3Wired
from openpulsar.core.profile_manager import (
    list_profiles,
)
from openpulsar.core.profile_manager import (
    list_profiles,
    save_profile_to_library,
    load_profile_from_library,
    delete_profile,
)

from openpulsar.core.device_mapper import (
    read_profile_from_mouse,
    apply_profile_to_mouse,
)


PULSAR_VENDOR_ID = "3710"


@contextmanager
def open_mouse():
    """Open the supported mouse and always release its USB interface."""
    mouse = find_supported_device() or PulsarXliteV3Wired()
    mouse.open()
    try:
        yield mouse
    finally:
        mouse.close()


def detect_devices():
    found = False

    for i in range(32):
        dev = f"/dev/hidraw{i}"

        result = subprocess.run(
            ["udevadm", "info", "-q", "property", "-n", dev],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            continue

        props = result.stdout

        if f"ID_VENDOR_ID={PULSAR_VENDOR_ID}" not in props:
            continue

        found = True
        model = "Unknown"
        pid = "Unknown"

        for line in props.splitlines():
            if line.startswith("ID_MODEL="):
                model = line.split("=", 1)[1]
            elif line.startswith("ID_MODEL_ID="):
                pid = line.split("=", 1)[1]

        print(f"{dev}: {model}  VID={PULSAR_VENDOR_ID} PID={pid}")

    if not found:
        print("No Pulsar HID device found.")


def show_status():
    with open_mouse() as mouse:
        print(f"{mouse.capabilities.name} — current settings")
        print("=" * 50)
        print()

        for profile in range(1, mouse.capabilities.num_profiles + 1):
            dpi = mouse.get_dpi_stages(profile)
            lod = mouse.get_lod(profile)

            print()
            print(f"Profile {profile}:")
            print(f"  Polling rate: {mouse.get_polling_rate(profile)} Hz")
            print(f"  Debounce: {mouse.get_debounce(profile)} ms")
            print(f"  Angle snap: {'on' if mouse.get_angle_snap(profile) else 'off'}")
            print(f"  Ripple control: {'on' if mouse.get_ripple_control(profile) else 'off'}")
            print(f"  Motion sync: {'on' if mouse.get_motion_sync(profile) else 'off'}")
            print(f"  LOD: {lod} mm")
            print(f"  DPI active stage: {dpi.get('active')}")
            print("  DPI stages:")

            stages = dpi.get("stages", [])
            active = dpi.get("active")

            for index, value in enumerate(stages, start=1):
                marker = " <" if index == active else ""

                if (
                    isinstance(value, tuple)
                    and len(value) == 2
                    and value[0] == value[1]
                ):
                    dpi_text = str(value[0])
                else:
                    dpi_text = str(value)

                print(f"    Stage {index}: {dpi_text} DPI{marker}")

def set_global_setting(setting, value, profile):
    with open_mouse() as mouse:
        if setting == "polling":
            hz = int(value)
            mouse.set_polling_rate(hz, profile)
            print(f"Profile {profile} polling rate set to {hz} Hz")

        elif setting == "debounce":
            ms = int(value)
            mouse.set_debounce(ms, profile)
            print(f"Profile {profile} debounce set to {ms} ms")

        elif setting == "motion-sync":
            enabled = value.lower() in ("on", "true", "1", "yes")
            mouse.set_motion_sync(enabled, profile)
            print(f"Profile {profile} motion sync: {'on' if enabled else 'off'}")

        elif setting == "angle-snap":
            enabled = value.lower() in ("on", "true", "1", "yes")
            mouse.set_angle_snap(enabled, profile)
            print(f"Profile {profile} angle snap: {'on' if enabled else 'off'}")

        elif setting == "ripple":
            enabled = value.lower() in ("on", "true", "1", "yes")
            mouse.set_ripple_control(enabled, profile)
            print(f"Profile {profile} ripple control: {'on' if enabled else 'off'}")

        elif setting == "dpi":
            stages = [int(x.strip()) for x in value.split(",")]
            active = 1
            mouse.set_dpi_stages(stages, active, profile)
            print(f"Profile {profile} DPI stages set to: {stages}")

        elif setting == "dpi-stage":
            stage = int(value)
            mouse.set_active_dpi_stage(stage, profile)
            print(f"Profile {profile} active DPI stage set to {stage}")

        else:
            raise SystemExit(f"Unknown setting: {setting}")

def export_profile(slot: int, name: str):
    with open_mouse() as mouse:
        print(f"Reading slot {slot}...")

        profile = read_profile_from_mouse(
            mouse,
            slot=slot,
            name=name,
        )

        print(f"Saving profile '{name}'...")
        save_profile_to_library(profile)
        print("Done")

def import_profile(name: str, slot: int):
    with open_mouse() as mouse:
        print(f"Loading profile '{name}'...")

        profile = load_profile_from_library(name)

        apply_profile_to_mouse(
            mouse,
            profile,
            slot,
            progress_callback=print,
        )

def remove_profile(name: str):
    delete_profile(name)
    print(f"Deleted profile '{name}'")

def main():
    parser = argparse.ArgumentParser(
        prog="openpulsar",
        description="Open source Pulsar mouse configuration utility",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "profiles",
        help="List saved profiles",
    )

    export_parser = subparsers.add_parser(
        "export-profile",
        help="Export mouse slot to library",
    )

    export_parser.add_argument(
        "slot",
        type=int,
    )

    export_parser.add_argument(
        "name",
    )

    import_parser = subparsers.add_parser(
        "import-profile",
        help="Import library profile to mouse",
    )

    import_parser.add_argument(
        "name",
    )

    import_parser.add_argument(
        "slot",
        type=int,
    )

    delete_parser = subparsers.add_parser(
        "delete-profile",
        help="Delete saved profile",
    )

    delete_parser.add_argument(
        "name",
    )

    subparsers.add_parser(
        "detect",
        help="Detect connected Pulsar HID devices",
    )

    subparsers.add_parser(
        "status",
        help="Show current mouse settings",
    )

    set_parser = subparsers.add_parser(
        "set",
        help="Set mouse setting"
    )

    set_parser.add_argument(
        "setting",
        choices=[
            "polling",
            "debounce",
            "motion-sync",
            "angle-snap",
            "ripple",
            "dpi",
            "dpi-stage",
        ],
    )

    set_parser.add_argument("value")
    set_parser.add_argument(
    "--profile",
    type=int,
    default=1,
    help="Memory slot (1-5)"
)

    args = parser.parse_args()

    if args.command == "detect":
        detect_devices()

    elif args.command == "profiles":
        for name in list_profiles():
            print(name)

    elif args.command == "status":
        show_status()

    elif args.command == "set":
        set_global_setting(
            args.setting,
            args.value,
            args.profile,
)
    elif args.command == "export-profile":
        export_profile(
            args.slot,
            args.name,
)

    elif args.command == "import-profile":
        import_profile(
            args.name,
            args.slot,
)

    elif args.command == "delete-profile":
        remove_profile(
            args.name,
)
    else:
        print("OpenPulsar v0.1")
        print("Try: openpulsar detect")
        print("Try: openpulsar status")
