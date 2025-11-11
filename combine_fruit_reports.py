"""
Combine Fruit Reports into JSON
Reads all CSV files from the fruit_reports directory and combines them into a single JSON file

This script:
1. Reads all CSV files from Main/data/vintrace_reports/fruit_reports/
2. Processes each CSV file
3. Combines all data into a single JSON structure
4. Saves to Main/data/vintrace_reports/analysis/combined_fruit_reports.json

Expected CSV Headers:
- Type
- Weigh tag #
- Vintage
- Variety
- Sub AVA
- Micro AVA
- Block
- Delivery Date
- Percent
- Relative Volume

Usage: python combine_fruit_reports.py

Author: GlipGlops-glitch
Created: 2025-01-11
"""
import os
import json
import pandas as pd
import glob
from datetime import datetime

# Input directory with fruit report CSVs
FRUIT_REPORTS_DIR = "Main/data/vintrace_reports/fruit_reports/"

# Output JSON file
OUTPUT_JSON_PATH = "Main/data/vintrace_reports/analysis/combined_fruit_reports.json"

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)


def process_fruit_reports():
    """
    Process all fruit report CSV files and combine them into a single JSON file
    
    Returns:
        dict: Combined data structure with all vessel fruit reports
    """
    print("\n" + "=" * 60)
    print("COMBINING FRUIT REPORTS")
    print("=" * 60)
    
    # Find all CSV files in the fruit reports directory
    csv_files = glob.glob(os.path.join(FRUIT_REPORTS_DIR, "*.csv"))
    
    if not csv_files:
        print(f"⚠️  No CSV files found in {FRUIT_REPORTS_DIR}")
        return None
    
    print(f"✓ Found {len(csv_files)} CSV file(s) to process")
    
    # Combined data structure
    combined_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_vessels": len(csv_files),
            "total_records": 0
        },
        "vessels": {}
    }
    
    # Process each CSV file
    total_records = 0
    successful_files = 0
    failed_files = []
    
    for csv_file in csv_files:
        # Extract vessel name from filename
        vessel_name = os.path.splitext(os.path.basename(csv_file))[0]
        
        print(f"\n📄 Processing: {vessel_name}")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Check if DataFrame is empty
            if df.empty:
                print(f"  ⚠️  Empty CSV file, skipping")
                failed_files.append((vessel_name, "Empty file"))
                continue
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')
            
            # Clean up NaN values (convert to None for JSON serialization)
            records = [
                {k: (None if pd.isna(v) else v) for k, v in record.items()}
                for record in records
            ]
            
            # Add to combined data
            combined_data["vessels"][vessel_name] = {
                "vessel_name": vessel_name,
                "record_count": len(records),
                "fruit_data": records
            }
            
            total_records += len(records)
            successful_files += 1
            print(f"  ✓ Processed {len(records)} record(s)")
            
        except Exception as e:
            print(f"  ❌ Error processing file: {e}")
            failed_files.append((vessel_name, str(e)))
    
    # Update metadata
    combined_data["metadata"]["total_records"] = total_records
    combined_data["metadata"]["successful_vessels"] = successful_files
    combined_data["metadata"]["failed_vessels"] = len(failed_files)
    
    # Print summary
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total CSV files: {len(csv_files)}")
    print(f"Successfully processed: {successful_files}")
    print(f"Failed: {len(failed_files)}")
    print(f"Total records: {total_records}")
    
    if failed_files:
        print("\nFailed files:")
        for vessel_name, error in failed_files:
            print(f"  ❌ {vessel_name}: {error}")
    
    print("=" * 60)
    
    return combined_data


def save_combined_json(data):
    """
    Save the combined data to JSON file
    
    Args:
        data: Combined data structure
    """
    if not data:
        print("❌ No data to save")
        return False
    
    try:
        with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Successfully saved combined data to: {OUTPUT_JSON_PATH}")
        
        # Print file size
        file_size = os.path.getsize(OUTPUT_JSON_PATH)
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.2f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.2f} MB"
        
        print(f"  File size: {size_str}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving JSON file: {e}")
        return False


def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("FRUIT REPORT COMBINER")
    print("=" * 60)
    
    # Check if input directory exists
    if not os.path.exists(FRUIT_REPORTS_DIR):
        print(f"❌ ERROR: Input directory does not exist: {FRUIT_REPORTS_DIR}")
        return
    
    # Process fruit reports
    combined_data = process_fruit_reports()
    
    if not combined_data:
        print("\n❌ No data was processed")
        return
    
    # Save to JSON
    success = save_combined_json(combined_data)
    
    if success:
        print("\n" + "=" * 60)
        print("✓ ALL OPERATIONS COMPLETED SUCCESSFULLY")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ OPERATION FAILED")
        print("=" * 60)


if __name__ == "__main__":
    main()
