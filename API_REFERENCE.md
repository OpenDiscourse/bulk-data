# API Endpoint Reference

This document provides a comprehensive breakdown of all API endpoints available through api.congress.gov and govinfo.gov.

## Table of Contents

- [Congress.gov API Endpoints](#congressgov-api-endpoints)
- [GovInfo.gov API Endpoints](#govinfogov-api-endpoints)
- [GovInfo.gov Bulk Data Endpoints](#govinfogov-bulk-data-endpoints)
- [Rate Limits and Best Practices](#rate-limits-and-best-practices)

---

## Congress.gov API Endpoints

**Base URL:** `https://api.congress.gov/v3`  
**Authentication:** API key required (`api_key` parameter)  
**Rate Limit:** 5,000 requests per hour  
**Format:** JSON or XML (specify with `format` parameter)

### Bills

#### List Bills
- **Endpoint:** `/bill`
- **Method:** GET
- **Parameters:**
  - `offset` (number): Pagination offset
  - `limit` (number): Results per page (max 250)
  - `format` (string): json or xml

#### List Bills by Congress
- **Endpoint:** `/bill/{congress}`
- **Example:** `/bill/118`
- **Parameters:** Same as List Bills

#### List Bills by Type
- **Endpoint:** `/bill/{congress}/{billType}`
- **Example:** `/bill/118/hr`
- **Bill Types:**
  - `hr` - House Bill
  - `s` - Senate Bill
  - `hjres` - House Joint Resolution
  - `sjres` - Senate Joint Resolution
  - `hconres` - House Concurrent Resolution
  - `sconres` - Senate Concurrent Resolution
  - `hres` - House Simple Resolution
  - `sres` - Senate Simple Resolution

#### Get Specific Bill
- **Endpoint:** `/bill/{congress}/{billType}/{billNumber}`
- **Example:** `/bill/118/hr/1`

#### Bill Sub-Resources
- `/bill/{congress}/{billType}/{billNumber}/actions` - Bill actions
- `/bill/{congress}/{billType}/{billNumber}/amendments` - Amendments to bill
- `/bill/{congress}/{billType}/{billNumber}/committees` - Committee referrals
- `/bill/{congress}/{billType}/{billNumber}/cosponsors` - Bill cosponsors
- `/bill/{congress}/{billType}/{billNumber}/relatedbills` - Related bills
- `/bill/{congress}/{billType}/{billNumber}/subjects` - Subject terms
- `/bill/{congress}/{billType}/{billNumber}/summaries` - Bill summaries
- `/bill/{congress}/{billType}/{billNumber}/text` - Bill text versions
- `/bill/{congress}/{billType}/{billNumber}/titles` - Bill titles

### Amendments

#### List Amendments
- **Endpoint:** `/amendment`
- **Parameters:** offset, limit, format

#### List Amendments by Congress
- **Endpoint:** `/amendment/{congress}`
- **Example:** `/amendment/118`

#### List Amendments by Type
- **Endpoint:** `/amendment/{congress}/{amendmentType}`
- **Amendment Types:**
  - `hamdt` - House Amendment
  - `samdt` - Senate Amendment

#### Get Specific Amendment
- **Endpoint:** `/amendment/{congress}/{amendmentType}/{amendmentNumber}`

#### Amendment Sub-Resources
- `/amendment/{congress}/{amendmentType}/{amendmentNumber}/actions`
- `/amendment/{congress}/{amendmentType}/{amendmentNumber}/cosponsors`
- `/amendment/{congress}/{amendmentType}/{amendmentNumber}/text`

### Laws

#### List Laws
- **Endpoint:** `/law`

#### List Laws by Congress
- **Endpoint:** `/law/{congress}`

#### List Laws by Type
- **Endpoint:** `/law/{congress}/{lawType}`
- **Law Types:**
  - `pub` - Public Law
  - `priv` - Private Law

#### Get Specific Law
- **Endpoint:** `/law/{congress}/{lawType}/{lawNumber}`

### Committees

#### List All Committees
- **Endpoint:** `/committee`

#### List Committees by Chamber
- **Endpoint:** `/committee/{chamber}`
- **Chambers:**
  - `house` - House of Representatives
  - `senate` - Senate
  - `joint` - Joint Committees

#### Get Specific Committee
- **Endpoint:** `/committee/{chamber}/{committeeCode}`

#### Committee Sub-Resources
- `/committee/{chamber}/{committeeCode}/bills` - Bills referred
- `/committee/{chamber}/{committeeCode}/reports` - Committee reports
- `/committee/{chamber}/{committeeCode}/nominations` - Nominations

### Members

#### List All Members
- **Endpoint:** `/member`

#### List Members by Congress
- **Endpoint:** `/member/congress/{congress}`

#### Get Specific Member
- **Endpoint:** `/member/{bioguideId}`

#### Member Sub-Resources
- `/member/{bioguideId}/sponsored-legislation` - Sponsored bills
- `/member/{bioguideId}/cosponsored-legislation` - Cosponsored bills

### Nominations

#### List Nominations
- **Endpoint:** `/nomination`

#### List Nominations by Congress
- **Endpoint:** `/nomination/{congress}`

#### Get Specific Nomination
- **Endpoint:** `/nomination/{congress}/{nominationNumber}`

### Treaties

#### List Treaties
- **Endpoint:** `/treaty`

#### List Treaties by Congress
- **Endpoint:** `/treaty/{congress}`

#### Get Specific Treaty
- **Endpoint:** `/treaty/{congress}/{treatyNumber}`

### Congressional Record

#### List Daily Congressional Record
- **Endpoint:** `/congressional-record`

### House Communications

#### List House Communications
- **Endpoint:** `/house-communication`

### Senate Communications

#### List Senate Communications
- **Endpoint:** `/senate-communication`

### Hearings

#### List Committee Hearings
- **Endpoint:** `/hearing`

### Committee Reports

#### List Committee Reports
- **Endpoint:** `/committee-report`

### Committee Prints

#### List Committee Prints
- **Endpoint:** `/committee-print`

### Committee Meetings

#### List Committee Meetings
- **Endpoint:** `/committee-meeting`

---

## GovInfo.gov API Endpoints

**Base URL:** `https://api.govinfo.gov`  
**Authentication:** API key required (`api_key` parameter)  
**Rate Limit:** 1,000 requests per hour  
**Format:** JSON (default)

### Collections

#### List All Collections
- **Endpoint:** `/collections`
- **Method:** GET
- **Parameters:**
  - `offset` (number): Pagination offset
  - `pageSize` (number): Results per page (max 100)

#### Get Collection Details
- **Endpoint:** `/collections/{collectionCode}`
- **Example:** `/collections/BILLS`

**Available Collections:**
- `BILLS` - Congressional Bills
- `BILLSTATUS` - Bill Status
- `BUDGET` - Budget Documents
- `CCAL` - Congressional Calendars
- `CDOC` - Congressional Documents
- `CFR` - Code of Federal Regulations
- `CHRG` - Congressional Hearings
- `COMPS` - Compiled Legislative Histories
- `CREC` - Congressional Record
- `CZIC` - Coastal Zone Information Center
- `ECFR` - Electronic Code of Federal Regulations
- `ECONI` - Economic Indicators
- `ERP` - Economic Report of the President
- `FR` - Federal Register
- `GAOREPORTS` - GAO Reports
- `GOVMAN` - Government Manual
- `GPO` - Additional GPO Publications
- `HJOURNAL` - House Journal
- `HMAN` - House Manual
- `HOB` - History of Bills
- `LSA` - List of CFR Sections Affected
- `PLAW` - Public Laws
- `PPP` - Public Papers of the Presidents
- `SERIALSET` - Serial Set
- `SJOURNAL` - Senate Journal
- `SMAN` - Senate Manual
- `STATUTE` - Statutes at Large
- `SUPREME_COURT` - Supreme Court Decisions
- `USCOURTS` - Courts Opinions
- `USCODE` - United States Code

### Packages

#### Get Package Summary
- **Endpoint:** `/packages/{packageId}/summary`
- **Example:** `/packages/BILLS-118hr1ih/summary`

#### Get Package Granules
- **Endpoint:** `/packages/{packageId}/granules`
- **Parameters:**
  - `offset` (number)
  - `pageSize` (number, max 100)

#### Get Package Siblings
- **Endpoint:** `/packages/{packageId}/siblings`

### Published Documents

#### List Published Documents by Date
- **Endpoint:** `/published/{dateIssuedStartDate}`
- **Example:** `/published/2024-01-01`
- **Parameters:**
  - `dateIssuedEndDate` (string): End date (YYYY-MM-DD)
  - `collection` (string): Filter by collection
  - `offset` (number)
  - `pageSize` (number, max 100)
  - `docClass` (string): Filter by document class

### Search

#### Search Packages
- **Endpoint:** `/search`
- **Method:** POST (also supports GET for simple queries)
- **Body:**
```json
{
  "query": "search terms",
  "pageSize": 100,
  "offsetMark": "*",
  "collection": "BILLS",
  "yearIssued": "2024",
  "docClass": "hr"
}
```

**Search Operators:**
- AND, OR, NOT
- Phrase search: "exact phrase"
- Wildcard: * (matches any characters)
- Field-specific: title:text, collection:BILLS

### Related Documents

#### Get Related Documents
- **Endpoint:** `/related/{accessId}`
- **Example:** `/related/GPO-BILLS-118hr1ih`

---

## GovInfo.gov Bulk Data Endpoints

**Base URL:** `https://www.govinfo.gov/bulkdata`  
**Authentication:** None required for bulk data listings  
**Format:** XML (default) or JSON

### Bulk Data Structure

Bulk data is organized hierarchically:
```
/bulkdata/{collection}/{congress?}/{session?}/{type?}
```

### Getting Listings

#### JSON Format
- **Pattern:** `/bulkdata/json/{collection}/...`
- **Example:** `https://www.govinfo.gov/bulkdata/json/BILLS/118/1/hr`
- **Headers:** `Accept: application/json`

#### XML Format
- **Pattern:** `/bulkdata/xml/{collection}/...`
- **Example:** `https://www.govinfo.gov/bulkdata/xml/BILLS/118/1/hr`
- **Headers:** `Accept: application/xml`

### Common Collections

#### Bills (BILLS)
- **Structure:** `/bulkdata/BILLS/{congress}/{session}/{billType}`
- **Example:** `/bulkdata/json/BILLS/118/1/hr`
- **Contains:** ZIP files with XML bill text

#### Bill Status (BILLSTATUS)
- **Structure:** `/bulkdata/BILLSTATUS/{congress}/{billType}`
- **Example:** `/bulkdata/json/BILLSTATUS/118/hr`
- **Contains:** XML files with bill status and metadata

#### Code of Federal Regulations (CFR)
- **Structure:** `/bulkdata/CFR/{year}/title-{title}`
- **Example:** `/bulkdata/json/CFR/2024/title-1`
- **Contains:** XML files for CFR titles

#### Electronic CFR (ECFR)
- **Structure:** `/bulkdata/ECFR/title-{title}`
- **Example:** `/bulkdata/json/ECFR/title-1`
- **Contains:** Current ECFR XML

#### Federal Register (FR)
- **Structure:** `/bulkdata/FR/{year}/{month}`
- **Example:** `/bulkdata/json/FR/2024/01`
- **Contains:** Daily Federal Register issues

#### Public Laws (PLAW)
- **Structure:** `/bulkdata/PLAW/{congress}/public`
- **Example:** `/bulkdata/json/PLAW/118/public`
- **Contains:** Enacted public laws

#### Statutes at Large (STATUTE)
- **Structure:** `/bulkdata/STATUTE/{statute}`
- **Example:** `/bulkdata/json/STATUTE/138`

#### US Code (USCODE)
- **Structure:** `/bulkdata/USCODE/title-{title}`
- **Example:** `/bulkdata/json/USCODE/title-1`

---

## Rate Limits and Best Practices

### Congress.gov API Rate Limits

- **Limit:** 5,000 requests per hour per API key
- **Headers:**
  - `X-Ratelimit-Limit`: Total allowed requests
  - `X-Ratelimit-Remaining`: Remaining requests in current hour
- **Demo Key:** 30 requests/hour, 50 requests/day (for testing only)

### GovInfo.gov API Rate Limits

- **Limit:** 1,000 requests per hour per API key
- **Headers:**
  - `X-Ratelimit-Limit`: Total allowed requests
  - `X-Ratelimit-Remaining`: Remaining requests
- **Demo Key:** 30 requests/hour, 50 requests/day

### Best Practices

1. **Use Maximum Page Size**
   - Congress.gov: 250 results per page
   - GovInfo.gov: 100 results per page

2. **Implement Rate Limiting**
   - Track requests per hour
   - Implement exponential backoff for errors
   - Monitor rate limit headers

3. **Use Pagination Efficiently**
   - Always use offset parameter for large datasets
   - Track `hasMore` or `nextPage` indicators
   - Process pages sequentially or with controlled parallelism

4. **Cache Responses**
   - Store ingested data locally
   - Use checksums to detect changes
   - Avoid re-fetching unchanged data

5. **Parallel Processing**
   - Limit concurrent requests (4-8 workers recommended)
   - Distribute requests across time to stay under rate limit
   - Use worker pools for better resource management

6. **Error Handling**
   - Handle 429 (Too Many Requests) gracefully
   - Implement retry logic with backoff
   - Log errors for debugging

7. **Accept Headers**
   - Always set appropriate `Accept` headers
   - Use `Accept: application/json` for JSON responses
   - Use `Accept: application/xml` for XML responses

8. **Bulk Data Access**
   - For large-scale ingestion, prefer bulk data endpoints
   - Bulk data doesn't count against API rate limits
   - Use bulk data for historical data, API for current data

### Request Pacing Example

For 5000 requests/hour limit:
- 5000 requests / 3600 seconds = ~1.39 requests/second
- Safe rate: 1 request per second
- With 4 workers: 1 request per 4 seconds per worker

For 1000 requests/hour limit:
- 1000 requests / 3600 seconds = ~0.28 requests/second
- Safe rate: 1 request per 4 seconds
- With 4 workers: 1 request per 16 seconds per worker

---

## Additional Resources

### Official Documentation

- **Congress.gov API:** https://api.congress.gov/
- **Congress.gov API GitHub:** https://github.com/LibraryOfCongress/api.congress.gov
- **GovInfo API:** https://api.govinfo.gov/docs/
- **GovInfo GitHub:** https://github.com/usgpo/api
- **Bulk Data Guide:** https://github.com/usgpo/bulk-data

### Support

- **Congress.gov Issues:** https://github.com/LibraryOfCongress/api.congress.gov/issues
- **GovInfo Issues:** https://github.com/usgpo/api/issues
- **API Key Registration:** https://api.data.gov/signup/
