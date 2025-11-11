#!/usr/bin/env python3
"""
Analyze All Inventory Lots

This script analyzes all lots currently in inventory by combining:
1. Vessel/lot data from vessels_main.json (current inventory snapshot)
2. Transaction lineage analysis to trace the history of each lot

Usage:
    # Basic usage - analyze all lots from transaction data
    python analyze_all_inventory_lots.py
    
    # With vessel data from vessels_main.json
    python analyze_all_inventory_lots.py --vessels-file Main/data/processed_vessels/vessels_main.json
    
    # Specify custom transaction file
    python analyze_all_inventory_lots.py --transaction-file Transaction_to_analysise.csv
    
    # Generate detailed reports
    python analyze_all_inventory_lots.py --detailed-reports
    
    # Export to specific directory
    python analyze_all_inventory_lots.py --output-dir inventory_analysis_reports

Steps to get vessel data:
    1. Fetch vessels from API: python fetch_Vessels.py
    2. Process vessels data: python melt_vessels.py
    3. Run this script: python analyze_all_inventory_lots.py --vessels-file Main/data/processed_vessels/vessels_main.json
"""

import sys
import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Set
import logging
from datetime import datetime

# Import the transaction lineage analyzer
try:
    from transaction_lineage_analyzer import TransactionLineageAnalyzer, BatchLineage
