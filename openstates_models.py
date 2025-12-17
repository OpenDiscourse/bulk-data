"""
OpenStates Data Models

Defines SQLAlchemy models for storing OpenStates legislative data in PostgreSQL.
Covers Bills, Legislators (People), Votes, Committees, and related entities.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, JSON, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator
import enum

# Use JSON type that works with both PostgreSQL (JSONB) and SQLite (JSON)
class JSONType(TypeDecorator):
    """
    JSON type that uses JSONB for PostgreSQL and JSON for other databases.
    """
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


Base = declarative_base()


class BillClassification(str, enum.Enum):
    """Enumeration of bill classifications."""
    BILL = "bill"
    RESOLUTION = "resolution"
    CONCURRENT_RESOLUTION = "concurrent resolution"
    JOINT_RESOLUTION = "joint resolution"
    CONSTITUTIONAL_AMENDMENT = "constitutional amendment"
    MEMORIAL = "memorial"
    PROCLAMATION = "proclamation"
    OTHER = "other"


class VoteResult(str, enum.Enum):
    """Enumeration of vote results."""
    PASS = "pass"
    FAIL = "fail"
    OTHER = "other"


class VoteOption(str, enum.Enum):
    """Enumeration of vote options."""
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    ABSENT = "absent"
    EXCUSED = "excused"
    NOT_VOTING = "not voting"
    OTHER = "other"


class Jurisdiction(Base):
    """
    Represents a U.S. state, territory, or federal jurisdiction.
    
    Attributes:
        id: Primary key
        name: Full name (e.g., "North Carolina")
        abbreviation: Two-letter code (e.g., "NC")
        classification: Type (state, territory, etc.)
        url: Official government website
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    __tablename__ = "jurisdictions"
    
    id = Column(String(100), primary_key=True)  # OCD ID format
    name = Column(String(255), nullable=False)
    abbreviation = Column(String(10), nullable=False, unique=True)
    classification = Column(String(50))
    url = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    bills = relationship("Bill", back_populates="jurisdiction")
    people = relationship("Person", back_populates="jurisdiction")
    legislative_sessions = relationship("LegislativeSession", back_populates="jurisdiction")


class LegislativeSession(Base):
    """
    Represents a legislative session.
    
    Attributes:
        id: Primary key
        identifier: Session identifier (e.g., "2023")
        name: Full session name
        jurisdiction_id: Foreign key to jurisdiction
        start_date: Session start date
        end_date: Session end date
        classification: Type of session (regular, special, etc.)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    __tablename__ = "legislative_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    jurisdiction_id = Column(String(100), ForeignKey("jurisdictions.id"), nullable=False)
    
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    classification = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="legislative_sessions")
    bills = relationship("Bill", back_populates="legislative_session")
    
    __table_args__ = (
        UniqueConstraint('jurisdiction_id', 'identifier', name='uq_jurisdiction_session'),
        Index('idx_session_jurisdiction', 'jurisdiction_id'),
    )


class Person(Base):
    """
    Represents a legislator or other government person.
    
    Attributes:
        id: Primary key (OpenStates person ID)
        name: Full name
        given_name: First name
        family_name: Last name
        email: Contact email
        jurisdiction_id: Foreign key to jurisdiction
        party: Political party affiliation
        current_role: Current position/role
        image_url: Profile photo URL
        extras: Additional metadata (JSONB)
        sources: Data sources (JSONB)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    __tablename__ = "people"
    
    id = Column(String(100), primary_key=True)  # OCD person ID
    name = Column(String(255), nullable=False)
    given_name = Column(String(100))
    family_name = Column(String(100))
    email = Column(String(255))
    
    jurisdiction_id = Column(String(100), ForeignKey("jurisdictions.id"), nullable=False)
    party = Column(String(100))
    current_role = Column(String(255))
    image_url = Column(String(500))
    
    extras = Column(JSONType)
    sources = Column(JSONType)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="people")
    bill_sponsorships = relationship("BillSponsorship", back_populates="person")
    vote_records = relationship("VoteRecord", back_populates="person")
    
    __table_args__ = (
        Index('idx_person_jurisdiction', 'jurisdiction_id'),
        Index('idx_person_name', 'name'),
    )


