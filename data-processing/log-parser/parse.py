#!/usr/bin/env python3
import sys
import csv
import os
import struct
import argparse
from datetime import datetime
from log_schema import SCHEMAS, ENUM_SIZE, parse_block, field_names, field_values

def main():
    parser = argparse.ArgumentParser(description='Parse uORB binary log files')
    parser.add_argument('log_file', help='Path to the binary log file')
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "parsed", timestamp)
    os.makedirs(output_dir, exist_ok=True)

    with open(args.log_file, 'rb') as f:
        data = f.read()

    outputs = {t: [] for t in SCHEMAS}
    offset = 0
    count = 0

    while offset < len(data):
        try:
            sensor_type = struct.unpack('<B', data[offset:offset+1])[0]
            if sensor_type not in SCHEMAS:
                raise ValueError(f"Unknown sensor type: {sensor_type}")

            name, cls = SCHEMAS[sensor_type]
            total_size = ENUM_SIZE + cls.SIZE

            if offset + total_size > len(data):
                print(f"Incomplete packet at offset {offset}, expected {total_size} bytes, only {len(data) - offset} remaining")
                break

            sensor_type, parsed = parse_block(data[offset:offset+total_size])
            count += 1
            outputs[sensor_type].append([count, sensor_type, name] + field_values(parsed))
            offset += total_size
        except Exception as e:
            print(f"Error at offset {offset}: {e}")
            break

    for sensor_type, rows in outputs.items():
        if not rows:
            continue
        name, cls = SCHEMAS[sensor_type]
        path = os.path.join(output_dir, f"{name}.csv")
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["packet_num", "type", "type_name"] + field_names(cls))
            writer.writerows(rows)

    print(f"\nTotal packets parsed: {count}", file=sys.stderr)
    print(f"CSV files saved to: {output_dir}", file=sys.stderr)

if __name__ == "__main__":
    main()
