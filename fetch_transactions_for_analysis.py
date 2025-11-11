#!/usr/bin/env python3
"""
Fetch Transaction Data from Vintrace API

This script fetches transaction data from the Vintrace API and saves it in a format
compatible with the transaction_lineage_analyzer.py tool.

Usage:
    python fetch_transactions_for_analysis.py --from-date 2025-09-01 --to-date 2025-11-11
    
    Or with specific filters:
    python fetch_transactions_for_analysis.py --from-date 2024-01-01 --batch-name "24CABSAUV*"
"""

import sys
import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Import the API client
try:
    from API import create_client_from_env, VintraceDataFetcher
except ImportError:
    print("ERROR: Could not import Vintrace API client")
    print("Make sure the API module is available in the API/ directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_transactions(from_date: str, to_date: str, **filters) -> list:
    """
    Fetch transactions from Vintrace API
    
    Args:
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        **filters: Additional filters (ownerName, batchName, wineryName)
        
    Returns:
        List of transaction dictionaries
    """
    logger.info("Connecting to Vintrace API...")
    client = create_client_from_env()
    fetcher = VintraceDataFetcher(client)
    
    logger.info(f"Fetching transactions from {from_date} to {to_date}")
    
    # Call the transaction search API
    response = client.transaction_search(
        dateFrom=from_date,
        dateTo=to_date,
        ownerName=filters.get('owner_name'),
        batchName=filters.get('batch_name'),
        wineryName=filters.get('winery_name')
    )
    
    # Extract transactions from the response
    transactions = response.get('items', []) if isinstance(response, dict) else response
    
    logger.info(f"Retrieved {len(transactions)} transactions")
    return transactions


def convert_to_analysis_format(api_transactions: list) -> list:
    """
    Convert API transaction format to analysis CSV format
    
    The API returns transaction data in a specific format. This function
    converts it to match the expected CSV structure with these fields:
    - Op Date
    - Op Id
    - Op Type
    - From Vessel
    - From Batch
    - To Vessel
    - To Batch
    - NET
    - Loss/Gain Amount (gal)
    - Loss/Gain Reason
    - Winery
    
    Args:
        api_transactions: List of transactions from the API
        
    Returns:
        List of dictionaries formatted for CSV export
    """
    converted = []
    
    for trans in api_transactions:
        # Map API fields to CSV fields
        # Note: Field names may vary - adjust based on actual API response
        row = {
            'Op Date': trans.get('date', trans.get('operationDate', '')),
            'Op Id': trans.get('id', trans.get('operationId', '')),
            'Op Type': trans.get('type', trans.get('operationType', '')),
            'From Vessel': trans.get('fromVessel', trans.get('sourceVessel', '')),
            'From Batch': trans.get('fromBatch', trans.get('sourceBatch', '')),
            'To Vessel': trans.get('toVessel', trans.get('destinationVessel', '')),
            'To Batch': trans.get('toBatch', trans.get('destinationBatch', '')),
            'NET': trans.get('net', trans.get('volume', 0)),
            'Loss/Gain Amount (gal)': trans.get('lossGain', trans.get('lossGainAmount', 0)),
            'Loss/Gain Reason': trans.get('lossGainReason', trans.get('reason', '')),
            'Winery': trans.get('winery', trans.get('wineryName', ''))
        }
        
        converted.append(row)
    
    return converted


def save_to_csv(transactions: list, output_file: str):
    """
    Save transactions to CSV file
    
    Args:
        transactions: List of transaction dictionaries
        output_file: Path to output CSV file
    """
    if not transactions:
        logger.warning("No transactions to save")
        return
    
    logger.info(f"Saving {len(transactions)} transactions to {output_file}")
    
    fieldnames = [
        'Op Date', 'Op Id', 'Op Type', 'From Vessel', 'From Batch',
        'To Vessel', 'To Batch', 'NET', 'Loss/Gain Amount (gal)',
        'Loss/Gain Reason', 'Winery'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    
    logger.info(f"Successfully saved to {output_file}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Fetch transaction data from Vintrace API for lineage analysis'
    )
    
    parser.add_argument(
        '--from-date',
        type=str,
        help='Start date in YYYY-MM-DD format (default: 30 days ago)',
        default=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    )
    
    parser.add_argument(
        '--to-date',
        type=str,
        help='End date in YYYY-MM-DD format (default: today)',
        default=datetime.now().strftime('%Y-%m-%d')
    )
    
    parser.add_argument(
        '--owner-name',
        type=str,
        help='Filter by owner name',
        default=None
    )
    
    parser.add_argument(
        '--batch-name',
        type=str,
        help='Filter by batch name',
        default=None
    )
    
    parser.add_argument(
        '--winery-name',
        type=str,
        help='Filter by winery name',
        default=None
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV file path',
        default='Transaction_to_analysise.csv'
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print("VINTRACE TRANSACTION FETCHER")
    print(f"{'='*80}\n")
    
    # Fetch transactions
    try:
        filters = {
            'owner_name': args.owner_name,
            'batch_name': args.batch_name,
            'winery_name': args.winery_name
        }
        
        api_transactions = fetch_transactions(
            args.from_date,
            args.to_date,
            **{k: v for k, v in filters.items() if v is not None}
        )
        
        if not api_transactions:
            logger.warning("No transactions found with the specified criteria")
            return
        
        # Convert to analysis format
        logger.info("Converting transactions to analysis format...")
        converted_transactions = convert_to_analysis_format(api_transactions)
        
        # Save to CSV
        save_to_csv(converted_transactions, args.output)
        
        print(f"\n{'='*80}")
        print("SUCCESS")
        print(f"{'='*80}")
        print(f"Fetched {len(api_transactions)} transactions")
        print(f"Saved to: {args.output}")
        print(f"\nNext steps:")
        print(f"  1. Review the data: head {args.output}")
        print(f"  2. Run analysis: python transaction_lineage_analyzer.py")
        print()
        
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
