# python tools/vintrace_grape_report_detail.py
import re
import os
import json
import pandas as pd
import io
import numpy as np

BOOKING_COLS = [
    "booking_id",
    "booking_row_id",  # <-- new unique PK field
    "Received on", "Delivered (t)", "Crushed (t)", "Volume (gal)",
    "Extraction Type", "Vessel", "Batch", "Yield (gal/tn)"
]
DELIVERY_COLS = [
    "Date Entered", "Marshalled", "Sampled", "Weighed In", "Weighed Out", "Winery", "Weigh tag #",
    "Booking #", "Booking Reference #", "Last Booking for Block", "Last Load for Booking",
    "Ownership", "Variety", "Net (tn)", "Gross (tn)", "Tare (tn)", "MOG Weight (tn)",
    "Received area", "No. of Bins", "Bin Description", "Grower", "Vineyard", "Block",
    "Block Expected Yield (tn)", "Sub AVA", "Hand/Machine", "MOG", "Grading", "($/tn)",
    "($/Area)", "Fruit cost", "Freight cost", "Contract", "Contract Amount(tn)", "Crushed",
    "Extracted (gal)", "Ex. Rate (Gallons per ton)", "Scales", "Carrier", "Shipping reference",
    "Truck No.", "Driver name", "Harvester", "Volume (gal)", "booking_id"  # <-- Included "Volume (gal)"
]

def clean_line(line):
    """Remove extra quotes and whitespace."""
    return line.strip().strip('"').replace('""', '"')

def parse_summary_lines(header, lines, booking_id):
    rows = []
    prev = [None] * len(header)
    for line in lines:
        line = clean_line(line)
        # Handle possible empty lines
        if not line or line.startswith("#"):
            continue
        cells = [cell.strip() for cell in line.split(',')[:8]]
        cells += [None] * (8 - len(cells))
        filled = [cells[i] if cells[i] not in ("", None) else prev[i] for i in range(8)]
        prev = [filled[i] if filled[i] not in ("", None) else prev[i] for i in range(8)]
        if any(filled):
            row_dict = dict(zip(BOOKING_COLS[2:], filled))
            row_dict["booking_id"] = booking_id
            rows.append(row_dict)
    return rows

def parse_and_save_tables(file_path, bookings_path, deliveries_path):
    os.makedirs(os.path.dirname(bookings_path), exist_ok=True)
    os.makedirs(os.path.dirname(deliveries_path), exist_ok=True)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    bookings_table = []
    deliveries_table = []

    # Split on summary markers, supporting both old and new CSV formats
    bookings = re.split(r'(?:^|\n)[\"\']?# Summary for Booking #', content)
    for booking in bookings[1:]:
        # Fix up missing marker after split
        booking = '# Summary for Booking #' + booking if not booking.startswith("#") else booking

        booking_id_match = re.search(r'# Summary for Booking #\s*([^\n,"]+)', booking)
        booking_id = booking_id_match.group(1).strip() if booking_id_match else 'unknown'

        # Find summary header (robust to quotes)
        summary_header_match = re.search(
            r'Received on,Delivered \(t\),Crushed \(t\),Volume \(gal\),Extraction Type,Vessel,Batch,Yield \(gal/tn\)', booking
        )
        if not summary_header_match:
            continue
        summary_header = [
            "Received on", "Delivered (t)", "Crushed (t)", "Volume (gal)",
            "Extraction Type", "Vessel", "Batch", "Yield (gal/tn)"
        ]
        start = summary_header_match.start()
        after_header = booking[start:]
        summary_lines = []
        for line in after_header.splitlines()[1:]:
            sline = clean_line(line)
            if sline.lower().startswith("delivery details"):
                break
            if sline and not sline.startswith("#") and not sline.lower().startswith("received on"):
                summary_lines.append(sline)

        booking_rows = parse_summary_lines(summary_header, summary_lines, booking_id)
        for idx, row in enumerate(booking_rows, 1):
            row["booking_row_id"] = f"{booking_id}_{idx}"
            full_row = {col: row.get(col) for col in BOOKING_COLS}
            bookings_table.append(full_row)

        # Capture the Volume (gal) value(s) for this booking
        # Use the first non-empty value, or None
        volume_gal = None
        for b_row in booking_rows:
            if b_row.get("Volume (gal)") not in [None, ""]:
                volume_gal = b_row["Volume (gal)"]
                break

        # Delivery details (robust to format)
        delivery_match = re.search(
            r'Delivery details:.*?\n(.*?)(?=\n(?:$|#|\")|\Z)', booking, re.DOTALL | re.IGNORECASE
        )
        if delivery_match:
            delivery_csv = delivery_match.group(1)
            delivery_lines = [clean_line(line) for line in delivery_csv.splitlines() if clean_line(line)]
            if delivery_lines:
                delivery_header = delivery_lines[0]
                delivery_rows = delivery_lines[1:]
                delivery_data = delivery_header + '\n' + '\n'.join(delivery_rows)
                try:
                    df = pd.read_csv(io.StringIO(delivery_data))
                    df['booking_id'] = booking_id
                    # Set the Volume (gal) column, using the value from the booking
                    df['Volume (gal)'] = volume_gal
                    df = df.replace([np.nan, np.inf, -np.inf], None)
                    # Ensure all DELIVERY_COLS (including "Volume (gal)") are present
                    for col in DELIVERY_COLS:
                        if col not in df.columns:
                            df[col] = None
                    df = df[DELIVERY_COLS]
                    deliveries_table.extend(df.to_dict(orient='records'))
                except Exception as exc:
                    print(f"Delivery parse error for {booking_id}: {exc}")

    with open(bookings_path, 'w', encoding='utf-8') as f:
        json.dump(bookings_table, f, indent=2, allow_nan=False)
    with open(deliveries_path, 'w', encoding='utf-8') as f:
        json.dump(deliveries_table, f, indent=2, allow_nan=False)

if __name__ == '__main__':
    file_path = 'Main/data/vintrace_reports/grape_detailz.csv'
    bookings_path = 'Main/data/vintrace_reports/vintrace_grape_bookings.json'
    deliveries_path = 'Main/data/vintrace_reports/vintrace_grape_deliveries.json'
    parse_and_save_tables(file_path, bookings_path, deliveries_path)