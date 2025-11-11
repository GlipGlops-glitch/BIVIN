"""
Pydantic models for Vintrace V6 API

Auto-generated from vintrace-v6-apis.yaml
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class AdditionOps(BaseModel):
    vesselId: Optional[int] = None
    vesselName: Optional[str] = None
    batchId: Optional[int] = None
    batchName: Optional[str] = None
    templateId: Optional[int] = None
    templateName: Optional[str] = None
    changeToState: Optional[str] = None
    volume: Optional[str] = None
    amount: Optional[float] = None
    unit: Optional[str] = None
    lotNumbers: Optional[List[str]] = None
    additive: Optional[Additives] = None


class AdditionSummaryItem(BaseModel):
    additive: Optional[Searchable] = None
    rate: Optional[RateAmount] = None


class AdditionsSummary(BaseModel):
    allergens: Optional[List[str]] = None
    additions: Optional[List[AdditionSummaryItem]] = None


class Additives(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None


class Address(BaseModel):
    street1: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None


class AnalysisOps(BaseModel):
    vesselId: Optional[int] = None
    vesselName: Optional[str] = None
    batchId: Optional[int] = None
    batchName: Optional[str] = None
    templateId: Optional[int] = None
    templateName: Optional[str] = None
    metrics: Optional[List[MetricAnalysis]] = None


class AssignWorkData(BaseModel):
    workOrderId: Optional[int] = None
    jobId: Optional[int] = None
    dateStarted: Optional[str] = None
    assignOperatorId: Optional[int] = None
    reassignWorkOrder: Optional[bool] = None


class AssignWorkResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    jobEndpointURL: Optional[str] = None
    workOrderEndpointURL: Optional[str] = None


class Attachment(BaseModel):
    id: Optional[int] = None
    fileName: Optional[str] = None
    fileType: Optional[str] = None
    description: Optional[str] = None
    contentType: Optional[str] = None
    fileContext: Optional[str] = None
    viewEndpoint: Optional[str] = None
    thumbEndpoint: Optional[str] = None
    dateStamp: Optional[str] = None
    fileSize: Optional[float] = None
    fileLocation: Optional[LocationDetails] = None


class BasicBatchDetails(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    vintage: Optional[Searchable] = None
    variety: Optional[Searchable] = None
    region: Optional[Searchable] = None


class BeverageTypeProperties(BaseModel):
    iconColour: Optional[str] = None
    statusCharacter: Optional[str] = None
    statusString: Optional[str] = None
    textColour: Optional[str] = None
    linkedBeverageType: Optional[Searchable] = None


class BrandAllocation(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    vintage: Optional[str] = None
    variety: Optional[str] = None
    region: Optional[str] = None
    geographicIndicator: Optional[str] = None
    owner: Optional[str] = None
    winery: Optional[str] = None


class Codeable(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    shortCode: Optional[str] = None
    externalCode: Optional[str] = None


class Components(BaseModel):
    quantity: Optional[int] = None
    unit: Optional[str] = None
    item: Optional[ItemSummary] = None


class Distribution(BaseModel):
    id: Optional[int] = None
    itemCode: Optional[str] = None
    qty: Optional[int] = None
    available: Optional[int] = None
    areaName: Optional[str] = None
    areaId: Optional[int] = None
    buildingName: Optional[str] = None
    wineryName: Optional[str] = None
    bay: Optional[str] = None
    lotCode: Optional[str] = None
    bondName: Optional[str] = None
    bondNumber: Optional[str] = None
    taxState: Optional[str] = None


class FieldValuePair(BaseModel):
    field: Optional[str] = None
    value: Optional[str] = None
    fieldId: Optional[int] = None
    canEdit: Optional[bool] = None
    canDeselect: Optional[bool] = None
    editableFieldType: Optional[str] = None


class FinalProduct(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    vintage: Optional[str] = None
    variety: Optional[str] = None
    region: Optional[str] = None
    geographicIndicator: Optional[str] = None


class FromVessel(BaseModel):
    name: Optional[str] = None
    id: Optional[int] = None
    beforeDetails: Optional[VesselDetails] = None
    afterDetails: Optional[VesselDetails] = None
    volOut: Optional[int] = None
    volOutUnit: Optional[str] = None


class FullBlockAssessment(BaseModel):
    id: Optional[int] = None
    block: Optional[Codeable] = None
    vintage: Optional[int] = None
    assessmentDate: Optional[str] = None
    assessedBy: Optional[Searchable] = None
    producingForecast: Optional[Weight] = None
    availableForecast: Optional[Weight] = None
    intendedUse: Optional[Searchable] = None
    harvestMethod: Optional[str] = None
    expectedHarvestDate: Optional[int] = None
    earliestHarvestDate: Optional[int] = None
    grading: Optional[Grading] = None
    expectedProgram: Optional[Searchable] = None
    contract: Optional[Searchable] = None
    sprayReportReceived: Optional[int] = None
    sprayReportAttachment: Optional[Attachment] = None
    capitalBlock: Optional[bool] = None
    capitalProjectNumber: Optional[str] = None
    cropInspected: Optional[int] = None
    comments: Optional[str] = None
    exceptionList: Optional[List[str]] = None
    intendedProduct: Optional[Searchable] = None
    attachments: Optional[Attachment] = None
    locationDetails: Optional[LocationDetails] = None


class FullBlockAssessmentRequest(BaseModel):
    id: Optional[int] = None
    block: Optional[Codeable] = None
    vintage: Optional[int] = None
    assessmentDate: Optional[str] = None
    assessedBy: Optional[Searchable] = None
    producingForecast: Optional[Weight] = None
    availableForecast: Optional[Weight] = None
    intendedUse: Optional[Searchable] = None
    harvestMethod: Optional[str] = None
    expectedHarvestDate: Optional[int] = None
    earliestHarvestDate: Optional[int] = None
    grading: Optional[Grading] = None
    expectedProgram: Optional[Searchable] = None
    contract: Optional[Searchable] = None
    sprayReportReceived: Optional[int] = None
    sprayReportAttachment: Optional[Attachment] = None
    capitalBlock: Optional[bool] = None
    capitalProjectNumber: Optional[str] = None
    cropInspected: Optional[int] = None
    comments: Optional[str] = None
    exceptionList: Optional[List[str]] = None
    intendedProduct: Optional[Searchable] = None
    attachments: Optional[Attachment] = None
    locationDetails: Optional[LocationDetails] = None


class Grading(BaseModel):
    id: Optional[int] = None
    value: Optional[str] = None
    scaleName: Optional[str] = None
    scaleId: Optional[int] = None


class Grower(BaseModel):
    pass

class IntakeOperation(BaseModel):
    operationId: Optional[int] = None
    processId: Optional[int] = None
    reversed: Optional[bool] = None
    effectiveDate: Optional[int] = None
    modified: Optional[int] = None
    bookingNumber: Optional[str] = None
    block: Optional[Codeable] = None
    vineyard: Optional[Codeable] = None
    winery: Optional[Searchable] = None
    grower: Optional[Grower] = None
    region: Optional[Codeable] = None
    variety: Optional[Codeable] = None
    owner: Optional[Codeable] = None
    vintage: Optional[int] = None
    deliveryStart: Optional[int] = None
    deliveryEnd: Optional[int] = None
    driverName: Optional[str] = None
    truckRegistration: Optional[str] = None
    carrier: Optional[Codeable] = None
    consignmentNote: Optional[str] = None
    docketNo: Optional[str] = None
    amount: Optional[Weight] = None
    grossAmount: Optional[Weight] = None
    tareAmount: Optional[Weight] = None
    metrics: Optional[List[SimpleMetric]] = None
    mog: Optional[Searchable] = None
    harvestMethod: Optional[str] = None
    intendedUse: Optional[Searchable] = None
    growerContract: Optional[Searchable] = None
    lastLoad: Optional[bool] = None
    fruitCost: Optional[float] = None
    fruitCostRateType: Optional[str] = None
    area: Optional[float] = None
    additionalDetails: Optional[Dict[str, Any]] = None
    externalWeighTag: Optional[str] = None


class IntakeOperationSearchResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    resultCount: Optional[int] = None
    resultLimit: Optional[int] = None
    nextResult: Optional[int] = None
    intakes: Optional[List[IntakeOperation]] = None


class InventorySummary(BaseModel):
    date: Optional[int] = None
    dateAsText: Optional[str] = None
    winery: Optional[str] = None
    quantity: Optional[int] = None
    committed: Optional[int] = None
    onOrder: Optional[int] = None
    available: Optional[int] = None
    unit: Optional[str] = None
    type: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    lotBatch: Optional[str] = None
    lotExpiryDate: Optional[str] = None
    lotExpiryDateAsText: Optional[str] = None
    lotManufactureDate: Optional[str] = None
    lotManufactureDateAsText: Optional[str] = None
    reorderCode: Optional[str] = None
    location: Optional[str] = None
    stockCategory: Optional[str] = None
    grading: Optional[Grading] = None
    price: Optional[str] = None
    priceAsText: Optional[str] = None
    taxClass: Optional[str] = None
    federalTaxClass: Optional[str] = None
    stateTaxClass: Optional[str] = None
    taxState: Optional[str] = None
    bond: Optional[str] = None
    sizeRatio: Optional[str] = None
    finalProducts: Optional[str] = None
    vintage: Optional[str] = None
    variety: Optional[str] = None
    region: Optional[str] = None
    program: Optional[str] = None
    productState: Optional[str] = None
    beverageType: Optional[str] = None
    baseMaterial: Optional[str] = None
    owner: Optional[str] = None
    assetAccount: Optional[str] = None
    cogsAccount: Optional[str] = None
    unitCost: Optional[float] = None
    unitCostAsText: Optional[str] = None
    totalCost: Optional[float] = None
    totalCostAsText: Optional[str] = None
    fruitCost: Optional[str] = None
    fruitCostAsText: Optional[str] = None
    bulkCost: Optional[str] = None
    bulkCostAsText: Optional[str] = None
    additiveCost: Optional[str] = None
    additiveCostAsText: Optional[str] = None
    operationCost: Optional[str] = None
    operationCostAsText: Optional[str] = None
    packagingCost: Optional[str] = None
    packagingCostAsText: Optional[str] = None
    storageCost: Optional[str] = None
    storageCostAsText: Optional[str] = None
    overheadCost: Optional[str] = None
    overheadCostAsText: Optional[str] = None
    freightCost: Optional[str] = None
    freightCostAsText: Optional[str] = None
    otherCost: Optional[str] = None
    otherCostAsText: Optional[str] = None
    sku: Optional[str] = None
    stockItemDetailsEndpoint: Optional[str] = None


class InventorySummaryResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    inventorySummaries: Optional[List[InventorySummary]] = None


class ItemSummary(BaseModel):
    id: Optional[int] = None
    itemType: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class Job(BaseModel):
    id: Optional[int] = None
    code: Optional[str] = None
    scheduledDate: Optional[int] = None
    finishedDate: Optional[str] = None
    scheduledDateAsText: Optional[str] = None
    finishedDateAsText: Optional[str] = None
    status: Optional[str] = None
    assignedBy: Optional[str] = None
    assignedTo: Optional[str] = None
    summaryText: Optional[str] = None
    miniSummaryText: Optional[str] = None
    jobColour: Optional[str] = None
    jobNumber: Optional[int] = None
    stepText: Optional[str] = None
    steps: Optional[List[JobStep]] = None
    endpointURL: Optional[str] = None
    jobVersion: Optional[int] = None
    workOrderId: Optional[int] = None
    type: Optional[str] = None
    operationType: Optional[str] = None


class JobField(BaseModel):
    fieldId: Optional[str] = None
    fieldName: Optional[str] = None
    fieldType: Optional[str] = None
    dataType: Optional[str] = None
    mandatory: Optional[bool] = None
    minSelections: Optional[int] = None
    maxSelections: Optional[int] = None
    selectedValues: Optional[List[JobFieldValue]] = None
    stringValue: Optional[str] = None


class JobFieldValue(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    dataType: Optional[str] = None
    code: Optional[str] = None
    # Language-agnostic values for fill types, such as `Full`, `Half`
    fillType: Optional[str] = None
    # Localised version of `fillType` for display purpose. If language settings is English, this will have the same value as `fillType`.
    fillTypeDisplay: Optional[str] = None
    confirmed: Optional[bool] = None
    amount: Optional[str] = None
    extraDetailKey: Optional[str] = None
    preferred: Optional[bool] = None
    breakdownMap: Optional[List[str]] = None
    additionalDetails: Optional[List[str]] = None


class JobStep(BaseModel):
    stepId: Optional[int] = None
    stepNumber: Optional[int] = None
    stepName: Optional[str] = None
    instructionText: Optional[str] = None
    fields: Optional[List[JobField]] = None
    endpointURL: Optional[str] = None


class LocationDetails(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formattedAddress: Optional[str] = None


class LossDetails(BaseModel):
    volume: Optional[int] = None
    volumeUnit: Optional[str] = None
    reason: Optional[str] = None


class MetricAnalysis(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    value: Optional[float] = None
    txtValue: Optional[str] = None
    unit: Optional[str] = None


class Party(BaseModel):
    primeName: Optional[str] = None
    phone: Optional[str] = None
    id: Optional[int] = None
    givenName: Optional[str] = None
    email: Optional[str] = None
    address: Optional[Address] = None
    isOrganization: Optional[bool] = None


class PartyResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    parties: Optional[List[Party]] = None


class PartyUpdateResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    party: Optional[Party] = None


class PriceList(BaseModel):
    countryCurrencyCode: Optional[str] = None
    taxPolicy: Optional[str] = None


class Product(BaseModel):
    id: Optional[int] = None
    batchCode: Optional[str] = None
    vesselId: Optional[int] = None
    description: Optional[str] = None
    descriptionCanEdit: Optional[bool] = None
    volume: Optional[Dict[str, Any]] = None
    vesselCode: Optional[str] = None
    hasDipTable: Optional[bool] = None
    dipTableEndpoint: Optional[str] = None
    colour: Optional[str] = None
    physicalProductState: Optional[str] = None
    vesselType: Optional[str] = None
    productStatus: Optional[str] = None
    productAnalysisEndpoint: Optional[str] = None
    productCompositionEndpoint: Optional[str] = None
    productEndpoint: Optional[str] = None
    liveMetrics: Optional[List[ProductLiveMetric]] = None
    fieldValuePairs: Optional[List[FieldValuePair]] = None
    canAccessNotes: Optional[bool] = None
    notesCount: Optional[int] = None
    notesEndpoint: Optional[str] = None
    beverageTypeProperties: Optional[BeverageTypeProperties] = None


class ProductCompositonData(BaseModel):
    key: Optional[str] = None
    value: Optional[float] = None
    valueStr: Optional[str] = None
    volume: Optional[str] = None
    unit: Optional[str] = None


class ProductCompositonSummary(BaseModel):
    compositionView: Optional[str] = None
    elementData: Optional[List[ProductCompositonData]] = None


class ProductListResponse(BaseModel):
    status: Optional[str] = None
    products: Optional[List[Product]] = None


class ProductLiveMetric(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    unit: Optional[str] = None
    dataType: Optional[str] = None
    dataTypeValues: Optional[str] = None
    minVal: Optional[int] = None
    maxVal: Optional[int] = None
    measurements: Optional[List[ProductLiveMetricMeasurement]] = None


class ProductLiveMetricMeasurement(BaseModel):
    value: Optional[str] = None
    rateOfChange: Optional[RateOfChangeResponse] = None
    measurementDateText: Optional[str] = None
    measurementDate: Optional[int] = None
    resultId: Optional[int] = None
    canDelete: Optional[bool] = None


class ProductResponse(BaseModel):
    status: Optional[str] = None
    product: Optional[Product] = None
    vessel: Optional[ProductVesselDetails] = None


class ProductUpdateData(BaseModel):
    productId: Optional[int] = None
    effectiveDate: Optional[str] = None
    updateFields: Optional[List[ProductUpdateField]] = None


class ProductUpdateField(BaseModel):
    propertyType: Optional[str] = None
    propertyValue: Optional[str] = None
    propertyId: Optional[int] = None


class ProductUpdateResponse(BaseModel):
    status: Optional[str] = None
    errorList: Optional[List[str]] = None
    product: Optional[Product] = None


class ProductVesselDetails(BaseModel):
    vesselId: Optional[int] = None
    containerType: Optional[str] = None


class QuantityBreakdown(BaseModel):
    onHand: Optional[int] = None
    committed: Optional[int] = None
    ordered: Optional[int] = None
    available: Optional[int] = None


class RateAmount(BaseModel):
    amount: Optional[str] = None
    rate: Optional[str] = None


class RateOfChangeResponse(BaseModel):
    value: Optional[float] = None
    sign: Optional[str] = None
    absValue: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None


class Refund(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    refundDate: Optional[int] = None
    refundDateAsText: Optional[str] = None
    reference: Optional[str] = None
    stockReturned: Optional[bool] = None
    storageAreaId: Optional[str] = None
    storageAreaName: Optional[str] = None
    customerId: Optional[int] = None
    customerName: Optional[str] = None
    refundStatus: Optional[str] = None
    notes: Optional[str] = None
    salesOrderId: Optional[int] = None
    salesOrderName: Optional[str] = None
    subTotal: Optional[float] = None
    total: Optional[float] = None
    taxBreakdown: Optional[List[TaxAmount]] = None
    refundLineItems: Optional[List[RefundLineItem]] = None
    posSaleReference: Optional[str] = None


class RefundLineItem(BaseModel):
    id: Optional[int] = None
    itemId: Optional[int] = None
    itemName: Optional[str] = None
    unitPrice: Optional[int] = None
    returnQuantity: Optional[int] = None
    returnTotal: Optional[int] = None
    taxAmount: Optional[float] = None


class RefundResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    refund: Optional[List[Refund]] = None


class RefundUpdateResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    refund: Optional[Refund] = None


class SalesOrder(BaseModel):
    id: Optional[int] = None
    invoiceDate: Optional[str] = None
    invoiceDateAsText: Optional[str] = None
    customerId: Optional[int] = None
    customerName: Optional[str] = None
    sendTo: Optional[Party] = None
    salesType: Optional[str] = None
    salesPriceListId: Optional[int] = None
    salesPriceListName: Optional[str] = None
    priceDetails: Optional[PriceList] = None
    salesOrderStatus: Optional[str] = None
    salesOrderItems: Optional[List[SalesOrderItem]] = None
    code: Optional[str] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    orderDate: Optional[int] = None
    orderDateAsText: Optional[str] = None
    wineryId: Optional[str] = None
    wineryName: Optional[str] = None
    fulfillment: Optional[str] = None
    fulfillmentDate: Optional[str] = None
    fulfillmentDateAsText: Optional[str] = None
    salesRegionId: Optional[str] = None
    salesRegionCode: Optional[str] = None
    notes: Optional[str] = None
    customerPickup: Optional[bool] = None
    disableAccountsSync: Optional[bool] = None
    subTotal: Optional[int] = None
    taxBreakdown: Optional[List[TaxAmount]] = None
    total: Optional[int] = None
    acctReference: Optional[str] = None
    posSaleReference: Optional[str] = None
    ignoreStockError: Optional[bool] = None
    externalTransactionId: Optional[str] = None


class SalesOrderItem(BaseModel):
    id: Optional[int] = None
    itemId: Optional[int] = None
    itemName: Optional[str] = None
    unitPrice: Optional[float] = None
    quantity: Optional[int] = None
    unitOfMeasure: Optional[str] = None
    discountPct: Optional[str] = None
    adjustment: Optional[str] = None
    taxAmount: Optional[float] = None
    lineTotal: Optional[int] = None
    accountId: Optional[int] = None
    accountCode: Optional[str] = None
    taxRateId: Optional[int] = None
    taxRateName: Optional[str] = None
    sku: Optional[str] = None
    externalReference: Optional[str] = None


class SalesOrderResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    salesOrders: Optional[List[SalesOrder]] = None


class SalesOrderUpdateResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    salesOrders: Optional[SalesOrder] = None


class SampleOperation(BaseModel):
    operationId: Optional[int] = None
    processId: Optional[int] = None
    reversed: Optional[bool] = None
    modified: Optional[int] = None
    block: Optional[Codeable] = None
    vineyard: Optional[Codeable] = None
    grower: Optional[Codeable] = None
    region: Optional[Codeable] = None
    variety: Optional[Codeable] = None
    owner: Optional[Codeable] = None
    vintage: Optional[int] = None
    recordedDate: Optional[int] = None
    reference: Optional[str] = None
    row: Optional[str] = None
    vine: Optional[str] = None
    grading: Optional[Grading] = None
    sampleArea: Optional[str] = None
    sampleType: Optional[str] = None
    laboratory: Optional[Codeable] = None
    analysisTemplate: Optional[Searchable] = None
    metrics: Optional[List[SimpleMetric]] = None
    additionalDetails: Optional[Dict[str, Any]] = None


class SampleOperationSearchResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    resultCount: Optional[int] = None
    resultLimit: Optional[int] = None
    nextResult: Optional[int] = None
    samples: Optional[List[SampleOperation]] = None


class SearchDescriptive(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None


class Searchable(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    summary: Optional[str] = None
    type: Optional[str] = None


class SimpleCoded(BaseModel):
    id: Optional[int] = None
    code: Optional[str] = None


class SimpleMetric(BaseModel):
    metricName: Optional[str] = None
    metricShortCode: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    recorded: Optional[str] = None
    metricId: Optional[int] = None


class SimpleSearchResponse(BaseModel):
    firstResult: Optional[int] = None
    maxResult: Optional[int] = None
    totalResultCount: Optional[int] = None
    type: Optional[str] = None
    nextURLPath: Optional[str] = None
    prevURLPath: Optional[str] = None
    simpleSearchResults: Optional[List[SimpleSearchResult]] = None


class SimpleSearchResult(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    summary: Optional[str] = None
    additionalDetails: Optional[Dict[str, Any]] = None


class StockBulkInfoDetail(BaseModel):
    endpoint: Optional[str] = None
    message: Optional[str] = None
    metrics: Optional[List[SimpleMetric]] = None
    compositionDetails: Optional[List[ProductCompositonSummary]] = None
    additionsSummary: Optional[List[AdditionsSummary]] = None


class StockDistributionDetail(BaseModel):
    endpoint: Optional[str] = None
    distributions: Optional[List[StockDistributionItem]] = None


class StockDistributionItem(BaseModel):
    id: Optional[int] = None
    item: Optional[StockItemBasics] = None
    winery: Optional[SearchDescriptive] = None
    building: Optional[SearchDescriptive] = None
    storageArea: Optional[SearchDescriptive] = None
    bay: Optional[str] = None
    unit: Optional[Unit] = None
    quantity: Optional[QuantityBreakdown] = None
    taxState: Optional[TaxState] = None
    virtual: Optional[bool] = None


class StockFieldsDetail(BaseModel):
    endpoint: Optional[str] = None
    fields: Optional[List[FieldValuePair]] = None


class StockForm(BaseModel):
    group: Optional[str] = None
    variant: Optional[str] = None


class StockHistoryItem(BaseModel):
    operationId: Optional[int] = None
    operatorName: Optional[str] = None
    quantity: Optional[int] = None
    balance: Optional[int] = None
    date: Optional[int] = None
    workorder: Optional[SimpleCoded] = None
    actionType: Optional[str] = None
    batch: Optional[str] = None
    item: Optional[StockItemBasics] = None
    attachments: Optional[List[Attachment]] = None
    canReverse: Optional[bool] = None


class StockHistoryItemsDetail(BaseModel):
    endpoint: Optional[str] = None
    firstResult: Optional[int] = None
    maxResult: Optional[int] = None
    totalResultCount: Optional[int] = None
    historyItems: Optional[List[StockHistoryItem]] = None


class StockItem(BaseModel):
    id: Optional[int] = None
    code: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    inactive: Optional[bool] = None
    modified: Optional[int] = None
    type: Optional[StockType] = None
    category: Optional[SearchDescriptive] = None
    beverageProperties: Optional[BeverageTypeProperties] = None
    unit: Optional[Unit] = None
    quantity: Optional[QuantityBreakdown] = None
    owner: Optional[SearchDescriptive] = None
    wineProduct: Optional[bool] = None
    lotTracked: Optional[bool] = None
    levelTracked: Optional[bool] = None
    tags: Optional[List[Tag]] = None
    userPermissions: Optional[List[str]] = None
    fields: Optional[StockFieldsDetail] = None
    distributions: Optional[StockDistributionDetail] = None
    historyItems: Optional[StockHistoryItemsDetail] = None
    rawComponents: Optional[StockRawComponentsDetail] = None
    bulkInfo: Optional[StockBulkInfoDetail] = None
    notes: Optional[StockNotesDetail] = None


class StockItemBasics(BaseModel):
    id: Optional[int] = None
    code: Optional[str] = None
    description: Optional[str] = None
    endpoint: Optional[str] = None


class StockItemDetails(BaseModel):
    id: Optional[int] = None
    code: Optional[str] = None
    description: Optional[str] = None
    itemType: Optional[str] = None
    unit: Optional[Unit] = None
    owner: Optional[Searchable] = None
    assetAccount: Optional[str] = None
    cogsAccount: Optional[str] = None
    category: Optional[Searchable] = None
    product: Optional[FinalProduct] = None
    brand: Optional[BrandAllocation] = None
    federalTaxClass: Optional[str] = None
    stateTaxClass: Optional[str] = None
    rawTaxClass: Optional[str] = None
    sku: Optional[str] = None
    labelAlcohol: Optional[int] = None
    lotTracked: Optional[bool] = None
    levelTracked: Optional[bool] = None
    subComponents: Optional[List[Components]] = None
    rawComponents: Optional[List[Components]] = None
    distributions: Optional[List[Distribution]] = None


class StockNote(BaseModel):
    id: Optional[int] = None
    date: Optional[str] = None
    dateText: Optional[str] = None
    who: Optional[str] = None
    subject: Optional[str] = None
    detail: Optional[str] = None
    item: Optional[Searchable] = None
    attachments: Optional[List[Attachment]] = None
    inactive: Optional[bool] = None


class StockNotesDetail(BaseModel):
    endpoint: Optional[str] = None
    maxResult: Optional[int] = None
    firstResult: Optional[int] = None
    totalResultCount: Optional[int] = None
    prevURLPath: Optional[str] = None
    nextURLPath: Optional[str] = None
    notes: Optional[List[StockNote]] = None


class StockRawComponentItem(BaseModel):
    endpoint: Optional[str] = None
    id: Optional[int] = None
    code: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[Unit] = None
    type: Optional[StockType] = None
    bomQuantity: Optional[float] = None
    beverageProperties: Optional[BeverageTypeProperties] = None


class StockRawComponentsDetail(BaseModel):
    endpoint: Optional[str] = None
    rawComponents: Optional[StockRawComponentItem] = None


class StockType(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None
    form: Optional[StockForm] = None


class SubmitJobRequest(BaseModel):
    jobId: Optional[int] = None
    submitType: Optional[str] = None
    dateStarted: Optional[str] = None
    fields: Optional[List[SubmitJobRequestField]] = None
    attachments: Optional[List[Attachment]] = None


class SubmitJobRequestField(BaseModel):
    fieldId: Optional[str] = None
    value: Optional[str] = None
    dataType: Optional[str] = None
    parentFieldId: Optional[str] = None
    selectedValues: Optional[List[SubmitJobRequestFieldValue]] = None


class SubmitJobRequestFieldValue(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    code: Optional[str] = None
    fillType: Optional[str] = None
    checked: Optional[bool] = None
    amount: Optional[str] = None
    preferred: Optional[bool] = None


class SubmitWorkOrderStepsResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None


class Tag(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    sortIndex: Optional[int] = None


class TaxAmount(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    ratePct: Optional[int] = None
    inclusive: Optional[bool] = None


class TaxState(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None
    defaultForInventory: Optional[bool] = None


class ToVessel(BaseModel):
    name: Optional[str] = None
    id: Optional[int] = None
    beforeDetails: Optional[VesselDetails] = None
    afterDetails: Optional[VesselDetails] = None
    volIn: Optional[int] = None
    volInUnit: Optional[str] = None


class TransOperation(BaseModel):
    formattedDate: Optional[str] = None
    date: Optional[int] = None
    operationId: Optional[int] = None
    operationTypeId: Optional[int] = None
    operationTypeName: Optional[str] = None
    subOperationTypeId: Optional[int] = None
    subOperationTypeName: Optional[str] = None
    workorder: Optional[str] = None
    jobNumber: Optional[str] = None
    treatment: Optional[str] = None
    assignedBy: Optional[str] = None
    completedBy: Optional[str] = None
    winery: Optional[str] = None
    fromVessel: Optional[FromVessel] = None
    toVessel: Optional[ToVessel] = None
    lossDetails: Optional[LossDetails] = None
    additionOps: Optional[AdditionOps] = None
    analysisOps: Optional[AnalysisOps] = None
    additionalDetails: Optional[str] = None


class TransactionSummaryResponse(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    transactionSummaries: Optional[List[TransOperation]] = None


class Unit(BaseModel):
    description: Optional[str] = None
    abbreviation: Optional[str] = None
    key: Optional[str] = None
    precision: Optional[int] = None


class VesselDetails(BaseModel):
    contentsId: Optional[int] = None
    batch: Optional[str] = None
    batchId: Optional[int] = None
    volume: Optional[int] = None
    volumeUnit: Optional[str] = None
    dip: Optional[str] = None
    state: Optional[str] = None
    rawTaxClass: Optional[str] = None
    federalTaxClass: Optional[str] = None
    stateTaxClass: Optional[str] = None
    program: Optional[str] = None
    batchDetails: Optional[BasicBatchDetails] = None
    bondNumber: Optional[str] = None
    bondRegisteredName: Optional[str] = None


class VolumeMeasurement(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None


class Weight(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None


class WorkOrder(BaseModel):
    id: Optional[int] = None
    code: Optional[str] = None
    jobCount: Optional[int] = None
    jobCountText: Optional[str] = None
    status: Optional[str] = None
    assignedTo: Optional[str] = None
    assignedBy: Optional[str] = None
    assignedDate: Optional[int] = None
    scheduledDate: Optional[int] = None
    assignedDateAsText: Optional[str] = None
    scheduledDateAsText: Optional[str] = None
    canAssign: Optional[bool] = None
    summary: Optional[str] = None
    indicators: Optional[List[str]] = None
    bond: Optional[str] = None
    winery: Optional[str] = None
    jobs: Optional[List[Job]] = None
    colourCode: Optional[str] = None
    endpointURL: Optional[str] = None


class WorkOrderSearchResponse(BaseModel):
    firstResult: Optional[int] = None
    maxResult: Optional[int] = None
    totalResultCount: Optional[int] = None
    nextURLPath: Optional[str] = None
    prevURLPath: Optional[str] = None
    listText: Optional[str] = None
    workOrders: Optional[List[WorkOrder]] = None

