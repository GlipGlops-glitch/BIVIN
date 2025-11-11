#python tools/vintrace_analysis_process.py
#!/usr/bin/env python3
"""
CSV to JSON Converter
Converts CSV to JSON keeping only the most recent metric values
"""

import csv
import json
from pathlib import Path
from datetime import datetime


def convert_value(value):
    """
    Convert string values to appropriate types (int, float, bool)
    
    Args:
        value: String value to convert
        
    Returns:
        Converted value or original string
    """
    if value == '':
        return None
        
    # Try to convert to number
    try:
        # Try int first
        if '.' not in value:
            return int(value)
        else:
            return float(value)
    except ValueError:
        # Try boolean
        if value.lower() in ('true', 'yes'):
            return True
        elif value.lower() in ('false', 'no'):
            return False
        else:
            # Keep as string
            return value


def parse_date(date_string):
    """
    Parse date string to datetime object for comparison
    
    Args:
        date_string: Date string to parse
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_string:
        return None
    
    # Try common date formats
    formats = [
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%m/%d/%Y',
        '%Y-%m-%d'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    return None


def is_metric_field(field_name):
    """
    Determine if a field is a metric (measurement) field
    
    Args:
        field_name: Name of the field
        
    Returns:
        True if field is a metric, False otherwise
    """
    # Fields that are NOT metrics (identity/metadata fields)
    non_metric_fields = [
        'date', 'batch', 'description', 'vessel', 'owner', 
        'laboratory', 'analysis template', 'winery'
    ]
    
    return field_name.lower() not in non_metric_fields


def csv_to_json(csv_file_path, json_file_path):
    """
    Convert CSV file to JSON format keeping only most recent metric values
    
    Args:
        csv_file_path: Path to input CSV file
        json_file_path: Path to output JSON file
    """
    records_dict = {}
    total_rows_read = 0
    
    # Read CSV file
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            # Read all lines first to check the file
            lines = csv_file.readlines()
            
            if len(lines) == 0:
                print(f"✗ Error: CSV file is empty")
                return
            
            print(f"📋 CSV file has {len(lines)} total lines (including header)")
            
            # Reset file pointer to beginning
            csv_file.seek(0)
            
            # Now use DictReader which will use first line as headers
            csv_reader = csv.DictReader(csv_file)
            
            # Get the headers
            headers = csv_reader.fieldnames
            print(f"📋 Column headers detected: {headers}")
            
            for row in csv_reader:
                total_rows_read += 1
                
                # Get the key fields
                batch = row.get('Batch', '').strip()
                vessel = row.get('Vessel', '').strip()
                winery = row.get('Winery', '').strip()
                date_str = row.get('Date', '').strip()
                
                # Skip rows without a batch (can't group them)
                if not batch:
                    continue
                
                # Parse the date
                date_obj = parse_date(date_str)
                
                # Create a unique key for this batch/vessel/winery combination
                record_key = (batch, vessel, winery)
                
                # Initialize record if it doesn't exist
                if record_key not in records_dict:
                    records_dict[record_key] = {
                        'Batch': batch,
                        'Vessel': vessel,
                        'Winery': winery,
                        'metrics': {}
                    }
                
                # Process each metric field
                for field_name, value in row.items():
                    if is_metric_field(field_name):
                        converted_value = convert_value(value)
                        if converted_value is not None:
                            # Check if we already have this metric
                            if field_name in records_dict[record_key]['metrics']:
                                # Compare dates and keep the most recent
                                existing_date = parse_date(records_dict[record_key]['metrics'][field_name]['date'])
                                
                                if date_obj and existing_date:
                                    if date_obj > existing_date:
                                        records_dict[record_key]['metrics'][field_name] = {
                                            'value': converted_value,
                                            'date': date_str
                                        }
                                elif date_obj:  # New date is valid, existing is not
                                    records_dict[record_key]['metrics'][field_name] = {
                                        'value': converted_value,
                                        'date': date_str
                                    }
                            else:
                                # First time seeing this metric
                                records_dict[record_key]['metrics'][field_name] = {
                                    'value': converted_value,
                                    'date': date_str
                                }
        
        print(f"✓ Successfully read {total_rows_read} data rows from {csv_file_path}")
        print(f"✓ Note: First row was used as header row (this is expected CSV behavior)")
        
    except FileNotFoundError:
        print(f"✗ Error: File '{csv_file_path}' not found.")
        return
    except Exception as e:
        print(f"✗ Error reading CSV file: {e}")
        return
    
    # Convert metrics from nested dict to flat structure (all in one object)
    data = []
    for record in records_dict.values():
        flat_record = {
            'Batch': record['Batch'],
            'Vessel': record['Vessel'],
            'Winery': record['Winery'],
            'metrics': {}
        }
        
        # Combine all metrics into a single object
        for metric_name, metric_data in record['metrics'].items():
            flat_record['metrics'][metric_name] = metric_data['value']
            flat_record['metrics'][f"{metric_name} - Date"] = metric_data['date']
        
        data.append(flat_record)
    
    # Create dummy record with all possible fields
    all_metric_fields = set()
    for record in records_dict.values():
        for metric_name in record['metrics'].keys():
            all_metric_fields.add(metric_name)
    
    dummy_metrics = {}
    for field in sorted(all_metric_fields):
        dummy_metrics[field] = 0.0
        dummy_metrics[f"{field} - Date"] = "1900-01-01 00:00"
    
    dummy_record = {
        'Batch': 'DUMMY',
        'Vessel': 'DUMMY',
        'Winery': 'DUMMY',
        'metrics': dummy_metrics
    }
    
    # Insert dummy record at the beginning
    data.insert(0, dummy_record)
    print(f"✓ Added dummy record with all fields for Power BI compatibility")
    
    # Create output directory if it doesn't exist
    output_path = Path(json_file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON file
    try:
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=2, ensure_ascii=False)
        
        print(f"✓ Successfully wrote JSON to {json_file_path}")
        print(f"✓ Total unique batch/vessel/winery combinations: {len(data) - 1}")
        total_metrics = sum(len([k for k in record['metrics'].keys() if not k.endswith(' - Date')]) for record in data)
        print(f"✓ Total unique metrics tracked: {total_metrics // len(data) if data else 0}")
        
    except Exception as e:
        print(f"✗ Error writing JSON file: {e}")


if __name__ == '__main__':
    # Input and output file paths
    INPUT_CSV = 'Main/data/vintrace_reports/analysis/Vintrace_analysis_export.csv'
    OUTPUT_JSON = 'Main/data/vintrace_reports/analysis/analysis.json'
    
    # Convert the file
    csv_to_json(INPUT_CSV, OUTPUT_JSON)