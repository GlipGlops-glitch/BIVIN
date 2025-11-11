"""
Generate Pydantic models and API client from OpenAPI specification

This script parses the vintrace-v6-apis.yaml file and generates:
1. Pydantic models for all schemas
2. API client with methods for all endpoints
3. Helper utilities for data fetching
"""

import yaml
import re
from typing import Dict, Any, List, Set
from pathlib import Path


def to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case"""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def to_pascal_case(name: str) -> str:
    """Convert string to PascalCase"""
    return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))


def get_python_type(schema: Dict[str, Any], schemas: Dict[str, Any]) -> str:
    """Convert OpenAPI schema type to Python type hint"""
    if '$ref' in schema:
        ref_name = schema['$ref'].split('/')[-1]
        return ref_name
    
    schema_type = schema.get('type', 'Any')
    schema_format = schema.get('format', '')
    
    if schema_type == 'string':
        if schema_format == 'date':
            return 'date'
        elif schema_format == 'date-time':
            return 'datetime'
        return 'str'
    elif schema_type == 'integer':
        return 'int'
    elif schema_type == 'number':
        return 'float'
    elif schema_type == 'boolean':
        return 'bool'
    elif schema_type == 'array':
        items = schema.get('items', {})
        item_type = get_python_type(items, schemas)
        return f'List[{item_type}]'
    elif schema_type == 'object':
        if 'properties' in schema:
            return 'Dict[str, Any]'
        elif 'additionalProperties' in schema:
            additional = schema['additionalProperties']
            if isinstance(additional, dict):
                value_type = get_python_type(additional, schemas)
                return f'Dict[str, {value_type}]'
            return 'Dict[str, Any]'
        return 'Dict[str, Any]'
    
    return 'Any'


def generate_model_class(name: str, schema: Dict[str, Any], schemas: Dict[str, Any]) -> str:
    """Generate a Pydantic model class from schema"""
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    description = schema.get('description', '')
    
    lines = []
    lines.append(f"class {name}(BaseModel):")
    
    if description:
        lines.append(f'    """{description}"""')
    
    if not properties:
        lines.append("    pass")
        return '\n'.join(lines)
    
    for prop_name, prop_schema in properties.items():
        prop_type = get_python_type(prop_schema, schemas)
        is_required = prop_name in required
        prop_description = prop_schema.get('description', '')
        
        # Handle optional fields
        if not is_required:
            prop_type = f'Optional[{prop_type}]'
        
        # Field definition
        field_line = f"    {prop_name}: {prop_type}"
        
        if not is_required:
            field_line += " = None"
        
        if prop_description:
            lines.append(f"    # {prop_description}")
        
        lines.append(field_line)
    
    lines.append("")
    return '\n'.join(lines)


def generate_models_file(spec: Dict[str, Any]) -> str:
    """Generate the complete models.py file"""
    schemas = spec.get('components', {}).get('schemas', {})
    
    lines = []
    lines.append('"""')
    lines.append('Pydantic models for Vintrace V6 API')
    lines.append('')
    lines.append('Auto-generated from vintrace-v6-apis.yaml')
    lines.append('"""')
    lines.append('')
    lines.append('from __future__ import annotations')
    lines.append('from typing import Optional, List, Dict, Any')
    lines.append('from datetime import date, datetime')
    lines.append('from pydantic import BaseModel, Field')
    lines.append('')
    lines.append('')
    
    # Generate all models
    for schema_name in sorted(schemas.keys()):
        schema = schemas[schema_name]
        model_code = generate_model_class(schema_name, schema, schemas)
        lines.append(model_code)
        lines.append('')
    
    return '\n'.join(lines)


