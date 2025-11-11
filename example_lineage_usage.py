#!/usr/bin/env python3
"""
Example: Using the Transaction Lineage Analyzer as a Python module

This script demonstrates how to use the transaction_lineage_analyzer module
programmatically in your own scripts.
"""

from transaction_lineage_analyzer import TransactionLineageAnalyzer
import json


def example_basic_usage():
    """Basic usage example"""
    print("="*80)
    print("EXAMPLE 1: Basic Usage")
    print("="*80)
    
    # Load the analyzer
    analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
    
    print(f"\nLoaded {len(analyzer.transactions)} transactions")
    print(f"Tracking {len(analyzer.batch_lineages)} unique batches")
    print()


def example_get_lineage():
    """Get lineage for a specific batch"""
    print("="*80)
    print("EXAMPLE 2: Get Lineage for a Specific Batch")
    print("="*80)
    
    analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
    
    # Get lineage for a specific batch
    batch_name = '24BLEND001'
    lineage = analyzer.get_batch_lineage(batch_name)
    
    if lineage:
        print(f"\nBatch: {batch_name}")
        print(f"Current Volume: {lineage.current_volume} gallons")
        print(f"Is On-Hand: {lineage.is_on_hand}")
        print(f"Has Left Inventory: {lineage.has_left_inventory}")
        print(f"\nContributing Batches ({len(lineage.contributing_batches)}):")
        for batch, gallons in lineage.contributing_batches.items():
            print(f"  - {batch}: {gallons} gallons")
    print()


def example_on_hand_inventory():
    """Get all on-hand inventory"""
    print("="*80)
    print("EXAMPLE 3: Current On-Hand Inventory")
    print("="*80)
    
    analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
    
    on_hand_batches = analyzer.get_all_on_hand_batches()
    
    print(f"\nFound {len(on_hand_batches)} batches currently on-hand:\n")
    
    for batch_name in on_hand_batches:
        lineage = analyzer.get_batch_lineage(batch_name)
        print(f"{batch_name:30} : {lineage.current_volume:>10.2f} gallons")
        
        # Show contributing batches
        if lineage.contributing_batches:
            print(f"  Contributing from {len(lineage.contributing_batches)} source batch(es):")
            for contrib, gal in lineage.contributing_batches.items():
                print(f"    - {contrib}: {gal} gal")
        else:
            print(f"  (Origin batch - no contributors)")
        print()


def example_full_lineage_tree():
    """Get full recursive lineage tree"""
    print("="*80)
    print("EXAMPLE 4: Full Lineage Tree (Recursive)")
    print("="*80)
    
    analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
    
    # Get full lineage tree for a final product
    batch_name = '24BLEND001-FINAL'
    tree = analyzer.get_full_lineage_tree(batch_name)
    
    print(f"\nFull lineage tree for {batch_name}:\n")
    print(json.dumps(tree, indent=2))
    print()


def example_generate_report():
    """Generate a formatted report"""
    print("="*80)
    print("EXAMPLE 5: Generate Formatted Report")
    print("="*80)
    
    analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
    
    # Generate report for a batch
    batch_name = '24IMPORT002'
    report = analyzer.generate_lineage_report(batch_name)
    
    print(report)
    print()


def example_analyze_losses():
    """Analyze losses across all transactions"""
    print("="*80)
    print("EXAMPLE 6: Analyze Losses and Gains")
    print("="*80)
    
    analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
    
    # Calculate total losses by reason
    losses_by_reason = {}
    total_loss = 0
    
    for trans in analyzer.transactions:
        if trans.loss_gain_amount > 0:
            reason = trans.loss_gain_reason or 'Unknown'
            if reason not in losses_by_reason:
                losses_by_reason[reason] = 0
            losses_by_reason[reason] += trans.loss_gain_amount
            total_loss += trans.loss_gain_amount
    
    print(f"\nTotal losses: {total_loss:.2f} gallons\n")
    print("Breakdown by reason:")
    for reason, amount in sorted(losses_by_reason.items(), key=lambda x: x[1], reverse=True):
        percentage = (amount / total_loss * 100) if total_loss > 0 else 0
        print(f"  {reason:20} : {amount:>8.2f} gal ({percentage:>5.1f}%)")
    print()


