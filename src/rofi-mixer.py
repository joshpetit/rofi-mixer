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
    choices=["sink", "source", "app"],
    default="sink",
    help="'sink' for speakers, 'source' for microphones, 'app' for applications",
)
parser.add_argument("pos_arg", type=str, nargs="?")
args = parser.parse_args()
first_arg = args.pos_arg
dev_type = args.type

if first_arg == "quit":
    quit()

use_hot_keys = "\x00use-hot-keys\x1ftrue\n"
keep_selection = "\x00keep-selection\x1ftrue\n"

if dev_type == "app":
    prompt = "\x00prompt\x1fSelect Application\n"
else:
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

def get_sink_input_from_app_name(app_name):
    res = os.popen(
        f'pactl list sink-inputs | grep -B20 "application.name = \\"{app_name}\\"" | grep "Sink Input" | cut -d "#" -f2 | xargs'
    )
    return res.read().strip()

if ROFI_RETV == 1:
    if dev_type == "app":
        app_name, sink_input = ROFI_INFO.split("||")
        # Nothing to do on selection for apps, just return to main view
    else:
        desc = ROFI_INFO
        device = get_device_from_desc(desc)
        os.system(f'pactl set-default-{dev_type} "{device}"')

if ROFI_RETV == 28:
    if dev_type == "app":
        app_name, sink_input = ROFI_INFO.split("||")
        os.system(f"pactl set-sink-input-volume {sink_input} +{VOLUME_DELTA}%")
    else:
        desc = ROFI_INFO
        device = get_device_from_desc(desc)
        os.system(f'pactl set-{dev_type}-volume "{device}" +{VOLUME_DELTA}%')

if ROFI_RETV == 27:
    if dev_type == "app":
        app_name, sink_input = ROFI_INFO.split("||")
        os.system(f"pactl set-sink-input-volume {sink_input} -{VOLUME_DELTA}%")
    else:
        desc = ROFI_INFO
        device = get_device_from_desc(desc)
        os.system(f'pactl set-{dev_type}-volume "{device}" -{VOLUME_DELTA}%')

if ROFI_RETV == 26:
    if dev_type == "app":
        app_name, sink_input = ROFI_INFO.split("||")
        os.system(f"pactl set-sink-input-mute {sink_input} toggle")
    else:
        desc = ROFI_INFO
        device = get_device_from_desc(desc)
        os.system(f'pactl set-{dev_type}-mute "{device}" toggle')

if ROFI_RETV == 25:
    if dev_type != "app":
        device = get_device_from_desc(ROFI_INFO)
        res = os.popen(f"pactl get-sink-volume {device}")
        line = res.read()
        volumes = line.split("/")
        left_volume = f"{volumes[1].strip()}"
        os.system(f"pactl set-sink-volume {device} {left_volume} {left_volume}")

def create_volume_bar(volume_percent):
    """Create a visual representation of volume level using Unicode block characters."""
    try:
        if "%" in volume_percent:
            volume_value = int(volume_percent.strip().rstrip("%"))
        else:
            volume_value = int(volume_percent.strip())
    except (ValueError, TypeError):
        volume_value = 0
    

    volume_value = max(0, min(100, volume_value))
    

    bar_length = 10
    filled_segments = int(round(volume_value / 100 * bar_length))
    

    filled = "▓"  
    empty = "░"   
    
    bar = filled * filled_segments + empty * (bar_length - filled_segments)
    
    return f"[{bar}] {volume_value}%"

def list_sinks_sources():
    res = os.popen(f"pactl list {dev_type}s")
    lines = res.read()
    res = os.popen(f"pactl get-default-{dev_type}")
    def_device = res.read().strip()
    
    last_device_match = ""
    last_volume_match = ""
    last_volume_percent = ""
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

        elif volume_re.match(line):
            volumes = line.split("/")
            volume_percent_match = re.search(r"(\d+)%", volumes[1])
            if volume_percent_match:
                last_volume_percent = volume_percent_match.group(1)
            
            volume_bar = create_volume_bar(last_volume_percent)
            last_volume_match = volume_bar
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

def list_applications():
    res = os.popen("pactl list sink-inputs")
    lines = res.read()
    
    app_name = ""
    app_volume = ""
    app_volume_percent = ""
    app_muted = ""
    sink_input = ""
    mute_icon = ""
    
    sink_input_re = re.compile(r"Sink Input #(\d+)")
    volume_re = re.compile(r"\s*Volume: ")
    mute_re = re.compile(r"\s*Mute: ")
    app_name_re = re.compile(r'\s*application\.name = "(.*)"')
    
    for line in lines.splitlines():
        sink_input_match = sink_input_re.match(line)
        if sink_input_match:
            if app_name and sink_input:
                rofi_info = f"\x00info\x1f{app_name}||{sink_input}"
                
                volume_bar = create_volume_bar(app_volume_percent)
                
                if len(app_name) < 40:
                    app_title = app_name
                else:
                    app_title = app_name[0:39] + "..."
                    
                print(f"{app_title} {volume_bar} {app_muted}{rofi_info}{mute_icon}".strip())
            
            sink_input = sink_input_match.group(1)
            app_name = ""
            app_volume = ""
            app_volume_percent = ""
            app_muted = ""
            mute_icon = ""
            
        elif volume_re.match(line):
            volumes = line.split("/")
            volume_percent_match = re.search(r"(\d+)%", volumes[1])
            if volume_percent_match:
                app_volume_percent = volume_percent_match.group(1)
            
            left_volume = f"{volumes[1].strip()}"
            right_volume = f"{volumes[3].strip()}" if len(volumes) > 3 else ""
            app_volume = f"{left_volume} {right_volume}"
            
        elif mute_re.match(line):
            muted = line.split("Mute: ")
            if muted[1] == "yes":
                app_muted = "(Muted)"
                mute_icon = '\x1ficon\x1f<span color="white">ﱝ</span>'
            else:
                app_muted = ""
                mute_icon = ""
                
        elif app_name_re.match(line):
            app_name = app_name_re.match(line).group(1)
    
    if app_name and sink_input:
        rofi_info = f"\x00info\x1f{app_name}||{sink_input}"
        
        volume_bar = create_volume_bar(app_volume_percent)
        
        if len(app_name) < 40:
            app_title = app_name
        else:
            app_title = app_name[0:39] + "..."
            
        print(f"{app_title} {volume_bar} {app_muted}{rofi_info}{mute_icon}".strip())

def main():
    if dev_type == "app":
        list_applications()
    else:
        list_sinks_sources()

if __name__ == '__main__':
    main()

