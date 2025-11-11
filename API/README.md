# Vintrace V6 API Client

Python client library for interacting with the Vintrace V6 REST API. This package provides a complete, type-safe interface to all Vintrace API endpoints with automatic pagination support, retry logic, and comprehensive data models.

## 🎯 Features

- **Complete API Coverage**: All 36 endpoints from Vintrace V6 API
- **99 Pydantic Models**: Type-safe data models for all API schemas
- **Automatic Pagination**: Built-in support for fetching all pages
- **Retry Logic**: Automatic retries for failed requests with exponential backoff
- **Type Hints**: Full typing support for better IDE integration
- **Easy Authentication**: Support for API key and basic authentication
- **Helper Utilities**: High-level functions for common data fetching tasks

## 📦 Installation

```bash
# Install required dependencies
pip install pydantic requests python-dotenv pyyaml
```

## 🚀 Quick Start

### Basic Usage

```python
from API import VintraceAPIClient

# Initialize the client
client = VintraceAPIClient(
    base_url="https://your-instance.vintrace.net/vinx2/api/v6",
    api_key="your-api-key"  # or use username/password
)

# Get work orders
work_orders = client.list_available_work_orders(
    assignedTo="MINE_ONLY",
    workOrderState="IN_PROGRESS"
)

# Get all products (with pagination)
all_products = client.get_all_pages(client.list_available_products)

# Get specific product details
product = client.product_search(id="12345")

# Search transactions
transactions = client.transaction_search(
    fromDate="2024-01-01",
    toDate="2024-12-31"
)
```

### Using Environment Variables

```python
from API import create_client_from_env

# Create client from .env file
client = create_client_from_env()

# Use the client
work_orders = client.list_available_work_orders()
```

Create a `.env` file with:

```env
VINTRACE_BASE_URL=https://your-instance.vintrace.net/vinx2/api/v6
VINTRACE_API_KEY=your-api-key
# OR for basic auth:
# VINTRACE_USERNAME=your-username
# VINTRACE_PASSWORD=your-password
```

### Using the Data Fetcher Helper

```python
from API import VintraceAPIClient, VintraceDataFetcher

client = VintraceAPIClient(
    base_url="https://your-instance.vintrace.net/vinx2/api/v6",
    api_key="your-api-key"
)

# Create data fetcher
fetcher = VintraceDataFetcher(client)

# Get all work orders from last 30 days
recent_work_orders = fetcher.get_recent_work_orders(days=30)

# Get complete stock details (includes all related data)
stock_details = fetcher.get_stock_details(stock_id="12345")

# Get all sales orders
all_sales_orders = fetcher.get_all_sales_orders()

# Search for intake operations
intake_ops = fetcher.search_intake_operations(
    fromDate="2024-01-01",
    toDate="2024-12-31"
)
```

## 📚 Available Endpoints

### Work Orders
- `list_available_work_orders()` - List work orders with filters
- `get_work_order_details_by_id_or_code()` - Get specific work order
- `assign_a_work_order()` - Assign work order to operator
- `get_job_details_by_id()` - Get job details
- `submit_job_details()` - Submit completed job

### Sales Orders
- `list_available_sales_orders()` - List sales orders
- `get_sales_order_details_by_id()` - Get by ID
- `get_sales_order_details_by_code()` - Get by code
- `create_or_update_a_sales_order()` - Create/update sales order

### Refunds
- `list_available_refunds()` - List refunds
- `get_refund_details_by_id()` - Get by ID
- `get_refund_details_by_code()` - Get by code
- `create_or_update_a_refund()` - Create/update refund

### Parties (Customers/Suppliers)
- `list_parties()` - List all parties
- `get_party_details_by_id()` - Get by ID
- `get_party_details_by_name()` - Get by name
- `create_or_update_a_party()` - Create/update party

### Products
- `product_search()` - Search for products
- `list_available_products()` - List all products
- `update_a_product()` - Update product details

### Transactions
- `transaction_search()` - Search transactions

### Operations
- `fruit_intake_operation_search()` - Search intake operations
- `maturity_samples_search()` - Search maturity samples
- `create_a_block_assessment()` - Create block assessment

### Stock/Inventory
- `view_a_single_stock_item()` - Get stock item details
- `view_list_of_details_fields()` - Get stock fields
- `view_distribtutions()` - Get stock distributions
- `view_history_items()` - Get stock history
- `view_raw_components()` - Get stock components
- `view_all_notes()` - Get stock notes
- `add_a_note()` - Add note to stock
- `view_a_single_note()` - Get specific note
- `update_a_note()` - Update note
- `view_bulk_product_details()` - Get bulk product info
- `list_available_stock()` - List inventory
- `get_stock_item_by_code_or_id()` - Stock lookup

### Search
- `list_results_for_item_type()` - Generic search for any item type

## 📖 Data Models

All API responses are validated against Pydantic models for type safety. Some key models include:

- `WorkOrder` - Work order details
- `Job` - Job information with steps and fields
- `SalesOrder` - Sales order with line items
- `Product` - Product information
- `Party` - Customer/supplier information
- `StockItem` - Inventory item details
- And 93 more models for complete API coverage!

