# API Endpoints Documentation

This document provides a comprehensive breakdown of the api.congress.gov and govinfo.gov APIs, including all endpoints, parameters, rate limits, and pagination details.

## Congress.gov API (api.congress.gov)

### Base URL
`https://api.congress.gov/v3`

### Authentication
- Requires API key from api.data.gov
- Include in query parameter: `api_key=YOUR_KEY`
- Or in header: `X-Api-Key: YOUR_KEY`

### Rate Limits
- **5,000 requests per hour** per API key
- Tracked via headers:
  - `X-Ratelimit-Limit`: Total requests allowed per hour
  - `X-Ratelimit-Remaining`: Requests remaining in current period

### Pagination
- **Offset-based pagination**
- Parameters:
  - `offset`: Starting position (default: 0)
  - `limit`: Number of results (default: 20, max: 250)
- Response includes pagination metadata

### Endpoints

#### 1. Bills (`/bill`)
Get list of bills from Congress.

**GET** `/v3/bill`

Parameters:
- `offset` (number): Pagination offset
- `limit` (number): Results per page (max 250)
- `fromDateTime` (string): Filter bills updated after this datetime
- `toDateTime` (string): Filter bills updated before this datetime
- `sort` (string): Sort order (updateDate+asc, updateDate+desc)
- `format` (string): Response format (json, xml)

**GET** `/v3/bill/{congress}`
- `congress` (number): Congress number (e.g., 118)

**GET** `/v3/bill/{congress}/{billType}`
- `congress` (number): Congress number
- `billType` (string): Bill type (hr, s, hjres, sjres, hconres, sconres, hres, sres)

**GET** `/v3/bill/{congress}/{billType}/{billNumber}`
- Get specific bill details

Related endpoints for specific bill:
- `/v3/bill/{congress}/{billType}/{billNumber}/actions`
- `/v3/bill/{congress}/{billType}/{billNumber}/amendments`
- `/v3/bill/{congress}/{billType}/{billNumber}/committees`
- `/v3/bill/{congress}/{billType}/{billNumber}/cosponsors`
- `/v3/bill/{congress}/{billType}/{billNumber}/relatedbills`
- `/v3/bill/{congress}/{billType}/{billNumber}/subjects`
- `/v3/bill/{congress}/{billType}/{billNumber}/summaries`
- `/v3/bill/{congress}/{billType}/{billNumber}/text`
- `/v3/bill/{congress}/{billType}/{billNumber}/titles`

#### 2. Amendments (`/amendment`)
Get congressional amendments.

**GET** `/v3/amendment`
- Same pagination parameters as bills

**GET** `/v3/amendment/{congress}`
**GET** `/v3/amendment/{congress}/{amendmentType}`
**GET** `/v3/amendment/{congress}/{amendmentType}/{amendmentNumber}`

Amendment types: hamdt, samdt

#### 3. Members (`/member`)
Get congressional members information.

**GET** `/v3/member`
**GET** `/v3/member/{bioguideId}`
- `bioguideId`: Unique member identifier

Related endpoints:
- `/v3/member/{bioguideId}/sponsored-legislation`
- `/v3/member/{bioguideId}/cosponsored-legislation`

#### 4. Committees (`/committee`)
Get committee information.

**GET** `/v3/committee`
**GET** `/v3/committee/{congress}`
**GET** `/v3/committee/{congress}/{chamber}`
- `chamber`: house, senate, joint

**GET** `/v3/committee/{chamber}/{committeeCode}`

Related endpoints:
- `/v3/committee/{chamber}/{committeeCode}/bills`
- `/v3/committee/{chamber}/{committeeCode}/reports`
- `/v3/committee/{chamber}/{committeeCode}/nominations`

#### 5. Nominations (`/nomination`)
Get presidential nominations.

**GET** `/v3/nomination`
**GET** `/v3/nomination/{congress}`
**GET** `/v3/nomination/{congress}/{nominationNumber}`

#### 6. Treaties (`/treaty`)
Get treaty information.

**GET** `/v3/treaty`
**GET** `/v3/treaty/{congress}`
**GET** `/v3/treaty/{congress}/{treatyNumber}`

#### 7. Congressional Record (`/congressional-record`)
Get Congressional Record data.

**GET** `/v3/congressional-record`

#### 8. House Communications (`/house-communication`)
**GET** `/v3/house-communication`
**GET** `/v3/house-communication/{congress}`

#### 9. Senate Communications (`/senate-communication`)
**GET** `/v3/senate-communication`
**GET** `/v3/senate-communication/{congress}`

#### 10. House Requirements (`/house-requirement`)
**GET** `/v3/house-requirement`
**GET** `/v3/house-requirement/{congress}`

#### 11. Summaries (`/summaries`)
Get bill summaries.

