# MemGraph REST API

Complete REST API for the MemGraph memory system. Provides HTTP endpoints for agent management, memory operations, context tracking, and cross-agent knowledge sharing.

## Quick Start

### 1. Start the API Server

```bash
# Using uvicorn directly
uvicorn memgraph.api.server:app --reload --port 8000

# Or using Python module
python -m memgraph.api.server
```

### 2. Access API Documentation

Open your browser and visit:
- **Interactive Docs (Swagger UI):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc
- **API Info:** http://localhost:8000

### 3. Check Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "MemGraph API",
  "version": "0.1.0"
}
```

---

## API Endpoints

### Agent Management

#### Register/Get Agent
```
POST /agents?agent_id=research_001&name=Research Assistant&agent_type=research
GET /agents/research_001
```

#### Agent Statistics
```
GET /agents/research_001/stats
```

Returns:
```json
{
  "agent_id": "research_001",
  "total_memories": 42,
  "average_importance": 0.75,
  "memory_types": {
    "fact": 15,
    "preference": 10,
    "observation": 17
  },
  "oldest_memory": "2025-10-28T14:30:00",
  "newest_memory": "2025-10-31T10:15:00"
}
```

---

### Memory Operations

#### Add Memory
```
POST /memories?agent_id=research_001&content=User prefers technical explanations&memory_type=preference&importance=0.8&context_id=ctx_123
```

Query Parameters:
- `agent_id` (required): Agent creating the memory
- `content` (required): Memory text (1-10000 chars)
- `memory_type` (optional): fact, preference, action, conversation, decision, observation (default: fact)
- `importance` (optional): 0.0-1.0 (default: 0.5)
- `context_id` (optional): Link to context/session

Returns:
```json
{
  "id": "mem_abc123def456",
  "content": "User prefers technical explanations",
  "memory_type": "preference",
  "importance": 0.8,
  "created_at": "2025-10-31T10:15:00",
  "updated_at": "2025-10-31T10:15:00",
  "metadata": {}
}
```

#### Get Memory
```
GET /memories/mem_abc123def456
```

#### Get Agent's Memories
```
GET /memories/agent/research_001?limit=20&memory_types=fact,preference&time_range_days=30
```

Query Parameters:
- `limit`: 1-100 (default: 10)
- `memory_types`: Comma-separated types (optional)
- `time_range_days`: Only recent memories (optional)

---

### Context/Session Management

#### Create Context
```
POST /contexts?name=Literature Review - Neural Networks&summary=Reviewing recent papers on transformers
```

Returns:
```json
{
  "id": "ctx_abc123",
  "name": "Literature Review - Neural Networks",
  "started_at": "2025-10-31T10:15:00",
  "ended_at": null,
  "summary": "Reviewing recent papers on transformers",
  "metadata": {}
}
```

---

### Retrieval (Core Query Operation)

#### Retrieve Relevant Context
```
POST /memories/retrieve?agent_id=research_001&query=What do I know about the user?&limit=10&min_importance=0.5&time_range_days=30
```

Query Parameters:
- `agent_id` (required): Agent making query
- `query` (required): Natural language query
- `limit` (optional): 1-50 (default: 5)
- `time_range_days` (optional): Filter by recency
- `memory_types` (optional): Comma-separated types
- `min_importance` (optional): 0.0-1.0 (default: 0.0)

Returns:
```json
{
  "memories": [
    {
      "memory": {
        "id": "mem_001",
        "content": "User is PhD student working on GNNs",
        "memory_type": "fact",
        "importance": 0.9,
        "created_at": "2025-10-28T14:30:00",
        "updated_at": "2025-10-28T14:30:00"
      },
      "agent_name": "Research Assistant",
      "relevance_score": 0.95
    },
    {
      "memory": {
        "id": "mem_002",
        "content": "User prefers technical explanations with code examples",
        "memory_type": "preference",
        "importance": 0.8,
        "created_at": "2025-10-29T09:00:00",
        "updated_at": "2025-10-29T09:00:00"
      },
      "agent_name": "Research Assistant",
      "relevance_score": 0.85
    }
  ],
  "total_found": 2,
  "query": "What do I know about the user?",
  "retrieved_at": "2025-10-31T10:15:00"
}
```

---

### Memory Relationships

#### Create Relationship
```
POST /relationships?from_memory_id=mem_001&to_memory_id=mem_002&relation_type=supports&strength=0.8&reason=Both discuss user research background
```

Relation Types:
- `supports`: Memory A supports/reinforces B
- `contradicts`: Memory A contradicts B
- `elaborates`: Memory A adds detail to B
- `follows`: Memory A follows B chronologically
- `relates_to`: General relationship
- `supersedes`: Memory A replaces/updates B

Returns:
```json
{
  "from_memory_id": "mem_001",
  "to_memory_id": "mem_002",
  "type": "supports",
  "strength": 0.8,
  "reason": "Both discuss user research background",
  "created_at": "2025-10-31T10:15:00"
}
```

#### Get Related Memories
```
GET /relationships/mem_001?max_depth=2&min_strength=0.5
```

Query Parameters:
- `max_depth`: 1-3 (default: 2)
- `min_strength`: 0.0-1.0 (default: 0.0)

Returns:
```json
[
  {
    "memory": {
      "id": "mem_002",
      "content": "User prefers technical explanations",
      "memory_type": "preference",
      "importance": 0.8,
      "created_at": "2025-10-29T09:00:00",
      "updated_at": "2025-10-29T09:00:00"
    },
    "relevance_score": 0.8
  }
]
```

---

### Cross-Agent Sharing

#### Share Memories
```
POST /sharing/grant?from_agent_id=research_001&to_agent_id=writing_001&memory_ids=mem_001,mem_002,mem_003&permission=read
```

Query Parameters:
- `from_agent_id` (required): Source agent
- `to_agent_id` (required): Target agent
- `memory_ids` (required): Comma-separated memory IDs
- `permission` (optional): read or write (default: read)

Returns:
```json
{
  "shared_count": 3,
  "from_agent_id": "research_001",
  "to_agent_id": "writing_001",
  "permission": "read"
}
```

#### Get Shared Memories
```
GET /sharing/writing_001?limit=20
```

Returns:
```json
[
  {
    "memory": {
      "id": "mem_001",
      "content": "User is PhD student",
      "memory_type": "fact",
      "importance": 0.9,
      "created_at": "2025-10-28T14:30:00",
      "updated_at": "2025-10-28T14:30:00"
    },
    "agent_name": "Research Assistant"
  }
]
```

---

## Error Handling

All endpoints return standard HTTP status codes:

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (invalid parameters) |
| 404 | Not found |
| 500 | Internal server error |
| 503 | Service unavailable (database not connected) |

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

Examples:
```
❌ Agent not found
GET /agents/nonexistent_id
→ 404: {"detail": "Agent nonexistent_id not found"}

