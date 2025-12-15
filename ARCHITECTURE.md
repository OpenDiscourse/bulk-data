# Project Architecture

## Overview

This MCP (Model Context Protocol) server provides systematic ingestion of bulk data from api.congress.gov and govinfo.gov APIs. It implements comprehensive rate limiting, deduplication tracking, and parallel processing capabilities.

## System Components

### 1. Core Infrastructure

#### MCP Server (`src/index.ts`)
- Main entry point implementing MCP protocol
- Handles tool registration and execution
- Manages server lifecycle and cleanup
- Uses stdio transport for communication

#### Configuration (`src/utils/config.ts`)
- Environment-based configuration loading
- API key management
- Rate limit configuration
- Worker pool settings
- Database path configuration

### 2. Rate Limiting

#### Token Bucket Algorithm (`src/utils/rate-limiter.ts`)
- Implements token bucket rate limiting
- Continuous token refill based on configured rate
- Automatic request throttling
- Real-time token tracking

**Key Features:**
- Congress.gov: 5,000 requests/hour
- GovInfo.gov: 1,000 requests/hour
- Prevents API rate limit violations
- Smooth request distribution

### 3. Data Tracking

#### Ingestion Tracker (`src/utils/ingestion-tracker.ts`)
- SQLite-based persistence
- SHA-256 checksumming for deduplication
- Indexed queries for performance
- Statistics and reporting

**Database Schema:**
```sql
CREATE TABLE ingestion_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  endpoint TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  ingested_at TEXT NOT NULL,
  checksum TEXT NOT NULL,
  metadata TEXT,
  UNIQUE(endpoint, resource_id)
);
```

**Indexes:**
- `idx_endpoint`: Fast endpoint filtering
- `idx_resource_id`: Quick resource lookup
- `idx_checksum`: Deduplication checks
- `idx_ingested_at`: Temporal queries

### 4. Parallel Processing

#### Worker Pool (`src/utils/worker-pool.ts`)
- Based on p-queue for task management
- Configurable concurrency
- Priority-based task execution
- Real-time statistics

**Features:**
- Configurable worker count (default: 4)
- Task prioritization
- Active task tracking
- Queue management

### 5. API Clients

#### Congress.gov Client (`src/utils/congress-client.ts`)
- RESTful API wrapper
- Automatic pagination handling
- Response parsing and normalization
- Rate limit integration

**Endpoints:**
- Bills (all types)
- Amendments
- Laws
- Committees
- Members
- Nominations
- Treaties

#### GovInfo.gov API Client (`src/utils/govinfo-client.ts`)
- API wrapper for GovInfo services
- Collection management
- Package operations
- Search functionality
- Published document queries

#### Bulk Data Client (`src/utils/govinfo-client.ts`)
- Direct bulk data access
- XML/JSON format support
- Collection browsing
- File download utilities

### 6. MCP Tools

#### Congress Tools (`src/tools/congress-tools.ts`)
- `congress_list_bills`: List bills with pagination
- `congress_get_bill`: Get specific bill details
- `congress_bulk_ingest_bills`: Bulk ingest with workers
- `congress_list_amendments`: List amendments
- `congress_list_laws`: List enacted laws
- `congress_list_committees`: List committees
- `congress_list_members`: List members

#### GovInfo Tools (`src/tools/govinfo-tools.ts`)
- `govinfo_list_collections`: List available collections
- `govinfo_get_package`: Get package details
- `govinfo_list_published`: List by publication date
- `govinfo_search_packages`: Search functionality
- `govinfo_bulk_data_collections`: List bulk collections
- `govinfo_bulk_data_listing`: Get bulk data files
- `govinfo_bulk_ingest_collection`: Bulk ingest with workers
- `govinfo_get_ingestion_stats`: Statistics reporting

## Data Flow

### 1. Request Flow

```
Client Request
    ↓
MCP Server (index.ts)
    ↓
Tool Handler (congress-tools.ts / govinfo-tools.ts)
    ↓
Rate Limiter Check (rate-limiter.ts)
    ↓
API Client (congress-client.ts / govinfo-client.ts)
    ↓
External API
    ↓
Response Processing
    ↓
Ingestion Tracking (if enabled)
    ↓
Client Response
```

### 2. Bulk Ingestion Flow

```
Bulk Ingest Request
    ↓
Tool Handler
    ↓
Pagination Loop
    ↓
Worker Pool Task Creation
    ↓
Parallel Execution (N workers)
    ├─ Worker 1: Rate Limit → API Call → Track
    ├─ Worker 2: Rate Limit → API Call → Track
    ├─ Worker 3: Rate Limit → API Call → Track
    └─ Worker N: Rate Limit → API Call → Track
    ↓
Aggregate Results
    ↓
Statistics Response
```

