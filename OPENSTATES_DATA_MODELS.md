# OpenStates Data Models Documentation

## Overview

This document describes the PostgreSQL database schema for storing OpenStates legislative data. The schema is designed to efficiently store and query data about jurisdictions, legislative sessions, bills, legislators, votes, and committees.

## Entity Relationship Diagram

```
Jurisdiction
    ├── LegislativeSession
    │   └── Bill
    │       ├── BillSponsorship → Person
    │       ├── BillVersion
    │       ├── BillDocument
    │       └── Vote
    │           └── VoteRecord → Person
    ├── Person
    └── Committee
```

## Tables and Fields

### Jurisdictions

Represents U.S. states, territories, and federal jurisdiction.

**Table:** `jurisdictions`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | String(100) | OpenStates jurisdiction ID (OCD format) | PRIMARY KEY |
| name | String(255) | Full jurisdiction name (e.g., "North Carolina") | NOT NULL |
| abbreviation | String(10) | Two-letter state code (e.g., "NC") | NOT NULL, UNIQUE |
| classification | String(50) | Type (state, territory, etc.) | |
| url | String(500) | Official government website | |
| created_at | DateTime | Record creation timestamp | NOT NULL |
| updated_at | DateTime | Record update timestamp | NOT NULL |

**Example:**
```json
{
  "id": "ocd-jurisdiction/country:us/state:nc/government",
  "name": "North Carolina",
  "abbreviation": "NC",
  "classification": "state",
  "url": "https://www.nc.gov"
}
```

**Indexes:**
- Primary key on `id`
- Unique index on `abbreviation`

---

### Legislative Sessions

Represents legislative sessions (regular, special, etc.).

**Table:** `legislative_sessions`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Auto-incrementing primary key | PRIMARY KEY |
| identifier | String(100) | Session identifier (e.g., "2023") | NOT NULL |
| name | String(255) | Full session name | NOT NULL |
| jurisdiction_id | String(100) | Parent jurisdiction | FOREIGN KEY → jurisdictions.id |
| start_date | DateTime | Session start date | |
| end_date | DateTime | Session end date | |
| classification | String(50) | Type (regular, special, etc.) | |
| created_at | DateTime | Record creation timestamp | NOT NULL |
| updated_at | DateTime | Record update timestamp | NOT NULL |

**Constraints:**
- Unique constraint on `(jurisdiction_id, identifier)`

**Indexes:**
- Primary key on `id`
- Index on `jurisdiction_id`
- Unique index on `(jurisdiction_id, identifier)`

---

### People (Legislators)

Represents legislators and other government officials.

**Table:** `people`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | String(100) | OpenStates person ID (OCD format) | PRIMARY KEY |
| name | String(255) | Full name | NOT NULL |
| given_name | String(100) | First name | |
| family_name | String(100) | Last name | |
| email | String(255) | Contact email | |
| jurisdiction_id | String(100) | Home jurisdiction | FOREIGN KEY → jurisdictions.id |
| party | String(100) | Political party affiliation | |
| current_role | String(255) | Current position/role | |
| image_url | String(500) | Profile photo URL | |
| extras | JSONB | Additional metadata | |
| sources | JSONB | Data sources | |
| created_at | DateTime | Record creation timestamp | NOT NULL |
| updated_at | DateTime | Record update timestamp | NOT NULL |

**Example:**
```json
{
  "id": "ocd-person/12345",
  "name": "Jane Smith",
  "party": "Democratic",
  "current_role": "North Carolina Senate - District 4",
  "email": "jane.smith@legislature.gov"
}
```

**Indexes:**
- Primary key on `id`
- Index on `jurisdiction_id`
- Index on `name`

---

### Bills

Represents legislative bills and resolutions.

**Table:** `bills`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | String(100) | OpenStates bill ID (OCD format) | PRIMARY KEY |
| identifier | String(100) | Bill number (e.g., "HB 475") | NOT NULL |
| title | Text | Bill title | NOT NULL |
| classification | String(50) | Bill type (bill, resolution, etc.) | NOT NULL |
| subject | JSONB | Array of subject areas | |
| abstracts | JSONB | Array of bill summaries | |
| jurisdiction_id | String(100) | Parent jurisdiction | FOREIGN KEY → jurisdictions.id |
| legislative_session_id | Integer | Parent session | FOREIGN KEY → legislative_sessions.id |
| from_organization | String(100) | Originating chamber | |
| actions | JSONB | Array of bill actions/history | |
| extras | JSONB | Additional metadata | |
| sources | JSONB | Data sources | |
| created_at | DateTime | Record creation timestamp | NOT NULL |
| updated_at | DateTime | Record update timestamp | NOT NULL |
| openstates_updated_at | DateTime | Last update from OpenStates | |

**Example:**
```json
{
  "id": "ocd-bill/12345",
  "identifier": "HB 475",
  "title": "An Act relating to education funding",
  "classification": "bill",
  "subject": ["education", "budget"],
  "from_organization": "lower"
}
```

