# API Endpoints Documentation

This document provides a comprehensive breakdown of the API endpoints available at api.congress.gov and govinfo.gov.

## api.congress.gov API

### Authentication
- **API Key Required**: Yes
- **Methods**: 
  - HTTP Header: `X-Api-Key: YOUR_KEY`
  - Query Parameter: `api_key=YOUR_KEY`
  - HTTP Basic Auth: username=YOUR_KEY, password=(empty)
- **Get Key**: Sign up at https://api.data.gov/signup/

### Rate Limits
- **Standard Key**: 5,000 requests per hour
- **DEMO_KEY**: 30 requests per IP per hour, 50 per day (not recommended for production)
- **Headers Returned**:
  - `X-RateLimit-Limit`: Total allowed requests
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Time when the limit resets

### Pagination
- **Default**: 20 results per request
- **Maximum**: 250 results per request
- **Offset Parameter**: `offset` - starting position (0-indexed)
- **Limit Parameter**: `limit` - number of results (max 250)

### Available Endpoints

#### 1. Bills (`/bill`)
**Purpose**: Retrieve legislative bill data
**Example**: `https://api.congress.gov/v3/bill?api_key=YOUR_KEY`
**Parameters**:
- `congress`: Congress number (e.g., 118)
- `type`: Bill type (hr, s, hjres, sjres, hconres, sconres, hres, sres)
- `limit`: Results per page (max 250)
- `offset`: Starting position

#### 2. Amendments (`/amendment`)
**Purpose**: Access amendment data
**Example**: `https://api.congress.gov/v3/amendment?api_key=YOUR_KEY`
**Parameters**: Similar to bills

#### 3. Committees (`/committee`)
**Purpose**: Get committee information
**Example**: `https://api.congress.gov/v3/committee?api_key=YOUR_KEY`
**Parameters**:
- `chamber`: house, senate, or joint
- `limit`, `offset`

#### 4. Members (`/member`)
**Purpose**: Information about Congress members
**Example**: `https://api.congress.gov/v3/member?api_key=YOUR_KEY`
**Parameters**:
- `currentMember`: true/false
- `limit`, `offset`

#### 5. Nominations (`/nomination`)
**Purpose**: Federal nominations data
**Example**: `https://api.congress.gov/v3/nomination?api_key=YOUR_KEY`

#### 6. Congressional Record (`/congressional-record`)
**Purpose**: Congressional Record entries
**Example**: `https://api.congress.gov/v3/congressional-record?api_key=YOUR_KEY`

#### 7. Committee Communications (`/committee-communication`)
**Purpose**: Committee communications
**Example**: `https://api.congress.gov/v3/committee-communication?api_key=YOUR_KEY`

#### 8. Treaties (`/treaty`)
**Purpose**: Treaty records
**Example**: `https://api.congress.gov/v3/treaty?api_key=YOUR_KEY`

## govinfo.gov API

### Authentication
- **API Key Required**: Yes (from api.data.gov)
- **Method**: Query parameter `api_key=YOUR_KEY`
- **Get Key**: https://api.data.gov/signup/

### Rate Limits
- **Hourly Rolling Limit**: Apply (specific numbers not publicly documented, use cautiously)
- **Best Practice**: Monitor response headers and implement exponential backoff

### Base URL
`https://api.govinfo.gov/`

### Available Endpoints

#### 1. Collections (`/collections`)
**Purpose**: List all available document collections
**Example**: `https://api.govinfo.gov/collections?api_key=YOUR_KEY`
**Response**: Array of collection codes and names

**Major Collections**:
- `BILLS`: Congressional bills
- `BILLSTATUS`: Bill status/progress
- `CFR`: Code of Federal Regulations
- `ECFR`: Electronic Code of Federal Regulations
- `FR`: Federal Register
- `USCODE`: United States Code
- `STATUTE`: Statutes at Large
- `CONGRECORD`: Congressional Record
- `CREC`: Congressional Record (alternative)
- `CHRG`: Committee hearings
- `CPRT`: Committee prints
- `CRPT`: Committee reports
- `HMAN`: House Manual
- `SMAN`: Senate Manual

#### 2. Collection Query (`/collections/{collection}`)
**Purpose**: Query documents in a specific collection
**Example**: `https://api.govinfo.gov/collections/BILLS?offset=0&pageSize=100&api_key=YOUR_KEY`
**Parameters**:
- `offset`: Starting position (0-indexed)
- `pageSize`: Results per page (default 100, max 1000)