❌ Invalid importance score
POST /memories?importance=1.5
→ 400: {"detail": "Ensure this value is less than or equal to 1."}

❌ Database not connected
GET /health
→ 503: {"detail": "MemoryGraph service not initialized"}
```

---

## Python Client Usage

```python
import requests

BASE_URL = "http://localhost:8000"

# Register agent
agent = requests.post(
    f"{BASE_URL}/agents",
    params={
        "agent_id": "research_001",
        "name": "Research Assistant",
        "agent_type": "research"
    }
).json()

# Add memory
memory = requests.post(
    f"{BASE_URL}/memories",
    params={
        "agent_id": "research_001",
        "content": "User prefers technical explanations",
        "memory_type": "preference",
        "importance": 0.8
    }
).json()

# Retrieve context
context = requests.post(
    f"{BASE_URL}/memories/retrieve",
    params={
        "agent_id": "research_001",
        "query": "How should I explain AI concepts?",
        "limit": 5,
        "min_importance": 0.5
    }
).json()

# Print results
for mem_response in context["memories"]:
    mem = mem_response["memory"]
    print(f"- {mem['content']} (importance: {mem['importance']})")
```

---

## Environment Variables

Configure via `.env` file:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=memgraph123
```

---

## Running Tests

Test the API with the included test script:

```bash
python test_api_endpoints.py
```

---

## API Architecture

```
FastAPI App
├── main.py              # App initialization, health checks
├── routes.py            # All endpoint implementations
├── server.py            # Entry point, uvicorn runner
└── utils.py             # Shared utilities (logging, error handling)

Integration:
├── memgraph.core.memory        ← MemoryGraph API
├── memgraph.core.graph         ← Neo4j operations
└── memgraph.core.models        ← Data validation (Pydantic)
```

---

## Performance Tips

1. **Batch Operations:** If adding many memories, consider batching requests
2. **Filtering:** Use `memory_types` and `time_range_days` to reduce query results
3. **Importance Threshold:** Set `min_importance` to filter low-value memories
4. **Relationship Depth:** Limit `max_depth` in relationship queries to 2-3

---

## Next Steps

- ✅ FastAPI REST API implemented
- ⬜ LangChain integration
- ⬜ Vector embeddings for semantic search
- ⬜ Advanced filtering and aggregation
- ⬜ WebSocket support for real-time updates

---

**Version:** 0.1.0  
**Last Updated:** October 31, 2025