**Indexes:**
- Primary key on `id`
- Index on `jurisdiction_id`
- Index on `legislative_session_id`
- Index on `identifier`
- Index on `openstates_updated_at` (for incremental updates)

---

### Bill Sponsorships

Links bills to their sponsors (legislators).

**Table:** `bill_sponsorships`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Auto-incrementing primary key | PRIMARY KEY |
| bill_id | String(100) | Parent bill | FOREIGN KEY → bills.id |
| person_id | String(100) | Sponsor (if linked) | FOREIGN KEY → people.id |
| classification | String(50) | Type (primary, cosponsor, etc.) | |
| name | String(255) | Sponsor name | NOT NULL |
| entity_type | String(50) | Type of entity (person, organization) | |
| primary | Boolean | Whether primary sponsor | DEFAULT FALSE |
| created_at | DateTime | Record creation timestamp | NOT NULL |

**Indexes:**
- Primary key on `id`
- Index on `bill_id`
- Index on `person_id`

---

### Bill Versions

Represents different versions of bill text.

**Table:** `bill_versions`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Auto-incrementing primary key | PRIMARY KEY |
| bill_id | String(100) | Parent bill | FOREIGN KEY → bills.id |
| note | String(500) | Version description | |
| date | DateTime | Version date | |
| links | JSONB | Array of URLs to bill text | |
| created_at | DateTime | Record creation timestamp | NOT NULL |

**Indexes:**
- Primary key on `id`
- Index on `bill_id`

---

### Bill Documents

Represents documents related to bills (reports, amendments, etc.).

**Table:** `bill_documents`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Auto-incrementing primary key | PRIMARY KEY |
| bill_id | String(100) | Parent bill | FOREIGN KEY → bills.id |
| note | String(500) | Document description | |
| date | DateTime | Document date | |
| links | JSONB | Array of URLs to document | |
| created_at | DateTime | Record creation timestamp | NOT NULL |

**Indexes:**
- Primary key on `id`
- Index on `bill_id`

---

### Votes

Represents legislative votes on bills.

**Table:** `votes`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | String(100) | OpenStates vote ID (OCD format) | PRIMARY KEY |
| bill_id | String(100) | Parent bill | FOREIGN KEY → bills.id |
| identifier | String(100) | Vote identifier | |
| motion_text | Text | Description of the motion | |
| motion_classification | String(100) | Type of motion | |
| start_date | DateTime | Vote date/time | NOT NULL |
| result | String(50) | Vote result (pass/fail) | NOT NULL |
| organization | String(100) | Chamber that held the vote | |
| counts | JSONB | Vote counts by option | |
| sources | JSONB | Data sources | |
| created_at | DateTime | Record creation timestamp | NOT NULL |
| updated_at | DateTime | Record update timestamp | NOT NULL |

**Example counts JSONB:**
```json
[
  {"option": "yes", "value": 30},
  {"option": "no", "value": 20},
  {"option": "abstain", "value": 2}
]
```

**Indexes:**
- Primary key on `id`
- Index on `bill_id`
- Index on `start_date`

---

### Vote Records

Represents individual legislator votes.

**Table:** `vote_records`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Auto-incrementing primary key | PRIMARY KEY |
| vote_id | String(100) | Parent vote | FOREIGN KEY → votes.id |
| person_id | String(100) | Voter (if linked) | FOREIGN KEY → people.id |
| option | String(50) | Vote option (yes/no/abstain/etc.) | NOT NULL |
| voter_name | String(255) | Name of voter | NOT NULL |
| created_at | DateTime | Record creation timestamp | NOT NULL |

**Indexes:**
- Primary key on `id`
- Index on `vote_id`
- Index on `person_id`

---

### Committees

Represents legislative committees.

**Table:** `committees`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | String(100) | OpenStates committee ID (OCD format) | PRIMARY KEY |
| name | String(500) | Committee name | NOT NULL |
| jurisdiction_id | String(100) | Parent jurisdiction | FOREIGN KEY → jurisdictions.id |
| chamber | String(50) | Chamber (upper/lower/joint) | |
| classification | String(100) | Committee type | |
| parent_id | String(100) | Parent committee (for subcommittees) | FOREIGN KEY → committees.id |
| extras | JSONB | Additional metadata | |
| sources | JSONB | Data sources | |
| created_at | DateTime | Record creation timestamp | NOT NULL |
| updated_at | DateTime | Record update timestamp | NOT NULL |

**Indexes:**
- Primary key on `id`
- Index on `jurisdiction_id`
- Index on `name`

---

### Ingestion Logs

Tracks data ingestion operations for monitoring.

**Table:** `ingestion_logs`

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Auto-incrementing primary key | PRIMARY KEY |
| operation_type | String(100) | Type of operation | NOT NULL |
| jurisdiction_id | String(100) | Target jurisdiction | |
| session_identifier | String(100) | Target session | |
| status | String(50) | Operation status | NOT NULL |
| items_processed | Integer | Number processed | DEFAULT 0 |
| items_failed | Integer | Number failed | DEFAULT 0 |
| start_time | DateTime | Operation start time | NOT NULL |
| end_time | DateTime | Operation end time | |
| error_message | Text | Error details if failed | |
| metadata | JSONB | Additional metadata | |