#### 3. Date-Based Query (`/collections/{collection}/{lastModifiedStartDate}`)
**Purpose**: Get new/updated packages since a date
**Example**: `https://api.govinfo.gov/collections/BILLS/2024-01-01T00:00:00Z?api_key=YOUR_KEY`
**Date Format**: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
**Parameters**:
- `lastModifiedEndDate`: Optional end date
- `offset`, `pageSize`

#### 4. Package Summary (`/packages/{packageId}/summary`)
**Purpose**: Get metadata for a specific package
**Example**: `https://api.govinfo.gov/packages/BILLS-118hr1-ih/summary?api_key=YOUR_KEY`
**Response**: Complete metadata including title, dates, download links

#### 5. Package Granules (`/packages/{packageId}/granules`)
**Purpose**: List components (granules) of a package
**Example**: `https://api.govinfo.gov/packages/FR-2024-01-02/granules?api_key=YOUR_KEY`
**Parameters**: `offset`, `pageSize`

#### 6. Published Date Query (`/published/{dateIssuedStartDate}`)
**Purpose**: List packages by publication date
**Example**: `https://api.govinfo.gov/published/2024-01-01?api_key=YOUR_KEY`
**Parameters**:
- `dateIssuedEndDate`: Optional end date
- `collection`: Filter by collection
- `offset`, `pageSize`

#### 7. Related Documents (`/related/{accessId}`)
**Purpose**: Discover relationships between documents
**Example**: `https://api.govinfo.gov/related/BILLS-118hr1?api_key=YOUR_KEY`

#### 8. Search (`/search`)
**Purpose**: Advanced search across collections
**Example**: `https://api.govinfo.gov/search?query=climate+change&collection=FR&api_key=YOUR_KEY`
**Parameters**:
- `query`: Search terms
- `collection`: Filter by collection
- `publishedDate`: Date range filter
- `offset`, `pageSize`

## Bulk Data Endpoints (govinfo.gov/bulkdata)

### Base URL
`https://www.govinfo.gov/bulkdata`

### Format Options
- **HTML**: Default browsing interface
- **XML**: Append `/xml` to any bulkdata URL
- **JSON**: Append `/json` to any bulkdata URL

### Important Headers
When programmatically accessing XML/JSON endpoints:
- JSON: `Accept: application/json`
- XML: `Accept: application/xml`

Without proper Accept headers, you may receive 406 (Not Acceptable) responses.

### Collection Examples

#### Bills
- **URL**: `https://www.govinfo.gov/bulkdata/BILLS`
- **Structure**: `/BILLS/{congress}/{session}/{type}`
- **Example**: `https://www.govinfo.gov/bulkdata/BILLS/118/1/hr`
- **JSON**: `https://www.govinfo.gov/bulkdata/json/BILLS/118/1/hr`
- **XML**: `https://www.govinfo.gov/bulkdata/xml/BILLS/118/1/hr`

#### Code of Federal Regulations (CFR)
- **URL**: `https://www.govinfo.gov/bulkdata/CFR`
- **Structure**: `/CFR/{year}/title-{title}`
- **Example**: `https://www.govinfo.gov/bulkdata/CFR/2024`

#### Federal Register
- **URL**: `https://www.govinfo.gov/bulkdata/FR`
- **Structure**: `/FR/{year}/{month}`
- **Example**: `https://www.govinfo.gov/bulkdata/FR/2024/01`

#### Electronic Code of Federal Regulations (ECFR)
- **URL**: `https://www.govinfo.gov/bulkdata/ECFR`

#### U.S. Code
- **URL**: `https://www.govinfo.gov/bulkdata/USCODE`

## Best Practices

### Rate Limiting Strategy
1. Track requests per hour (5000 for Congress API)
2. Implement request queue with rate limiter
3. Use exponential backoff on rate limit errors
4. Monitor `X-RateLimit-*` headers

### Pagination Strategy
1. Start with `offset=0`
2. Use maximum page size (250 for Congress, 1000 for GovInfo)
3. Track last successful offset
4. Continue until response contains fewer results than page size

### Deduplication Strategy
1. Use package IDs or unique identifiers as keys
2. Store ingested package metadata in database
3. Check existence before downloading
4. Track last modified dates for updates

### Parallel Processing Strategy
1. Divide work by collection or date ranges
2. Each worker maintains its own offset tracker
3. Central coordination to prevent overlap
4. Worker pool size based on rate limits (e.g., 10-20 workers for 5000 req/hr)

### Error Handling
1. Retry on network errors (exponential backoff)
2. Handle 429 (rate limit) by waiting for reset
3. Handle 404 (not found) by skipping
4. Log all errors with context for debugging
