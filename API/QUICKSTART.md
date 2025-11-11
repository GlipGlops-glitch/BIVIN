# Quick Start Guide - Vintrace API Client

This guide will help you get started with the Vintrace API client in minutes.

## Installation

1. **Install dependencies:**
   ```bash
   cd API
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   
   Create a `.env` file in the project root:
   ```env
   VINTRACE_BASE_URL=https://your-instance.vintrace.net/vinx2/api/v6
   VINTRACE_API_KEY=your-api-key-here
   # OR for basic authentication:
   # VINTRACE_USERNAME=your-username
   # VINTRACE_PASSWORD=your-password
   ```

## Basic Usage

### Example 1: Simple Data Fetch

```python
from API import create_client_from_env

# Create client from environment variables
client = create_client_from_env()

# Get work orders
response = client.list_available_work_orders()
work_orders = response.get('results', [])

print(f"Found {len(work_orders)} work orders")
for wo in work_orders[:5]:
    print(f"- {wo.get('name')}: {wo.get('status')}")
```

### Example 2: Using the Data Fetcher Helper

```python
from API import create_client_from_env, VintraceDataFetcher

client = create_client_from_env()
fetcher = VintraceDataFetcher(client)

# Get all products (handles pagination automatically)
products = fetcher.get_all_products()
print(f"Total products: {len(products)}")

# Get work orders from last 7 days
recent_work_orders = fetcher.get_recent_work_orders(days=7)
print(f"Work orders in last 7 days: {len(recent_work_orders)}")
```

### Example 3: Direct Client Usage

```python
from API import VintraceAPIClient

# Initialize with direct credentials
client = VintraceAPIClient(
    base_url="https://your-instance.vintrace.net/vinx2/api/v6",
    api_key="your-api-key"
)

# Search for transactions
transactions = client.transaction_search(
    fromDate="2024-01-01",
    toDate="2024-12-31"
)

# Get detailed stock information
stock = client.view_a_single_stock_item(id="12345")
print(f"Stock: {stock.get('name')}")
```

## Running the Examples

The `API/examples/` directory contains ready-to-run scripts:

```bash
# Export all products to CSV
cd API/examples
python3 example_export_products.py

# Fetch work orders from last 7 days
python3 example_work_orders.py

# Get complete stock details
python3 example_stock_details.py 12345

# Search and analyze transactions
python3 example_transactions.py

# Comprehensive data export
python3 example_bulk_export.py
```

## Common Tasks

### Get All Pages of Data

```python
# Automatic pagination
all_products = client.get_all_pages(
    client.list_available_products
)

# With filters
filtered_work_orders = client.get_all_pages(
    client.list_available_work_orders,
    assignedTo="MINE_ONLY",
    workOrderState="IN_PROGRESS"
)
```

### Search with Filters

```python
# Search transactions
transactions = client.transaction_search(
    fromDate="2024-01-01",
    toDate="2024-12-31",
    productId=123
)

# Search intake operations
intake_ops = client.fruit_intake_operation_search(
    vintage="2024",
    vineyardName="Vineyard A"
)
```

### Get Complete Stock Information

```python
from API import VintraceDataFetcher, create_client_from_env

client = create_client_from_env()
fetcher = VintraceDataFetcher(client)

# Get stock with all related data
stock = fetcher.get_stock_details(stock_id="12345")

# Access different aspects
print(f"Fields: {len(stock.get('fields', []))}")
print(f"History: {len(stock.get('history', []))}")
print(f"Components: {len(stock.get('components', []))}")
print(f"Notes: {len(stock.get('notes', []))}")
```

### Export to CSV

```python
import csv

products = client.get_all_pages(client.list_available_products)

with open('products.csv', 'w', newline='') as f:
    if products:
        writer = csv.DictWriter(f, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)
```

## Available API Methods

### Work Orders
- `list_available_work_orders(**filters)` - List work orders
- `get_work_order_details_by_id_or_code(id)` - Get specific work order
- `assign_a_work_order(data)` - Assign work order
- `submit_job_details(data)` - Submit job

### Products
- `list_available_products(**filters)` - List all products
- `product_search(id)` - Search for product
- `update_a_product(data)` - Update product

### Sales Orders
- `list_available_sales_orders(**filters)` - List sales orders
- `get_sales_order_details_by_id(id)` - Get by ID
- `create_or_update_a_sales_order(data)` - Create/update

### Stock/Inventory
- `view_a_single_stock_item(id)` - Get stock item
- `list_available_stock(**filters)` - List inventory
- `get_stock_item_by_code_or_id(code, id)` - Stock lookup
- `view_list_of_details_fields(id)` - Get stock fields
- `view_distribtutions(id)` - Get distributions
- `view_history_items(id)` - Get history
- `view_raw_components(id)` - Get components
- `view_all_notes(id)` - Get notes

### Search
- `transaction_search(**criteria)` - Search transactions
- `fruit_intake_operation_search(**criteria)` - Search intakes
- `maturity_samples_search(**criteria)` - Search samples
- `list_results_for_item_type(**criteria)` - Generic search

## Error Handling

```python
from requests.exceptions import HTTPError

try:
    product = client.product_search(id="12345")
except HTTPError as e:
    if e.response.status_code == 404:
        print("Product not found")
    elif e.response.status_code == 401:
        print("Authentication failed")
    else:
        print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Tips

1. **Use pagination helpers**: `get_all_pages()` automatically handles pagination
2. **Use the data fetcher**: `VintraceDataFetcher` provides high-level methods
3. **Check response structure**: API returns paginated results with metadata
4. **Handle errors gracefully**: Use try/except blocks for API calls
5. **Use type hints**: All methods have proper type hints for IDE support

## Next Steps

- Read the full [API README](README.md) for comprehensive documentation
- Explore the [examples](examples/) directory for more use cases
- Check the [OpenAPI spec](vintrace-v6-apis.yaml) for detailed endpoint information
- Review the generated [models](vintrace_models.py) for data structures

## Troubleshooting

**Authentication errors**: Verify your API key or credentials in `.env`

**Import errors**: Ensure you're in the correct directory and dependencies are installed

**Connection errors**: Check your base URL and network connectivity

**Data not found**: Verify the ID/code you're searching for exists in Vintrace

## Support

For API-specific questions, refer to the Vintrace API documentation or contact support@vintrace.com
