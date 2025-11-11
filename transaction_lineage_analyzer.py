#!/usr/bin/env python3
"""
Transaction Lineage Analyzer

Analyzes transaction data to track vessel-batch lineage, showing which vessel-batches 
contributed gallons to other vessel-batches. This enables Power BI reporting to trace 
the full history of any vessel-batch.

Features:
- Load transaction data from CSV files
- Track lineage from source batches to destination batches using Src Vol Change and Dest Vol Change
- Accurate gallon tracking accounting for losses/gains during transfers
- Generate reports showing all contributing batches to a final product
- Export data in Power BI compatible formats (CSV, JSON)
- Support for various transaction types: Transfer, Blend, Adjustment, Receipt, On-Hand

Volume Tracking:
- Uses Src Vol Change (gallons leaving source) and Dest Vol Change (gallons arriving at destination)
- NET field is preserved but not used for lineage tracking as it often equals 0
- Properly accounts for losses/gains between source and destination

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
        # Basic transaction info
        self.op_date = data.get('Op Date', '')
        self.tx_id = data.get('Tx Id', '')
        self.op_id = data.get('Op Id', '')
        self.work_order = data.get('Work Order', '')
        self.txn_type = data.get('Txn Type', '')
        self.op_type = data.get('Op Type', '')
        self.reversed = data.get('Reversed', '')
        self.operator = data.get('Operator', '')
        self.date_entered = data.get('Date Entered', '')
        self.entered_by = data.get('Entered By', '')
        
        # Source vessel and batch information (Pre and Post states)
        self.src_vessel = data.get('Src Vessel', '')
        self.src_batch_pre = data.get('Src Batch Pre', '')
        self.src_pre_tax_state = data.get('Src Pre Tax State', '')
        self.src_pre_tax_class = data.get('Src Pre Tax Class', '')
        self.src_batch_pre_owner = data.get('Src Batch Pre Owner', '')
        self.src_batch_pre_bond = data.get('Src Batch Pre Bond', '')
        self.src_program_pre = data.get('Src Program Pre', '')
        self.src_grading_pre = data.get('Src Grading Pre', '')
        self.src_state_pre = data.get('Src State Pre', '')
        self.src_dsp_account_pre = data.get('Src DSP Account Pre', '')
        self.src_vol_pre = self._safe_float(data.get('Src Vol Pre', 0))
        
        self.src_batch_post = data.get('Src Batch Post', '')
        self.src_post_tax_state = data.get('Src Post Tax State', '')
        self.src_post_tax_class = data.get('Src Post Tax Class', '')
        self.src_batch_post_owner = data.get('Src Batch Post Owner', '')
        self.src_batch_post_bond = data.get('Src Batch Post Bond', '')
        self.src_program_post = data.get('Src Program Post', '')
        self.src_grading_post = data.get('Src Grading Post', '')
        self.src_state_post = data.get('Src State Post', '')
        self.src_dsp_account_post = data.get('Src DSP Account Post', '')
        self.src_vol_post = self._safe_float(data.get('Src Vol Post', 0))
        self.src_vol_change = self._safe_float(data.get('Src Vol Change', 0))
        
        # Source alcohol and proof information
        self.src_alcohol_pre = self._safe_float(data.get('Src Alcohol Pre', 0))
        self.src_proof_pre = self._safe_float(data.get('Src Proof Pre', 0))
        self.src_proof_gallons_pre = self._safe_float(data.get('Src Proof Gallons Pre', 0))
        self.src_alcohol_post = self._safe_float(data.get('Src Alcohol Post', 0))
        self.src_proof_post = self._safe_float(data.get('Src Proof Post', 0))
        self.src_proof_gallons_post = self._safe_float(data.get('Src Proof Gallons Post', 0))
        self.src_vol_proof_gal_change = self._safe_float(data.get('Src Vol Proof Gal Change', 0))
        
        # Destination vessel and batch information (Pre and Post states)
        self.dest_vessel = data.get('Dest Vessel', '')
        self.dest_batch_pre = data.get('Dest Batch Pre', '')
        self.dest_pre_tax_state = data.get('Dest Pre Tax State', '')
        self.dest_pre_tax_class = data.get('Dest Pre Tax Class', '')
        self.dest_batch_pre_owner = data.get('Dest Batch Pre Owner', '')
        self.dest_batch_pre_bond = data.get('Dest Batch Pre Bond', '')
        self.dest_program_pre = data.get('Dest Program Pre', '')
        self.dest_grading_pre = data.get('Dest Grading Pre', '')
        self.dest_state_pre = data.get('Dest State Pre', '')
        self.dest_dsp_account_pre = data.get('Dest DSP Account Pre', '')
        self.dest_vol_pre = self._safe_float(data.get('Dest Vol Pre', 0))
        
        self.dest_batch_post = data.get('Dest Batch Post', '')
        self.dest_post_tax_state = data.get('Dest Post Tax State', '')
        self.dest_post_tax_class = data.get('Dest Post Tax Class', '')
        self.dest_batch_post_owner = data.get('Dest Batch Post Owner', '')
        self.dest_batch_post_bond = data.get('Dest Batch Post Bond', '')
        self.dest_program_post = data.get('Dest Program Post', '')
        self.dest_grading_post = data.get('Dest Grading Post', '')
        self.dest_state_post = data.get('Dest State Post', '')
        self.dest_dsp_account_post = data.get('Dest DSP Account Post', '')
        self.dest_vol_post = self._safe_float(data.get('Dest Vol Post', 0))
        self.dest_vol_change = self._safe_float(data.get('Dest Vol Change', 0))
        
        # Destination alcohol and proof information
        self.dest_alcohol_pre = self._safe_float(data.get('Dest Alcohol Pre', 0))
        self.dest_proof_pre = self._safe_float(data.get('Dest Proof Pre', 0))
        self.dest_proof_gallons_pre = self._safe_float(data.get('Dest Proof Gallons Pre', 0))
        self.dest_alcohol_post = self._safe_float(data.get('Dest Alcohol Post', 0))
        self.dest_proof_post = self._safe_float(data.get('Dest Proof Post', 0))
        self.dest_proof_gallons_post = self._safe_float(data.get('Dest Proof Gallons Post', 0))
        self.dest_vol_proof_gal_change = self._safe_float(data.get('Dest Vol Proof Gal Change', 0))
        
        # Loss/Gain information
        self.loss_gain_amount = self._safe_float(data.get('Loss/Gain Amount (gal)', 0))
        self.loss_gain_amount_proof = self._safe_float(data.get('Loss/Gain Amount (proof gal)', 0))
        self.loss_gain_reason = data.get('Loss/Gain Reason', '')
        self.net = self._safe_float(data.get('NET', 0))
        
        # Legacy fields for backward compatibility
        self.from_vessel = data.get('From Vessel', '') or self.src_vessel
        self.from_batch = data.get('From Batch', '') or self.src_batch_pre
        self.to_vessel = data.get('To Vessel', '') or self.dest_vessel
        self.to_batch = data.get('To Batch', '') or self.dest_batch_post
        self.winery = data.get('Winery', '')
    
    @staticmethod
    def _safe_float(value) -> float:
        """Safely convert value to float, handling empty strings and None"""
        if value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
        
    def __repr__(self):
        src_batch = self.src_batch_pre or self.from_batch
        dest_batch = self.dest_batch_post or self.to_batch
        return f"Transaction({self.op_id}: {src_batch} -> {dest_batch}, {self.net} gal)"
    
    def to_dict(self) -> Dict:
        """Convert transaction to dictionary"""
        return {
            'Op Date': self.op_date,
            'Tx Id': self.tx_id,
            'Op Id': self.op_id,
            'Work Order': self.work_order,
            'Txn Type': self.txn_type,
            'Op Type': self.op_type,
            'Reversed': self.reversed,
            'Operator': self.operator,
            'Date Entered': self.date_entered,
            'Entered By': self.entered_by,
            'Src Vessel': self.src_vessel,
            'Src Batch Pre': self.src_batch_pre,
            'Src Pre Tax State': self.src_pre_tax_state,
            'Src Pre Tax Class': self.src_pre_tax_class,
            'Src Batch Pre Owner': self.src_batch_pre_owner,
            'Src Batch Pre Bond': self.src_batch_pre_bond,
            'Src Program Pre': self.src_program_pre,
            'Src Grading Pre': self.src_grading_pre,
            'Src State Pre': self.src_state_pre,
            'Src DSP Account Pre': self.src_dsp_account_pre,
            'Src Vol Pre': self.src_vol_pre,
            'Src Batch Post': self.src_batch_post,
            'Src Post Tax State': self.src_post_tax_state,
            'Src Post Tax Class': self.src_post_tax_class,
            'Src Batch Post Owner': self.src_batch_post_owner,
            'Src Batch Post Bond': self.src_batch_post_bond,
            'Src Program Post': self.src_program_post,
            'Src Grading Post': self.src_grading_post,
            'Src State Post': self.src_state_post,
            'Src DSP Account Post': self.src_dsp_account_post,
            'Src Vol Post': self.src_vol_post,
            'Src Vol Change': self.src_vol_change,
            'Src Alcohol Pre': self.src_alcohol_pre,
            'Src Proof Pre': self.src_proof_pre,
            'Src Proof Gallons Pre': self.src_proof_gallons_pre,
            'Src Alcohol Post': self.src_alcohol_post,
            'Src Proof Post': self.src_proof_post,
            'Src Proof Gallons Post': self.src_proof_gallons_post,
            'Src Vol Proof Gal Change': self.src_vol_proof_gal_change,
            'Dest Vessel': self.dest_vessel,
            'Dest Batch Pre': self.dest_batch_pre,
            'Dest Pre Tax State': self.dest_pre_tax_state,
            'Dest Pre Tax Class': self.dest_pre_tax_class,
            'Dest Batch Pre Owner': self.dest_batch_pre_owner,
            'Dest Batch Pre Bond': self.dest_batch_pre_bond,
            'Dest Program Pre': self.dest_program_pre,
            'Dest Grading Pre': self.dest_grading_pre,
            'Dest State Pre': self.dest_state_pre,
            'Dest DSP Account Pre': self.dest_dsp_account_pre,
            'Dest Vol Pre': self.dest_vol_pre,
            'Dest Batch Post': self.dest_batch_post,
            'Dest Post Tax State': self.dest_post_tax_state,
            'Dest Post Tax Class': self.dest_post_tax_class,
            'Dest Batch Post Owner': self.dest_batch_post_owner,
            'Dest Batch Post Bond': self.dest_batch_post_bond,
            'Dest Program Post': self.dest_program_post,
            'Dest Grading Post': self.dest_grading_post,
            'Dest State Post': self.dest_state_post,
            'Dest DSP Account Post': self.dest_dsp_account_post,
            'Dest Vol Post': self.dest_vol_post,
            'Dest Vol Change': self.dest_vol_change,
            'Dest Alcohol Pre': self.dest_alcohol_pre,
            'Dest Proof Pre': self.dest_proof_pre,
            'Dest Proof Gallons Pre': self.dest_proof_gallons_pre,
            'Dest Alcohol Post': self.dest_alcohol_post,
            'Dest Proof Post': self.dest_proof_post,
            'Dest Proof Gallons Post': self.dest_proof_gallons_post,
            'Dest Vol Proof Gal Change': self.dest_vol_proof_gal_change,
            'Loss/Gain Amount (gal)': self.loss_gain_amount,
            'Loss/Gain Amount (proof gal)': self.loss_gain_amount_proof,
            'Loss/Gain Reason': self.loss_gain_reason,
            'NET': self.net
        }


class BatchLineage:
    """Represents the complete lineage of a vessel-batch"""
    
    def __init__(self, batch_name: str):
        self.batch_name = batch_name
        self.contributing_batches: Dict[str, float] = {}  # batch_name -> total gallons contributed
        self.contributing_transactions: List[Transaction] = []
        self.outgoing_transactions: List[Transaction] = []
        self.losses: List[Dict] = []  # List of loss/gain records with reason
        self.current_volume = 0.0
        self.is_on_hand = False
        self.has_left_inventory = False
        
    def add_incoming_transaction(self, transaction: Transaction, gallons: float):
        """Add a transaction that contributed to this batch
        
        Now accounts for pre/post batch states:
        - Uses src_batch_pre as the source batch for lineage tracking
        - Tracks the actual contributing batch properly
        """
        # Use the pre-transaction source batch name for lineage tracking
        source_batch = transaction.src_batch_pre or transaction.from_batch
        if source_batch and source_batch != self.batch_name:
            if source_batch not in self.contributing_batches:
                self.contributing_batches[source_batch] = 0.0
            self.contributing_batches[source_batch] += gallons
        self.contributing_transactions.append(transaction)
        
        # Track losses/gains for this transaction
        if transaction.loss_gain_amount != 0:
            self.losses.append({
                'amount': transaction.loss_gain_amount,
                'reason': transaction.loss_gain_reason,
                'op_date': transaction.op_date,
                'op_id': transaction.op_id,
                'op_type': transaction.op_type
            })
        
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
            'losses': self.losses,
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
        """Build the lineage relationships from transactions
        
        This method accounts for:
        - Pre/post batch states (batch identity can change during transactions)
        - Volume changes using Src Vol Change and Dest Vol Change for accurate gallon tracking
        - Source batches may have different pre/post names (Src Batch Pre/Post)
        - Destination batches may have different pre/post names (Dest Batch Pre/Post)
        
        Volume Tracking:
        - Uses Dest Vol Change for incoming transactions (gallons arriving at destination)
        - Uses Src Vol Change for adjustments when Dest Vol Change is 0
        - NET field is not used for lineage tracking as it often equals 0
        """
        logger.info("Building lineage relationships...")
        
        # First pass: create all batch lineage objects for all batch variants
        all_batches = set()
        for trans in self.transactions:
            # Add source batch variants (pre and post states)
            if trans.src_batch_pre:
                all_batches.add(trans.src_batch_pre)
            if trans.src_batch_post:
                all_batches.add(trans.src_batch_post)
            
            # Add destination batch variants (pre and post states)
            if trans.dest_batch_pre:
                all_batches.add(trans.dest_batch_pre)
            if trans.dest_batch_post:
                all_batches.add(trans.dest_batch_post)
            
            # Add legacy field values for backward compatibility
            if trans.from_batch:
                all_batches.add(trans.from_batch)
            if trans.to_batch:
                all_batches.add(trans.to_batch)
                
        for batch in all_batches:
            self.batch_lineages[batch] = BatchLineage(batch)
            
        # Second pass: populate lineage relationships
        for trans in self.transactions:
            # Determine actual source and destination batches
            # For lineage tracking, we use:
            # - Source: the pre-transaction batch (what it was called before)
            # - Destination: the post-transaction batch (what it's called after)
            src_batch = trans.src_batch_pre or trans.from_batch
            dest_batch = trans.dest_batch_post or trans.to_batch
            
            # Also track if batch identity changed during transaction
            src_batch_post = trans.src_batch_post or trans.from_batch
            dest_batch_pre = trans.dest_batch_pre or trans.to_batch
            
            # Handle different operation types
            if trans.op_type == 'On-Hand':
                # This batch is currently in inventory
                # Use the post-transaction batch name as that's the current state
                current_batch = dest_batch or dest_batch_pre
                if current_batch and current_batch in self.batch_lineages:
                    self.batch_lineages[current_batch].is_on_hand = True
                    # Use dest_vol_post as the current volume for on-hand batches
                    self.batch_lineages[current_batch].current_volume = trans.dest_vol_post
                    
            elif trans.op_type in ['Transfer', 'Blend', 'Receipt']:
                # Material moved from one batch to another
                # Track lineage from source to destination
                # Use dest_vol_change to track how much arrived at the destination
                if dest_batch and dest_batch in self.batch_lineages:
                    self.batch_lineages[dest_batch].add_incoming_transaction(trans, abs(trans.dest_vol_change))
                    
                if src_batch and src_batch in self.batch_lineages:
                    self.batch_lineages[src_batch].add_outgoing_transaction(trans)
                    # Mark that this batch has left (at least partially)
                    if trans.op_type != 'Receipt':  # Receipts don't indicate leaving
                        self.batch_lineages[src_batch].has_left_inventory = True
                
                # If batch identity changed during transaction, track that relationship
                if src_batch_post and src_batch_post != src_batch and src_batch_post in self.batch_lineages:
                    # Source batch changed its name, track the outgoing from the new name too
                    self.batch_lineages[src_batch_post].add_outgoing_transaction(trans)
                    
                if dest_batch_pre and dest_batch_pre != dest_batch and dest_batch_pre in self.batch_lineages:
                    # Destination batch had a different name before, track incoming to the old name too
                    self.batch_lineages[dest_batch_pre].add_incoming_transaction(trans, abs(trans.dest_vol_change))
                        
            elif trans.op_type in ['Adjustment', 'Measurement', 'Treatment', 'Analysis']:
                # Adjustments, measurements, treatments affect the batch but may not indicate movement
                # These can change batch properties (tax state, grading, etc.) without moving volume
                # Use dest_vol_change if available, otherwise src_vol_change
                target_batch = dest_batch or dest_batch_pre or src_batch_post or src_batch
                if target_batch and target_batch in self.batch_lineages:
                    # For adjustments, use dest_vol_change if available and non-zero, otherwise src_vol_change
                    volume_change = abs(trans.dest_vol_change) if trans.dest_vol_change != 0 else abs(trans.src_vol_change)
                    self.batch_lineages[target_batch].add_incoming_transaction(trans, volume_change)
                    
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
    
    def export_detailed_lineage_to_csv(self, output_file: str, batch_filter: Optional[str] = None):
        """
        Export detailed lineage relationships to CSV with pre/post batch information
        
        This export includes batch state changes (pre/post) for better lineage tracking.
        Each row represents a transaction showing how batches changed during the operation.
        
        Args:
            output_file: Path to output CSV file
            batch_filter: Optional filter - 'on-hand', 'shipped', or None for all
        """
        logger.info(f"Exporting detailed lineage with pre/post batch states to {output_file}")
        
        rows = []
        for batch_name, lineage in self.batch_lineages.items():
            # Apply filter
            if batch_filter == 'on-hand' and not lineage.is_on_hand:
                continue
            elif batch_filter == 'shipped' and not lineage.has_left_inventory:
                continue
            
            # Export each contributing transaction with detailed pre/post information
            for trans in lineage.contributing_transactions:
                rows.append({
                    'Destination_Batch': batch_name,
                    'Op_Date': trans.op_date,
                    'Tx_Id': trans.tx_id,
                    'Op_Id': trans.op_id,
                    'Op_Type': trans.op_type,
                    'Txn_Type': trans.txn_type,
                    'Work_Order': trans.work_order,
                    # Source batch information
                    'Src_Vessel': trans.src_vessel,
                    'Src_Batch_Pre': trans.src_batch_pre,
                    'Src_Batch_Post': trans.src_batch_post,
                    'Src_Batch_Changed': 'Yes' if (trans.src_batch_pre != trans.src_batch_post and 
                                                     trans.src_batch_pre and trans.src_batch_post and 
                                                     trans.src_batch_post != '--') else 'No',
                    'Src_Vol_Pre': trans.src_vol_pre,
                    'Src_Vol_Post': trans.src_vol_post,
                    'Src_Vol_Change': trans.src_vol_change,
                    'Src_Tax_State_Pre': trans.src_pre_tax_state,
                    'Src_Tax_State_Post': trans.src_post_tax_state,
                    'Src_Owner_Pre': trans.src_batch_pre_owner,
                    'Src_Owner_Post': trans.src_batch_post_owner,
                    'Src_Program_Pre': trans.src_program_pre,
                    'Src_Program_Post': trans.src_program_post,
                    'Src_State_Pre': trans.src_state_pre,
                    'Src_State_Post': trans.src_state_post,
                    # Destination batch information
                    'Dest_Vessel': trans.dest_vessel,
                    'Dest_Batch_Pre': trans.dest_batch_pre,
                    'Dest_Batch_Post': trans.dest_batch_post,
                    'Dest_Batch_Changed': 'Yes' if (trans.dest_batch_pre != trans.dest_batch_post and 
                                                      trans.dest_batch_pre and trans.dest_batch_post and 
                                                      trans.dest_batch_post != '--') else 'No',
                    'Dest_Vol_Pre': trans.dest_vol_pre,
                    'Dest_Vol_Post': trans.dest_vol_post,
                    'Dest_Vol_Change': trans.dest_vol_change,
                    'Dest_Tax_State_Pre': trans.dest_pre_tax_state,
                    'Dest_Tax_State_Post': trans.dest_post_tax_state,
                    'Dest_Owner_Pre': trans.dest_batch_pre_owner,
                    'Dest_Owner_Post': trans.dest_batch_post_owner,
                    'Dest_Program_Pre': trans.dest_program_pre,
                    'Dest_Program_Post': trans.dest_program_post,
                    'Dest_State_Pre': trans.dest_state_pre,
                    'Dest_State_Post': trans.dest_state_post,
                    # Transaction details
                    'NET': trans.net,
                    'Loss_Gain_Amount_Gal': trans.loss_gain_amount,
                    'Loss_Gain_Amount_Proof_Gal': trans.loss_gain_amount_proof,
                    'Loss_Gain_Reason': trans.loss_gain_reason,
                    # Lineage context
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
            logger.info(f"Exported {len(rows)} detailed lineage records")
        else:
            logger.warning("No lineage relationships to export")
        
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
    
    # Export detailed lineage with pre/post batch information
    analyzer.export_detailed_lineage_to_csv(str(output_dir / 'detailed_lineage_with_pre_post.csv'))
    
    # Export all transactions
    analyzer.export_transactions_to_csv(str(output_dir / 'all_transactions.csv'))
    
    # Export to JSON
    analyzer.export_to_json(str(output_dir / 'complete_lineage.json'))
    
    print(f"\n{'='*80}")
    print("EXPORTS COMPLETE")
    print(f"{'='*80}")
    print(f"Output directory: {output_dir}")
    print(f"  - batch_lineage.csv (simple lineage relationships)")
    print(f"  - batch_lineage_on_hand.csv (only on-hand batches)")
    print(f"  - detailed_lineage_with_pre_post.csv (lineage with batch state changes)")
    print(f"  - all_transactions.csv (all transactions with full details)")
    print(f"  - complete_lineage.json (full data)")
    print()


if __name__ == '__main__':
    main()
