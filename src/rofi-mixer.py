#!/bin/env python3

import os
import re
import sys
VOLUME_DELTA=5
ROFI_RETV=os.getenv("ROFI_RETV")
args = sys.argv
first_arg = args[1] if len(args) > 1 else ''
if first_arg == "quit":
    quit()
first_arg=first_arg.split(" Left:")[0]

use_hot_keys="\x00use-hot-keys\x1ftrue\n"
prompt="\x00prompt\x1fSelect Output\n"

print(f"{use_hot_keys}{prompt}")

def get_device_from_desc(description):
    res = os.popen(f'pactl list sinks| grep -C2 "Description: {description}"|grep Name|cut -d: -f2|xargs');
    return res.read().strip()

def get_desc_from_device(device):
    res = os.popen(f'pactl list sinks| grep -C2 {device} | grep -e "Description" | cut -d: -f2')
    return res.read().strip()

if ROFI_RETV == "1":
    desc=first_arg
    device=get_device_from_desc(desc)
    os.system(f'pactl set-default-sink "{device}"')

if ROFI_RETV == "28":
    desc=first_arg
    device=get_device_from_desc(desc)
    os.system(f'pactl set-sink-volume "{device}" +{VOLUME_DELTA}%')

if ROFI_RETV == "27":
    desc=first_arg
    device=get_device_from_desc(desc)
    os.system(f'pactl set-sink-volume "{device}" -{VOLUME_DELTA}%')

if ROFI_RETV == "26":
    desc=first_arg
    device=get_device_from_desc(desc)
    os.system(f'pactl set-sink-mute "{device}" toggle')



def main():
    res = os.popen("pactl list sinks")
    lines = res.read()
    last_device_match = ""
    last_volume_match = ""
    last_mute_match = ""
    muted=False
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
                muted=True
            else:
                muted=False
                last_mute_match = ""
        # This is the last thing to be matched
        elif volume_re.match(line):
            volumes = line.split("/")
            left_volume = f"Left: {volumes[1].strip()}"
            right_volume = f"Right: {volumes[3].strip()}" if len(volumes) > 2 else ""
            last_volume_match = f"{left_volume} {right_volume}"
            if muted:
                mute_icon='\x00icon\x1f<span color="white">ﱝ</span>'
            else:
                mute_icon=""
            print(f"{last_device_match} {last_volume_match} {last_mute_match}{mute_icon}".strip())

main()