**GET** `/v3/summaries`
**GET** `/v3/summaries/{congress}`

#### 12. Congress (`/congress`)
Get information about specific Congress sessions.

**GET** `/v3/congress`
**GET** `/v3/congress/{congress}`
**GET** `/v3/congress/current`

---

## GovInfo.gov API (api.govinfo.gov)

### Base URL
`https://api.govinfo.gov`

### Authentication
- Requires API key from api.data.gov
- Include in header: `X-Api-Key: YOUR_KEY`

### Rate Limits
- **5,000 requests per hour** per API key
- Same api.data.gov infrastructure as Congress.gov

### Pagination
- **Cursor-based pagination** using `offsetMark`
- Parameters:
  - `offsetMark` (string): Pagination cursor (use "*" for first page)
  - `pageSize` (number): Results per page (default: 100)
- Response includes `nextPage` field with next offsetMark

### Endpoints

#### 1. Collections (`/collections`)
Get list of all available collections.

**GET** `/collections`

Returns collections like:
- BILLS - Congressional Bills
- PLAW - Public and Private Laws
- STATUTE - Statutes at Large
- CFR - Code of Federal Regulations
- ECFR - Electronic Code of Federal Regulations
- FR - Federal Register
- CREC - Congressional Record
- And many more...

**GET** `/collections/{collectionCode}`
Get packages within a specific collection.

Parameters:
- `offsetMark`: Pagination cursor
- `pageSize`: Results per page
- `startDate`: Filter by start date (YYYY-MM-DD)
- `endDate`: Filter by end date (YYYY-MM-DD)

#### 2. Packages (`/packages`)
Get package information.

**GET** `/packages/{packageId}/summary`
Get summary information for a package.

**GET** `/packages/{packageId}/granules`
Get granules (sub-elements) of a package.

Parameters:
- `offsetMark`: Pagination cursor
- `pageSize`: Results per page

**GET** `/packages/{packageId}/related`
Get related packages.

**GET** `/packages/{packageId}/versions`
Get different versions of a package.

#### 3. Published (`/published`)
Get content by publication date.

**GET** `/published/{dateIssuedStartDate}`
**GET** `/published/{dateIssuedStartDate}/{dateIssuedEndDate}`

Parameters:
- `collection`: Filter by collection code
- `offsetMark`: Pagination cursor
- `pageSize`: Results per page
- `modifiedSince`: Filter by modification date

#### 4. Search (`/search`)
Search for content across collections.

**POST** `/search`

Request body:
```json
{
  "query": "search terms",
  "pageSize": 100,
  "offsetMark": "*",
  "sorts": [
    {
      "field": "relevancy",
      "sortOrder": "DESC"
    }
  ],
  "historical": true,
  "resultLevel": "default"
}
```

Parameters:
- `query`: Search query string
- `collection`: Filter by collection
- `pageSize`: Results per page
- `offsetMark`: Pagination cursor
- `congress`: Filter by congress number
- `docClass`: Filter by document class
- `yearIssued`: Filter by year

#### 5. Related (`/related`)
Get related documents.

**GET** `/related/{packageId}`

---

## GovInfo Bulk Data Endpoints (govinfo.gov/bulkdata)

### Base URL
`https://www.govinfo.gov/bulkdata`

### Authentication
- No API key required for bulk data access
- Rate limiting still applies (use considerately)

### Format Support
Access via URL format:
- **JSON**: `https://www.govinfo.gov/bulkdata/json/{path}`
- **XML**: `https://www.govinfo.gov/bulkdata/xml/{path}`

### Important Headers
- `Accept: application/json` for JSON responses
- `Accept: application/xml` for XML responses
- Without proper Accept headers, may receive 406 error

### Collections

#### 1. Bills (BILLS)
Structure: `/BILLS/{congress}/{session}/{billType}`

Example:
- `/BILLS/118/1/hr` - House bills, 118th Congress, Session 1
- JSON: `https://www.govinfo.gov/bulkdata/json/BILLS/118/1/hr`
- XML: `https://www.govinfo.gov/bulkdata/xml/BILLS/118/1/hr`

Bill types:
- `hr` - House bills
- `s` - Senate bills
- `hjres` - House joint resolutions
- `sjres` - Senate joint resolutions
- `hconres` - House concurrent resolutions
- `sconres` - Senate concurrent resolutions
- `hres` - House simple resolutions
- `sres` - Senate simple resolutions

#### 2. Code of Federal Regulations (CFR)
Structure: `/CFR/{year}/title-{titleNumber}`

Example:
- `/CFR/2024/title-1`
- Covers all 50 titles of the CFR

#### 3. Electronic Code of Federal Regulations (ECFR)
Structure: `/ECFR/title-{titleNumber}`

Example:
- `/ECFR/title-1`
- Current, up-to-date version of CFR