class Bill(Base):
    """
    Represents a legislative bill.
    
    Attributes:
        id: Primary key (OpenStates bill ID)
        identifier: Bill number (e.g., "HB 475")
        title: Bill title
        classification: Bill type (bill, resolution, etc.)
        subject: Bill subjects/topics (JSONB array)
        abstracts: Bill summaries (JSONB)
        jurisdiction_id: Foreign key to jurisdiction
        legislative_session_id: Foreign key to legislative session
        from_organization: Originating chamber
        actions: Bill actions/history (JSONB)
        extras: Additional metadata (JSONB)
        sources: Data sources (JSONB)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
        openstates_updated_at: Last update from OpenStates
    """
    __tablename__ = "bills"
    
    id = Column(String(100), primary_key=True)  # OCD bill ID
    identifier = Column(String(100), nullable=False)
    title = Column(Text, nullable=False)
    classification = Column(String(50), nullable=False)
    
    subject = Column(JSONType)  # Array of subjects
    abstracts = Column(JSONType)  # Array of abstracts with notes
    
    jurisdiction_id = Column(String(100), ForeignKey("jurisdictions.id"), nullable=False)
    legislative_session_id = Column(Integer, ForeignKey("legislative_sessions.id"), nullable=False)
    
    from_organization = Column(String(100))  # Chamber (upper/lower)
    
    actions = Column(JSONType)  # Array of action objects
    extras = Column(JSONType)
    sources = Column(JSONType)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    openstates_updated_at = Column(DateTime)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="bills")
    legislative_session = relationship("LegislativeSession", back_populates="bills")
    sponsorships = relationship("BillSponsorship", back_populates="bill", cascade="all, delete-orphan")
    versions = relationship("BillVersion", back_populates="bill", cascade="all, delete-orphan")
    documents = relationship("BillDocument", back_populates="bill", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="bill", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_bill_jurisdiction', 'jurisdiction_id'),
        Index('idx_bill_session', 'legislative_session_id'),
        Index('idx_bill_identifier', 'identifier'),
        Index('idx_bill_updated', 'openstates_updated_at'),
    )


class BillSponsorship(Base):
    """
    Represents a bill sponsorship relationship.
    
    Attributes:
        id: Primary key
        bill_id: Foreign key to bill
        person_id: Foreign key to person
        classification: Type of sponsorship (primary, cosponsor, etc.)
        name: Sponsor name (if person not linked)
        entity_type: Type of entity (person, organization)
        primary: Whether this is the primary sponsor
        created_at: Record creation timestamp
    """
    __tablename__ = "bill_sponsorships"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(String(100), ForeignKey("bills.id"), nullable=False)
    person_id = Column(String(100), ForeignKey("people.id"))
    
    classification = Column(String(50))
    name = Column(String(255), nullable=False)
    entity_type = Column(String(50))
    primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    bill = relationship("Bill", back_populates="sponsorships")
    person = relationship("Person", back_populates="bill_sponsorships")
    
    __table_args__ = (
        Index('idx_sponsorship_bill', 'bill_id'),
        Index('idx_sponsorship_person', 'person_id'),
    )


class BillVersion(Base):
    """
    Represents a version of a bill text.
    
    Attributes:
        id: Primary key
        bill_id: Foreign key to bill
        note: Version description
        date: Version date
        links: URLs to bill text (JSONB)
        created_at: Record creation timestamp
    """
    __tablename__ = "bill_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(String(100), ForeignKey("bills.id"), nullable=False)
    
    note = Column(String(500))
    date = Column(DateTime)
    links = Column(JSONType)  # Array of link objects
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    bill = relationship("Bill", back_populates="versions")
    
    __table_args__ = (
        Index('idx_version_bill', 'bill_id'),
    )


class BillDocument(Base):
    """
    Represents a document related to a bill.
    
    Attributes:
        id: Primary key
        bill_id: Foreign key to bill
        note: Document description
        date: Document date
        links: URLs to document (JSONB)
        created_at: Record creation timestamp
    """
    __tablename__ = "bill_documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(String(100), ForeignKey("bills.id"), nullable=False)
    
    note = Column(String(500))
    date = Column(DateTime)
    links = Column(JSONType)  # Array of link objects
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    bill = relationship("Bill", back_populates="documents")
    
    __table_args__ = (
        Index('idx_document_bill', 'bill_id'),
    )


