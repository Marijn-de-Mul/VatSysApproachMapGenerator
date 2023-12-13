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

for i, line in enumerate(lines):
    line_parts = line.split(',')
    if line_parts[0] == 'A' and line_parts[1] == icao:
        airport_coords = line_parts[3:5]
        airport_coords = '+'.join(airport_coords)
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
                r_coords = r_line.split(',')[8:10]
                r_coords = '+'.join(r_coords)

                threshold_elem = ET.SubElement(runway_elem, "Threshold")
                threshold_elem.set("Name", r_number)
                threshold_elem.set("Position", r_coords)

                if r_number.rstrip('LRC') == runway_number:
                    threshold_elem.set("ExtendedCentrelineTrack", "245.38")
                    threshold_elem.set("ExtendedCentrelineLength", "12")
                    threshold_elem.set("ExtendedCentrelineTickInterval", "1")

            tree = ET.ElementTree(root)
            ET.indent(root, space="    ")

            with open(file_path, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
                tree.write(f, encoding='utf-8')

        break