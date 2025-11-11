"""
Example: Get complete stock information

This script demonstrates how to:
1. Fetch detailed stock information
2. Retrieve all related data (fields, history, components, notes)
3. Display comprehensive stock details
"""

from API import create_client_from_env, VintraceDataFetcher
import json


def display_stock_details(stock):
    """Display formatted stock information"""
    print("\n" + "="*60)
    print(f"Stock Item: {stock.get('name', 'N/A')}")
    print("="*60)
    
    print(f"\nBasic Information:")
    print(f"  ID: {stock.get('id')}")
    print(f"  Code: {stock.get('code')}")
    print(f"  Type: {stock.get('type', {}).get('name', 'N/A')}")
    print(f"  Status: {stock.get('status')}")
    print(f"  Volume: {stock.get('volume')} {stock.get('volumeUnit', '')}")
    
    # Fields
    fields = stock.get('fields', [])
    if fields:
        print(f"\nCustom Fields ({len(fields)}):")
        for field in fields[:10]:  # Show first 10
            print(f"  - {field.get('name')}: {field.get('value')}")
        if len(fields) > 10:
            print(f"  ... and {len(fields) - 10} more")
    
    # History
    history = stock.get('history', [])
    if history:
        print(f"\nHistory Items ({len(history)}):")
        for item in history[:5]:  # Show first 5
            print(f"  - {item.get('date')}: {item.get('description')}")
        if len(history) > 5:
            print(f"  ... and {len(history) - 5} more")
    
    # Components
    components = stock.get('components', [])
    if components:
        print(f"\nRaw Components ({len(components)}):")
        for comp in components[:5]:
            print(f"  - {comp.get('name')}: {comp.get('percentage', 0):.1f}%")
        if len(components) > 5:
            print(f"  ... and {len(components) - 5} more")
    
    # Distributions
    distributions = stock.get('distributions', [])
    if distributions:
        print(f"\nDistributions ({len(distributions)}):")
        for dist in distributions[:5]:
            print(f"  - {dist.get('location')}: {dist.get('quantity')}")
        if len(distributions) > 5:
            print(f"  ... and {len(distributions) - 5} more")
    
    # Notes
    notes = stock.get('notes', [])
    if notes:
        print(f"\nNotes ({len(notes)}):")
        for note in notes[:3]:
            print(f"  - [{note.get('date')}] {note.get('text', '')[:50]}...")
        if len(notes) > 3:
            print(f"  ... and {len(notes) - 3} more")
    
    # Bulk info
    bulk_info = stock.get('bulk_info', {})
    if bulk_info:
        print(f"\nBulk Product Details:")
        print(f"  Alcohol: {bulk_info.get('alcohol')}%")
        print(f"  pH: {bulk_info.get('pH')}")
        print(f"  TA: {bulk_info.get('TA')}")


def main():
    # Get stock ID from user or use default
    import sys
    
    if len(sys.argv) > 1:
        stock_id = sys.argv[1]
    else:
        print("Usage: python example_stock_details.py <stock_id>")
        print("\nUsing example stock ID: 12345")
        stock_id = "12345"
    
    # Create client and fetcher
    print("Connecting to Vintrace API...")
    client = create_client_from_env()
    fetcher = VintraceDataFetcher(client)
    
    # Fetch complete stock details
    print(f"\nFetching complete details for stock ID: {stock_id}...")
    try:
        stock = fetcher.get_stock_details(stock_id)
        
        # Display the details
        display_stock_details(stock)
        
        # Save to JSON
        output_file = f"stock_{stock_id}_details.json"
        with open(output_file, 'w') as f:
            json.dump(stock, f, indent=2)
        print(f"\n\nFull details saved to {output_file}")
        
    except Exception as e:
        print(f"\nError fetching stock details: {e}")
        print("Please verify the stock ID and your API credentials.")


if __name__ == '__main__':
    main()
