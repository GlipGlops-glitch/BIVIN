"""
Example: Search and analyze transactions

This script demonstrates how to:
1. Search for transactions in a date range
2. Filter by transaction type
3. Analyze and summarize the results
"""

from API import create_client_from_env, VintraceDataFetcher
from datetime import datetime, timedelta
from collections import defaultdict


def analyze_transactions(transactions):
    """Analyze and summarize transaction data"""
    
    # Group by type
    by_type = defaultdict(list)
    total_volume = 0
    
    for trans in transactions:
        trans_type = trans.get('type', 'Unknown')
        by_type[trans_type].append(trans)
        
        # Sum volumes if available
        volume = trans.get('volume', 0)
        if isinstance(volume, (int, float)):
            total_volume += volume
    
    # Print summary
    print("\n" + "="*60)
    print("Transaction Summary")
    print("="*60)
    
    print(f"\nTotal Transactions: {len(transactions)}")
    print(f"Total Volume: {total_volume:,.2f}L")
    
    print(f"\nBreakdown by Type:")
    for trans_type, items in sorted(by_type.items()):
        type_volume = sum(t.get('volume', 0) for t in items if isinstance(t.get('volume'), (int, float)))
        print(f"  {trans_type}: {len(items)} transactions, {type_volume:,.2f}L")
    
    # Show recent transactions
    print(f"\nMost Recent Transactions:")
    sorted_trans = sorted(
        transactions, 
        key=lambda x: x.get('date', ''), 
        reverse=True
    )
    
    for trans in sorted_trans[:10]:
        date = trans.get('date', 'N/A')
        trans_type = trans.get('type', 'N/A')
        volume = trans.get('volume', 0)
        description = trans.get('description', 'N/A')
        print(f"  [{date}] {trans_type}: {volume}L - {description[:40]}")


def main():
    # Create client and fetcher
    print("Connecting to Vintrace API...")
    client = create_client_from_env()
    fetcher = VintraceDataFetcher(client)
    
    # Define date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    from_date = start_date.strftime('%Y-%m-%d')
    to_date = end_date.strftime('%Y-%m-%d')
    
    print(f"\nSearching transactions from {from_date} to {to_date}...")
    
    # Search for transactions
    transactions = fetcher.search_transactions(
        fromDate=from_date,
        toDate=to_date
    )
    
    print(f"Found {len(transactions)} transactions")
    
    if transactions:
        # Analyze the results
        analyze_transactions(transactions)
        
        # Save to file
        import json
        output_file = f"transactions_{from_date}_to_{to_date}.json"
        with open(output_file, 'w') as f:
            json.dump(transactions, f, indent=2)
        print(f"\n\nFull data saved to {output_file}")
    else:
        print("No transactions found in the specified date range.")


if __name__ == '__main__':
    main()
