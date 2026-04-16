"""
Interactive CLI menu for selecting audio input and output devices.

Shown on every startup. Selected indices are saved to .env for reference
but the menu always runs.
"""

from pathlib import Path
from typing import Optional

import sounddevice as sd

ENV_FILE = Path(".env")


def _write_device_to_env(key: str, index: int) -> None:
    """Update or append a device key in .env."""
    text = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
    lines = text.splitlines()
    new_line = f"{key}={index}"
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = new_line
            ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    with ENV_FILE.open("a", encoding="utf-8") as f:
        f.write(f"\n{new_line}\n")


def _list_devices() -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Return (input_devices, output_devices) as lists of (index, label)."""
    inputs, outputs = [], []
    for idx, dev in enumerate(sd.query_devices()):
        label = f"[{idx}] {dev['name']}"
        if dev["max_input_channels"] > 0:
            inputs.append((idx, f"{label}  ({dev['max_input_channels']} in)"))
        if dev["max_output_channels"] > 0:
            outputs.append((idx, f"{label}  ({dev['max_output_channels']} out)"))
    return inputs, outputs


def _prompt_choice(devices: list[tuple[int, str]], kind: str) -> int:
    """Print device list and return the chosen device index."""
    print(f"\nAvailable {kind} devices:")
    for _, label in devices:
        print(f"  {label}")
    valid = {idx for idx, _ in devices}
    while True:
        raw = input(f"Select {kind} device number: ").strip()
        if raw.isdigit() and int(raw) in valid:
            return int(raw)
        print(f"  Invalid choice. Enter one of: {sorted(valid)}")


def select_devices() -> tuple[int, int]:
    """Show the device selection menu and return (input_idx, output_idx)."""
    inputs, outputs = _list_devices()

    print("\n--- Audio Device Setup ---")
    input_idx = _prompt_choice(inputs, "input (microphone)")
    output_idx = _prompt_choice(outputs, "output (speakers)")

    _write_device_to_env("INPUT_DEVICE", input_idx)
    _write_device_to_env("OUTPUT_DEVICE", output_idx)
    print()

    return input_idx, output_idx