except ImportError:
    print("ERROR: Could not import transaction_lineage_analyzer")
    print("Make sure transaction_lineage_analyzer.py is in the same directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def load_vessels_from_json(vessels_file: str) -> List[Dict]:
    """
    Load vessel data from vessels_main.json
    
    Args:
        vessels_file: Path to vessels_main.json file
        
    Returns:
        List of vessel dictionaries
    """
    logger.info(f"Loading vessel data from {vessels_file}")
    
    try:
        with open(vessels_file, 'r', encoding='utf-8') as f:
            vessels = json.load(f)
        
        logger.info(f"Loaded {len(vessels)} vessels")
        return vessels
        
    except FileNotFoundError:
        logger.error(f"Vessel file not found: {vessels_file}")
        logger.info("\nTo create vessels_main.json:")
        logger.info("  1. Run: python fetch_Vessels.py")
        logger.info("  2. Run: python melt_vessels.py")
        logger.info("  3. File will be at: Main/data/processed_vessels/vessels_main.json")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing vessel JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading vessels: {e}")
        return []


def convert_transaction_csv_to_simple_format(input_file: str, output_file: str) -> bool:
    """
    Convert the complex transaction CSV to the simple format expected by the analyzer.
    
    The input CSV has columns like:
    - Op Date, Tx Id, Op Id, Op Type, Src Batch Pre, Dest Batch Post, NET, etc.
    
    The output CSV needs:
    - Op Date, Op Id, Op Type, From Vessel, From Batch, To Vessel, To Batch, 
      NET, Loss/Gain Amount (gal), Loss/Gain Reason, Winery
      
    Args:
        input_file: Path to input CSV (complex format)
        output_file: Path to output CSV (simple format)
        
    Returns:
        True if conversion successful, False otherwise
    """
    logger.info(f"Converting transaction data from {input_file} to {output_file}")
    
    try:
        converted_rows = []
        
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Extract the key fields
                converted_row = {
                    'Op Date': row.get('Op Date', ''),
                    'Op Id': row.get('Op Id', row.get('Tx Id', '')),
                    'Op Type': row.get('Op Type', ''),
                    'From Vessel': row.get('Src Vessel', ''),
                    'From Batch': row.get('Src Batch Pre', ''),
                    'To Vessel': row.get('Dest Vessel', ''),
                    'To Batch': row.get('Dest Batch Post', ''),
                    'NET': row.get('NET', '0'),
                    'Loss/Gain Amount (gal)': row.get('Loss/Gain Amount (gal)', '0'),
                    'Loss/Gain Reason': row.get('Loss/Gain Reason', ''),
                    'Winery': ''  # Not available in the source data
                }
                
                converted_rows.append(converted_row)
        
        # Write converted data
        if converted_rows:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=converted_rows[0].keys())
                writer.writeheader()
                writer.writerows(converted_rows)
            
            logger.info(f"Successfully converted {len(converted_rows)} transactions")
            return True
        else:
            logger.warning("No transactions found to convert")
            return False
            
    except Exception as e:
        logger.error(f"Error converting transaction data: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_on_hand_batches_from_vessels(vessels: List[Dict]) -> Set[str]:
    """
    Extract batch names from vessel data that are currently on-hand
    
    Args:
        vessels: List of vessel dictionaries from vessels_main.json
        
    Returns:
        Set of batch names (wine_batch_name) that have volume > 0
    """
    on_hand_batches = set()
    
    for vessel in vessels:
        volume = vessel.get('volume_value', 0)
        batch_name = vessel.get('wine_batch_name', '')
        
        # A vessel is "on-hand" if it has volume and a batch name
        if volume and volume > 0 and batch_name:
            on_hand_batches.add(batch_name)
    
    logger.info(f"Found {len(on_hand_batches)} unique batches with volume > 0 in vessel data")
    return on_hand_batches


def generate_inventory_summary_report(
    analyzer: TransactionLineageAnalyzer,
    vessel_batches: Optional[Set[str]] = None,
    output_dir: Path = None
) -> str:
    """
    Generate a summary report for all inventory lots
    
    Args:
        analyzer: TransactionLineageAnalyzer instance
        vessel_batches: Optional set of batch names from vessel data (to cross-reference)
        output_dir: Directory to save the report
        
    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 100)
    report.append("INVENTORY LOTS ANALYSIS SUMMARY")
    report.append("=" * 100)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Get on-hand batches from transaction data
    on_hand_from_transactions = analyzer.get_all_on_hand_batches()
    
    report.append(f"On-hand batches from transaction data: {len(on_hand_from_transactions)}")
    
    if vessel_batches:
        report.append(f"Batches with volume from vessel data: {len(vessel_batches)}")
        
        # Find overlap and differences
        in_both = set(on_hand_from_transactions) & vessel_batches
        only_in_transactions = set(on_hand_from_transactions) - vessel_batches
        only_in_vessels = vessel_batches - set(on_hand_from_transactions)
        
        report.append(f"Batches found in both sources: {len(in_both)}")
        report.append(f"Batches only in transactions: {len(only_in_transactions)}")
        report.append(f"Batches only in vessels: {len(only_in_vessels)}")
        report.append("")
        
        if only_in_transactions:
            report.append("WARNING: Batches in transactions but not in vessel data:")
            for batch in sorted(only_in_transactions)[:10]:  # Show first 10
                report.append(f"  - {batch}")
            if len(only_in_transactions) > 10:
                report.append(f"  ... and {len(only_in_transactions) - 10} more")
            report.append("")
        
        if only_in_vessels:
            report.append("NOTE: Batches in vessel data but not marked as on-hand in transactions:")
            for batch in sorted(only_in_vessels)[:10]:  # Show first 10
                report.append(f"  - {batch}")
            if len(only_in_vessels) > 10:
                report.append(f"  ... and {len(only_in_vessels) - 10} more")
            report.append("")
    
    report.append("=" * 100)
    report.append("ON-HAND INVENTORY DETAILS")
    report.append("=" * 100)
    report.append(f"{'Batch Name':<40} {'Volume (gal)':<15} {'Contributing Batches':<20}")
    report.append("-" * 100)
    
    # Combine batches from both sources
    all_batches = set(on_hand_from_transactions)
    if vessel_batches:
        all_batches = all_batches | vessel_batches
    
    total_volume = 0
    for batch_name in sorted(all_batches):
        lineage = analyzer.get_batch_lineage(batch_name)
        
        if lineage:
            volume = lineage.current_volume
            total_volume += volume
            contrib_count = len(lineage.contributing_batches)
            
            report.append(
                f"{batch_name:<40} {volume:>13.2f}   {contrib_count:>18}"
            )
        else:
            # Batch is in vessel data but not in transaction data
            report.append(
                f"{batch_name:<40} {'N/A':<15} {'N/A':<20}"
            )
    
    report.append("-" * 100)
    report.append(f"{'Total Volume:':<40} {total_volume:>13.2f}")
    report.append("=" * 100)
    
    report_text = "\n".join(report)
    
    # Save to file if output directory specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_file = output_dir / "inventory_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logger.info(f"Saved summary report to {summary_file}")
    
    return report_text


def generate_detailed_batch_reports(
    analyzer: TransactionLineageAnalyzer,
    batches: Set[str],
    output_dir: Path
):
    """
    Generate detailed lineage reports for each batch
    
    Args:
        analyzer: TransactionLineageAnalyzer instance
        batches: Set of batch names to analyze
        output_dir: Directory to save individual reports
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating detailed reports for {len(batches)} batches...")
    
    for idx, batch_name in enumerate(sorted(batches), 1):
        # Generate report
        report = analyzer.generate_lineage_report(batch_name)
        
        # Save to individual file
        safe_filename = batch_name.replace('/', '_').replace('\\', '_')
        report_file = output_dir / f"{safe_filename}_lineage.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        if idx % 10 == 0:
            logger.info(f"  Generated {idx}/{len(batches)} reports")
    
    logger.info(f"All detailed reports saved to {output_dir}")


def export_analysis_data(
    analyzer: TransactionLineageAnalyzer,
    output_dir: Path
):
    """
    Export analysis data in various formats for further analysis
    
    Args:
        analyzer: TransactionLineageAnalyzer instance
        output_dir: Directory to save exports
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Exporting analysis data...")
    
    # Export all lineage relationships
    analyzer.export_lineage_to_csv(
        str(output_dir / 'all_batch_lineage.csv')
    )
    
    # Export only on-hand batches
    analyzer.export_lineage_to_csv(
        str(output_dir / 'on_hand_batch_lineage.csv'),
        batch_filter='on-hand'
    )
    
    # Export all transactions
    analyzer.export_transactions_to_csv(
        str(output_dir / 'all_transactions.csv')
    )
    
    # Export complete JSON
    analyzer.export_to_json(
        str(output_dir / 'complete_lineage_data.json')
    )
    
    logger.info(f"Exported analysis data to {output_dir}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Analyze all inventory lots using transaction and vessel data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--transaction-file',
        type=str,
        default='Transaction_to_analysise.csv',
        help='Path to transaction CSV file (default: Transaction_to_analysise.csv)'
    )
    
    parser.add_argument(
        '--vessels-file',
        type=str,
        help='Path to vessels_main.json file (optional, enhances analysis)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='inventory_analysis_reports',
        help='Output directory for reports (default: inventory_analysis_reports)'
    )
    
    parser.add_argument(
        '--detailed-reports',
        action='store_true',
        help='Generate detailed lineage reports for each batch'
    )
    
    parser.add_argument(
        '--convert-only',
        action='store_true',
        help='Only convert transaction file to simple format and exit'
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*100}")
    print("INVENTORY LOTS ANALYZER")
    print(f"{'='*100}\n")
    
    # Check if transaction file exists
    if not Path(args.transaction_file).exists():
        logger.error(f"Transaction file not found: {args.transaction_file}")
        logger.info("\nTo get transaction data:")
        logger.info("  Option 1: Use existing Transaction_to_analysise.csv")
        logger.info("  Option 2: Fetch from API: python fetch_transactions_for_analysis.py")
        sys.exit(1)
    
    # Convert transaction file to simple format
    temp_simple_file = Path(args.output_dir) / 'transactions_simple_format.csv'
    temp_simple_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not convert_transaction_csv_to_simple_format(args.transaction_file, str(temp_simple_file)):
        logger.error("Failed to convert transaction data")
        sys.exit(1)
    
    if args.convert_only:
        print(f"\n✓ Converted transaction data to: {temp_simple_file}")
        print("You can now use this file with transaction_lineage_analyzer.py")
        return
    
    # Load the analyzer with converted data
    logger.info("Loading transaction lineage analyzer...")
    analyzer = TransactionLineageAnalyzer(str(temp_simple_file))
    
    # Load vessel data if provided
    vessel_batches = None
    if args.vessels_file:
        vessels = load_vessels_from_json(args.vessels_file)
        if vessels:
            vessel_batches = get_on_hand_batches_from_vessels(vessels)
    
    # Generate summary report
    output_dir = Path(args.output_dir)
    summary = generate_inventory_summary_report(analyzer, vessel_batches, output_dir)
    print("\n" + summary)
    
    # Export analysis data
    export_analysis_data(analyzer, output_dir)
    
    # Generate detailed reports if requested
    if args.detailed_reports:
        on_hand_batches = analyzer.get_all_on_hand_batches()
        if vessel_batches:
            on_hand_batches = set(on_hand_batches) | vessel_batches
        
        detailed_dir = output_dir / 'detailed_batch_reports'
        generate_detailed_batch_reports(analyzer, on_hand_batches, detailed_dir)
    
    # Final summary
    print(f"\n{'='*100}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*100}")
    print(f"\nOutput directory: {output_dir}")
    print("Files generated:")
    print("  ✓ inventory_summary.txt - Summary of all inventory lots")
    print("  ✓ all_batch_lineage.csv - All lineage relationships (Power BI compatible)")
    print("  ✓ on_hand_batch_lineage.csv - Only on-hand batches (Power BI compatible)")
    print("  ✓ all_transactions.csv - All transaction data")
    print("  ✓ complete_lineage_data.json - Complete data in JSON format")
    if args.detailed_reports:
        print("  ✓ detailed_batch_reports/ - Individual reports for each batch")
    
    print("\nNext steps:")
    print("  1. Review inventory_summary.txt for overview")
    print("  2. Import CSV files into Power BI for visualization")
    print("  3. Use JSON file for custom analysis or integration")
    
    if not args.vessels_file:
        print("\nTIP: For enhanced analysis, include vessel data:")
        print("  1. Run: python fetch_Vessels.py")
        print("  2. Run: python melt_vessels.py")
        print("  3. Run this script with: --vessels-file Main/data/processed_vessels/vessels_main.json")
    
    print()


if __name__ == '__main__':
    main()
