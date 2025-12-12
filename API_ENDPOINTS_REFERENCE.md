# API Endpoints Reference

Complete breakdown of all API endpoints and bulk data collections available from api.congress.gov and govinfo.gov.

## Table of Contents
1. [api.congress.gov Endpoints](#apicongressgov-endpoints)
2. [api.govinfo.gov Endpoints](#apigovinfogov-endpoints)
3. [govinfo.gov Bulk Data Collections](#govinfogov-bulk-data-collections)
4. [Rate Limits and Best Practices](#rate-limits-and-best-practices)

---

## api.congress.gov Endpoints

**Base URL**: `https://api.congress.gov/v3`  
**Authentication**: API key required (from api.data.gov)  
**Rate Limit**: 5,000 requests per hour  
**Pagination**: Up to 250 results per request, uses offset parameter

### Bills
- **Endpoint**: `/bill` or `/bill/{congress}` or `/bill/{congress}/{billType}`
- **Description**: Retrieve bills from Congress
- **Parameters**:
  - `congress` (optional): Congress number (e.g., 118)
  - `billType` (optional): Type of bill (hr, s, hjres, sjres, hconres, sconres, hres, sres)
  - `offset`: Pagination offset (default: 0)
  - `limit`: Items per page (max: 250, default: 20)
- **Sub-endpoints**:
  - `/bill/{congress}/{billType}/{billNumber}`: Specific bill details
  - `/bill/{congress}/{billType}/{billNumber}/actions`: Bill actions
  - `/bill/{congress}/{billType}/{billNumber}/amendments`: Bill amendments
  - `/bill/{congress}/{billType}/{billNumber}/committees`: Related committees
  - `/bill/{congress}/{billType}/{billNumber}/cosponsors`: Bill cosponsors
  - `/bill/{congress}/{billType}/{billNumber}/relatedbills`: Related bills
  - `/bill/{congress}/{billType}/{billNumber}/subjects`: Legislative subjects
  - `/bill/{congress}/{billType}/{billNumber}/summaries`: Bill summaries
  - `/bill/{congress}/{billType}/{billNumber}/text`: Bill text versions
  - `/bill/{congress}/{billType}/{billNumber}/titles`: Bill titles

### Amendments
- **Endpoint**: `/amendment` or `/amendment/{congress}`
- **Description**: Congressional amendments
- **Parameters**:
  - `congress` (optional): Congress number
  - `offset`, `limit`: Pagination
- **Sub-endpoints**:
  - `/amendment/{congress}/{amendmentType}/{amendmentNumber}`: Specific amendment
  - `/amendment/{congress}/{amendmentType}/{amendmentNumber}/actions`: Amendment actions
  - `/amendment/{congress}/{amendmentType}/{amendmentNumber}/cosponsors`: Amendment cosponsors
  - `/amendment/{congress}/{amendmentType}/{amendmentNumber}/amendments`: Amendments to this amendment
  - `/amendment/{congress}/{amendmentType}/{amendmentNumber}/text`: Amendment text

### Laws
- **Endpoint**: `/law` or `/law/{congress}` or `/law/{congress}/{lawType}`
- **Description**: Public and private laws
- **Parameters**:
  - `congress` (optional): Congress number
  - `lawType` (optional): pub (public) or priv (private)
  - `offset`, `limit`: Pagination
- **Sub-endpoints**:
  - `/law/{congress}/{lawType}/{lawNumber}`: Specific law details

### Members
- **Endpoint**: `/member` or `/member/congress/{congress}`
- **Description**: Members of Congress
- **Parameters**:
  - `congress` (optional): Congress number
  - `offset`, `limit`: Pagination
- **Sub-endpoints**:
  - `/member/{bioguideId}`: Specific member details
  - `/member/{bioguideId}/sponsored-legislation`: Bills sponsored
  - `/member/{bioguideId}/cosponsored-legislation`: Bills cosponsored

### Committee Reports
- **Endpoint**: `/committee-report` or `/committee-report/{congress}`
- **Description**: Congressional committee reports
- **Parameters**:
  - `congress` (optional): Congress number
  - `offset`, `limit`: Pagination
- **Sub-endpoints**:
  - `/committee-report/{congress}/{reportType}/{reportNumber}`: Specific report
  - `/committee-report/{congress}/{reportType}/{reportNumber}/text`: Report text

### Congressional Record
- **Endpoint**: `/congressional-record` or `/congressional-record/{congress}`
- **Description**: Daily Congressional Record
- **Parameters**:
  - `congress` (optional): Congress number
  - `offset`, `limit`: Pagination
- **Sub-endpoints**:
  - `/congressional-record/{volume}/{issue}`: Specific issue
  - `/congressional-record/{volume}/{issue}/{section}`: Specific section

### Nominations
- **Endpoint**: `/nomination` or `/nomination/{congress}`
- **Description**: Presidential nominations
- **Parameters**:
  - `congress` (optional): Congress number
  - `offset`, `limit`: Pagination
- **Sub-endpoints**:
  - `/nomination/{congress}/{nominationNumber}`: Specific nomination
  - `/nomination/{congress}/{nominationNumber}/actions`: Nomination actions

### Committees
- **Endpoint**: `/committee` or `/committee/{congress}`
- **Description**: Congressional committees
- **Parameters**:
  - `congress` (optional): Congress number
  - `offset`, `limit`: Pagination
- **Sub-endpoints**:
  - `/committee/{chamber}/{committeeCode}`: Specific committee
  - `/committee/{chamber}/{committeeCode}/bills`: Committee bills
  - `/committee/{chamber}/{committeeCode}/reports`: Committee reports

---

## api.govinfo.gov Endpoints

**Base URL**: `https://api.govinfo.gov`  
**Authentication**: API key required (from api.data.gov)  
**Rate Limit**: 1,000 requests per hour  
**Pagination**: Up to 1,000 results per request, uses offset parameter

### Collections
- **Endpoint**: `/collections`
- **Description**: List all available collections
- **Parameters**: None (no pagination)
- **Response**: Array of collection metadata

### Collection by Date
- **Endpoint**: `/collections/{collectionCode}/{startDate}` or `/collections/{collectionCode}/{startDate}/{endDate}`
- **Description**: Get documents from a collection within a date range
- **Parameters**:
  - `collectionCode`: Collection identifier (e.g., BILLS, CFR, FR)
  - `startDate`: Start date (YYYY-MM-DD format)
  - `endDate` (optional): End date (YYYY-MM-DD format)
  - `offset`: Pagination offset
  - `pageSize`: Items per page (max: 1000)
- **Available Collections**:
  - BILLS, BILLSTATUS, CFR, ECFR, FR, CREC, PLAW, STATUTE, USCOURTS, PPP, and many more

### Packages
- **Endpoint**: `/packages/{packageId}/summary`
- **Description**: Get package metadata
- **Parameters**:
  - `packageId`: Unique package identifier
- **Sub-endpoints**:
  - `/packages/{packageId}/granules`: Package granules (sub-documents)
  - `/packages/{packageId}/related`: Related packages
  - `/packages/{packageId}/htm`: HTML content
  - `/packages/{packageId}/pdf`: PDF content
  - `/packages/{packageId}/xml`: XML content
  - `/packages/{packageId}/mods`: MODS metadata

### Published
- **Endpoint**: `/published/{dateIssuedStartDate}` or `/published/{dateIssuedStartDate}/{dateIssuedEndDate}`
- **Description**: Get documents by published date
- **Parameters**:
  - `dateIssuedStartDate`: Start date (YYYY-MM-DD)
  - `dateIssuedEndDate` (optional): End date
  - `offset`, `pageSize`: Pagination
  - `collection` (optional): Filter by collection
  - `docClass` (optional): Filter by document class

### Search
- **Endpoint**: `/search`
- **Description**: Full-text search across all collections
- **Parameters**:
  - `query`: Search query
  - `offset`, `pageSize`: Pagination
  - `collection` (optional): Filter by collection
  - `publishedDate` (optional): Filter by date
  - `governmentAuthor` (optional): Filter by author

---

## govinfo.gov Bulk Data Collections

**Base URL**: `https://www.govinfo.gov/bulkdata`  
**Authentication**: None required  
**Rate Limit**: ~1,000 requests per hour (same infrastructure as API)  
**Format**: XML and JSON listings available

### Available Collections

#### BILLS - Congressional Bills
- **Path**: `/bulkdata/BILLS/{congress}/{session}/{billType}`
- **Example**: `/bulkdata/BILLS/118/1/hr`
- **Format**: XML files
- **Structure**: Organized by congress, session, and bill type

#### BILLSTATUS - Bill Status
- **Path**: `/bulkdata/BILLSTATUS/{congress}/{billType}`
- **Example**: `/bulkdata/BILLSTATUS/118/hr`
- **Format**: XML files
- **Structure**: Status information for all bills

#### CFR - Code of Federal Regulations
- **Path**: `/bulkdata/CFR/{year}/title-{title}`
- **Example**: `/bulkdata/CFR/2024/title-1`
- **Format**: XML files
- **Structure**: Annual CFR organized by title

#### ECFR - Electronic Code of Federal Regulations
- **Path**: `/bulkdata/ECFR/title-{title}`
- **Example**: `/bulkdata/ECFR/title-1`
- **Format**: XML files
- **Structure**: Current CFR organized by title

#### FR - Federal Register
- **Path**: `/bulkdata/FR/{year}/{month}`
- **Example**: `/bulkdata/FR/2024/01`
- **Format**: XML files
- **Structure**: Daily Federal Register issues

#### CREC - Congressional Record
- **Path**: `/bulkdata/CREC/{year}/{month}`
- **Example**: `/bulkdata/CREC/2024/01`
- **Format**: XML files
- **Structure**: Daily Congressional Record

#### PLAW - Public and Private Laws
- **Path**: `/bulkdata/PLAW/{congress}/public` or `/bulkdata/PLAW/{congress}/private`
- **Example**: `/bulkdata/PLAW/118/public`
- **Format**: XML files
- **Structure**: Organized by congress and type

#### STATUTE - Statutes at Large
- **Path**: `/bulkdata/STATUTE/{volume}`
- **Example**: `/bulkdata/STATUTE/130`
- **Format**: XML files
- **Structure**: Organized by volume

#### USCOURTS - U.S. Courts Opinions
- **Path**: `/bulkdata/USCOURTS/{year}/{court}`
- **Example**: `/bulkdata/USCOURTS/2024/ca1`
- **Format**: XML files
- **Structure**: Organized by year and court

#### PPP - Public Papers of the Presidents
- **Path**: `/bulkdata/PPP/{year}`
- **Example**: `/bulkdata/PPP/2024`
- **Format**: XML files
- **Structure**: Organized by year

### Additional Collections
- **CHRG** - Committee Hearings
- **CPRT** - Committee Prints
- **CDOC** - Committee Documents
- **CZIC** - Printed Congressional Documents
- **GAOREPORTS** - GAO Reports
- **SERIALSET** - Serial Set
- **GOVMAN** - U.S. Government Manual
- **GOVPUB** - Government Publications
- **PCOMP** - Presidential Compilations

---

## Rate Limits and Best Practices

### api.congress.gov
- **Limit**: 5,000 requests per hour per API key
- **Calculation**: ~83 requests per minute
- **Best Practice**: 
  - Use batch operations when possible
  - Cache responses
  - Use pagination efficiently (max 250 items per request)
  - Monitor rate limit headers in responses

### api.govinfo.gov
- **Limit**: 1,000 requests per hour per API key
- **Calculation**: ~16 requests per minute
- **Best Practice**:
  - Prefer bulk data downloads for large datasets
  - Use date ranges to batch requests
  - Cache package metadata
  - Use pagination efficiently (max 1000 items per request)

### govinfo.gov/bulkdata
- **Limit**: Shares infrastructure with API (~1,000 req/hour)
- **Best Practice**:
  - Download directory listings first
  - Plan download strategy before starting
  - Use parallel downloads with rate limiting
  - Verify file integrity after download

### General Best Practices

1. **Respect Rate Limits**
   - Implement rate limiting in your client
   - Use exponential backoff on errors
   - Monitor throttling statistics

2. **Efficient Pagination**
   - Use maximum page size allowed
   - Track offset to resume on interruption
   - Process results in batches

3. **Data Deduplication**
   - Track downloaded/processed items
   - Use checksums or unique IDs
   - Skip already-processed items

4. **Parallel Processing**
   - Use worker pools for parallelism
   - Coordinate workers to respect rate limits
   - Implement retry logic

5. **Error Handling**
   - Retry transient errors (network, rate limits)
   - Log permanent errors (404, 403)
   - Implement circuit breakers

6. **Monitoring**
   - Track success/failure rates
   - Monitor rate limit usage
   - Log processing statistics

---

## Example API Calls

### Congress API - Get Bills from 118th Congress
```
GET https://api.congress.gov/v3/bill/118?api_key=YOUR_KEY&limit=250&offset=0
```

### GovInfo API - Get BILLS Collection from January 2024
```
GET https://api.govinfo.gov/collections/BILLS/2024-01-01?api_key=YOUR_KEY&pageSize=1000&offset=0
```

### Bulk Data - List Federal Register for January 2024
```
GET https://www.govinfo.gov/bulkdata/json/FR/2024/01
Accept: application/json
```

---

This reference provides a comprehensive overview of all available endpoints and how to use them effectively with proper rate limiting and pagination.
