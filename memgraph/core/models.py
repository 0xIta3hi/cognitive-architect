"""
MemGraph Core Data Models

Pydantic models for type safety and validation across the system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid


# ══════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════


class MemoryType(str, Enum):
    """Types of memories that can be stored."""
    PREFERENCE = "preference"      # User preferences/settings
    FACT = "fact"                  # Factual information
    ACTION = "action"              # Actions taken by agent
    CONVERSATION = "conversation"  # Conversational context
    DECISION = "decision"          # Decisions made
    OBSERVATION = "observation"    # Observed patterns


class RelationType(str, Enum):
    """Types of relationships between memories."""
    SUPPORTS = "supports"          # Memory A supports/reinforces B
    CONTRADICTS = "contradicts"    # Memory A contradicts B
    ELABORATES = "elaborates"      # Memory A adds detail to B
    FOLLOWS = "follows"            # Memory A follows B chronologically
    RELATES_TO = "relates_to"      # General relationship
    SUPERSEDES = "supersedes"      # Memory A replaces/updates B


class EntityType(str, Enum):
    """Types of entities that can be extracted."""
    CONCEPT = "concept"            # Abstract concepts
    PERSON = "person"              # People
    PLACE = "place"                # Locations
    PAPER = "paper"                # Research papers
    ORGANIZATION = "organization"  # Organizations
    EVENT = "event"                # Events


# ══════════════════════════════════════════════════════════════
# CORE MODELS
# ══════════════════════════════════════════════════════════════


class Agent(BaseModel):
    """Represents an AI agent that creates/uses memories."""
    
    id: str = Field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(default="general", max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Agent name cannot be empty')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "agent_abc123def456",
                "name": "Research Assistant",
                "type": "research",
                "metadata": {"version": "1.0", "capabilities": ["search", "summarize"]}
            }
        }


class Memory(BaseModel):
    """Represents a single memory unit in the graph."""
    
    id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:16]}")
    content: str = Field(..., min_length=1, max_length=10000)
    memory_type: MemoryType = Field(default=MemoryType.FACT)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    embedding_id: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('content')
    @classmethod
    def content_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Memory content cannot be empty')
        return v.strip()
    
    @field_validator('importance')
    @classmethod
    def importance_valid_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError('Importance must be between 0.0 and 1.0')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "mem_abc123def456789",
                "content": "User prefers concise explanations with code examples",
                "memory_type": "preference",
                "importance": 0.8,
                "metadata": {"topic": "communication_style", "verified": True}
            }
        }


class Context(BaseModel):
    """Represents a conversation or task session."""
    
    id: str = Field(default_factory=lambda: f"ctx_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., min_length=1, max_length=300)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    summary: Optional[str] = Field(default=None, max_length=5000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('ended_at')
    @classmethod
    def ended_after_started(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v and 'started_at' in info.data and v < info.data['started_at']:
            raise ValueError('ended_at must be after started_at')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "ctx_abc123def456",
                "name": "Literature Review Session - Neural Networks",
                "summary": "Discussed recent advances in transformer architectures",
                "metadata": {"papers_reviewed": 5, "duration_minutes": 45}
            }
        }


class Entity(BaseModel):
    """Represents an extracted entity from memories."""
    
    id: str = Field(default_factory=lambda: f"ent_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., min_length=1, max_length=200)
    type: EntityType = Field(default=EntityType.CONCEPT)
    description: Optional[str] = Field(default=None, max_length=2000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Entity name cannot be empty')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "ent_neural_nets",
                "name": "Neural Networks",
                "type": "concept",
                "description": "Computational models inspired by biological neural networks",
                "metadata": {"field": "machine_learning", "popularity": "high"}
            }
        }


# ══════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ══════════════════════════════════════════════════════════════


class AddMemoryRequest(BaseModel):
    """Request to add a new memory."""
    
    agent_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1, max_length=10000)
    memory_type: MemoryType = Field(default=MemoryType.FACT)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    context_id: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_research_001",
                "content": "User is working on a thesis about graph neural networks",
                "memory_type": "fact",
                "importance": 0.9,
                "metadata": {"topic": "research", "deadline": "2025-12-01"}
            }
        }


class RetrieveContextRequest(BaseModel):
    """Request to retrieve relevant context."""
    
    agent_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=50)
    time_range_days: Optional[int] = Field(default=None, ge=1)
    memory_types: Optional[List[MemoryType]] = Field(default=None)
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_research_001",
                "query": "What do I know about the user's research interests?",
                "limit": 10,
                "time_range_days": 30,
                "min_importance": 0.5
            }
        }


class ShareMemoryRequest(BaseModel):
    """Request to share memories between agents."""
    
    from_agent_id: str = Field(..., min_length=1)
    to_agent_id: str = Field(..., min_length=1)
    memory_ids: List[str] = Field(..., min_items=1)
    permission: str = Field(default="read", pattern="^(read|write)$")
    
    @field_validator('to_agent_id')
    @classmethod
    def agents_must_differ(cls, v: str, info) -> str:
        if 'from_agent_id' in info.data and v == info.data['from_agent_id']:
            raise ValueError('Cannot share memories with the same agent')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_agent_id": "agent_research_001",
                "to_agent_id": "agent_writing_001",
                "memory_ids": ["mem_abc123", "mem_def456"],
                "permission": "read"
            }
        }


class MemoryResponse(BaseModel):
    """Response containing memory data."""
    
    memory: Memory
    agent_name: Optional[str] = Field(default=None)
    context_name: Optional[str] = Field(default=None)
    relevance_score: Optional[float] = Field(default=None)
    related_memories: List[str] = Field(default_factory=list)


class ContextResponse(BaseModel):
    """Response containing retrieved context."""
    
    memories: List[MemoryResponse]
    total_found: int
    query: str
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


# ══════════════════════════════════════════════════════════════
# RELATIONSHIP MODELS
# ══════════════════════════════════════════════════════════════


class MemoryRelationship(BaseModel):
    """Represents a relationship between two memories."""
    
    from_memory_id: str
    to_memory_id: str
    type: RelationType
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    reason: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('to_memory_id')
    @classmethod
    def memories_must_differ(cls, v: str, info) -> str:
        if 'from_memory_id' in info.data and v == info.data['from_memory_id']:
            raise ValueError('Cannot create relationship with the same memory')
        return v


class TemporalQuery(BaseModel):
    """Query for temporal memory patterns."""
    
    agent_id: str
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    memory_types: Optional[List[MemoryType]] = Field(default=None)
    
    @field_validator('end_time')
    @classmethod
    def end_after_start(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v and 'start_time' in info.data and info.data['start_time'] and v < info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
    
