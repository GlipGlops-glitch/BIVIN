"""
Example: Export all products to CSV

This script demonstrates how to:
1. Fetch all products using pagination
2. Export to CSV format
3. Include relevant product details
"""

from API import create_client_from_env
import csv
from datetime import datetime


def main():
    # Create client
    print("Connecting to Vintrace API...")
    client = create_client_from_env()
    
    # Fetch all products (handles pagination automatically)
    print("Fetching all products (this may take a moment)...")
    products = client.get_all_pages(client.list_available_products)
    
    print(f"\nFetched {len(products)} products")
    
    if not products:
        print("No products found!")
        return
    
    # Prepare CSV output
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"vintrace_products_{timestamp}.csv"
    
    # Define fields to export
    fields = [
        'id', 'name', 'description', 'status', 'vintage', 
        'variety', 'region', 'volume', 'alcoholLevel',
        'createdDate', 'modifiedDate'
    ]
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        
        for product in products:
            # Flatten nested objects if needed
            row = {}
            for field in fields:
                value = product.get(field)
                # Handle nested objects
                if isinstance(value, dict):
                    value = value.get('name') or value.get('id') or str(value)
                row[field] = value
            writer.writerow(row)
    
    print(f"\nProducts exported to {output_file}")
    
    # Print sample
    print("\nFirst 5 products:")
    for i, product in enumerate(products[:5], 1):
        print(f"{i}. {product.get('name', 'N/A')} - {product.get('status', 'N/A')}")


if __name__ == '__main__':
    main()
