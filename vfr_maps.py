import csv
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from xml.dom import minidom
import re

dir_path = "Output"
os.makedirs(dir_path, exist_ok=True)

Ujung = False

def format_position(lat, lon):
    lat_sign = '+' if lat >= 0 else '-'
    lon_sign = '+' if lon >= 0 else '-'
    lat = abs(lat)
    lon = abs(lon)
    lat_str = f"{lat_sign}{lat:02.4f}".zfill(8)
    lon_str = f"{lon_sign}{lon:03.4f}".zfill(9)
    return f"{lat_str}{lon_str}"

def parse_lat_lon(value):
    if not value:
        return None
    direction = {'N': 1, 'E': 1, 'S': -1, 'W': -1}
    new_val = re.match(r"(\d{2,3})(\d{2})(\d{2}(\.\d{2})?)([NSEW])", value)
    if new_val is None:
        raise ValueError(f"Invalid value: {value}")
    return (int(new_val.group(1)) + int(new_val.group(2))/60 + float(new_val.group(3))/3600) * direction[new_val.group(5)]

def prettify_xml(xml_str):
    parsed = minidom.parseString(xml_str)
    lines = parsed.toprettyxml(indent="    ").split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

data = defaultdict(lambda: defaultdict(list))
with open('vfr.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data[row['Region']][row['RouteName']].append(row)

root = ET.Element('Maps')

for region, routes in data.items():
    total_lat = 0
    total_long = 0
    count = 0

    if routes:
        if Ujung: 
            map = ET.SubElement(root, 'Map', {'Type': 'System2', 'Name': f'{region.upper()}_VFR', 'Priority': '3'})
            map_names = ET.SubElement(root, 'Map', {'Type': 'System2', 'Name': f'{region.upper()}_VFR_NAMES', 'Priority': '3'})
        else: 
            map = ET.SubElement(root, 'Map', {'Type': 'System', 'Name': f'{region.upper()}_VFR', 'Priority': '3', 'CustomColourName': 'SuperGreen'})
            map_names = ET.SubElement(root, 'Map', {'Type': 'System', 'Name': f'{region.upper()}_VFR_NAMES', 'Priority': '3', 'CustomColourName': 'SuperGreen'})

        symbol = ET.SubElement(map, 'Symbol', {'Type': 'SolidTriangle'})
        label = ET.SubElement(map_names, 'Label')

        for route, points in routes.items():
            line_points = []
            for point in points:
                lat = parse_lat_lon(point['PointLat'])
                lon = parse_lat_lon(point['PointLong'])
                            
                if not lat or not lon:
                    continue

                if lat != 0 and lon != 0:
                    formatted_position = format_position(lat, lon)
                    line_points.append(formatted_position)
                    total_lat += lat
                    total_long += lon
                    count += 1

                    ET.SubElement(label, 'Point', {'Name': point['PointName']}).text = formatted_position

            if line_points:
                ET.SubElement(map, 'Line').text = "/".join(line_points)

                for point in line_points:
                    ET.SubElement(symbol, 'Point').text = point

        if count > 0:
            center_lat = total_lat / count
            center_long = total_long / count
            center = format_position(center_lat, center_long)
            map.set('Center', center)
            map_names.set('Center', center)
        else:
            root.remove(map)
            root.remove(map_names)

xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')

formatted_xml_str = prettify_xml(xml_str)

with open(os.path.join(dir_path, 'VFR.xml'), 'w') as f:
    f.write(formatted_xml_str)