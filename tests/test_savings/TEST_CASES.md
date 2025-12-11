# Savings Endpoints Test Suite

## Overview
Comprehensive pytest test suite for the savings module endpoints with 15+ test cases covering all functionality.

## Test File Location
`tests/test_savings/test_savings_endpoints.py`

## Test Cases

### 1. **test_create_daily_saving** ✅
- **Purpose**: Test creating a single daily saving
- **Endpoint**: `POST /savings/create`
- **Assertions**:
  - Status code 201 (Created)
  - Response contains correct name and amount
  - Response includes user_id and auto-generated id
  - Timestamp (created_at) is included

### 2. **test_create_multiple_daily_savings** ✅
- **Purpose**: Test creating multiple daily savings in sequence
- **Endpoint**: `POST /savings/create`
- **Assertions**:
  - Each creation returns 201
  - Each saving has correct data
  - Multiple records are created successfully

### 3. **test_get_savings_this_week** ✅
- **Purpose**: Test retrieving savings for current week
- **Endpoint**: `GET /savings/period?period=this_week`
- **Assertions**:
  - Status code 200
  - Period filter returns "this_week"
  - Total amount is correctly calculated
  - Transaction count is accurate
  - Transactions are returned with correct data

### 4. **test_get_savings_this_month** ✅
- **Purpose**: Test retrieving savings for current month
- **Endpoint**: `GET /savings/period?period=this_month`
- **Assertions**:
  - Status code 200
  - Multiple records are aggregated correctly
  - Total amount (450.0) is sum of all amounts
  - Transaction count = 3

### 5. **test_get_savings_this_year** ✅
- **Purpose**: Test retrieving savings for current year
- **Endpoint**: `GET /savings/period?period=this_year`
- **Assertions**:
  - Status code 200
  - All records from year are included
  - Total amount = 1500.0 (100+200+300+400+500)
  - Transaction count = 5

### 6. **test_get_savings_last_six_months** ✅
- **Purpose**: Test retrieving savings for last 6 months
- **Endpoint**: `GET /savings/period?period=last_six_months`
- **Assertions**:
  - Status code 200
  - Period filter returns "last_six_months"
  - Total amount is correct
  - Records within 6-month window are included

### 7. **test_get_all_savings_with_pagination** ✅
- **Purpose**: Test retrieving all savings with pagination
- **Endpoint**: `GET /savings/all?limit=5&offset=0`
- **Assertions**:
  - First page returns 5 records
  - Most recent record appears first (desc order)
  - Second page (offset=5) returns next 5 records
  - Pagination works correctly with limit and offset

### 8. **test_invalid_period** ✅
- **Purpose**: Test error handling for invalid period
- **Endpoint**: `GET /savings/period?period=invalid_period`
- **Assertions**:
  - Status code 400 (Bad Request)
  - Error message mentions "Invalid period"

### 9. **test_empty_savings_list** ✅
- **Purpose**: Test retrieving savings when no records exist
- **Endpoint**: `GET /savings/period?period=this_week`
- **Assertions**:
  - Status code 200
  - Total amount = 0.0
  - Transaction count = 0
  - Empty transactions array returned

### 10. **test_unauthorized_access** ✅
- **Purpose**: Test endpoint access without authentication
- **Endpoint**: `POST /savings/create` (without token)
- **Assertions**:
  - Status code 403 (Forbidden)
  - Request is rejected without Bearer token

### 11. **test_user_isolation** ✅
- **Purpose**: Test data isolation between users
- **Endpoint**: `GET /savings/period?period=this_month` (multiple users)
- **Assertions**:
  - User 1 only sees their savings (100.0)
  - User 2 only sees their savings (200.0)
  - Users cannot access each other's data
  - Transaction counts are isolated

### 12. **test_create_saving_with_decimal_amount** ✅
- **Purpose**: Test creating savings with decimal precision
- **Endpoint**: `POST /savings/create`
- **Assertions**:
  - Decimal amounts (123.45) are preserved
  - Floating-point precision is maintained
  - Status code 201

### 13. **test_create_saving_with_zero_amount** ✅
- **Purpose**: Test edge case with zero amount
- **Endpoint**: `POST /savings/create`
- **Assertions**:
  - Zero amount is accepted
  - Status code 201
  - Amount is stored as 0.0

### 14. **test_pagination_with_large_offset** ✅
- **Purpose**: Test pagination with offset exceeding total records
- **Endpoint**: `GET /savings/all?limit=10&offset=100`
- **Assertions**:
  - Status code 200
  - Empty list returned when offset exceeds total
  - No error thrown for out-of-range offset

## Test Coverage Matrix

| Feature | Test Case | Coverage |
|---------|-----------|----------|
| Create Savings | test_create_daily_saving | ✅ |
| Create Multiple | test_create_multiple_daily_savings | ✅ |
| Period Filter - Week | test_get_savings_this_week | ✅ |
| Period Filter - Month | test_get_savings_this_month | ✅ |
| Period Filter - Year | test_get_savings_this_year | ✅ |
| Period Filter - 6 Months | test_get_savings_last_six_months | ✅ |
| Pagination | test_get_all_savings_with_pagination | ✅ |
| Invalid Period | test_invalid_period | ✅ |
| Empty Results | test_empty_savings_list | ✅ |
| Authentication | test_unauthorized_access | ✅ |
| User Isolation | test_user_isolation | ✅ |
| Decimal Amounts | test_create_saving_with_decimal_amount | ✅ |
| Zero Amount | test_create_saving_with_zero_amount | ✅ |
| Large Offset | test_pagination_with_large_offset | ✅ |

## Running the Tests

### Run all savings tests:
```bash
pytest tests/test_savings/test_savings_endpoints.py -v
```

### Run specific test:
```bash
pytest tests/test_savings/test_savings_endpoints.py::test_create_daily_saving -v
```

### Run with coverage:
```bash
pytest tests/test_savings/test_savings_endpoints.py --cov=ppgc_backend.app.controllers.savings --cov-report=html
```

### Run async tests:
```bash
pytest tests/test_savings/test_savings_endpoints.py -v --asyncio-mode=auto
```

## Helper Functions

### `create_test_user()`
Creates a test user with default or custom credentials for testing
- Parameters: `db`, `email`, `first_name`
- Returns: User instance with authentication token

## Test Structure

All tests follow the same pattern:
1. **Unpack fixtures** - Get AsyncClient and AsyncSession
2. **Create test user** - User-specific data testing
3. **Get token** - Generate JWT for authentication
4. **Execute request** - Call API endpoint
5. **Assert response** - Verify status code and data
6. **Validate result** - Check calculations and data integrity

## Key Features Tested

✅ **CRUD Operations**
- Create daily savings records
- Retrieve by period
- List all with pagination

✅ **Period Filtering**
- This week
- This month
- This year
- Last six months

✅ **Data Aggregation**
- Total amount calculation
- Transaction counting
- Correct ordering

✅ **Security**
- Authentication requirement
- User data isolation
- Unauthorized access rejection

✅ **Edge Cases**
- Zero amounts
- Decimal precision
- Large offsets
- Empty result sets
- Invalid periods

✅ **Pagination**
- Limit parameter
- Offset parameter
- Correct ordering (most recent first)