class Vote(Base):
    """
    Represents a legislative vote on a bill.
    
    Attributes:
        id: Primary key (OpenStates vote ID)
        bill_id: Foreign key to bill
        identifier: Vote identifier
        motion_text: Description of the motion
        motion_classification: Type of motion
        start_date: Vote date/time
        result: Vote result (pass/fail)
        organization: Chamber that held the vote
        counts: Vote counts by option (JSONB)
        sources: Data sources (JSONB)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    __tablename__ = "votes"
    
    id = Column(String(100), primary_key=True)  # OCD vote ID
    bill_id = Column(String(100), ForeignKey("bills.id"), nullable=False)
    
    identifier = Column(String(100))
    motion_text = Column(Text)
    motion_classification = Column(String(100))
    start_date = Column(DateTime, nullable=False)
    result = Column(String(50), nullable=False)
    
    organization = Column(String(100))  # Chamber
    counts = Column(JSONType)  # Array of count objects
    sources = Column(JSONType)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    bill = relationship("Bill", back_populates="votes")
    vote_records = relationship("VoteRecord", back_populates="vote", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_vote_bill', 'bill_id'),
        Index('idx_vote_date', 'start_date'),
    )


class VoteRecord(Base):
    """
    Represents an individual legislator's vote.
    
    Attributes:
        id: Primary key
        vote_id: Foreign key to vote
        person_id: Foreign key to person
        option: Vote option (yes/no/abstain/etc.)
        voter_name: Name of voter (if person not linked)
        created_at: Record creation timestamp
    """
    __tablename__ = "vote_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vote_id = Column(String(100), ForeignKey("votes.id"), nullable=False)
    person_id = Column(String(100), ForeignKey("people.id"))
    
    option = Column(String(50), nullable=False)
    voter_name = Column(String(255), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    vote = relationship("Vote", back_populates="vote_records")
    person = relationship("Person", back_populates="vote_records")
    
    __table_args__ = (
        Index('idx_vote_record_vote', 'vote_id'),
        Index('idx_vote_record_person', 'person_id'),
    )


class Committee(Base):
    """
    Represents a legislative committee.
    
    Attributes:
        id: Primary key (OpenStates committee ID)
        name: Committee name
        jurisdiction_id: Foreign key to jurisdiction
        chamber: Chamber (upper/lower/joint)
        classification: Committee type
        parent_id: Parent committee (for subcommittees)
        extras: Additional metadata (JSONB)
        sources: Data sources (JSONB)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    __tablename__ = "committees"
    
    id = Column(String(100), primary_key=True)  # OCD committee ID
    name = Column(String(500), nullable=False)
    jurisdiction_id = Column(String(100), ForeignKey("jurisdictions.id"), nullable=False)
    
    chamber = Column(String(50))
    classification = Column(String(100))
    parent_id = Column(String(100), ForeignKey("committees.id"))
    
    extras = Column(JSONType)
    sources = Column(JSONType)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    parent = relationship("Committee", remote_side=[id], backref="subcommittees")
    
    __table_args__ = (
        Index('idx_committee_jurisdiction', 'jurisdiction_id'),
        Index('idx_committee_name', 'name'),
    )


class IngestionLog(Base):
    """
    Tracks data ingestion operations for monitoring and resumption.
    
    Attributes:
        id: Primary key
        operation_type: Type of operation (bills, people, votes, etc.)
        jurisdiction_id: Target jurisdiction
        session_identifier: Legislative session
        status: Operation status (running, completed, failed)
        items_processed: Number of items processed
        items_failed: Number of items that failed
        start_time: Operation start time
        end_time: Operation end time
        error_message: Error details if failed
        operation_metadata: Additional operation metadata (JSONB)
    """
    __tablename__ = "ingestion_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(String(100), nullable=False)
    jurisdiction_id = Column(String(100))
    session_identifier = Column(String(100))
    
    status = Column(String(50), nullable=False)  # running, completed, failed
    items_processed = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime)
    error_message = Column(Text)
    operation_metadata = Column(JSONType)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word
    
    __table_args__ = (
        Index('idx_ingestion_type', 'operation_type'),
        Index('idx_ingestion_status', 'status'),
        Index('idx_ingestion_time', 'start_time'),
    )
