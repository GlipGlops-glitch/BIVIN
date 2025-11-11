"""
Example: Comprehensive data export

This script demonstrates how to:
1. Fetch multiple data types from Vintrace
2. Export everything to organized JSON files
3. Generate a summary report
"""

from API import create_client_from_env, VintraceDataFetcher
from datetime import datetime
import json
import os


def safe_fetch(func, name, *args, **kwargs):
    """Safely fetch data with error handling"""
    try:
        print(f"  Fetching {name}...")
        data = func(*args, **kwargs)
        count = len(data) if isinstance(data, list) else 1
        print(f"    ✓ {count} items")
        return data
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return []


def main():
    # Create output directory
    output_dir = f"vintrace_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Vintrace Data Export")
    print(f"Output directory: {output_dir}\n")
    
    # Create client and fetcher
    print("Connecting to Vintrace API...")
    client = create_client_from_env()
    fetcher = VintraceDataFetcher(client)
    
    # Fetch all data types
    print("\nFetching data...")
    
    data = {
        'work_orders': safe_fetch(fetcher.get_all_work_orders, "Work Orders"),
        'products': safe_fetch(fetcher.get_all_products, "Products"),
        'sales_orders': safe_fetch(fetcher.get_all_sales_orders, "Sales Orders"),
        'parties': safe_fetch(fetcher.get_all_parties, "Parties"),
        'refunds': safe_fetch(fetcher.get_all_refunds, "Refunds"),
        'recent_work_orders': safe_fetch(fetcher.get_recent_work_orders, "Recent Work Orders (7 days)", days=7),
        'inventory': safe_fetch(fetcher.get_inventory_summary, "Inventory Summary"),
    }
    
    # Save each data type to separate file
    print("\nSaving data...")
    for data_type, items in data.items():
        if items:
            filename = os.path.join(output_dir, f"{data_type}.json")
            with open(filename, 'w') as f:
                json.dump(items, f, indent=2)
            print(f"  ✓ {filename}")
    
    # Generate summary report
    print("\nGenerating summary report...")
    summary = {
        'export_date': datetime.now().isoformat(),
        'data_types': {},
        'totals': {}
    }
    
    for data_type, items in data.items():
        count = len(items) if isinstance(items, list) else (1 if items else 0)
        summary['data_types'][data_type] = count
    
    summary['totals']['total_items'] = sum(summary['data_types'].values())
    
    # Save summary
    summary_file = os.path.join(output_dir, 'summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("Export Summary")
    print("="*60)
    for data_type, count in summary['data_types'].items():
        print(f"{data_type:25} : {count:6} items")
    print("-"*60)
    print(f"{'TOTAL':25} : {summary['totals']['total_items']:6} items")
    print("="*60)
    
    print(f"\n✓ Export complete! All files saved to: {output_dir}")


if __name__ == '__main__':
    main()