### 3. Deduplication Flow

```
Resource Data
    ↓
Generate SHA-256 Checksum
    ↓
Query Database (endpoint + resource_id + checksum)
    ↓
    ├─ Match Found → Skip (return 'skipped')
    └─ No Match → Insert Record (return 'ingested')
```

## Performance Characteristics

### Rate Limiting
- **Congress.gov**: ~1.39 requests/second max
- **GovInfo.gov**: ~0.28 requests/second max
- Token refill is continuous (not periodic)
- Requests automatically throttled when bucket depletes

### Worker Pool
- Default: 4 concurrent workers
- Configurable up to system limits
- Tasks distributed across workers
- Automatic load balancing

### Database
- Indexed for fast lookups
- Unique constraint prevents duplicates
- Supports concurrent reads
- Write operations serialized

## Scalability Considerations

### Horizontal Scaling
- Multiple server instances can share database
- Rate limiters are per-instance
- Distribute load across multiple API keys
- Worker count adjustable per instance

### Vertical Scaling
- Increase worker count for more parallelism
- Database can handle millions of records
- Memory usage scales with worker count
- CPU usage scales with concurrent tasks

## Security

### API Key Management
- Keys stored in environment variables
- Never logged or exposed
- Separate keys for each API
- Support for demo keys (testing only)

### Data Validation
- Zod schema validation for all inputs
- Type-safe TypeScript implementation
- SQL injection prevention (parameterized queries)
- Checksum verification for data integrity

## Error Handling

### API Errors
- 429 (Rate Limit): Automatic throttling
- 404 (Not Found): Graceful skip
- 401 (Unauthorized): Configuration error
- 500 (Server Error): Retry logic recommended

### Application Errors
- Database errors: Transaction rollback
- Worker errors: Task isolation
- Network errors: Timeout and retry
- Validation errors: Clear error messages

## Monitoring and Observability

### Real-time Metrics
- Rate limiter: Remaining tokens
- Worker pool: Active/pending/queued counts
- Ingestion: Total/skipped/errors

### Historical Data
- Ingestion timestamp tracking
- Resource type breakdown
- Endpoint-specific statistics
- Temporal analysis support

## Extension Points

### Adding New Endpoints
1. Add method to appropriate client
2. Create tool in tool file
3. Register in main server
4. Update documentation

### Adding New APIs
1. Create new client class
2. Implement rate limiter
3. Create tool definitions
4. Register tools in server

### Custom Processing
- Extend ingestion tracker for custom fields
- Add post-processing hooks
- Implement custom deduplication logic
- Add transformation pipelines

## Testing Strategy

### Unit Tests
- Rate limiter validation
- Ingestion tracker operations
- Worker pool management
- Configuration loading

### Integration Tests
- End-to-end API calls
- Database operations
- Multi-worker scenarios
- Error handling

### Performance Tests
- Rate limiting accuracy
- Worker pool throughput
- Database query performance
- Memory usage profiling

## Deployment

### Requirements
- Node.js 18+
- SQLite3
- Network access to APIs
- Valid API keys

### Environment Setup
```bash
export CONGRESS_API_KEY=xxx
export GOVINFO_API_KEY=xxx
export MAX_WORKERS=4
```

### Production Considerations
- Monitor rate limit usage
- Database backup strategy
- Log aggregation
- Error alerting
- Health checks

## Future Enhancements

### Potential Features
1. **Incremental Updates**: Track last sync, fetch only new data
2. **Resume Capability**: Continue interrupted bulk ingestions
3. **Export Formats**: JSON, CSV, XML export
4. **Webhook Support**: Real-time notifications
5. **Advanced Filtering**: Complex query capabilities
6. **Caching Layer**: Redis for hot data
7. **Metrics Dashboard**: Real-time visualization
8. **Multi-tenancy**: Support multiple users/API keys
9. **Compression**: Reduce storage requirements
10. **Batch Processing**: Optimize database writes

### Performance Optimizations
1. **Bulk Inserts**: Batch database operations
2. **Connection Pooling**: Database connection reuse
3. **Request Batching**: Combine API requests
4. **Lazy Loading**: On-demand data fetching
5. **Smart Caching**: Reduce redundant API calls

## Maintenance

### Regular Tasks
- Monitor API rate limit usage
- Review ingestion statistics
- Database optimization (VACUUM)
- Update API client for new endpoints
- Dependency updates

### Troubleshooting
- Check API key validity
- Verify rate limit headers
- Review database indexes
- Monitor worker queue depth
- Check disk space for database
