#!/usr/bin/env python3
"""
Transaction Lineage Analyzer

Analyzes transaction data to track vessel-batch lineage, showing which vessel-batches 
contributed gallons to other vessel-batches. This enables Power BI reporting to trace 
the full history of any vessel-batch.

Features:
- Load transaction data from CSV files
- Track lineage from source batches to destination batches
- Generate reports showing all contributing batches to a final product
- Export data in Power BI compatible formats (CSV, JSON)
- Support for various transaction types: Transfer, Blend, Adjustment, Receipt, On-Hand

Usage:
    python transaction_lineage_analyzer.py
    
    Or import as a module:
    from transaction_lineage_analyzer import TransactionLineageAnalyzer
    analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
    lineage = analyzer.get_batch_lineage('24BLEND001-FINAL')
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class Transaction:
    """Represents a single transaction/operation"""
    
    def __init__(self, data: Dict):
        self.op_date = data.get('Op Date', '')
        self.op_id = data.get('Op Id', '')
        self.op_type = data.get('Op Type', '')
        self.from_vessel = data.get('From Vessel', '')
        self.from_batch = data.get('From Batch', '')
        self.to_vessel = data.get('To Vessel', '')
        self.to_batch = data.get('To Batch', '')
        self.net = float(data.get('NET', 0))
        self.loss_gain_amount = float(data.get('Loss/Gain Amount (gal)', 0))
        self.loss_gain_reason = data.get('Loss/Gain Reason', '')
        self.winery = data.get('Winery', '')
        
    def __repr__(self):
        return f"Transaction({self.op_id}: {self.from_batch} -> {self.to_batch}, {self.net} gal)"
    
    def to_dict(self) -> Dict:
        """Convert transaction to dictionary"""
        return {
            'Op Date': self.op_date,
            'Op Id': self.op_id,
            'Op Type': self.op_type,
            'From Vessel': self.from_vessel,
            'From Batch': self.from_batch,
            'To Vessel': self.to_vessel,
            'To Batch': self.to_batch,
            'NET': self.net,
            'Loss/Gain Amount (gal)': self.loss_gain_amount,
            'Loss/Gain Reason': self.loss_gain_reason,
            'Winery': self.winery
        }


class BatchLineage:
    """Represents the complete lineage of a vessel-batch"""
    
    def __init__(self, batch_name: str):
        self.batch_name = batch_name
        self.contributing_batches: Dict[str, float] = {}  # batch_name -> total gallons contributed
        self.contributing_transactions: List[Transaction] = []
        self.outgoing_transactions: List[Transaction] = []
        self.current_volume = 0.0
        self.is_on_hand = False
        self.has_left_inventory = False
        
    def add_incoming_transaction(self, transaction: Transaction, gallons: float):
        """Add a transaction that contributed to this batch"""
        source_batch = transaction.from_batch
        if source_batch and source_batch != self.batch_name:
            if source_batch not in self.contributing_batches:
                self.contributing_batches[source_batch] = 0.0
            self.contributing_batches[source_batch] += gallons
        self.contributing_transactions.append(transaction)
        
    def add_outgoing_transaction(self, transaction: Transaction):
        """Add a transaction where this batch contributed to another"""
        self.outgoing_transactions.append(transaction)
        
    def to_dict(self) -> Dict:
        """Convert lineage to dictionary"""
        return {
            'batch_name': self.batch_name,
            'current_volume': self.current_volume,
            'is_on_hand': self.is_on_hand,
            'has_left_inventory': self.has_left_inventory,
            'contributing_batches': self.contributing_batches,
            'total_contributing_batches': len(self.contributing_batches),
            'incoming_transaction_count': len(self.contributing_transactions),
            'outgoing_transaction_count': len(self.outgoing_transactions)
        }


class TransactionLineageAnalyzer:
    """Main analyzer class for transaction lineage tracking"""
    
    def __init__(self, csv_file_path: Optional[str] = None):
        """
        Initialize the analyzer
        
        Args:
            csv_file_path: Path to CSV file with transaction data
        """
        self.transactions: List[Transaction] = []
        self.batch_lineages: Dict[str, BatchLineage] = {}
        
        if csv_file_path:
            self.load_from_csv(csv_file_path)
            
    def load_from_csv(self, csv_file_path: str):
        """
        Load transaction data from CSV file
        
        Args:
            csv_file_path: Path to CSV file
        """
        logger.info(f"Loading transactions from {csv_file_path}")
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    transaction = Transaction(row)
                    self.transactions.append(transaction)
                    
            logger.info(f"Loaded {len(self.transactions)} transactions")
            self._build_lineage()
            
        except FileNotFoundError:
            logger.error(f"File not found: {csv_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise
            
    def _build_lineage(self):
        """Build the lineage relationships from transactions"""
        logger.info("Building lineage relationships...")
        
        # First pass: create all batch lineage objects
        all_batches = set()
        for trans in self.transactions:
            if trans.from_batch:
                all_batches.add(trans.from_batch)
            if trans.to_batch:
                all_batches.add(trans.to_batch)
                
        for batch in all_batches:
            self.batch_lineages[batch] = BatchLineage(batch)
            
        # Second pass: populate lineage relationships
        for trans in self.transactions:
            to_batch = trans.to_batch
            from_batch = trans.from_batch
            
            # Handle different operation types
            if trans.op_type == 'On-Hand':
                # This batch is currently in inventory
                if to_batch in self.batch_lineages:
                    self.batch_lineages[to_batch].is_on_hand = True
                    self.batch_lineages[to_batch].current_volume = trans.net
                    
            elif trans.op_type in ['Transfer', 'Blend', 'Receipt']:
                # Material moved from one batch to another
                if to_batch and to_batch in self.batch_lineages:
                    self.batch_lineages[to_batch].add_incoming_transaction(trans, trans.net)
                    
                if from_batch and from_batch in self.batch_lineages:
                    self.batch_lineages[from_batch].add_outgoing_transaction(trans)
                    # Mark that this batch has left (at least partially)
                    if trans.op_type != 'Receipt':  # Receipts don't indicate leaving
                        self.batch_lineages[from_batch].has_left_inventory = True
                        
            elif trans.op_type == 'Adjustment':
                # Adjustments affect the batch but don't indicate movement
                if to_batch and to_batch in self.batch_lineages:
                    self.batch_lineages[to_batch].add_incoming_transaction(trans, trans.net)
                    
        logger.info(f"Built lineage for {len(self.batch_lineages)} batches")
        
    def get_batch_lineage(self, batch_name: str) -> Optional[BatchLineage]:
        """
        Get the complete lineage for a specific batch
        
        Args:
            batch_name: Name of the batch to trace
            
        Returns:
            BatchLineage object or None if batch not found
        """
        return self.batch_lineages.get(batch_name)
    
    def get_full_lineage_tree(self, batch_name: str, visited: Optional[Set[str]] = None) -> Dict:
        """
        Get the full lineage tree recursively for a batch
        
        Args:
            batch_name: Name of the batch to trace
            visited: Set of already visited batches (to prevent cycles)
            
        Returns:
            Dictionary containing the full lineage tree
        """
        if visited is None:
            visited = set()
            
        if batch_name in visited:
            return {'batch_name': batch_name, 'cycle_detected': True}
            
        visited.add(batch_name)
        
        lineage = self.get_batch_lineage(batch_name)
        if not lineage:
            return {'batch_name': batch_name, 'not_found': True}
            
        tree = {
            'batch_name': batch_name,
            'current_volume': lineage.current_volume,
            'is_on_hand': lineage.is_on_hand,
            'has_left_inventory': lineage.has_left_inventory,
            'contributing_batches': []
        }
        
        # Recursively get lineage for each contributing batch
        for contributing_batch, gallons in lineage.contributing_batches.items():
            sub_tree = self.get_full_lineage_tree(contributing_batch, visited.copy())
            sub_tree['gallons_contributed'] = gallons
            tree['contributing_batches'].append(sub_tree)
            
        return tree
    
    def get_all_on_hand_batches(self) -> List[str]:
        """Get list of all batches currently on-hand"""
        return [
            batch_name for batch_name, lineage in self.batch_lineages.items()
            if lineage.is_on_hand
        ]
    
    def get_all_shipped_batches(self) -> List[str]:
        """Get list of all batches that have left inventory"""
        return [
            batch_name for batch_name, lineage in self.batch_lineages.items()
            if lineage.has_left_inventory and not lineage.is_on_hand
        ]
    
    def generate_lineage_report(self, batch_name: str) -> str:
        """
        Generate a human-readable lineage report for a batch
        
        Args:
            batch_name: Name of the batch to report on
            
        Returns:
            Formatted string report
        """
        lineage = self.get_batch_lineage(batch_name)
        if not lineage:
            return f"Batch '{batch_name}' not found in transactions"
            
        report = []
        report.append("="*80)
        report.append(f"LINEAGE REPORT FOR: {batch_name}")
        report.append("="*80)
        report.append(f"Status: {'ON-HAND' if lineage.is_on_hand else 'SHIPPED' if lineage.has_left_inventory else 'UNKNOWN'}")
        report.append(f"Current Volume: {lineage.current_volume:.2f} gallons")
        report.append("")
        
        if lineage.contributing_batches:
            report.append(f"CONTRIBUTING BATCHES ({len(lineage.contributing_batches)}):")
            report.append("-"*80)
            for contrib_batch, gallons in sorted(lineage.contributing_batches.items()):
                report.append(f"  {contrib_batch:30} : {gallons:>10.2f} gallons")
            report.append("")
        else:
            report.append("No contributing batches (this may be an original receipt)")
            report.append("")
            
        if lineage.contributing_transactions:
            report.append(f"INCOMING TRANSACTIONS ({len(lineage.contributing_transactions)}):")
            report.append("-"*80)
            for trans in lineage.contributing_transactions:
                report.append(f"  {trans.op_date:12} {trans.op_id:12} {trans.op_type:12} "
                            f"{trans.from_batch:20} -> {trans.to_batch:20} "
                            f"{trans.net:>8.2f} gal")
            report.append("")
            
        if lineage.outgoing_transactions:
            report.append(f"OUTGOING TRANSACTIONS ({len(lineage.outgoing_transactions)}):")
            report.append("-"*80)
            for trans in lineage.outgoing_transactions:
                report.append(f"  {trans.op_date:12} {trans.op_id:12} {trans.op_type:12} "
                            f"{trans.from_batch:20} -> {trans.to_batch:20} "
                            f"{trans.net:>8.2f} gal")
            report.append("")
            
        report.append("="*80)
        
        return "\n".join(report)
    
    def export_lineage_to_csv(self, output_file: str, batch_filter: Optional[str] = None):
        """
        Export lineage relationships to CSV for Power BI
        
        Args:
            output_file: Path to output CSV file
            batch_filter: Optional filter - 'on-hand', 'shipped', or None for all
        """
        logger.info(f"Exporting lineage to {output_file}")
        
        rows = []
        for batch_name, lineage in self.batch_lineages.items():
            # Apply filter
            if batch_filter == 'on-hand' and not lineage.is_on_hand:
                continue
            elif batch_filter == 'shipped' and not lineage.has_left_inventory:
                continue
                
            # Create a row for each contributing batch
            if lineage.contributing_batches:
                for contrib_batch, gallons in lineage.contributing_batches.items():
                    rows.append({
                        'Destination_Batch': batch_name,
                        'Source_Batch': contrib_batch,
                        'Gallons_Contributed': gallons,
                        'Destination_Current_Volume': lineage.current_volume,
                        'Destination_Is_On_Hand': lineage.is_on_hand,
                        'Destination_Has_Left': lineage.has_left_inventory
                    })
            else:
                # No contributing batches - this is an origin batch
                rows.append({
                    'Destination_Batch': batch_name,
                    'Source_Batch': '',
                    'Gallons_Contributed': 0,
                    'Destination_Current_Volume': lineage.current_volume,
                    'Destination_Is_On_Hand': lineage.is_on_hand,
                    'Destination_Has_Left': lineage.has_left_inventory
                })
                
        # Write CSV
        if rows:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            logger.info(f"Exported {len(rows)} lineage relationships")
        else:
            logger.warning("No lineage relationships to export")
            
    def export_transactions_to_csv(self, output_file: str):
        """
        Export all transactions to CSV for Power BI
        
        Args:
            output_file: Path to output CSV file
        """
        logger.info(f"Exporting transactions to {output_file}")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if self.transactions:
                writer = csv.DictWriter(f, fieldnames=self.transactions[0].to_dict().keys())
                writer.writeheader()
                for trans in self.transactions:
                    writer.writerows([trans.to_dict()])
                    
        logger.info(f"Exported {len(self.transactions)} transactions")
        
    def export_to_json(self, output_file: str):
        """
        Export complete lineage data to JSON
        
        Args:
            output_file: Path to output JSON file
        """
        logger.info(f"Exporting to JSON: {output_file}")
        
        data = {
            'metadata': {
                'total_transactions': len(self.transactions),
                'total_batches': len(self.batch_lineages),
                'on_hand_batches': len(self.get_all_on_hand_batches()),
                'shipped_batches': len(self.get_all_shipped_batches())
            },
            'batches': {
                batch_name: lineage.to_dict()
                for batch_name, lineage in self.batch_lineages.items()
            },
            'transactions': [trans.to_dict() for trans in self.transactions]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Exported complete lineage data to JSON")


def main():
    """Main execution function with example usage"""
    
    # Initialize analyzer with CSV file
    csv_file = 'Transaction_to_analysise.csv'
    
    print(f"\n{'='*80}")
    print("TRANSACTION LINEAGE ANALYZER")
    print(f"{'='*80}\n")
    
    analyzer = TransactionLineageAnalyzer(csv_file)
    
    # Show summary
    print(f"Loaded {len(analyzer.transactions)} transactions")
    print(f"Tracking {len(analyzer.batch_lineages)} unique batches")
    print(f"On-hand batches: {len(analyzer.get_all_on_hand_batches())}")
    print(f"Shipped batches: {len(analyzer.get_all_shipped_batches())}")
    print()
    
    # Show all on-hand batches
    print("ON-HAND BATCHES:")
    print("-"*80)
    for batch in analyzer.get_all_on_hand_batches():
        lineage = analyzer.get_batch_lineage(batch)
        print(f"  {batch:30} : {lineage.current_volume:>10.2f} gallons, "
              f"{len(lineage.contributing_batches)} contributing batches")
    print()
    
    # Generate detailed report for a specific batch
    example_batch = '24BLEND001-FINAL'
    if example_batch in analyzer.batch_lineages:
        print(analyzer.generate_lineage_report(example_batch))
        
        # Show full lineage tree
        print("\nFULL LINEAGE TREE:")
        print("-"*80)
        tree = analyzer.get_full_lineage_tree(example_batch)
        print(json.dumps(tree, indent=2))
        print()
    
    # Export data
    output_dir = Path('lineage_reports')
    output_dir.mkdir(exist_ok=True)
    
    # Export lineage relationships for Power BI
    analyzer.export_lineage_to_csv(str(output_dir / 'batch_lineage.csv'))
    analyzer.export_lineage_to_csv(str(output_dir / 'batch_lineage_on_hand.csv'), batch_filter='on-hand')
    
    # Export all transactions
    analyzer.export_transactions_to_csv(str(output_dir / 'all_transactions.csv'))
    
    # Export to JSON
    analyzer.export_to_json(str(output_dir / 'complete_lineage.json'))
    
    print(f"\n{'='*80}")
    print("EXPORTS COMPLETE")
    print(f"{'='*80}")
    print(f"Output directory: {output_dir}")
    print(f"  - batch_lineage.csv (all lineage relationships)")
    print(f"  - batch_lineage_on_hand.csv (only on-hand batches)")
    print(f"  - all_transactions.csv (all transactions)")
    print(f"  - complete_lineage.json (full data)")
    print()


if __name__ == '__main__':
    main()
