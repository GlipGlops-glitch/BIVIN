"""
Utility functions for working with Vintrace API

Provides helper functions for common data fetching and processing tasks.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .vintrace_api_client import VintraceAPIClient


class VintraceDataFetcher:
    """Helper class for fetching and processing Vintrace data"""
    
    def __init__(self, client: VintraceAPIClient):
        """
        Initialize the data fetcher
        
        Args:
            client: Configured VintraceAPIClient instance
        """
        self.client = client
    
    def get_all_work_orders(self, **filters) -> List[Dict[str, Any]]:
        """
        Fetch all work orders across all pages
        
        Args:
            **filters: Optional filters (assignedTo, workOrderState, fromDate, toDate, etc.)
        
        Returns:
            List of all work orders
        """
        return self.client.get_all_pages(self.client.list_available_work_orders, **filters)
    
    def get_all_products(self, **filters) -> List[Dict[str, Any]]:
        """
        Fetch all products across all pages
        
        Args:
            **filters: Optional filters for products
        
        Returns:
            List of all products
        """
        return self.client.get_all_pages(self.client.list_available_products, **filters)
    
    def get_all_sales_orders(self, **filters) -> List[Dict[str, Any]]:
        """
        Fetch all sales orders across all pages
        
        Args:
            **filters: Optional filters for sales orders
        
        Returns:
            List of all sales orders
        """
        return self.client.get_all_pages(self.client.list_available_sales_orders, **filters)
    
    def get_all_parties(self, **filters) -> List[Dict[str, Any]]:
        """
        Fetch all parties across all pages
        
        Args:
            **filters: Optional filters for parties
        
        Returns:
            List of all parties
        """
        return self.client.get_all_pages(self.client.list_parties, **filters)
    
    def get_all_refunds(self, **filters) -> List[Dict[str, Any]]:
        """
        Fetch all refunds across all pages
        
        Args:
            **filters: Optional filters for refunds
        
        Returns:
            List of all refunds
        """
        return self.client.get_all_pages(self.client.list_available_refunds, **filters)
    
    def get_recent_work_orders(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get work orders from the last N days
        
        Args:
            days: Number of days to look back (default: 7)
        
        Returns:
            List of recent work orders
        """
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        return self.get_all_work_orders(fromDate=from_date, toDate=to_date)
    
    def search_transactions(self, **criteria) -> List[Dict[str, Any]]:
        """
        Search for transactions with given criteria
        
        Args:
            **criteria: Search criteria for transactions
        
        Returns:
            List of matching transactions
        """
        return self.client.get_all_pages(self.client.transaction_search, **criteria)
    
    def get_stock_details(self, stock_id: str) -> Dict[str, Any]:
        """
        Get complete stock details including all related information
        
        Args:
            stock_id: The stock item ID
        
        Returns:
            Dictionary with complete stock information
        """
        stock = self.client.view_a_single_stock_item(id=stock_id)
        
        # Fetch related data
        try:
            stock['fields'] = self.client.view_list_of_details_fields(id=stock_id)
        except:
            stock['fields'] = []
        
        try:
            stock['distributions'] = self.client.view_distribtutions(id=stock_id)
        except:
            stock['distributions'] = []
        
        try:
            stock['history'] = self.client.view_history_items(id=stock_id)
        except:
            stock['history'] = []
        
        try:
            stock['components'] = self.client.view_raw_components(id=stock_id)
        except:
            stock['components'] = []
        
        try:
            stock['notes'] = self.client.view_all_notes(id=stock_id)
        except:
            stock['notes'] = []
        
        try:
            stock['bulk_info'] = self.client.view_bulk_product_details(id=stock_id)
        except:
            stock['bulk_info'] = {}
        
        return stock
    
    def get_inventory_summary(self, **filters) -> Dict[str, Any]:
        """
        Get inventory summary with optional filters
        
        Args:
            **filters: Optional filters for inventory
        
        Returns:
            Inventory summary data
        """
        return self.client.list_available_stock(**filters)
    
    def search_intake_operations(self, **criteria) -> List[Dict[str, Any]]:
        """
        Search for fruit intake operations
        
        Args:
            **criteria: Search criteria
        
        Returns:
            List of matching intake operations
        """
        return self.client.get_all_pages(self.client.fruit_intake_operation_search, **criteria)
    
    def search_sample_operations(self, **criteria) -> List[Dict[str, Any]]:
        """
        Search for maturity samples
        
        Args:
            **criteria: Search criteria
        
        Returns:
            List of matching sample operations
        """
        return self.client.get_all_pages(self.client.maturity_samples_search, **criteria)


def create_client_from_env() -> VintraceAPIClient:
    """
    Create a VintraceAPIClient from environment variables
    
    Expected environment variables:
        VINTRACE_BASE_URL: Base URL for the API
        VINTRACE_API_KEY: API key (optional)
        VINTRACE_USERNAME: Username for basic auth (optional)
        VINTRACE_PASSWORD: Password for basic auth (optional)
    
    Returns:
        Configured VintraceAPIClient instance
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    base_url = os.getenv('VINTRACE_BASE_URL')
    if not base_url:
        raise ValueError("VINTRACE_BASE_URL environment variable is required")
    
    api_key = os.getenv('VINTRACE_API_KEY')
    username = os.getenv('VINTRACE_USERNAME')
    password = os.getenv('VINTRACE_PASSWORD')
    
    return VintraceAPIClient(
        base_url=base_url,
        api_key=api_key,
        username=username,
        password=password
    )