def get_endpoint_params(parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract and format endpoint parameters"""
    params = []
    for param in parameters or []:
        params.append({
            'name': param.get('name'),
            'in': param.get('in'),
            'required': param.get('required', False),
            'type': param.get('schema', {}).get('type', 'str'),
            'description': param.get('description', '')
        })
    return params


def generate_api_method(path: str, method: str, operation: Dict[str, Any]) -> str:
    """Generate a method for an API endpoint"""
    operation_id = operation.get('operationId', '')
    summary = operation.get('summary', '')
    description = operation.get('description', '')
    parameters = operation.get('parameters', [])
    
    # Create method name from operation ID or path
    if operation_id:
        method_name = to_snake_case(operation_id.replace(' ', '_'))
    else:
        method_name = to_snake_case(path.replace('/', '_').replace('{', '').replace('}', ''))
        method_name = f"{method}_{method_name}"
    
    # Clean up method name
    method_name = re.sub(r'_+', '_', method_name).strip('_')
    
    lines = []
    
    # Build parameter list
    params_list = ["self"]
    
    # Add path parameters
    path_params = [p for p in parameters if p.get('in') == 'path']
    for param in path_params:
        param_name = param.get('name')
        params_list.append(f"{param_name}: str")
    
    # Add query parameters
    query_params = [p for p in parameters if p.get('in') == 'query']
    for param in query_params:
        param_name = param.get('name')
        param_type = param.get('schema', {}).get('type', 'str')
        python_type = {'string': 'str', 'integer': 'int', 'boolean': 'bool', 'number': 'float'}.get(param_type, 'str')
        
        if param.get('required'):
            params_list.append(f"{param_name}: {python_type}")
        else:
            params_list.append(f"{param_name}: Optional[{python_type}] = None")
    
    # Add request body for POST/PUT
    if method in ['post', 'put', 'patch']:
        params_list.append(f"data: Optional[Dict[str, Any]] = None")
    
    # Format method signature (with line wrapping if needed)
    method_signature = f"    def {method_name}("
    if len(params_list) <= 3 or len(', '.join(params_list)) < 80:
        method_signature += ', '.join(params_list) + ") -> Dict[str, Any]:"
        lines.append(method_signature)
    else:
        lines.append(f"    def {method_name}(")
        for i, param in enumerate(params_list):
            if i < len(params_list) - 1:
                lines.append(f"        {param},")
            else:
                lines.append(f"        {param}) -> Dict[str, Any]:")
    
    
    # Add docstring
    doc_lines = []
    if summary:
        doc_lines.append(f'        """{summary}')
    else:
        doc_lines.append(f'        """')
    
    if description:
        doc_lines.append(f"        ")
        doc_lines.append(f"        {description}")
    
    if parameters:
        doc_lines.append(f"        ")
        doc_lines.append(f"        Args:")
        for param in parameters:
            param_name = param.get('name')
            param_desc = param.get('description', '')
            doc_lines.append(f"            {param_name}: {param_desc}")
    
    doc_lines.append(f'        """')
    lines.extend(doc_lines)
    
    # Build URL
    url_path = path
    for param in path_params:
        param_name = param.get('name')
        url_path = url_path.replace(f'{{{param_name}}}', f'{{{param_name}}}')
    
    lines.append(f'        url = f"{url_path}"')
    
    # Build params dict for query parameters
    if query_params:
        lines.append("        params = {}")
        for param in query_params:
            param_name = param.get('name')
            lines.append(f"        if {param_name} is not None:")
            lines.append(f"            params['{param_name}'] = {param_name}")
    else:
        lines.append("        params = None")
    
    # Make request
    if method in ['post', 'put', 'patch']:
        lines.append(f"        return self._request('{method.upper()}', url, params=params, json=data)")
    else:
        lines.append(f"        return self._request('{method.upper()}', url, params=params)")
    
    lines.append("")
    return '\n'.join(lines)


def generate_api_client_file(spec: Dict[str, Any]) -> str:
    """Generate the complete api_client.py file"""
    paths = spec.get('paths', {})
    
    lines = []
    lines.append('"""')
    lines.append('Vintrace V6 API Client')
    lines.append('')
    lines.append('Auto-generated from vintrace-v6-apis.yaml')
    lines.append('"""')
    lines.append('')
    lines.append('import requests')
    lines.append('from typing import Optional, Dict, Any, List')
    lines.append('from datetime import datetime')
    lines.append('import time')
    lines.append('')
    lines.append('')
    lines.append('class VintraceAPIClient:')
    lines.append('    """Client for Vintrace V6 API')
    lines.append('    ')
    lines.append('    This client provides methods for all Vintrace API endpoints.')
    lines.append('    ')
    lines.append('    Example:')
    lines.append('        client = VintraceAPIClient(')
    lines.append('            base_url="https://your-instance.vintrace.net/vinx2/api/v6",')
    lines.append('            api_key="your-api-key"')
    lines.append('        )')
    lines.append('        work_orders = client.list_available_work_orders()')
    lines.append('    """')
    lines.append('')
    lines.append('    def __init__(self, base_url: str, api_key: Optional[str] = None,')
    lines.append('                 username: Optional[str] = None, password: Optional[str] = None,')
    lines.append('                 timeout: int = 30, max_retries: int = 3):')
    lines.append('        """')
    lines.append('        Initialize the Vintrace API client')
    lines.append('        ')
    lines.append('        Args:')
    lines.append('            base_url: Base URL for the Vintrace API (e.g., "https://your-instance.vintrace.net/vinx2/api/v6")')
    lines.append('            api_key: API key for authentication (optional)')
    lines.append('            username: Username for basic auth (optional)')
    lines.append('            password: Password for basic auth (optional)')
    lines.append('            timeout: Request timeout in seconds (default: 30)')
    lines.append('            max_retries: Maximum number of retries for failed requests (default: 3)')
    lines.append('        """')
    lines.append('        self.base_url = base_url.rstrip("/")')
    lines.append('        self.api_key = api_key')
    lines.append('        self.username = username')
    lines.append('        self.password = password')
    lines.append('        self.timeout = timeout')
    lines.append('        self.max_retries = max_retries')
    lines.append('        self.session = requests.Session()')
    lines.append('        ')
    lines.append('        # Set up authentication headers')
    lines.append('        if api_key:')
    lines.append('            self.session.headers.update({"Authorization": f"Bearer {api_key}"})')
    lines.append('        elif username and password:')
    lines.append('            self.session.auth = (username, password)')
    lines.append('        ')
    lines.append('        self.session.headers.update({"Accept": "application/json"})')
    lines.append('')
    lines.append('    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:')
    lines.append('        """Make an HTTP request with retry logic"""')
    lines.append('        url = f"{self.base_url}{path}"')
    lines.append('        kwargs.setdefault("timeout", self.timeout)')
    lines.append('        ')
    lines.append('        for attempt in range(self.max_retries):')
    lines.append('            try:')
    lines.append('                response = self.session.request(method, url, **kwargs)')
    lines.append('                response.raise_for_status()')
    lines.append('                ')
    lines.append('                # Handle empty responses')
    lines.append('                if not response.content:')
    lines.append('                    return {}')
    lines.append('                ')
    lines.append('                return response.json()')
    lines.append('            except requests.exceptions.HTTPError as e:')
    lines.append('                if attempt == self.max_retries - 1:')
    lines.append('                    raise')
    lines.append('                # Retry on 5xx errors')
    lines.append('                if e.response.status_code >= 500:')
    lines.append('                    time.sleep(2 ** attempt)')
    lines.append('                    continue')
    lines.append('                raise')
    lines.append('            except requests.exceptions.RequestException as e:')
    lines.append('                if attempt == self.max_retries - 1:')
    lines.append('                    raise')
    lines.append('                time.sleep(2 ** attempt)')
    lines.append('        ')
    lines.append('        raise Exception(f"Failed to {method} {url} after {self.max_retries} attempts")')
    lines.append('')
    lines.append('    def get_all_pages(self, method_func, **kwargs) -> List[Dict[str, Any]]:')
    lines.append('        """')
    lines.append('        Fetch all pages from a paginated endpoint')
    lines.append('        ')
    lines.append('        Args:')
    lines.append('            method_func: The API method to call (e.g., self.list_available_work_orders)')
    lines.append('            **kwargs: Arguments to pass to the method')
    lines.append('        ')
    lines.append('        Returns:')
    lines.append('            List of all results from all pages')
    lines.append('        """')
    lines.append('        all_results = []')
    lines.append('        first_result = 0')
    lines.append('        max_result = kwargs.get("max", 100)')
    lines.append('        ')
    lines.append('        while True:')
    lines.append('            kwargs["first"] = str(first_result)')
    lines.append('            kwargs["max"] = str(max_result)')
    lines.append('            ')
    lines.append('            response = method_func(**kwargs)')
    lines.append('            ')
    lines.append('            # Handle different response formats')
    lines.append('            if isinstance(response, dict):')
    lines.append('                results = response.get("results", [])')
    lines.append('                total = response.get("totalResultCount", 0)')
    lines.append('            else:')
    lines.append('                results = response if isinstance(response, list) else []')
    lines.append('                total = len(results)')
    lines.append('            ')
    lines.append('            all_results.extend(results)')
    lines.append('            ')
    lines.append('            # Check if there are more pages')
    lines.append('            if len(all_results) >= total:')
    lines.append('                break')
    lines.append('            ')
    lines.append('            first_result += max_result')
    lines.append('        ')
    lines.append('        return all_results')
    lines.append('')
    lines.append('    # =================================================================')
    lines.append('    # API ENDPOINTS')
    lines.append('    # =================================================================')
    lines.append('')
    
    # Generate methods for each endpoint
    for path, methods in sorted(paths.items()):
        for method, operation in methods.items():
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                method_code = generate_api_method(path, method.lower(), operation)
                lines.append(method_code)
    
    return '\n'.join(lines)


def generate_utilities_file() -> str:
    """Generate utilities.py with helper functions"""
    return '''"""
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
'''


def main():
    """Main function to generate all files"""
    # Load the OpenAPI spec
    spec_path = Path(__file__).parent / 'vintrace-v6-apis.yaml'
    
    with open(spec_path, 'r') as f:
        spec = yaml.safe_load(f)
    
    print("Generating Pydantic models...")
    models_code = generate_models_file(spec)
    models_path = Path(__file__).parent / 'vintrace_models.py'
    with open(models_path, 'w') as f:
        f.write(models_code)
    print(f"✓ Generated {models_path}")
    
    print("\nGenerating API client...")
    client_code = generate_api_client_file(spec)
    client_path = Path(__file__).parent / 'vintrace_api_client.py'
    with open(client_path, 'w') as f:
        f.write(client_code)
    print(f"✓ Generated {client_path}")
    
    print("\nGenerating utilities...")
    utils_code = generate_utilities_file()
    utils_path = Path(__file__).parent / 'vintrace_api_utils.py'
    with open(utils_path, 'w') as f:
        f.write(utils_code)
    print(f"✓ Generated {utils_path}")
    
    # Create __init__.py for easy imports
    init_code = '''"""
Vintrace V6 API Client Package

Provides Python client for Vintrace V6 REST API.
"""

from .vintrace_api_client import VintraceAPIClient
from .vintrace_api_utils import VintraceDataFetcher, create_client_from_env
from .vintrace_models import *

__all__ = ['VintraceAPIClient', 'VintraceDataFetcher', 'create_client_from_env']
'''
    init_path = Path(__file__).parent / '__init__.py'
    with open(init_path, 'w') as f:
        f.write(init_code)
    print(f"✓ Generated {init_path}")
    
    print("\n" + "="*60)
    print("Generation complete!")
    print("="*60)
    print(f"\nGenerated {len(spec.get('components', {}).get('schemas', {}))} Pydantic models")
    print(f"Generated {len(spec.get('paths', {}))} API endpoint methods")
    print("\nFiles created:")
    print(f"  - {models_path}")
    print(f"  - {client_path}")
    print(f"  - {utils_path}")
    print(f"  - {init_path}")


if __name__ == '__main__':
    main()
