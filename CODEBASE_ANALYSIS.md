# MemGraph Codebase - Comprehensive Technical Analysis

**Date:** January 28, 2026  
**Project:** MemGraph - Open-source memory layer for AI agents with persistent context graphs  
**Status:** Early Development (MVP launching Nov 12, 2025)

---

## 1. Architecture Overview

### File Structure & Module Organization

```
MemGraph/
├── memgraph/
│   ├── api/                          # FastAPI REST endpoints
│   │   ├── main.py                  # FastAPI app initialization
│   │   ├── routes.py                # Endpoint definitions
│   │   └── llm.py                   # LLM integration (Google Gemini)
│   ├── core/                        # Core business logic
│   │   ├── memory.py                # Main MemoryGraph interface
│   │   ├── graph.py                 # Neo4j database operations
│   │   └── models.py                # Pydantic data models
│   └── integrations/
│       └── langchain_agent.py       # LangChain memory backend
├── app/                             # Next.js frontend
│   ├── layout.tsx
│   ├── page.tsx
│   └── playground/
│       └── page.tsx
├── src/                             # Frontend components
│   ├── components/                  # React components
│   │   ├── AgentCreationForm.tsx
│   │   ├── AgentDetails.tsx
│   │   ├── AgentLoader.tsx
│   │   ├── ChatInterface.tsx
│   │   ├── GraphView.tsx
│   │   └── Navigation.tsx
│   └── lib/                         # Frontend utilities
│       ├── memgraph.ts              # API client
│       └── api/
│           ├── client.ts
│           └── index.ts
├── tests/                           # Test directory (minimal)
├── examples/
│   └── langchain_integration.py     # Integration examples
├── memgraph/
│   └── __init__.py
└── [test scripts]
    ├── test_agent_state.py
    ├── test_backend_manual.py
    ├── test_chat_debug.py
    └── test_quick_memory.py
```

### Main Entry Point

**Primary Entry Point:** [memgraph/api/main.py](memgraph/api/main.py)

- **Framework:** FastAPI 0.104.1
- **Server:** Uvicorn (async ASGI)
- **Start Command:** `python -m uvicorn memgraph.api.main:app --reload`

**Startup Flow:**
1. FastAPI app initialization with lifespan context manager
2. MemoryGraph instance creation with Neo4j connection
3. CORS middleware configuration
4. Router registration (agents, memories, contexts, relationships, sharing, chat)
5. Health check verification

```python
# Lifespan management (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MemoryGraph & verify connection
    _memory_graph = MemoryGraph(neo4j_uri, neo4j_user, neo4j_password)
    if _memory_graph.health_check():
        logger.info("✅ MemoryGraph connected successfully")
    
    yield  # App runs
    
    # Shutdown: Close database connection
    _memory_graph.close()
```

### Component Organization

**Layered Architecture:**

1. **API Layer** (routes.py)
   - RESTful endpoints for all operations
   - Request/response validation with Pydantic
   - Error handling and logging

2. **Core Logic Layer** (memory.py)
   - High-level MemoryGraph interface
   - Business logic for memory operations
   - Context management

3. **Database Layer** (graph.py)
   - Neo4j query execution
   - Data transformation (Neo4j↔Python)
   - Relationship management

4. **Data Models** (models.py)
   - Pydantic models for validation
   - Enum definitions for memory/relationship types

5. **Integration Layer** (langchain_agent.py)
   - LangChain memory backend implementation
   - Tool definitions for agent use

### Graph Database

