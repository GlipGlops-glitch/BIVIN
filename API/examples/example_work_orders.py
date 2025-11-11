"""
Example: Fetch all work orders from the last 7 days

This script demonstrates how to:
1. Connect to the Vintrace API
2. Fetch work orders with date filters
3. Process and display the results
"""

from API import create_client_from_env, VintraceDataFetcher
from datetime import datetime, timedelta
import json


def main():
    # Create client from environment variables
    print("Connecting to Vintrace API...")
    client = create_client_from_env()
    
    # Create data fetcher helper
    fetcher = VintraceDataFetcher(client)
    
    # Get work orders from last 7 days
    print("\nFetching work orders from last 7 days...")
    work_orders = fetcher.get_recent_work_orders(days=7)
    
    print(f"\nFound {len(work_orders)} work orders\n")
    
    # Display summary
    status_counts = {}
    for wo in work_orders:
        status = wo.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"Work Order: {wo.get('name', 'N/A')}")
        print(f"  Status: {status}")
        print(f"  Scheduled: {wo.get('scheduledDate', 'N/A')}")
        print(f"  Assigned to: {wo.get('assignedToName', 'Unassigned')}")
        print()
    
    # Print summary statistics
    print("\n" + "="*50)
    print("Summary by Status:")
    print("="*50)
    for status, count in sorted(status_counts.items()):
        print(f"{status}: {count}")
    
    # Optional: Save to JSON file
    output_file = "work_orders_export.json"
    with open(output_file, 'w') as f:
        json.dump(work_orders, f, indent=2)
    print(f"\nFull data saved to {output_file}")


if __name__ == '__main__':
    main()