## 🔧 Advanced Features

### Pagination

The client automatically handles pagination for list endpoints:

```python
# Get all results across all pages
all_work_orders = client.get_all_pages(
    client.list_available_work_orders,
    assignedTo="ANYONE",
    workOrderState="ANY"
)

# Manual pagination
page_1 = client.list_available_work_orders(first="0", max="50")
page_2 = client.list_available_work_orders(first="50", max="50")
```

### Error Handling

```python
from requests.exceptions import HTTPError

try:
    product = client.product_search(id="12345")
except HTTPError as e:
    if e.response.status_code == 404:
        print("Product not found")
    else:
        print(f"API error: {e}")
```

### Custom Timeout and Retries

```python
client = VintraceAPIClient(
    base_url="https://your-instance.vintrace.net/vinx2/api/v6",
    api_key="your-api-key",
    timeout=60,  # 60 seconds
    max_retries=5  # retry up to 5 times
)
```

## 📝 Examples

### Example 1: Get Today's Work Orders

```python
from datetime import datetime
from API import create_client_from_env

client = create_client_from_env()

today = datetime.now().strftime('%Y-%m-%d')
work_orders = client.list_available_work_orders(
    fromDate=today,
    toDate=today,
    assignedTo="MINE_ONLY",
    workOrderState="IN_PROGRESS"
)

for wo in work_orders.get('results', []):
    print(f"Work Order: {wo.get('name')} - {wo.get('status')}")
```

### Example 2: Export All Products to CSV

```python
import csv
from API import VintraceAPIClient

client = VintraceAPIClient(
    base_url="https://your-instance.vintrace.net/vinx2/api/v6",
    api_key="your-api-key"
)

# Get all products
products = client.get_all_pages(client.list_available_products)

# Export to CSV
with open('products.csv', 'w', newline='') as f:
    if products:
        writer = csv.DictWriter(f, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)

print(f"Exported {len(products)} products to products.csv")
```

### Example 3: Search and Process Transactions

```python
from API import VintraceDataFetcher, create_client_from_env

client = create_client_from_env()
fetcher = VintraceDataFetcher(client)

# Search for transactions in date range
transactions = fetcher.search_transactions(
    fromDate="2024-01-01",
    toDate="2024-12-31",
    type="ADDITION"  # or REMOVAL, TRANSFER, etc.
)

# Process transactions
total_volume = 0
for trans in transactions:
    volume = trans.get('volume', 0)
    total_volume += volume
    print(f"Transaction {trans.get('id')}: {volume}L")

print(f"Total volume: {total_volume}L")
```

### Example 4: Complete Stock Information

```python
from API import VintraceDataFetcher, create_client_from_env

client = create_client_from_env()
fetcher = VintraceDataFetcher(client)

# Get complete stock details with all related information
stock = fetcher.get_stock_details(stock_id="12345")

print(f"Stock: {stock.get('name')}")
print(f"Volume: {stock.get('volume')}")
print(f"Fields: {len(stock.get('fields', []))}")
print(f"History items: {len(stock.get('history', []))}")
print(f"Components: {len(stock.get('components', []))}")
print(f"Notes: {len(stock.get('notes', []))}")
```

### Example 5: Bulk Data Export

```python
from API import VintraceDataFetcher, create_client_from_env
import json

client = create_client_from_env()
fetcher = VintraceDataFetcher(client)

# Fetch all data types
data = {
    'work_orders': fetcher.get_all_work_orders(),
    'products': fetcher.get_all_products(),
    'sales_orders': fetcher.get_all_sales_orders(),
    'parties': fetcher.get_all_parties(),
    'inventory': fetcher.get_inventory_summary()
}

# Save to JSON
with open('vintrace_export.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Export complete!")
for key, value in data.items():
    count = len(value) if isinstance(value, list) else 1
    print(f"  {key}: {count} items")
```

## 🏗️ Generated Files

This package includes the following auto-generated files:

- **`vintrace_models.py`** - 99 Pydantic models for all API schemas
- **`vintrace_api_client.py`** - Main API client with all 36 endpoint methods
- **`vintrace_api_utils.py`** - Helper utilities for common tasks
- **`__init__.py`** - Package initialization
- **`generate_api_client.py`** - Generator script (can be re-run if API spec changes)

## 🔄 Regenerating the Client

If the API specification changes, regenerate the client:

```bash
cd API
python3 generate_api_client.py
```

This will regenerate all models and client methods from the latest `vintrace-v6-apis.yaml`.

## 📋 API Documentation

For complete API documentation, refer to the [Vintrace V6 API specification](vintrace-v6-apis.yaml).

The API supports:
- Pagination for all list endpoints
- Filtering by various criteria
- Date range searches
- Full CRUD operations where applicable

## 🤝 Contributing

When the Vintrace API is updated:

1. Update `vintrace-v6-apis.yaml` with the latest spec
2. Run `python3 generate_api_client.py` to regenerate code
3. Test the changes
4. Update this README if new features are added

## 📄 License

Internal use only - Ste Michelle Wine Estates

## 👤 Author

GlipGlops-glitch
Generated: 2024-11-11
