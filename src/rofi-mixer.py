#!/bin/env python3

import os
import re
import argparse

VOLUME_DELTA = 5
res = os.getenv("ROFI_RETV")
if res is not None:
    ROFI_RETV = int(res)
else:
    ROFI_RETV = -1

ROFI_INFO = os.getenv("ROFI_INFO")
parser = argparse.ArgumentParser(description="Rofi sound mixer")
parser.add_argument(
    "--type",
    type=str,
    nargs="?",
    const="sink",
    default="sink",
    help="'sink' for speakers 'source' for microphones",
)
parser.add_argument("pos_arg", type=str, nargs="?")
args = parser.parse_args()
first_arg = args.pos_arg
dev_type = args.type

if first_arg == "quit":
    quit()

use_hot_keys = "\x00use-hot-keys\x1ftrue\n"
keep_selection = "\x00keep-selection\x1ftrue\n"
prompt = f"\x00prompt\x1fSelect {'Speaker' if dev_type == 'sink' else 'Microphone'}\n"

print(f"{use_hot_keys}{prompt}{keep_selection}")


def get_device_from_desc(description):
    res = os.popen(
        f'pactl list {dev_type}s| grep -C2 "Description: {description}"|grep Name|cut -d: -f2|xargs'
    )
    return res.read().strip()


def get_desc_from_device(device):
    res = os.popen(
        f'pactl list {dev_type}s| grep -C2 {device} | grep -e "Description" | cut -d: -f2'
    )
    return res.read().strip()


if ROFI_RETV == 1:
    desc = ROFI_INFO
    device = get_device_from_desc(desc)
    os.system(f'pactl set-default-{dev_type} "{device}"')

if ROFI_RETV == 28:
    desc = ROFI_INFO
    device = get_device_from_desc(desc)
    os.system(f'pactl set-{dev_type}-volume "{device}" +{VOLUME_DELTA}%')

if ROFI_RETV == 27:
    desc = ROFI_INFO
    device = get_device_from_desc(desc)
    os.system(f'pactl set-{dev_type}-volume "{device}" -{VOLUME_DELTA}%')

if ROFI_RETV == 26:
    desc = ROFI_INFO
    device = get_device_from_desc(desc)
    os.system(f'pactl set-{dev_type}-mute "{device}" toggle')

if ROFI_RETV == 25:
    device = get_device_from_desc(ROFI_INFO)
    res = os.popen(f"pactl get-sink-volume {device}")
    line = res.read()
    volumes = line.split("/")
    left_volume = f"{volumes[1].strip()}"
    os.system(f"pactl set-sink-volume {device} {left_volume} {left_volume}")


def main():
    res = os.popen(f"pactl list {dev_type}s")
    lines = res.read()
    res = os.popen(f"pactl get-default-{dev_type}")
    def_device = res.read().strip()
    last_device_match = ""
    last_volume_match = ""
    last_mute_match = ""
    prefix = ""
    mute_icon = ""
    rofi_info = ""
    description_re = re.compile(r"\s*Description: ")
    volume_re = re.compile(r"\s*Volume: ")
    mute_re = re.compile(r"\s*Mute: ")
    for line in lines.splitlines():
        if description_re.match(line):
            last_device_match = line.split("Description: ")[1]
        elif mute_re.match(line):
            muted = line.split("Mute: ")
            if muted[1] == "yes":
                last_mute_match = "(Muted)"
                mute_icon = '\x1ficon\x1f<span color="white">ﱝ</span>'
            else:
                mute_icon = ""
                last_mute_match = ""
        # This is the last thing to be matched
        elif volume_re.match(line):
            volumes = line.split("/")
            left_volume = f"Left: {volumes[1].strip()}"
            right_volume = f"Right: {volumes[3].strip()}" if len(volumes) > 3 else ""
            last_volume_match = f"{left_volume} {right_volume}"
            rofi_info = f"\x00info\x1f{last_device_match}"
            if def_device == get_device_from_desc(last_device_match):
                prefix = "*"
            else:
                prefix = ""
            if len(last_device_match) < 40:
                dev_title = last_device_match
            else:
                dev_title = last_device_match[0:39] + "..."
            print(
                f"{prefix} {dev_title} {last_volume_match} {last_mute_match}{rofi_info}{mute_icon}".strip()
            )

if __name__ == '__main__':
  main()