**Status values:**
- `running` - Operation in progress
- `completed` - Successfully completed
- `failed` - Failed with errors

**Indexes:**
- Primary key on `id`
- Index on `operation_type`
- Index on `status`
- Index on `start_time`

---

## Data Types

### JSONB Fields

Several tables use PostgreSQL's JSONB data type for flexible, structured data:

- **subjects** (bills): Array of subject strings
- **abstracts** (bills): Array of objects with `note` and `abstract` fields
- **actions** (bills): Array of action objects with `date`, `description`, `classification`
- **extras**: Free-form additional metadata
- **sources**: Array of source objects with `url` and `note`
- **links**: Array of link objects with `url` and optional `media_type`
- **counts** (votes): Array of count objects with `option` and `value`

### Enumerations

While stored as strings in the database, these fields have defined valid values:

**Bill Classification:**
- `bill`
- `resolution`
- `concurrent resolution`
- `joint resolution`
- `constitutional amendment`
- `memorial`
- `proclamation`
- `other`

**Vote Result:**
- `pass`
- `fail`
- `other`

**Vote Option:**
- `yes`
- `no`
- `abstain`
- `absent`
- `excused`
- `not voting`
- `other`

---

## Relationships

### One-to-Many Relationships

1. **Jurisdiction → LegislativeSession**
   - One jurisdiction has many sessions
   
2. **Jurisdiction → Person**
   - One jurisdiction has many people
   
3. **Jurisdiction → Bill**
   - One jurisdiction has many bills
   
4. **LegislativeSession → Bill**
   - One session has many bills
   
5. **Bill → BillSponsorship**
   - One bill has many sponsorships
   
6. **Bill → BillVersion**
   - One bill has many versions
   
7. **Bill → BillDocument**
   - One bill has many documents
   
8. **Bill → Vote**
   - One bill has many votes
   
9. **Vote → VoteRecord**
   - One vote has many vote records

### Many-to-Many Relationships

1. **Person ↔ Bill** (through BillSponsorship)
   - Many people can sponsor many bills
   
2. **Person ↔ Vote** (through VoteRecord)
   - Many people can vote on many bills

---

## Query Examples

### Get all bills from a jurisdiction and session

```sql
SELECT b.* 
FROM bills b
JOIN legislative_sessions ls ON b.legislative_session_id = ls.id
JOIN jurisdictions j ON b.jurisdiction_id = j.id
WHERE j.abbreviation = 'NC'
  AND ls.identifier = '2023';
```

### Get all sponsors for a bill

```sql
SELECT p.name, p.party, bs.classification, bs.primary
FROM bill_sponsorships bs
LEFT JOIN people p ON bs.person_id = p.id
WHERE bs.bill_id = 'ocd-bill/12345'
ORDER BY bs.primary DESC, p.name;
```

### Get vote results with individual votes

```sql
SELECT v.motion_text, v.result, v.start_date,
       vr.voter_name, vr.option
FROM votes v
JOIN vote_records vr ON v.id = vr.vote_id
WHERE v.bill_id = 'ocd-bill/12345'
ORDER BY v.start_date, vr.voter_name;
```

### Get recent ingestion operations

```sql
SELECT operation_type, jurisdiction_id, status,
       items_processed, items_failed,
       start_time, end_time
FROM ingestion_logs
ORDER BY start_time DESC
LIMIT 10;
```

---

## Performance Considerations

### Indexes

All foreign keys are indexed for efficient joins. Additional indexes on frequently queried fields:
- `bills.identifier` - for bill number lookups
- `bills.openstates_updated_at` - for incremental updates
- `people.name` - for legislator searches
- `votes.start_date` - for temporal queries

### JSONB Queries

JSONB fields support efficient queries using GIN indexes:

```sql
-- Create GIN index on subjects
CREATE INDEX idx_bill_subjects ON bills USING GIN (subject);

-- Query bills by subject
SELECT * FROM bills WHERE subject @> '["education"]'::jsonb;
```

### Partitioning

For very large datasets, consider partitioning:
- `bills` by `legislative_session_id` or `created_at`
- `votes` by `start_date`
- `ingestion_logs` by `start_time`

---

## Migration Strategy

### Initial Setup

```python
from openstates_db import OpenStatesDatabase

db = OpenStatesDatabase('postgresql://user:pass@localhost/openstates')
db.create_tables()
```

### Schema Updates

Use Alembic for schema migrations:

```bash
# Initialize alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migration
alembic upgrade head
```

---

## Data Integrity

### Cascading Deletes

Related entities are deleted when parent is deleted:
- Deleting a bill deletes its sponsorships, versions, documents, and votes
- Deleting a vote deletes its vote records

### Upsert Logic

All major entities support upsert (insert or update):
- Jurisdictions: updated if ID exists
- People: updated if ID exists
- Bills: updated if ID exists, related entities recreated
- Votes: updated if ID exists, vote records recreated

This ensures data stays current with OpenStates updates.
