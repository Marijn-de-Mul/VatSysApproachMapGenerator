import os
import xml.etree.ElementTree as ET
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--icao', type=str, required=True, help='4 letter ICAO code')
args = parser.parse_args()

icao = args.icao.upper()

dir_path = "Output"
os.makedirs(dir_path, exist_ok=True)

with open('Navdata/Airports.txt', 'r') as f:
    lines = f.readlines()

def format_position(lat, lon):
    lat_sign = '+' if lat >= 0 else '-'
    lon_sign = '+' if lon >= 0 else '-'
    lat = abs(lat)
    lon = abs(lon)
    lat_str = f"{lat_sign}{lat:02.4f}".zfill(8)
    lon_str = f"{lon_sign}{lon:03.4f}".zfill(9)
    return f"{lat_str}{lon_str}"

for i, line in enumerate(lines):
    line_parts = line.split(',')
    if line_parts[0] == 'A' and line_parts[1] == icao:
        lat, lon = map(float, line_parts[3:5])
        airport_coords = format_position(lat, lon)
        runway_lines = []
        unique_runway_numbers = set()
        for j in range(i+1, len(lines)):
            if lines[j].startswith('R,'):
                runway_lines.append(lines[j])
                runway_number = lines[j].split(',')[1].rstrip('LRC')
                unique_runway_numbers.add(runway_number)
            else:
                break

        for runway_number in unique_runway_numbers:
            file_path = os.path.join(dir_path, f"{icao}_RW{runway_number}.xml")

            if os.path.exists(file_path):
                os.remove(file_path)

            root = ET.Element("Maps")
            map_elem = ET.SubElement(root, "Map")
            map_elem.set("Type", "System")
            map_elem.set("Name", f"{icao}_RW{runway_number}")
            map_elem.set("Priority", "3")
            map_elem.set("Center", airport_coords)

            runway_elem = ET.SubElement(map_elem, "Runway")
            runway_elem.set("Name", runway_number)

            for r_line in runway_lines:
                r_number = r_line.split(',')[1]
                lat, lon = map(float, r_line.split(',')[8:10])
                r_coords = format_position(lat, lon)

                threshold_elem = ET.SubElement(runway_elem, "Threshold")
                threshold_elem.set("Name", r_number)
                threshold_elem.set("Position", r_coords)

                if r_number.rstrip('LRC') == runway_number:
                    threshold_elem.set("ExtendedCentrelineTrack", "245.38")
                    threshold_elem.set("ExtendedCentrelineLength", "12")
                    threshold_elem.set("ExtendedCentrelineTickInterval", "1")

            # Parse SIDs
            with open(f'Navdata/Proc/{icao}.txt', 'r') as f:
                sid_lines = f.readlines()

            # Create a set to store waypoints that have already been added
            added_waypoints = set()

            for sid_line in sid_lines:
                sid_parts = sid_line.split(',')
                if sid_parts[0] == 'SID' and sid_parts[2].rstrip('LRC') == runway_number:
                    sid_name = sid_parts[1]
                    comment = ET.Comment(f'SID: {sid_name}, Runway: {runway_number}')
                    map_elem.append(comment)  # Add the comment to the 'Map' element
                    line_elem = ET.SubElement(map_elem, "Line")
                    line_elem.set("Pattern", "Dotted")
                    line_elem.text = ''  # Initialize line_elem.text to an empty string

                    waypoints = sid_lines[sid_lines.index(sid_line)+1:]
                    for waypoint in waypoints:
                        if waypoint.startswith('SID'):  # Stop when we reach the next 'SID' line
                            break
                        if waypoint.startswith(('VA', 'DF', 'TF', 'CF')):  # Only add the line as a waypoint if it starts with a waypoint code
                            waypoint_parts = waypoint.split(',')
                            waypoint_name = waypoint_parts[1]  # The waypoint name is the first item in the line
                            line_elem.text += waypoint_name + '/'

                    # Remove the trailing '/' from the last waypoint
                    if line_elem.text.endswith('/'):
                        line_elem.text = line_elem.text[:-1]
                                
            tree = ET.ElementTree(root)
            ET.indent(root, space="    ")

            with open(file_path, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
                tree.write(f, encoding='utf-8')

        break