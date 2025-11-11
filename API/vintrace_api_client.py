"""
Vintrace V6 API Client

Auto-generated from vintrace-v6-apis.yaml
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
import time


class VintraceAPIClient:
    """Client for Vintrace V6 API
    
    This client provides methods for all Vintrace API endpoints.
    
    Example:
        client = VintraceAPIClient(
            base_url="https://your-instance.vintrace.net/vinx2/api/v6",
            api_key="your-api-key"
        )
        work_orders = client.list_available_work_orders()
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None,
                 username: Optional[str] = None, password: Optional[str] = None,
                 timeout: int = 30, max_retries: int = 3):
        """
        Initialize the Vintrace API client
        
        Args:
            base_url: Base URL for the Vintrace API (e.g., "https://your-instance.vintrace.net/vinx2/api/v6")
            api_key: API key for authentication (optional)
            username: Username for basic auth (optional)
            password: Password for basic auth (optional)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries for failed requests (default: 3)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.username = username
        self.password = password
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Set up authentication headers
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        elif username and password:
            self.session.auth = (username, password)
        
        self.session.headers.update({"Accept": "application/json"})

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request with retry logic"""
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                
                # Handle empty responses
                if not response.content:
                    return {}
                
                return response.json()
            except requests.exceptions.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise
                # Retry on 5xx errors
                if e.response.status_code >= 500:
                    time.sleep(2 ** attempt)
                    continue
                raise
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        
        raise Exception(f"Failed to {method} {url} after {self.max_retries} attempts")

    def get_all_pages(self, method_func, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch all pages from a paginated endpoint
        
        Args:
            method_func: The API method to call (e.g., self.list_available_work_orders)
            **kwargs: Arguments to pass to the method
        
        Returns:
            List of all results from all pages
        """
        all_results = []
        first_result = 0
        max_result = kwargs.get("max", 100)
        
        while True:
            kwargs["first"] = str(first_result)
            kwargs["max"] = str(max_result)
            
            response = method_func(**kwargs)
            
            # Handle different response formats
            if isinstance(response, dict):
                results = response.get("results", [])
                total = response.get("totalResultCount", 0)
            else:
                results = response if isinstance(response, list) else []
                total = len(results)
            
            all_results.extend(results)
            
            # Check if there are more pages
            if len(all_results) >= total:
                break
            
            first_result += max_result
        
        return all_results

    # =================================================================
    # API ENDPOINTS
    # =================================================================

    def create_a_block_assessment(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a block assessment
        
        Create a block assessment for a specific block and vintage
        """
        url = f"/block-assessments/create"
        params = None
        return self._request('POST', url, params=params, json=data)

    def fruit_intake_operation_search(
        self,
        modifiedSince: Optional[str] = None,
        operationId: Optional[int] = None,
        processId: Optional[int] = None,
        deliveryDocket: Optional[str] = None,
        intakeDocket: Optional[str] = None,
        externalWeighTag: Optional[str] = None,
        externalSystemBlocksOnly: Optional[bool] = None,
        externalBlockId: Optional[str] = None,
        blockId: Optional[int] = None,
        blockName: Optional[str] = None,
        vineyardId: Optional[int] = None,
        vineyardName: Optional[str] = None,
        wineryId: Optional[int] = None,
        wineryName: Optional[str] = None,
        growerType: Optional[str] = None,
        growerId: Optional[int] = None,
        growerName: Optional[str] = None,
        ownerId: Optional[int] = None,
        ownerName: Optional[str] = None,
        vintage: Optional[str] = None,
        recordedAfter: Optional[str] = None,
        recordedBefore: Optional[str] = None,
        customAdapter: Optional[str] = None,
        maxResults: Optional[int] = None,
        firstResult: Optional[int] = None) -> Dict[str, Any]:
        """Fruit intake operation search
        
        Returns a list of fruit intake operations matching search criteria.
        
        Args:
            modifiedSince: Filter on records that have been added/modified/reversed since this date - represented as milliseconds since 01/01/1970 00:00:00 GMT
            operationId: Operation id to filter on for a specific fruit intake operation
            processId: Delivery process id to filter all intakes for a specific delivery
            deliveryDocket: Docket/Weigh Tag number as generated by vintrace to identify a specific fruit delivery
            intakeDocket: Docket/Weigh Tag number as generated by vintrace to identify a specific fruit intake
            externalWeighTag: 3rd party weigh tag as provided by external system to identify a specific fruit intake
            externalSystemBlocksOnly: Only show fruit intakes for blocks that have an external id set
            externalBlockId: Only show fruit intakes for the block with matching externalBlockId
            blockId: Only show fruit intakes for the block with matching vintrace internal identifier
            blockName: Only show fruit intakes for the blocks with matching this name
            vineyardId: Only show fruit intakes for the vineyard with matching vintrace internal identifier
            vineyardName: Only show fruit intakes for the vineyards matching this name
            wineryId: Only show fruit intakes for the winery with matching vintrace internal identifier
            wineryName: Only show fruit intakes for the wineries matching this name
            growerType: Only show fruit intakes for the grower type matching
            growerId: Only show fruit intakes for the grower with matching vintrace internal identifier
            growerName: Only show fruit intakes for the grower matching this name
            ownerId: Only show fruit intakes for the owner with matching vintrace internal identifier
            ownerName: Only show fruit intakes for the owner matching this name
            vintage: Only show fruit intakes for this vintage in YYYY format
            recordedAfter: Filter on records with an effective date after this date - represented as milliseconds since 01/01/1970 00:00:00 GMT
            recordedBefore: Filter on records with an effective date before this date - represented as milliseconds since 01/01/1970 00:00:00 GMT
            customAdapter: Special adapter reference to provide customized fields in additionalDetails map.  Use as directed by vintrace
            maxResults: Maximum results to fetch in a page of data
            firstResult: Skip over this many results
        """
        url = f"/intake-operations/search"
        params = {}
        if modifiedSince is not None:
            params['modifiedSince'] = modifiedSince
        if operationId is not None:
            params['operationId'] = operationId
        if processId is not None:
            params['processId'] = processId
        if deliveryDocket is not None:
            params['deliveryDocket'] = deliveryDocket
        if intakeDocket is not None:
            params['intakeDocket'] = intakeDocket
        if externalWeighTag is not None:
            params['externalWeighTag'] = externalWeighTag
        if externalSystemBlocksOnly is not None:
            params['externalSystemBlocksOnly'] = externalSystemBlocksOnly
        if externalBlockId is not None:
            params['externalBlockId'] = externalBlockId
        if blockId is not None:
            params['blockId'] = blockId
        if blockName is not None:
            params['blockName'] = blockName
        if vineyardId is not None:
            params['vineyardId'] = vineyardId
        if vineyardName is not None:
            params['vineyardName'] = vineyardName
        if wineryId is not None:
            params['wineryId'] = wineryId
        if wineryName is not None:
            params['wineryName'] = wineryName
        if growerType is not None:
            params['growerType'] = growerType
        if growerId is not None:
            params['growerId'] = growerId
        if growerName is not None:
            params['growerName'] = growerName
        if ownerId is not None:
            params['ownerId'] = ownerId
        if ownerName is not None:
            params['ownerName'] = ownerName
        if vintage is not None:
            params['vintage'] = vintage
        if recordedAfter is not None:
            params['recordedAfter'] = recordedAfter
        if recordedBefore is not None:
            params['recordedBefore'] = recordedBefore
        if customAdapter is not None:
            params['customAdapter'] = customAdapter
        if maxResults is not None:
            params['maxResults'] = maxResults
        if firstResult is not None:
            params['firstResult'] = firstResult
        return self._request('GET', url, params=params)

    def list_available_stock(
        self,
        max: Optional[str] = None,
        first: Optional[str] = None,
        date: Optional[str] = None,
        stockType: Optional[str] = None,
        ownerName: Optional[str] = None,
        showEquivalentType: Optional[str] = None,
        breakoutCosting: Optional[bool] = None,
        disableCommitHeaders: Optional[bool] = None) -> Dict[str, Any]:
        """List available stock
        
        Returns a list of all stock items.
        
        Args:
            max: The starting index of results.
            first: The starting index of results.
            date: The date to report stock up to, excluding stock changes done after it in YYYY-MM-DD format.
            stockType: String that matches the Stock Type of the Stock Items. Possible values are Additive, Closure, Glass/Container, Other, Wine batch, Single x1, Case x3, Case x, Case x12, Case x2, Pallet (full), Dry goods.
            ownerName: String that matches the Owner's name on the Stock Items.
            showEquivalentType: Displays the ratio of what the inventory item's volume/qty is equivalent to the given showEquivalentType Possible values 750ml bottle, 375ml bottle, 9L case (dozen), 4.5L case, Litres.
            breakoutCosting: When true, this retrieves each costing's category of costs and details each types cost. User needs "Can view costs" permission to view the costs.
            disableCommitHeaders: When true, does not show an item's committed stock amount details.
        """
        url = f"/inventory/"
        params = {}
        if max is not None:
            params['max'] = max
        if first is not None:
            params['first'] = first
        if date is not None:
            params['date'] = date
        if stockType is not None:
            params['stockType'] = stockType
        if ownerName is not None:
            params['ownerName'] = ownerName
        if showEquivalentType is not None:
            params['showEquivalentType'] = showEquivalentType
        if breakoutCosting is not None:
            params['breakoutCosting'] = breakoutCosting
        if disableCommitHeaders is not None:
            params['disableCommitHeaders'] = disableCommitHeaders
        return self._request('GET', url, params=params)

    def view_a_single_stock_item(self, id: str, expand: Optional[str] = None) -> Dict[str, Any]:
        """View a single stock item
        
        Args:
            id: Stock item id
            expand: Comma separated list of the details that you want to expand. Possible values are `fields`, `distributions`, `notes`, `historyItems`, `rawComponents`, `bulkInfo`
        """
        url = f"/mrp/stock/{id}"
        params = {}
        if expand is not None:
            params['expand'] = expand
        return self._request('GET', url, params=params)

    def view_bulk_product_details(self, id: str) -> Dict[str, Any]:
        """View bulk product details
        
        Returns details like metrics, compositions, allergens and additives (from last bottling) about the bulk product linked to a stock item.
        
        Args:
            id: 
        """
        url = f"/mrp/stock/{id}/bulk-info"
        params = None
        return self._request('GET', url, params=params)

    def view_distribtutions(self, id: str) -> Dict[str, Any]:
        """View distribtutions
        
        Returns a list of distributions for a stock item.
        
        Args:
            id: Stock item id
        """
        url = f"/mrp/stock/{id}/distributions/"
        params = None
        return self._request('GET', url, params=params)

    def view_list_of_details_fields(self, id: str) -> Dict[str, Any]:
        """View list of details fields
        
        Returns a list of detail fields for a stock item.
        
        Args:
            id: Stock item id
        """
        url = f"/mrp/stock/{id}/fields/"
        params = None
        return self._request('GET', url, params=params)

    def view_history_items(self, id: str, firstResult: float, maxResult: float) -> Dict[str, Any]:
        """View History items
        
        A paginated list of history items for a stock item.
        
        Args:
            id: Stock item id
            firstResult: 
            maxResult: 
        """
        url = f"/mrp/stock/{id}/history-items"
        params = {}
        if firstResult is not None:
            params['firstResult'] = firstResult
        if maxResult is not None:
            params['maxResult'] = maxResult
        return self._request('GET', url, params=params)

    def view_all_notes(self, firstResult: Optional[float] = None, maxResult: Optional[float] = None) -> Dict[str, Any]:
        """View all notes
        
        A paginated list of notes for a stock item.
        
        Args:
            None: 
            firstResult: 
            maxResult: 
        """
        url = f"/mrp/stock/{id}/notes"
        params = {}
        if firstResult is not None:
            params['firstResult'] = firstResult
        if maxResult is not None:
            params['maxResult'] = maxResult
        return self._request('GET', url, params=params)

    def add_a_note(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a Note
        
        Add a note to a stock item.
        
        Args:
            None: 
        """
        url = f"/mrp/stock/{id}/notes"
        params = None
        return self._request('POST', url, params=params, json=data)

    def view_a_single_note(self, id: str, noteId: str) -> Dict[str, Any]:
        """View a single Note
        
        View a note for a stock item.
        
        Args:
            id: id of the note
            noteId: id of the note
        """
        url = f"/mrp/stock/{id}/notes/{noteId}"
        params = None
        return self._request('GET', url, params=params)

    def update_a_note(self, id: str, noteId: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update a Note
        
        Update a note attached to a stock item
        
        Args:
            id: id of the note
            noteId: id of the note
        """
        url = f"/mrp/stock/{id}/notes/{noteId}/updates"
        params = None
        return self._request('POST', url, params=params, json=data)

    def view_raw_components(self, id: str) -> Dict[str, Any]:
        """View raw components
        
        Returns a paginated list of raw components for a stock item.
        
        Args:
            id: 
        """
        url = f"/mrp/stock/{id}/raw-components"
        params = None
        return self._request('GET', url, params=params)

    def create_or_update_a_party(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create or update a party
        
        To update a party, you need to provide the `id` of the party.
        """
        url = f"/party"
        params = None
        return self._request('POST', url, params=params, json=data)

    def get_party_details_by_name(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get party details by name
        
        Returns a single party with a given code.
        
        Args:
            name: The primeName (surname) if the party is an individual or the primeName (company name) if the party is an organisation.
        """
        url = f"/party/"
        params = {}
        if name is not None:
            params['name'] = name
        return self._request('GET', url, params=params)

    def list_parties(
        self,
        max: Optional[str] = None,
        first: Optional[str] = None,
        startsWith: Optional[str] = None,
        category: Optional[str] = None) -> Dict[str, Any]:
        """List parties
        
        Returns a list of the first 100 parties.
        
        Args:
            max: The starting index of results. Default: 100.
            first: The starting index of results.
            startsWith: String that matches the primeName (Surname field in vintrace for individuals, Company Name for organisations) with the given string against the start of the name.
            category: Category of the party: All, Individuals, Organisations.
        """
        url = f"/party/list/"
        params = {}
        if max is not None:
            params['max'] = max
        if first is not None:
            params['first'] = first
        if startsWith is not None:
            params['startsWith'] = startsWith
        if category is not None:
            params['category'] = category
        return self._request('GET', url, params=params)

    def get_party_details_by_id(self, id: str) -> Dict[str, Any]:
        """Get party details by id
        
        Returns a single party with a given id.
        
        Args:
            id: The ID of the party.
        """
        url = f"/party/{id}"
        params = None
        return self._request('GET', url, params=params)

    def update_a_product(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update a product
        
        To update a product, you need to provide the `productId` of the product. The propertyTypes that are available to be updated from this endpoint Grading, ProductState, Program, ProductCategory, Varietal, Region, Vintage, Description. You can query for the `propertyId` of the propertyType by using the /search endpoint.
        """
        url = f"/product-update"
        params = None
        return self._request('POST', url, params=params, json=data)

    def list_available_products(
        self,
        barcode: Optional[str] = None,
        max: Optional[str] = None,
        first: Optional[str] = None,
        skipMetrics: Optional[bool] = None) -> Dict[str, Any]:
        """List available products
        
        Returns a list of all active products.
        
        Args:
            barcode: Can either be the vessel code or the asset ID.
            max: The starting index of results. Default: 100.
            first: The starting index of results.
            skipMetrics: False by default,if true will not include the metric data in the results.
        """
        url = f"/products/list"
        params = {}
        if barcode is not None:
            params['barcode'] = barcode
        if max is not None:
            params['max'] = max
        if first is not None:
            params['first'] = first
        if skipMetrics is not None:
            params['skipMetrics'] = skipMetrics
        return self._request('GET', url, params=params)

    def product_search(self, barcode: Optional[str] = None) -> Dict[str, Any]:
        """Search for a product by id
        
        Searches for a product using an id and returns the product details and vessel information.
        
        Args:
            barcode: The barcode to search for.
        """
        url = f"/products/{id}"
        params = {}
        if barcode is not None:
            params['barcode'] = barcode
        return self._request('GET', url, params=params)

    def create_or_update_a_refund(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create or update a refund
        
        To update a refund, you need to provide the `id' of the refund.
        """
        url = f"/refund"
        params = None
        return self._request('POST', url, params=params, json=data)

    def get_refund_details_by_code(self, code: Optional[str] = None) -> Dict[str, Any]:
        """Get refund details by code
        
        Returns a single refund with a given code.
        
        Args:
            code: The refund name.
        """
        url = f"/refund/"
        params = {}
        if code is not None:
            params['code'] = code
        return self._request('GET', url, params=params)

    def list_available_refunds(
        self,
        max: Optional[str] = None,
        first: Optional[str] = None,
        startsWith: Optional[str] = None,
        status: Optional[str] = None,
        customerName: Optional[str] = None,
        startDate: Optional[str] = None,
        endDate: Optional[str] = None,
        salesOrderName: Optional[str] = None) -> Dict[str, Any]:
        """List available refunds
        
        Returns a list of the first 100 refunds.
        
        Args:
            max: The starting index of results.
            first: The starting index of results.
            startsWith: String that matches the QuickSearchResult against the start of the name.
            status: Status of the sales order: Awaiting approval, Approved.
            customerName: Customer on the sales order.
            startDate: Start date to filter out the results of the sales orders in YYYY-MM-DD format.
            endDate: End date to filter out the results of the sales orders in YYYY-MM-DD format.
            salesOrderName: String that matches the sales order code of the refund.
        """
        url = f"/refund/list/"
        params = {}
        if max is not None:
            params['max'] = max
        if first is not None:
            params['first'] = first
        if startsWith is not None:
            params['startsWith'] = startsWith
        if status is not None:
            params['status'] = status
        if customerName is not None:
            params['customerName'] = customerName
        if startDate is not None:
            params['startDate'] = startDate
        if endDate is not None:
            params['endDate'] = endDate
        if salesOrderName is not None:
            params['salesOrderName'] = salesOrderName
        return self._request('GET', url, params=params)

    def get_refund_details_by_id(self, id: str) -> Dict[str, Any]:
        """Get refund details by id
        
        Returns a single refund with a given id.
        
        Args:
            id: The ID of the refund.
        """
        url = f"/refund/{id}"
        params = None
        return self._request('GET', url, params=params)

    def create_or_update_a_sales_order(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create or update a sales order
        
        For sales order with discounts and accounting integration with Xero is turned on for the customer, enter the discount as percentage value in `discountPct` field. Otherwise, if accounting integration is off, enter the discount in `adjustment` field as a dollar value. To update a sales order, you need to provide the `id' of the sales order.
        """
        url = f"/sales-order"
        params = None
        return self._request('POST', url, params=params, json=data)

    def get_sales_order_details_by_code(self, code: Optional[str] = None) -> Dict[str, Any]:
        """Get sales order details by code
        
        Returns a single sales order with a given code.
        
        Args:
            code: The sales order number.
        """
        url = f"/sales-order/"
        params = {}
        if code is not None:
            params['code'] = code
        return self._request('GET', url, params=params)

    def list_available_sales_orders(
        self,
        max: Optional[str] = None,
        first: Optional[str] = None,
        startsWith: Optional[str] = None,
        status: Optional[str] = None,
        customerName: Optional[str] = None,
        startDate: Optional[str] = None,
        endDate: Optional[str] = None,
        invStartDate: Optional[str] = None,
        invEndDate: Optional[str] = None,
        externalTransactionId: Optional[str] = None) -> Dict[str, Any]:
        """List available sales orders
        
        Returns a list of the first 100 sales orders.
        
        Args:
            max: The starting index of results.
            first: The starting index of results.
            startsWith: String that matches the QuickSearchResult against the start of the name.
            status: Status of the sales order: New, Approved, Payment in Progress, Paid.
            customerName: Customer on the sales order.
            startDate: Start date to filter out the results of the sales orders in YYYY-MM-DD format.
            endDate: End date to filter out the results of the sales orders in YYYY-MM-DD format.
            invStartDate: The starting invoiced date to filter out sales order results in YYYY-MM-DD format.
            invEndDate: The ending invoiced date to filter out sales order results in YYYY-MM-DD format.
            externalTransactionId: External transaction ID linked to the sales order.
        """
        url = f"/sales-order/list/"
        params = {}
        if max is not None:
            params['max'] = max
        if first is not None:
            params['first'] = first
        if startsWith is not None:
            params['startsWith'] = startsWith
        if status is not None:
            params['status'] = status
        if customerName is not None:
            params['customerName'] = customerName
        if startDate is not None:
            params['startDate'] = startDate
        if endDate is not None:
            params['endDate'] = endDate
        if invStartDate is not None:
            params['invStartDate'] = invStartDate
        if invEndDate is not None:
            params['invEndDate'] = invEndDate
        if externalTransactionId is not None:
            params['externalTransactionId'] = externalTransactionId
        return self._request('GET', url, params=params)

    def get_sales_order_details_by_id(self, id: str) -> Dict[str, Any]:
        """Get sales order details by id
        
        Returns a single sales order with a given id.
        
        Args:
            id: The ID of the sales order.
        """
        url = f"/sales-order/{id}"
        params = None
        return self._request('GET', url, params=params)

    def maturity_samples_search(
        self,
        modifiedSince: Optional[str] = None,
        operationId: Optional[int] = None,
        processId: Optional[int] = None,
        externalSystemBlocksOnly: Optional[bool] = None,
        externalBlockId: Optional[str] = None,
        blockId: Optional[int] = None,
        blockName: Optional[str] = None,
        vineyardId: Optional[int] = None,
        vineyardName: Optional[str] = None,
        growerId: Optional[int] = None,
        growerName: Optional[str] = None,
        ownerId: Optional[int] = None,
        ownerName: Optional[str] = None,
        vintage: Optional[str] = None,
        recordedAfter: Optional[str] = None,
        recordedBefore: Optional[str] = None,
        customAdapter: Optional[str] = None,
        maxResults: Optional[int] = None,
        firstResult: Optional[int] = None) -> Dict[str, Any]:
        """Maturity samples search
        
        Returns a list of fruit intake operations matching search criteria.
        
        Args:
            modifiedSince: Filter on records that have been added/modified/reversed since this date - represented as milliseconds since 01/01/1970 00:00:00 GMT
            operationId: Operation id to filter on for a specific fruit intake operation
            processId: Delivery process id to filter all intakes for a specific delivery
            externalSystemBlocksOnly: Only show fruit intakes for blocks that have an external id set
            externalBlockId: Only show fruit intakes for the block with matching externalBlockId
            blockId: Only show fruit intakes for the block with matching vintrace internal identifier
            blockName: Only show fruit intakes for the blocks with matching this name
            vineyardId: Only show fruit intakes for the vineyard with matching vintrace internal identifier
            vineyardName: Only show fruit intakes for the vineyards matching this name
            growerId: Only show fruit intakes for the grower with matching vintrace internal identifier
            growerName: Only show fruit intakes for the grower matching this name
            ownerId: Only show fruit intakes for the owner with matching vintrace internal identifier
            ownerName: Only show fruit intakes for the owner matching this name
            vintage: Only show fruit intakes for this vintage in YYYY format
            recordedAfter: Filter on records with an effective date after this date - represented as milliseconds since 01/01/1970 00:00:00 GMT
            recordedBefore: Filter on records with an effective date before this date - represented as milliseconds since 01/01/1970 00:00:00 GMT
            customAdapter: Special adapter reference to provide customized fields in additionalDetails map.  Use as directed by vintrace
            maxResults: Maximum results to fetch in a page of data
            firstResult: Skip over this many results
        """
        url = f"/sample-operations/search"
        params = {}
        if modifiedSince is not None:
            params['modifiedSince'] = modifiedSince
        if operationId is not None:
            params['operationId'] = operationId
        if processId is not None:
            params['processId'] = processId
        if externalSystemBlocksOnly is not None:
            params['externalSystemBlocksOnly'] = externalSystemBlocksOnly
        if externalBlockId is not None:
            params['externalBlockId'] = externalBlockId
        if blockId is not None:
            params['blockId'] = blockId
        if blockName is not None:
            params['blockName'] = blockName
        if vineyardId is not None:
            params['vineyardId'] = vineyardId
        if vineyardName is not None:
            params['vineyardName'] = vineyardName
        if growerId is not None:
            params['growerId'] = growerId
        if growerName is not None:
            params['growerName'] = growerName
        if ownerId is not None:
            params['ownerId'] = ownerId
        if ownerName is not None:
            params['ownerName'] = ownerName
        if vintage is not None:
            params['vintage'] = vintage
        if recordedAfter is not None:
            params['recordedAfter'] = recordedAfter
        if recordedBefore is not None:
            params['recordedBefore'] = recordedBefore
        if customAdapter is not None:
            params['customAdapter'] = customAdapter
        if maxResults is not None:
            params['maxResults'] = maxResults
        if firstResult is not None:
            params['firstResult'] = firstResult
        return self._request('GET', url, params=params)

    def list_results_for_item_type(
        self,
        type: str,
        first: Optional[str] = None,
        startsWith: Optional[str] = None,
        exactMatch: Optional[bool] = None) -> Dict[str, Any]:
        """List results for item type
        
        Args:
            type: Supported types are grading, owner, program, varietal, vintage, productState, region, block, grower, productCategory, batch, product, tank, vessel, containerEquipment, barrel, bin
            first: The starting index of results.
            startsWith: String that matches the search result against the start of the name.
            exactMatch: If false - we do a 'like' query where 'T-50' would return 'T-50', 'T-500'. When true it only returns 'T-50'
        """
        url = f"/search/list/"
        params = {}
        if type is not None:
            params['type'] = type
        if first is not None:
            params['first'] = first
        if startsWith is not None:
            params['startsWith'] = startsWith
        if exactMatch is not None:
            params['exactMatch'] = exactMatch
        return self._request('GET', url, params=params)

    def get_stock_item_by_code_or_id(self, code: Optional[str] = None, id: Optional[str] = None) -> Dict[str, Any]:
        """Get stock item by code or id
        
        Returns a single stock item by code or id.
        
        Args:
            code: String that matches the code of the Stock Item matching against the start of the name.
            id: The ID of the Stock Item.
        """
        url = f"/stock/lookup"
        params = {}
        if code is not None:
            params['code'] = code
        if id is not None:
            params['id'] = id
        return self._request('GET', url, params=params)

    def transaction_search(
        self,
        dateFrom: Optional[str] = None,
        dateTo: Optional[str] = None,
        ownerName: Optional[str] = None,
        batchName: Optional[str] = None,
        wineryName: Optional[str] = None) -> Dict[str, Any]:
        """Transaction search
        
        Returns a list of all operations. These are the same transactions that get generated from Work Detail Report in vintrace.
        
        Args:
            dateFrom: Format in YYYY-MM-DD format. Defaults to current date if not provided. Search for operations completed on or after this date.
            dateTo: Format in YYYY-MM-DD format.  Defaults to current date if not provided. Search for operations completed on or before this date.
            ownerName: String that matches the owner name.
            batchName: String that matches the batch name.
            wineryName: String that matches the winery name.
        """
        url = f"/transaction/search/"
        params = {}
        if dateFrom is not None:
            params['dateFrom'] = dateFrom
        if dateTo is not None:
            params['dateTo'] = dateTo
        if ownerName is not None:
            params['ownerName'] = ownerName
        if batchName is not None:
            params['batchName'] = batchName
        if wineryName is not None:
            params['wineryName'] = wineryName
        return self._request('GET', url, params=params)

    def assign_a_work_order(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Assign a work order
        
        Assign a work order to me
        """
        url = f"/workorders/assign"
        params = None
        return self._request('POST', url, params=params, json=data)

    def submit_job_details(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Submit job details
        """
        url = f"/workorders/jobs/submit"
        params = None
        return self._request('POST', url, params=params, json=data)

    def get_job_details_by_id(self, jobId: str) -> Dict[str, Any]:
        """Get job details by id
        
        Returns a single job with a given id or code.
        
        Args:
            jobId: The ID of the job.
        """
        url = f"/workorders/jobs/{jobId}"
        params = None
        return self._request('GET', url, params=params)

    def list_available_work_orders(
        self,
        max: Optional[str] = None,
        first: Optional[str] = None,
        startsWith: Optional[str] = None,
        assignedTo: Optional[str] = None,
        workOrderState: Optional[str] = None,
        fromDate: Optional[str] = None,
        toDate: Optional[str] = None,
        countOnly: Optional[bool] = None,
        wineryId: Optional[int] = None) -> Dict[str, Any]:
        """List available work orders
        
        By default returns a list of all work orders that are in "Ready", "In progress", or "Submitted" states and are assigned to me or unassigned with a date range from 7 days ago to 3 days from now.
        
        Args:
            max: The starting index of results.
            first: The starting index of results.
            startsWith: String that matches the QuickSearchResult against the start of the name.
            assignedTo: A high-level filter to the work order assignedTo field, from the operator's perspective. Possible values are AVAILABLE_TO_ME, ANYONE, MINE_ONLY, UNASSIGNED. Default value is AVAILABLE_TO_ME.
            workOrderState: A high-level filter for the work order status, from the operator's perspective. Possible values are ANY, IN_PROGRESS, NOT_STARTED, SUBMITTED, INCOMPLETE. Default value is ANY.
            fromDate: Format in YYYY-MM-DD format. Search for work orders with a scheduled date on or after this date. Default value is 7 days ago.
            toDate: in YYYY-MM-DD format. Search for work orders with a scheduled date on or before this date. Default value is 3 days from now.
            countOnly: Returns the number of results only.
            wineryId: Winery id to filter on for work orders
        """
        url = f"/workorders/list/"
        params = {}
        if max is not None:
            params['max'] = max
        if first is not None:
            params['first'] = first
        if startsWith is not None:
            params['startsWith'] = startsWith
        if assignedTo is not None:
            params['assignedTo'] = assignedTo
        if workOrderState is not None:
            params['workOrderState'] = workOrderState
        if fromDate is not None:
            params['fromDate'] = fromDate
        if toDate is not None:
            params['toDate'] = toDate
        if countOnly is not None:
            params['countOnly'] = countOnly
        if wineryId is not None:
            params['wineryId'] = wineryId
        return self._request('GET', url, params=params)

    def get_work_order_details_by_id_or_code(self, id: str, code: Optional[str] = None) -> Dict[str, Any]:
        """Get work order details by id or code
        
        Returns a single work order with a given id or code.
        
        Args:
            id: The ID of the work order.
            code: The TWL number of the work order.
        """
        url = f"/workorders/{id}"
        params = {}
        if code is not None:
            params['code'] = code
        return self._request('GET', url, params=params)