**Database:** Neo4j 5.14.1  
**Connection:** Bolt protocol (neo4j://localhost:7687)  
**Authentication:** Username/password

**Node Types:**
- `Agent` - AI agents that create/use memories
- `Memory` - Individual memory units
- `Context` - Sessions/conversations grouping memories
- `Entity` - Extracted entities from memories (not heavily used)

**Relationship Types:**
- `CREATED` - Agent → Memory (creation relationship with timestamp)
- `PART_OF` - Memory → Context (session grouping)
- `RELATES_TO` - Memory → Memory (explicit relationships with strength/type)
- `ACCESSED` - Agent → Memory (cross-agent sharing with permission)

**Database Connection:**
```python
# Neo4j driver initialization with bolt protocol
driver = Neo4jDriver.driver(uri, auth=(user, password))
driver.verify_connectivity()
```

---

## 2. Entity Extraction Pipeline

**Status:** NOT FULLY IMPLEMENTED

**Current State:**
- Entity model defined in models.py (`EntityType` enum with: CONCEPT, PERSON, PLACE, PAPER, ORGANIZATION, EVENT)
- Entity node type exists in database schema
- **No NLP/extraction logic** currently implemented

**Entity Model Definition:**
```python
class Entity(BaseModel):
    """Represents an extracted entity from memories."""
    id: str = Field(default_factory=lambda: f"ent_{uuid.uuid4().hex[:12]}")
    name: str                          # Entity name
    type: EntityType                   # Type classification
    description: Optional[str]         # Description
    metadata: Dict[str, Any]          # Additional data
```

**Entity Types:**
- `CONCEPT` - Abstract concepts (e.g., "neural networks")
- `PERSON` - People names
- `PLACE` - Locations/places
- `PAPER` - Research papers
- `ORGANIZATION` - Organizations
- `EVENT` - Events

**Missing Implementation:**
- ❌ NLP library integration (spaCy, transformers, etc.)
- ❌ Automatic entity extraction from memory content
- ❌ Entity deduplication logic
- ❌ Coreference resolution (e.g., "he" → "John")
- ❌ Entity linking to external databases
- ❌ Disambiguation logic

**Note:** Currently, memories are stored as plain text without automatic entity extraction. This is a planned feature for future development.

---

## 3. Graph Storage Schema

### Node Properties

#### Agent Node
```python
CREATE (a:Agent {
    id: str,              # Unique agent identifier
    name: str,            # Human-readable name
    type: str,            # Agent type (research, writing, coding, etc.)
    created_at: datetime, # Creation timestamp
    metadata: json_str    # Additional metadata
})
```

**Example:**
```cypher
CREATE (a:Agent {
    id: "research_assistant_001",
    name: "Research Assistant",
    type: "research",
    created_at: datetime.utcnow(),
    metadata: '{"version": "1.0", "capabilities": ["search", "analyze"]}'
})
```

#### Memory Node
```python
CREATE (m:Memory {
    id: str,                    # Unique memory ID
    content: str,               # Memory text (max 10,000 chars)
    memory_type: str,          # Type enum value
    importance: float,          # 0.0-1.0 importance score
    created_at: datetime,       # Creation timestamp
    updated_at: datetime,       # Last update timestamp
    embedding_id: str|null,    # Vector embedding ID (for future use)
    metadata: json_str          # Custom metadata
})
```

**Memory Types:**
- `preference` - User preferences/settings
- `fact` - Factual information
- `action` - Actions taken by agent
- `conversation` - Conversational context
- `decision` - Decisions made
- `observation` - Observed patterns
- `interaction` - User interactions (stored from chat endpoint)

**Example:**
```python
memory = Memory(
    id="mem_abc123def456789",
    content="User prefers concise explanations with code examples",
    memory_type=MemoryType.PREFERENCE,
    importance=0.8,
    metadata={"topic": "communication_style", "verified": True}
)
```

#### Context Node
```python
CREATE (c:Context {
    id: str,                    # Context ID
    name: str,                  # Session name
    started_at: datetime,       # Start timestamp
    ended_at: datetime|null,   # End timestamp (nullable)
    summary: str|null,          # Session summary
    metadata: json_str          # Custom metadata
})
```

#### Entity Node (Minimal)
```python
CREATE (e:Entity {
    id: str,           # Entity ID
    name: str,         # Entity name
    type: str,         # Entity type
    description: str,  # Description
    metadata: json_str # Metadata
})
```

### Relationship Properties

#### CREATED Relationship (Agent → Memory)
```python
(a:Agent)-[c:CREATED {
    at: datetime          # Creation timestamp
}]->(m:Memory)
```

#### PART_OF Relationship (Memory → Context)
```python
(m:Memory)-[p:PART_OF {
    at: datetime          # Association timestamp
}]->(c:Context)
```

#### RELATES_TO Relationship (Memory → Memory)
```python
(m1:Memory)-[r:RELATES_TO {
    type: str,            # Relationship type (supports, contradicts, etc.)
    strength: float,      # 0.0-1.0 strength score
    reason: str|null,     # Optional explanation
    created_at: datetime  # Creation timestamp
}]->(m2:Memory)
```

**Relationship Types:**
- `supports` - m1 supports/reinforces m2
- `contradicts` - m1 contradicts m2
- `elaborates` - m1 adds detail to m2
- `follows` - m1 follows m2 chronologically
- `relates_to` - General relationship
- `supersedes` - m1 replaces/updates m2

#### ACCESSED Relationship (Agent → Memory, Cross-Agent Sharing)
```python
(a:Agent)-[acc:ACCESSED {
    at: datetime,          # Access timestamp
    permission: str,       # "read" or "write"
    shared_by: str         # Source agent ID
}]->(m:Memory)
```

### Node/Edge Creation Example

**Adding a Memory:**
```python
def add_memory(agent_id: str, memory: Memory, context_id: Optional[str] = None):
    """Add memory to graph with relationships."""
    query = """
    MATCH (a:Agent {id: $agent_id})
    CREATE (m:Memory {
        id: $id,
        content: $content,
        memory_type: $memory_type,
        importance: $importance,
        created_at: datetime($created_at),
        updated_at: datetime($updated_at),
        embedding_id: $embedding_id,
        metadata: $metadata
    })
    CREATE (a)-[:CREATED {at: datetime($created_at)}]->(m)
    """
    
    if context_id:
        query += """
        WITH m
        MATCH (c:Context {id: $context_id})
        CREATE (m)-[:PART_OF {at: datetime($created_at)}]->(c)
        """
    
    query += "RETURN m"
    
    # Execute with parameters
    with driver.session() as session:
        result = session.run(query, id=memory.id, content=memory.content, ...)
```

### Versioning & Temporal Tracking

**Current Implementation:**
- `created_at` - Immutable creation timestamp on all nodes
- `updated_at` - Updated timestamp on Memory nodes (but not actively updated)
- No explicit versioning mechanism

**Temporal Relationships:**
- All relationships track creation timestamps (`at`, `created_at`)
- Can query memories within time ranges using `time_range_days` parameter

**Missing:**
- ❌ Full audit trail/version history
- ❌ Soft delete (archived) vs hard delete
- ❌ Change tracking between versions
- ❌ Temporal queries for "state at time T"

---

## 4. Relationship Extraction

**Status:** PARTIALLY IMPLEMENTED

### Current Approach

**Relationship Creation:** Manual, via API endpoint
```python
@router_relationships.post("")
async def create_relationship(
    from_memory_id: str,
    to_memory_id: str,
    relation_type: str,      # User specifies type
    strength: float,          # User specifies strength
    reason: Optional[str]     # User provides reason
)
```

**Relationship Types Supported:**
```python
class RelationType(str, Enum):
    SUPPORTS = "supports"           # A supports/reinforces B
    CONTRADICTS = "contradicts"     # A contradicts B
    ELABORATES = "elaborates"       # A adds detail to B
    FOLLOWS = "follows"             # A follows B chronologically
    RELATES_TO = "relates_to"       # General relationship
    SUPERSEDES = "supersedes"       # A replaces/updates B
```

### Relationship Extraction Logic

**User/API Creates Explicit Relationships:**
```python
def relate(self, from_memory_id: str, to_memory_id: str, 
           relation_type: str = "relates_to", strength: float = 0.5):
    """Create explicit relationship between memories."""
    relationship = MemoryRelationship(
        from_memory_id=from_memory_id,
        to_memory_id=to_memory_id,
        type=RelationType(relation_type),
        strength=strength,
        reason=reason
    )
    return self.graph.create_memory_relationship(relationship)
```

### Coreference Resolution

**Status:** NOT IMPLEMENTED

- ❌ No pronoun resolution (e.g., "he" → "John")
- ❌ No named entity linking
- ❌ No automatic relationship inference from text
- ❌ No NLP-based relationship extraction

**Note:** All relationships are explicitly created by users/agents via the API. There's no automatic NLP pipeline to extract relationships from memory content.

---

## 5. Memory Storage & Retrieval

### Core Operations

#### Add Memory Function

**Function Signature:**
```python
def add(
    self,
    agent_id: str,                    # Agent creating memory
    content: str,                     # Memory text (max 10k chars)
    memory_type: str = "fact",        # Type: preference, fact, action, conversation, decision, observation
    importance: float = 0.5,          # 0.0-1.0 importance score
    context_id: Optional[str] = None, # Optional session ID
    metadata: Optional[Dict] = None   # Additional metadata
) -> Memory
```

**Implementation:**
```python
def add(self, agent_id: str, content: str, memory_type: str = "fact", 
        importance: float = 0.5, context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None) -> Memory:
    
    # Verify agent exists
    agent = self.graph.get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found. Register agent first.")
    
    # Create memory object
    memory = Memory(
        content=content,
        memory_type=MemoryType(memory_type),
        importance=importance,
        metadata=metadata or {}
    )
    
    # Store in graph with relationships
    return self.graph.add_memory(agent_id, memory, context_id)
```

**Database Operation (Neo4j):**
```cypher
MATCH (a:Agent {id: $agent_id})
CREATE (m:Memory {
    id: $id,
    content: $content,
    memory_type: $memory_type,
    importance: $importance,
    created_at: datetime($created_at),
    updated_at: datetime($updated_at),
    embedding_id: $embedding_id,
    metadata: $metadata
})
CREATE (a)-[:CREATED {at: datetime($created_at)}]->(m)
[IF context_id:]
MATCH (c:Context {id: $context_id})
CREATE (m)-[:PART_OF {at: datetime($created_at)}]->(c)
RETURN m
```

#### Retrieve Memory Function

**Function Signature:**
```python
def retrieve(
    self,
    agent_id: str,                       # Agent making query
    query: str,                          # Natural language query
    limit: int = 5,                      # Max results
    time_range_days: Optional[int] = None,  # Time filter
    memory_types: Optional[List[str]] = None, # Type filter
    min_importance: float = 0.0          # Importance threshold
) -> ContextResponse
```

**Implementation (Simplified):**
```python
def retrieve(self, agent_id: str, query: str, limit: int = 5, ...):
    # Get agent's memories with filters
    memories = self.graph.get_agent_memories(
        agent_id=agent_id,
        limit=limit,
        memory_types=type_enums,
        time_range_days=time_range_days
    )
    
    # Filter by importance threshold
    if min_importance > 0.0:
        memories = [m for m in memories if m.memory.importance >= min_importance]
    
    # TODO: Add semantic search ranking when vector store integrated
    # Currently: Sort by recency and importance
    memories.sort(
        key=lambda m: (m.memory.importance, m.memory.created_at),
        reverse=True
    )
    
    return ContextResponse(
        memories=memories[:limit],
        total_found=len(memories),
        query=query
    )
```

**Database Query (Simplified):**
```cypher
MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory)
WHERE m.memory_type IN $memory_types
  AND c.at > datetime() - duration('P' + $days + 'D')
RETURN m, a.name as agent_name, c.at as created_at
ORDER BY c.at DESC
LIMIT $limit
```

### Confidence Scoring

**Current Implementation:**
- `importance` field (0.0-1.0) on each Memory node
- Used for filtering and sorting
- No dynamic confidence calculation

**Missing:**
- ❌ Relevance scoring based on semantic similarity to query
- ❌ Recency scoring (time decay)
- ❌ Context-based confidence adjustment
- ❌ Certainty levels (uncertain, likely, confirmed)

**TODO Note in Code:**
```python
# TODO: Add semantic search ranking when vector store is integrated
# For now, return by recency and importance
```

### Duplicate Handling

**Current State:**
- ❌ No automatic deduplication
- ❌ No similarity detection
- ❌ Duplicates allowed (same content can be stored multiple times)

**Approach if Needed:**
- Would need embedding/vector storage (not yet implemented)
- Could use Neo4j similarity queries
- Would require text similarity threshold

---

## 6. Context Management

### Context Retrieval Function

**How Much Context is Passed to LLM:**

In the chat endpoint:
```python
# Retrieve relevant context from agent's memories
context_response = memory_graph.retrieve(
    agent_id=agent_id,
    query=message,
    limit=5,                # Default: 5 memories
    min_importance=0.3      # Default: importance ≥ 0.3
)

# Build context for LLM
memory_context = "\n- ".join([m.memory.content for m in relevant_memories])
memory_context = "- " + memory_context  # Format as bullet list
```

**Context Window:**
- Default: 5 most relevant memories (configurable)
- LangChain integration: `context_window_size: int = 5` (in MemGraphMemory)
- Context includes full memory content + agent name

**Context Retrieval Function Signature:**
```python
def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Load context from MemGraph for LangChain agent."""
    query = inputs.get("input", "")
    
    # Retrieve from MemGraph
    context = self.memory_graph.retrieve(
        agent_id=self.agent_id,
        query=query,
        limit=self.context_window_size,
        min_importance=self.min_importance
    )
    
    # Format for inclusion in prompt
    memory_text = self._format_memories(context)
    
    return {self.memory_variables[0]: memory_text}
```

### Intelligent Context Pruning/Ranking

**Current Strategy:**
1. **Time-based filtering** - Optional: only last N days
2. **Importance-based filtering** - Optional: minimum threshold
3. **Type-based filtering** - Optional: specific memory types
4. **Recency sorting** - Sorted by `created_at` DESC and importance

**Missing:**
- ❌ Semantic similarity to query (no embeddings yet)
- ❌ Learned importance weighting per agent
- ❌ Context compression for long documents
- ❌ Adaptive context window sizing
- ❌ Relevance feedback loop

**Example Ranking:**
```python
# Sort by importance (primary) then recency (secondary)
memories.sort(
    key=lambda m: (m.memory.importance, m.memory.created_at),
    reverse=True
)
```

### Recent vs Old Memories Weighting

**Current Implementation:**
- ❌ No temporal decay function
- ❌ Equal weighting for old vs recent (only recency used for sorting)

**Potential Enhancement:**
- Could implement exponential time decay: `weight = importance * exp(-age_days / half_life)`
- Currently: Just sort newest first within same importance level

---

## 7. Conflict Resolution

**Status:** MINIMAL IMPLEMENTATION

### Handling Contradictory Information

**What Exists:**
- `supersedes` relationship type indicates one memory replaces another
- Users can manually create such relationships

**What's Missing:**
- ❌ Automatic conflict detection
- ❌ Contradiction flagging
- ❌ Resolution strategy selection
- ❌ Confidence-based conflict resolution

### Current Relationship Types Include Conflict Markers

```python
class RelationType(str, Enum):
    CONTRADICTS = "contradicts"  # Explicit marker
    SUPERSEDES = "supersedes"    # Indicates replacement
```

**Manual Usage:**
```python
# User explicitly creates contradiction relationship
memory.relate(
    from_memory_id="mem_new_info",
    to_memory_id="mem_old_info",
    relation_type="supersedes",
    strength=0.9,
    reason="Updated information contradicts previous assumption"
)
```

**Missing Conflict Logic:**
```python
# Example: Would need something like this (NOT IMPLEMENTED)
def detect_conflicts(query_result: List[Memory]) -> List[ConflictReport]:
    """Detect contradictions in retrieved memories."""
    # Extract entities and claims from memory content
    # Check for contradictory claims
    # Return conflict reports
    pass

def resolve_conflicts(conflicts: List[ConflictReport]) -> ResolvedMemory:
    """Apply conflict resolution strategy."""
    # Options: take newest, take highest importance, ask user
    pass
```

---

## 8. Multi-User/Agent Support

### Agent Isolation

**Agent Registration:**
```python
def register_agent(
    self,
    agent_id: str,      # Unique ID per agent
    name: str,
    agent_type: str = "general",
    metadata: Optional[Dict] = None
) -> Agent
```

**Each Agent is Isolated:**
- Separate memory space (Agent node + CREATED relationships)
- Distinct memory queries per `agent_id`
- No cross-contamination of memories

**Example:**
```python
# Agent 1's memories
memory.register_agent("agent_1", "Research Assistant")
memory.add(agent_id="agent_1", content="Found paper on neural nets")

# Agent 2's memories (isolated)
memory.register_agent("agent_2", "Writing Assistant")
memory.add(agent_id="agent_2", content="User prefers technical writing")

# Retrieving agent_1's context doesn't include agent_2's memories
context = memory.retrieve(agent_id="agent_1", query="What do I know?")
# Result: Only "Found paper on neural nets"
```

### Memory Isolation Between Users

**Graph Query Enforces Isolation:**
```cypher
# All queries filtered by agent_id
MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory)
RETURN m
```

**No way for one agent to accidentally access another's memories** unless explicitly shared.

### Cross-Agent Sharing

**Share Function:**
```python
def share(
    self,
    from_agent_id: str,  # Source agent
    to_agent_id: str,    # Target agent
    memory_ids: List[str],
    permission: str = "read"  # "read" or "write"
) -> int  # Number shared
```

**Database Operation:**
```cypher
MATCH (from:Agent {id: $from_agent_id})
MATCH (to:Agent {id: $to_agent_id})
MATCH (from)-[:CREATED]->(m:Memory {id: $memory_id})
MERGE (to)-[a:ACCESSED {
    at: datetime(),
    permission: $permission,
    shared_by: $from_agent_id
}]->(m)
```

**Retrieve Shared Memories:**
```python
def get_shared_memories(agent_id: str, limit: int = 10):
    """Get memories other agents shared with me."""
    # Query ACCESSED relationships
```

**User Context Management in API:**
```python
# Each request specifies agent_id
@router_memories.post("")
async def add_memory(
    agent_id: str = Query(...),  # User/agent identifier
    content: str = Query(...),
    ...
):
    # All operations scoped to this agent_id
    memory = memory_graph.add(agent_id=agent_id, ...)
```

---

## 9. API Endpoints

### Complete Endpoint List

#### **AGENTS** - `/agents`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/agents?agent_id=...&name=...&agent_type=...` | Register new agent |
| GET | `/agents/{agent_id}` | Get agent details |
| GET | `/agents/{agent_id}/stats` | Get agent statistics |

**Agent Registration Example:**
```http
POST /agents?agent_id=research_001&name=Research Assistant&agent_type=research
Response: {
  "id": "research_001",
  "name": "Research Assistant",
  "type": "research",
  "created_at": "2025-01-28T10:00:00",
  "metadata": {}
}
```

#### **MEMORIES** - `/memories`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/memories?agent_id=...&content=...` | Add memory |
| GET | `/memories/{memory_id}` | Get specific memory |
| GET | `/memories/agent/{agent_id}` | Get all agent memories |
| GET | `/memories/graph?agent_id=...` | Get graph for visualization |
| POST | `/memories/retrieve` | Query with natural language |

**Add Memory Example:**
```http
POST /memories?agent_id=research_001&content=User researches neural networks&memory_type=fact&importance=0.8
Response: {
  "id": "mem_abc123...",
  "content": "User researches neural networks",
  "memory_type": "fact",
  "importance": 0.8,
  "created_at": "2025-01-28T10:00:00",
  "metadata": {}
}
```

**Retrieve Memory Example:**
```http
POST /memories/retrieve?agent_id=research_001&query=What do you know about the user?&limit=5
Response: {
  "memories": [
    {
      "memory": { ... },
      "agent_name": "Research Assistant",
      "relevance_score": 0.85
    }
  ],
  "total_found": 5,
  "query": "What do you know about the user?",
  "retrieved_at": "2025-01-28T10:00:00"
}
```

**Get Graph Data Example:**
```http
GET /memories/graph?agent_id=research_001
Response: {
  "nodes": [
    {
      "id": "mem_abc123",
      "label": "User researches neural networks...",
      "type": "fact",
      "importance": 0.8
    }
  ],
  "edges": [
    {
      "source": "mem_abc123",
      "target": "mem_def456",
      "type": "relates",
      "strength": 0.7
    }
  ],
  "agent_id": "research_001",
  "stats": {
    "total_nodes": 12,
    "total_edges": 8
  }
}
```

#### **CONTEXTS** - `/contexts`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/contexts?name=...` | Create context/session |

**Create Context Example:**
```http
POST /contexts?name=Literature Review - Neural Networks&summary=Reviewing recent papers
Response: {
  "id": "ctx_abc123...",
  "name": "Literature Review - Neural Networks",
  "started_at": "2025-01-28T10:00:00",
  "ended_at": null,
  "summary": "Reviewing recent papers",
  "metadata": {}
}
```

#### **RELATIONSHIPS** - `/relationships`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/relationships` | Create relationship |
| GET | `/relationships/{memory_id}` | Get related memories |

**Create Relationship Example:**
```http
POST /relationships?from_memory_id=mem_abc&to_memory_id=mem_def&relation_type=supports&strength=0.8
Response: {
  "from_memory_id": "mem_abc",
  "to_memory_id": "mem_def",
  "type": "supports",
  "strength": 0.8,
  "reason": null,
  "created_at": "2025-01-28T10:00:00"
}
```

**Get Related Memories Example:**
```http
GET /relationships/mem_abc?max_depth=2&min_strength=0.5
Response: [
  {
    "memory": { ... },
    "relevance_score": 0.75
  }
]
```

#### **SHARING** - `/sharing`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/sharing/grant` | Share memories between agents |
| GET | `/sharing/{agent_id}` | Get memories shared with agent |

**Share Memories Example:**
```http
POST /sharing/grant?from_agent_id=research_001&to_agent_id=writing_001&memory_ids=mem_abc,mem_def&permission=read
Response: {
  "shared_count": 2,
  "from_agent_id": "research_001",
  "to_agent_id": "writing_001",
  "permission": "read"
}
```

**Get Shared Memories Example:**
```http
GET /sharing/writing_001?limit=20
Response: [
  {
    "memory": { ... },
    "agent_name": "Research Assistant"
  }
]
```

#### **CHAT** - `/chat` (Frontend Integration)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/chat` | Chat with agent |

**Chat Example:**
```http
POST /chat
{
  "agent_id": "research-agent",
  "message": "What do you know about neural networks?"
}

Response: {
  "response": "I remember you're researching neural networks. Based on our previous discussions, I know you're interested in transformer architectures specifically...",
  "agent_id": "research-agent",
  "context_memories": "3"
}
```

#### **HEALTH** - `/health`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Check API health |

---

## 10. Integration Points

### LangChain Integration

**Integration File:** [memgraph/integrations/langchain_agent.py](memgraph/integrations/langchain_agent.py)

#### MemGraphMemory - LangChain Memory Backend

**Class Definition:**
```python
class MemGraphMemory(BaseChatMemory):
    """LangChain memory backend using MemGraph for persistence."""
    
    memory_graph: Any                    # MemoryGraph instance
    agent_id: str                        # Agent identifier
    session_id: Optional[str]            # Optional session ID
    return_messages: bool = True         # Return message objects
    context_window_size: int = 5         # Max memories to retrieve
    min_importance: float = 0.5          # Minimum importance threshold
```

**Key Methods:**

1. **save_context()** - Store conversation to MemGraph
   ```python
   def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]):
       """Save human and AI messages as memories with relationships."""
       # Stores human message
       human_memory = memory_graph.add(
           agent_id=self.agent_id,
           content=f"User: {input_str}",
           memory_type=MemoryType.CONVERSATION,
           importance=0.8
       )
       
       # Stores AI response
       ai_memory = memory_graph.add(
           agent_id=self.agent_id,
           content=f"Assistant: {output_str}",
           memory_type=MemoryType.CONVERSATION,
           importance=0.8
       )
       
       # Creates relationship
       memory_graph.relate(
           from_memory_id=human_memory.id,
           to_memory_id=ai_memory.id,
           relation_type="RESPONSE_TO",
           strength=0.9
       )
   ```

2. **load_memory_variables()** - Retrieve context for prompt
   ```python
   def load_memory_variables(self, inputs: Dict[str, Any]):
       """Retrieve relevant memories for current query."""
       context = memory_graph.retrieve(
           agent_id=self.agent_id,
           query=inputs.get("input", ""),
           limit=self.context_window_size,
           min_importance=self.min_importance
       )
       memory_text = self._format_memories(context)
       return {self.memory_variables[0]: memory_text}
   ```

3. **clear()** - Clear session memory
   ```python
   def clear(self) -> None:
       """Clear memory for this agent."""
       # Note: Doesn't delete from MemGraph (preserves audit trail)
       pass
   ```

#### MemGraphToolkit - LangChain Tools

**Tools Available:**

1. **add_memory()** - Agent can add memories
   ```python
   def add_memory(
       self,
       content: str,
       memory_type: str = "fact",
       importance: float = 0.7,
       tags: Optional[List[str]] = None
   ) -> Dict[str, Any]
   ```

2. **retrieve_memories()** - Agent can query memories
   ```python
   def retrieve_memories(
       self,
       query: str,
       limit: int = 5,
       min_importance: float = 0.5
   ) -> Dict[str, Any]
   ```

### Expected Usage Workflow

**Step 1: Initialize Memory**
```python
from memgraph.integrations.langchain_agent import MemGraphMemory
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

memory = MemGraphMemory(
    agent_id="research_assistant",
    session_id="session_123",
    context_window_size=10
)
```

**Step 2: Create Agent**
```python
llm = OpenAI()
agent = initialize_agent(
    tools=[...],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)
```

**Step 3: Run Agent**
```python
# First interaction
response1 = agent.run("Tell me about neural networks")
# Stores conversation in MemGraph

# Second interaction (has access to previous memories)
response2 = agent.run("Based on what you know, explain backpropagation")
# Retrieves context from MemGraph
```

### Example Integration

**File:** [examples/langchain_integration.py](examples/langchain_integration.py)

Contains examples for:
1. Research agent with memory
2. Conversational agent with context
3. Multi-turn conversation with persistent state

---

## 11. Testing & Examples

### Test Files

| File | Purpose | Status |
|------|---------|--------|
| [test_agent_state.py](test_agent_state.py) | Diagnostic script for agent state | ✅ Implemented |
| [test_backend_manual.py](test_backend_manual.py) | Manual backend testing | ⚠️ Minimal |
| [test_chat_debug.py](test_chat_debug.py) | Chat endpoint debugging | ⚠️ Minimal |
| [test_quick_memory.py](test_quick_memory.py) | Quick memory operations | ⚠️ Minimal |

### Test Agents State Script

**[test_agent_state.py](test_agent_state.py) - Diagnostics:**
```python
#!/usr/bin/env python3
"""Diagnostic script to check agent state and memories."""

# Checks:
# 1. Agent registration
# 2. Memory retrieval
# 3. Query functionality
# 4. Memory statistics

# Run: python test_agent_state.py
```

**Example Output:**
```
============================================================
🔍 AGENT STATE DIAGNOSTIC
============================================================

✅ Agent found: Agent(id='test-agent', name='Test Agent', type='general')

============================================================
📝 MEMORIES FOR test-agent
============================================================

1. PREFERENCE
   Content: User prefers brief answers
   Importance: 0.8
   Created: 2025-01-28T10:00:00

2. FACT
   Content: User is researching neural networks
   Importance: 0.7
   Created: 2025-01-28T10:30:00
```

### Example Integration Script

**[examples/langchain_integration.py](examples/langchain_integration.py) - Examples:**

```python
# Example 1: Research Agent with Memory
def example_research_agent():
    """Create research agent that remembers between conversations."""
    memory = create_langchain_memory(
        agent_id="research_agent",
        session_id="research_20231031_001",
        context_window_size=10
    )
    
    agent = initialize_agent(
        tools=[search_wikipedia],
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True
    )
    
    # First query
    response1 = agent.run("What are neural networks?")
    
    # Second query (remembers context)
    response2 = agent.run("Explain backpropagation")

# Example 2: Multi-turn Conversation
def example_conversational_agent():
    """Conversational agent with persistent context."""
    memory = create_langchain_memory(
        agent_id="chat_agent",
        session_id="chat_20231031_001"
    )
    
    # Multiple turns in conversation
    for user_input in ["Hi, I'm working on AI", "Tell me about RL", "Any books?"]:
        response = agent.run(user_input)
```

### Unit Tests

**Status:** ❌ **NO UNIT TESTS FOUND**

**Missing:**
- ❌ pytest test suite
- ❌ Neo4j fixtures for testing
- ❌ Mock tests for API endpoints
- ❌ Integration tests
- ❌ Edge case tests

**Could Add:**
```python
# Example structure (not currently present):
import pytest
from memgraph.core.memory import MemoryGraph

@pytest.fixture
def memory_graph():
    """Create test MemoryGraph with mock Neo4j."""
    return MemoryGraph(uri="bolt://localhost:7687")

def test_add_memory(memory_graph):
    """Test adding a memory."""
    memory = memory_graph.add(
        agent_id="test",
        content="Test content"
    )
    assert memory.id is not None

def test_retrieve_memory(memory_graph):
    """Test retrieving memories."""
    context = memory_graph.retrieve(
        agent_id="test",
        query="Find test"
    )
    assert len(context.memories) > 0
```

---

## 12. Missing/TODO Items

### Explicit TODOs in Code

**1. Main API - [memgraph/api/main.py](memgraph/api/main.py#L104)**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    ...
)
```
- Currently allows all origins
- Should restrict to specific domains in production

**2. Memory Retrieval - [memgraph/core/memory.py](memgraph/core/memory.py#L241)**
```python
# TODO: Add semantic search ranking when vector store is integrated
# For now, return by recency and importance
memories.sort(
    key=lambda m: (m.memory.importance, m.memory.created_at),
    reverse=True
)
```
- Currently no semantic similarity ranking
- Waiting for vector embedding store

### Incomplete Features

| Feature | Status | Notes |
|---------|--------|-------|
| **Entity Extraction** | ❌ NOT IMPLEMENTED | No NLP pipeline for auto entity recognition |
| **Semantic Search** | ❌ PARTIAL | Sorting only, no embeddings/vector store |
| **Conflict Detection** | ❌ NOT IMPLEMENTED | Can mark relationships as "contradicts" but no auto detection |
| **Coreference Resolution** | ❌ NOT IMPLEMENTED | No pronoun resolution |
| **Time-based Decay** | ❌ NOT IMPLEMENTED | No exponential recency weighting |
| **Duplicate Detection** | ❌ NOT IMPLEMENTED | Could store duplicate memories |
| **Unit Tests** | ❌ NOT IMPLEMENTED | No test suite |
| **Version History** | ❌ NOT IMPLEMENTED | No full audit trail |
| **Entity Linking** | ❌ NOT IMPLEMENTED | No external database integration |
| **Relationship Extraction** | ⚠️ PARTIAL | Manual only, no NLP extraction |

### Known Limitations

1. **No Vector Embeddings**
   - Current retrieval is keyword/recency based
   - Semantic similarity not supported
   - Would need integration with embedding model + vector DB

2. **No Automatic Entity Recognition**
   - Must manually specify entities
   - No NLP pipeline for extraction
   - No deduplication of entity references

3. **No Automatic Relationship Extraction**
   - Relationships created manually via API
   - No inference from text content
   - No relationship discovery

4. **Limited Conflict Resolution**
   - Can mark contradictions
   - No automatic detection
   - No resolution strategy

5. **No Production Security**
   - CORS allows all origins
   - No authentication mechanism
   - No rate limiting

6. **Minimal Testing**
   - No unit test suite
   - Manual testing only
   - No CI/CD integration

7. **No Caching**
   - Every query hits database
   - No query result caching
   - No agent state caching

### Roadmap Notes

From README.md:
```
## Roadmap
- [x] Core architecture design
- [ ] Neo4j integration           # In progress
- [ ] Basic memory storage/retrieval   # Implemented
- [ ] LangChain integration       # Implemented
- [ ] Cross-agent sharing         # Implemented
- [ ] Visual graph viewer         # Partially implemented
- [ ] Documentation              # In progress
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Components: ChatInterface, GraphView, AgentDetails  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────┬──────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Routes Layer (routes.py)                          │    │
│  │  - /agents, /memories, /contexts                   │    │
│  │  - /relationships, /sharing, /chat                 │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Business Logic (memory.py)                         │    │
│  │  - MemoryGraph class (main interface)               │    │
│  │  - register_agent(), add(), retrieve()              │    │
│  │  - share(), get_related()                           │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  LLM Integration (llm.py)                           │    │
│  │  - Google Gemini API calls                          │    │
│  │  - Prompt engineering                              │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────────┬─────────────────────────────────────┘
                         │ Bolt Protocol
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Neo4j Database                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Node Types:                                       │    │
│  │  • Agent (with metadata)                           │    │
│  │  • Memory (with importance score)                  │    │
│  │  • Context (conversation grouping)                 │    │
│  │  • Entity (extracted entities)                     │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Relationships:                                    │    │
│  │  • CREATED (Agent → Memory)                        │    │
│  │  • RELATES_TO (Memory → Memory)                    │    │
│  │  • PART_OF (Memory → Context)                      │    │
│  │  • ACCESSED (Agent → Memory, sharing)              │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘

                    Integration Points
┌────────────────────────────────────────────────────────────┐
│  LangChain (langchain_agent.py)                             │
│  • MemGraphMemory - LangChain memory backend                │
│  • MemGraphToolkit - Agent-accessible tools                │
│  • Enables persistent context for LangChain agents         │
└────────────────────────────────────────────────────────────┘
```

---

## Summary

### What's Implemented ✅

1. **Core Architecture**
   - FastAPI REST API with dependency injection
   - Neo4j database with comprehensive schema
   - Pydantic models for validation
   - Clean separation of concerns (API → Logic → DB)

2. **Memory Operations**
   - Add memories with importance scoring
   - Retrieve memories with multi-filter support
   - Time-based queries
   - Type-based filtering
   - Basic recency/importance ranking

3. **Relationships**
   - Create explicit relationships between memories
   - Support 6 relationship types
   - Traverse relationship graphs (depth-limited)
   - Strength-based filtering

4. **Multi-Agent Support**
   - Agent registration and isolation
   - Cross-agent memory sharing
   - Permission-based access (read/write)
   - Per-agent statistics

5. **LangChain Integration**
   - BaseChatMemory implementation
   - Context loading from MemGraph
   - Conversation persistence
   - Agent toolkit with memory operations

6. **Utilities**
   - Health checks
   - Graph visualization data (ReactFlow format)
   - Agent statistics
   - Chat endpoint with LLM integration

### What's Missing ❌

1. **NLP Pipeline**
   - No automatic entity extraction
   - No coreference resolution
   - No relationship extraction from text
   - No named entity linking

2. **Advanced Search**
   - No semantic similarity (no embeddings)
   - No vector store integration
   - No full-text search
   - No query expansion

3. **Conflict Management**
   - No automatic conflict detection
   - No contradiction inference
   - No resolution strategies
   - No confidence scoring beyond importance

4. **Production Features**
   - No authentication
   - No rate limiting
   - CORS allows all origins
   - No caching mechanism

5. **Testing**
   - No unit tests
   - No integration tests
   - No test fixtures
   - Manual testing only

6. **Advanced Features**
   - No version history/audit trail
   - No temporal queries
   - No time decay for recency
   - No duplicate detection
   - No deduplication strategy

### Technology Stack

**Backend:**
- Python 3.8+
- FastAPI 0.104.1
- Uvicorn (ASGI server)
- Neo4j 5.14.1
- Pydantic 2.5.0

**Frontend:**
- Next.js 14.0
- React 18.2
- ReactFlow 11.10 (graph visualization)
- TypeScript 5.0
- TailwindCSS 3.3

**Integrations:**
- LangChain 0.1.0
- Google Generative AI (Gemini)
- Neo4j Python driver 5.14.1

**Development:**
- pytest 7.4.3
- black (code formatting)
- ruff (linting)

---

## Deployment

**Development Command:**
```bash
python -m uvicorn memgraph.api.main:app --reload
```

**Environment Variables Needed:**
```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=12345678
GOOGLE_API_KEY=<your-gemini-api-key>
GEMINI_API_KEY=<optional-alternative>
```

**Frontend:**
```bash
npm run dev
```

This completes the comprehensive technical analysis of the MemGraph codebase.