def example_export_for_powerbi():
    """Export data for Power BI"""
    print("="*80)
    print("EXAMPLE 7: Export Data for Power BI")
    print("="*80)
    
    analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
    
    # Export different formats
    print("\nExporting data in multiple formats...")
    
    # All lineage relationships
    analyzer.export_lineage_to_csv('example_exports/all_lineage.csv')
    print("✓ Exported all_lineage.csv (simple lineage)")
    
    # Only on-hand batches
    analyzer.export_lineage_to_csv('example_exports/on_hand_lineage.csv', batch_filter='on-hand')
    print("✓ Exported on_hand_lineage.csv (only on-hand)")
    
    # Detailed lineage with pre/post batch tracking
    analyzer.export_detailed_lineage_to_csv('example_exports/detailed_lineage_with_pre_post.csv')
    print("✓ Exported detailed_lineage_with_pre_post.csv (with batch state changes)")
    
    # All transactions
    analyzer.export_transactions_to_csv('example_exports/all_transactions.csv')
    print("✓ Exported all_transactions.csv (full transaction data)")
    
    # Complete JSON
    analyzer.export_to_json('example_exports/complete_data.json')
    print("✓ Exported complete_data.json")
    
    print("\nFiles ready for Power BI import!")
    print()


def example_batch_state_changes():
    """Show examples of batch state changes during transactions"""
    print("="*80)
    print("EXAMPLE 9: Batch State Changes During Transactions")
    print("="*80)
    
    analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
    
    print("\nFinding transactions where batch identity changed...\n")
    
    # Find examples of batch state changes
    changes_found = 0
    for trans in analyzer.transactions:
        # Check if source batch changed
        src_changed = (trans.src_batch_pre != trans.src_batch_post and 
                      trans.src_batch_pre and trans.src_batch_post and 
                      trans.src_batch_post != '--')
        
        # Check if destination batch changed
        dest_changed = (trans.dest_batch_pre != trans.dest_batch_post and 
                       trans.dest_batch_pre and trans.dest_batch_post and 
                       trans.dest_batch_post != '--')
        
        if src_changed or dest_changed:
            changes_found += 1
            if changes_found <= 5:  # Show first 5 examples
                print(f"Example {changes_found}:")
                print(f"  Date: {trans.op_date}")
                print(f"  Op Type: {trans.op_type}")
                print(f"  Op ID: {trans.op_id}")
                
                if src_changed:
                    print(f"  Source batch changed:")
                    print(f"    Pre:  {trans.src_batch_pre} ({trans.src_pre_tax_state})")
                    print(f"    Post: {trans.src_batch_post} ({trans.src_post_tax_state})")
                    
                if dest_changed:
                    print(f"  Destination batch changed:")
                    print(f"    Pre:  {trans.dest_batch_pre} ({trans.dest_pre_tax_state})")
                    print(f"    Post: {trans.dest_batch_post} ({trans.dest_post_tax_state})")
                
                print(f"  NET: {trans.net} gallons")
                print()
    
    print(f"Total transactions with batch identity changes: {changes_found}")
    print("This demonstrates why pre/post batch tracking is critical for accurate lineage!")
    print()

def example_trace_batch_history():
    """Trace the complete history of a batch"""
    print("="*80)
    print("EXAMPLE 8: Trace Complete Batch History")
    print("="*80)
    
    analyzer = TransactionLineageAnalyzer('Transaction_to_analysise.csv')
    
    batch_name = '24BLEND001'
    lineage = analyzer.get_batch_lineage(batch_name)
    
    if lineage:
        print(f"\nComplete history for {batch_name}:\n")
        
        # Show all incoming transactions
        print(f"INCOMING TRANSACTIONS ({len(lineage.contributing_transactions)}):")
        for trans in lineage.contributing_transactions:
            print(f"  {trans.op_date} | {trans.op_type:12} | "
                  f"{trans.from_batch:20} → {trans.to_batch:20} | "
                  f"{trans.net:>8.2f} gal | "
                  f"Loss: {trans.loss_gain_amount:>5.2f} ({trans.loss_gain_reason})")
        
        # Show all outgoing transactions
        if lineage.outgoing_transactions:
            print(f"\nOUTGOING TRANSACTIONS ({len(lineage.outgoing_transactions)}):")
            for trans in lineage.outgoing_transactions:
                print(f"  {trans.op_date} | {trans.op_type:12} | "
                      f"{trans.from_batch:20} → {trans.to_batch:20} | "
                      f"{trans.net:>8.2f} gal")
    print()


def main():
    """Run all examples"""
    
    print("\n" + "="*80)
    print("TRANSACTION LINEAGE ANALYZER - PYTHON API EXAMPLES")
    print("="*80 + "\n")
    
    # Run all examples
    example_basic_usage()
    example_get_lineage()
    example_on_hand_inventory()
    example_full_lineage_tree()
    example_generate_report()
    example_analyze_losses()
    example_trace_batch_history()
    example_batch_state_changes()  # NEW: Show batch state changes
    
    # Create export directory for last example
    import os
    os.makedirs('example_exports', exist_ok=True)
    example_export_for_powerbi()
    
    print("="*80)
    print("ALL EXAMPLES COMPLETE!")
    print("="*80)
    print("\nCheck the example_exports/ directory for exported files.")
    print()


if __name__ == '__main__':
    main()
