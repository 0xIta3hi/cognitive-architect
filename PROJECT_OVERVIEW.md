# MemGraph Development Context for GitHub Copilot

## Project Overview
Building **MemGraph** - an open-source AI agent memory system using knowledge graphs for persistent context and cross-agent knowledge sharing.

**Tech Stack:**
- Neo4j Community Edition (graph database)
- Python 3.10+ with FastAPI
- LangChain/LangGraph for agent integration
- Pydantic for data validation

**Goal:** Ship MVP in 14 days (started Oct 29, 2025). Target: 3 university CS professors using it within 30 days of launch.

---

## ✅ COMPLETED (Days 1-2)

### 1. Environment Setup ✓
- Neo4j Desktop installed and running (bolt://localhost:7687)
- Python virtual environment created
- Dependencies installed: neo4j==5.14.1, fastapi==0.104.1, langchain==0.1.0, pydantic==2.5.0
- Database schema created (constraints and indexes)

### 2. Project Structure ✓
```
memgraph/
├── memgraph/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py        ✅ DONE
│   │   ├── graph.py         ✅ DONE  
│   │   └── memory.py        ✅ DONE
│   ├── api/                 ⬜ TODO
│   ├── integrations/        ⬜ TODO
│   └── utils/               ⬜ TODO
├── tests/
├── examples/
├── .env
└── requirements.txt
```

### 3. Core Library Implementation ✓

**File: `memgraph/core/models.py` (380 lines)**
- Pydantic models: Agent, Memory, Context, Entity
- Enums: MemoryType, RelationType, EntityType
- Request/Response models: AddMemoryRequest, RetrieveContextRequest, ShareMemoryRequest
- Full validation with field validators

**File: `memgraph/core/graph.py` (550 lines)**
- Class: `MemGraphDB` - handles all Neo4j operations
- Agent operations: create_agent, get_agent, get_or_create_agent
- Memory operations: add_memory, get_memory, get_agent_memories
- Context operations: create_context
- Relationship operations: create_memory_relationship, get_related_memories
- Cross-agent sharing: share_memory, get_shared_memories
- **Important:** Metadata serialized as JSON strings (Neo4j limitation)

**File: `memgraph/core/memory.py` (460 lines)**
- Class: `MemoryGraph` - main developer-facing API
- Clean interface: `add()`, `retrieve()`, `relate()`, `share()`
- Agent registration: `register_agent()`
- Context management: `create_context()`
- Statistics: `get_stats()`

### 4. Neo4j Schema ✓
```cypher
// Nodes: Agent, Memory, Context, Entity
// Relationships: CREATED, ACCESSED, PART_OF, RELATES_TO, MENTIONS, SHARES_WITH, SUPERSEDES

// Constraints and indexes created for performance
```

### 5. Testing ✓
- Basic workflow test created: `test_basic_usage.py`
- Tests: agent registration, memory creation, retrieval, relationships, cross-agent sharing
- **Status:** Core library working, test passes

---

## 🚧 IN PROGRESS / BLOCKED

### Current Issue: RESOLVED
- ~~Metadata serialization error~~ ✅ Fixed (using json.dumps/loads)
- Core library now fully functional

---

## 📋 TODO - NEXT STEPS (Days 3-7)

### Phase 1: FastAPI REST Endpoints (Priority 1)
**Goal:** Allow HTTP access to MemGraph for any client

**Files to Create:**

1. **`memgraph/api/__init__.py`**
   - Empty init file

2. **`memgraph/api/main.py`** (~200 lines)
   - FastAPI app initialization
   - Dependency injection for MemoryGraph instance
   - Health check endpoint: `GET /health`
   - CORS middleware for web clients

3. **`memgraph/api/routes.py`** (~300 lines)
   - `POST /agents` - Register agent
   - `GET /agents/{agent_id}` - Get agent
   - `POST /memories` - Add memory
   - `GET /memories/{memory_id}` - Get memory
   - `POST /memories/retrieve` - Retrieve context (main endpoint)
   - `GET /agents/{agent_id}/memories` - List agent memories
   - `POST /memories/relate` - Create relationship
   - `GET /memories/{memory_id}/related` - Get related memories
   - `POST /memories/share` - Share memories between agents
   - `GET /agents/{agent_id}/shared` - Get shared memories
   - `POST /contexts` - Create context
   - `GET /agents/{agent_id}/stats` - Get agent statistics

4. **`memgraph/api/models.py`** (~100 lines)
   - API-specific request/response models (if needed beyond core models)
   - Error response schemas

**Example endpoint structure:**
```python
@router.post("/memories", response_model=MemoryResponse)
async def add_memory(
    request: AddMemoryRequest,
    memory_graph: MemoryGraph = Depends(get_memory_graph)
):
    memory = memory_graph.add(...)
    return MemoryResponse(memory=memory)
```

**Test with:**
```bash
uvicorn memgraph.api.main:app --reload
# Access: http://localhost:8000/docs (Swagger UI)
```

---

### Phase 2: LangChain Integration (Priority 2)
**Goal:** Drop-in memory for LangChain agents (2-3 lines to add memory)

**Files to Create:**

1. **`memgraph/integrations/__init__.py`**
   - Export main classes

2. **`memgraph/integrations/langchain_memory.py`** (~200 lines)
   - Custom `BaseChatMessageHistory` subclass
   - Implement: `add_message()`, `clear()`, `messages` property
   - Auto-convert chat messages to Memory objects
   - Integration with MemoryGraph.add() and retrieve()

3. **`examples/langchain_integration.py`** (~80 lines)
   - Example: LangChain agent with MemGraph memory
   - Show: conversation with persistent context

**Target Usage:**
```python
from memgraph.integrations import MemGraphChatHistory
from langchain.agents import AgentExecutor

memory = MemGraphChatHistory(
    agent_id="my_agent",
    neo4j_uri="bolt://localhost:7687"
)

agent = AgentExecutor(..., memory=memory)
```

---

### Phase 3: Examples & Documentation (Priority 3)

**Files to Create:**

1. **`examples/basic_usage.py`** (~50 lines)
   - Simple agent memory storage/retrieval

2. **`examples/cross_agent_sharing.py`** (~80 lines)
   - Research assistant shares knowledge with writing assistant

3. **`examples/research_workflow.py`** (~120 lines)
   - University research use case (your target audience)
   - Track papers, experiments, insights

4. **`README.md`** (~300 lines)
   - Quick start guide
   - Installation instructions
   - Usage examples
   - Architecture diagram
   - Comparison with Mem0/Zep/Letta

5. **`docs/API.md`** (~200 lines)
   - All API endpoints documented
   - Request/response examples

---

## 🎯 MVP Feature Checklist

**Week 1 (Days 1-7):**
- [x] Core memory system (Neo4j + Python library)
- [x] Basic data models and validation
- [x] Graph operations (CRUD + relationships)
- [ ] FastAPI REST endpoints ← **NEXT**
- [ ] LangChain integration
- [ ] Basic examples

**Week 2 (Days 8-14):**
- [ ] Cross-agent memory sharing (already built, need examples)
- [ ] Temporal queries (filter by date ranges)
- [ ] Simple web UI for graph visualization (D3.js)
- [ ] Documentation and README
- [ ] PyPI package preparation

**Out of Scope (Post-MVP):**
- Vector search integration (Qdrant/Weaviate)
- Advanced temporal reasoning
- Multi-graph support
- Enterprise features

---

## 🔑 Key Design Decisions

1. **Metadata as JSON strings:** Neo4j doesn't support nested maps, so all `metadata` fields are serialized with `json.dumps()` and deserialized with `json.loads()`

2. **Class naming:** Main class is `MemGraphDB` (not GraphDatabase to avoid Neo4j driver conflict)

3. **Memory types:** preference, fact, action, conversation, decision, observation

4. **Relationship types:** supports, contradicts, elaborates, follows, relates_to, supersedes

5. **Importance scoring:** 0.0-1.0 float for ranking memories during retrieval

6. **Context grouping:** Memories can belong to Context (session/conversation)

7. **Agent-centric:** Everything tied to agents (creator/accessor)

---

## 🐛 Known Issues / Technical Debt

1. **No vector search yet:** Retrieval currently by recency + importance only (semantic search = future)
2. **No authentication:** FastAPI endpoints will be open (add JWT in production)
3. **No rate limiting:** Add in production
4. **Basic error handling:** Need more robust error messages
5. **No async support:** All operations are synchronous (consider async Neo4j driver later)

---

## 💡 Coding Conventions

- **Type hints everywhere:** Python 3.10+ style
- **Docstrings:** Google style with Args/Returns/Examples
- **Error handling:** Raise ValueError/ConnectionError with clear messages
- **Validation:** Pydantic models handle all validation
- **IDs:** Auto-generated with uuid.uuid4().hex (e.g., `mem_abc123def456`)
- **Timestamps:** UTC datetime, converted to ISO strings for Neo4j

---

## 🚀 Immediate Next Task

**Create the FastAPI layer** so MemGraph can be accessed over HTTP:

1. Start with `memgraph/api/main.py` - basic FastAPI app setup
2. Then `memgraph/api/routes.py` - all REST endpoints
3. Test with Swagger UI at http://localhost:8000/docs
4. Verify all CRUD operations work via HTTP

**Success Criteria:**
- All core library functions accessible via REST API
- Swagger docs auto-generated and complete
- Can test with curl/Postman
- Returns proper HTTP status codes (200, 201, 404, 500)

---

## 📚 Reference Links

- Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/current/
- FastAPI Docs: https://fastapi.tiangolo.com/
- LangChain Memory: https://python.langchain.com/docs/modules/memory/
- Pydantic V2: https://docs.pydantic.dev/latest/

---

## 🎓 Target Users (University Focus)

**Use Case:** CS professors running AI research agents need:
- Memory of past experiments/results
- Collaboration between different research agents
- Citation tracking and paper references
- Reproducible research workflows

**Differentiator:** Research-optimized features (entities for papers, version control for memory evolution)

---

## ⚡ Development Environment

```bash
# Activate venv
source venv/bin/activate

# Start Neo4j Desktop (must be running)
# Open: http://localhost:7474

# Run tests
python test_basic_usage.py

# Start API (when ready)
uvicorn memgraph.api.main:app --reload

# Format code
black memgraph/
ruff check memgraph/
```

**Environment Variables (.env):**
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=memgraph123
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=DEBUG
```

---

## 🎯 Success Metrics

**MVP Launch (Day 14):**
- [ ] Core library published to PyPI
- [ ] FastAPI server deployable
- [ ] LangChain integration working
- [ ] 3 complete examples
- [ ] README with quick start

**Post-Launch (Day 30):**
- [ ] 3 university professors using it
- [ ] GitHub repo public with docs
- [ ] Community feedback collected

---

**STATUS:** Core library complete and tested. Ready to build FastAPI REST layer next.

**BLOCKERS:** None currently.

**QUESTIONS FOR YOU (GitHub Copilot):**
1. Generate FastAPI app structure with dependency injection for MemoryGraph
2. Create all REST endpoints following the core library API
3. Add proper error handling and HTTP status codes
4. Include request/response examples in docstrings