#### 4. Federal Register (FR)
Structure: `/FR/{year}/{month}`

Example:
- `/FR/2024/12` - December 2024
- `/FR/2024/12/01` - Specific date

#### 5. Congressional Record (CREC)
Structure: `/CREC/{year}/{month}`

Example:
- `/CREC/2024/12`

#### 6. Public Laws (PLAW)
Structure: `/PLAW/{congress}/public`
- `/PLAW/{congress}/private`

#### 7. Statutes at Large (STATUTE)
Structure: `/STATUTE/{statute}`

### Other Collections Available via Bulk Data

- **BILLSTATUS** - Bill status XML
- **BILLSUM** - Bill summaries
- **CHRG** - Congressional hearings
- **COMPS** - Compiled legislative histories
- **CRPT** - Committee reports
- **GPO** - Government Printing Office style manual
- **HJOURNAL** - House Journal
- **SJOURNAL** - Senate Journal
- **USCOURTS** - U.S. Courts opinions

---

## Best Practices

### Rate Limiting Strategy

1. **Track requests locally**: Maintain counter per API
2. **Implement backoff**: When approaching limit, slow down
3. **Monitor headers**: Check `X-Ratelimit-Remaining`
4. **Reset awareness**: Track reset time, wait if needed
5. **Batch operations**: Group related requests

### Pagination Strategy

#### For Congress.gov (offset-based):
```javascript
let offset = 0;
const limit = 250; // Maximum
let hasMore = true;

while (hasMore) {
  const response = await fetch(`/bill?offset=${offset}&limit=${limit}`);
  const data = await response.json();
  
  // Process data
  
  offset += limit;
  hasMore = offset < data.pagination.count;
}
```

#### For GovInfo.gov (cursor-based):
```javascript
let offsetMark = "*";
const pageSize = 100;
let hasMore = true;

while (hasMore) {
  const response = await fetch(`/collections/BILLS?offsetMark=${offsetMark}&pageSize=${pageSize}`);
  const data = await response.json();
  
  // Process data
  
  offsetMark = data.nextPage;
  hasMore = !!offsetMark && offsetMark !== "*";
}
```

### Parallel Processing Guidelines

1. **Respect rate limits**: Distribute requests across time
2. **Worker count**: Start with 3-5 workers
3. **Priority queue**: Process critical data first
4. **Error handling**: Retry failed requests with backoff
5. **Progress tracking**: Monitor completion status
6. **Deduplication**: Check before re-fetching

### Data Organization

Recommended directory structure:
```
data/
├── congress/
│   ├── bills/
│   │   ├── 118/
│   │   └── 117/
│   ├── amendments/
│   └── members/
├── govinfo/
│   ├── BILLS/
│   ├── CFR/
│   ├── FR/
│   └── ECFR/
└── tracking/
    └── ingestion-records.json
```

---

## API Response Examples

### Congress.gov Bill Response
```json
{
  "bill": {
    "congress": 118,
    "type": "hr",
    "number": "1",
    "title": "...",
    "updateDate": "2024-12-10",
    "actions": {
      "count": 5,
      "url": "https://api.congress.gov/v3/bill/118/hr/1/actions"
    }
  },
  "pagination": {
    "count": 1000,
    "next": "https://api.congress.gov/v3/bill?offset=250&limit=250"
  }
}
```

### GovInfo Package Response
```json
{
  "count": 100,
  "offset": 0,
  "nextPage": "next-offset-mark-here",
  "packages": [
    {
      "packageId": "BILLS-118hr1ih",
      "lastModified": "2024-12-10T10:00:00Z",
      "title": "...",
      "download": {
        "txtLink": "...",
        "pdfLink": "...",
        "xmlLink": "..."
      }
    }
  ]
}
```

---

## Error Handling

### Common Error Codes

- **401 Unauthorized**: Invalid or missing API key
- **403 Forbidden**: Access denied
- **404 Not Found**: Resource doesn't exist
- **406 Not Acceptable**: Wrong Accept header (bulk data)
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily down

### Retry Strategy

```javascript
async function fetchWithRetry(url, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url);
      if (response.status === 429) {
        // Rate limited - wait and retry
        await sleep(60000); // Wait 1 minute
        continue;
      }
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(1000 * Math.pow(2, i)); // Exponential backoff
    }
  }
}
```

---

## Summary

This comprehensive documentation covers all major endpoints for both APIs. The MCP server implementation provides tools to access all these endpoints with proper rate limiting, pagination, and error handling built in.

Key takeaways:
1. **Both APIs use 5,000 req/hour limit**
2. **Congress.gov uses offset pagination**
3. **GovInfo uses cursor pagination**
4. **Bulk data requires Accept headers**
5. **API keys are required for most endpoints**
6. **Proper tracking prevents duplicate ingestion**
