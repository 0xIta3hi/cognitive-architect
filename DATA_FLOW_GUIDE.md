# Data Flow & Architecture Diagrams

## 1. Overall System Architecture

```
╔══════════════════════════════════════════════════════════════════════════╗
║                           USER INTERFACE                                  ║
║                                                                            ║
║  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       ║
║  │ ChatInterface    │  │ GraphView        │  │ AgentDetails     │       ║
║  │ (Chat Tab)       │  │ (Graph Tab)      │  │ (Info Tab)       │       ║
║  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘       ║
║           │                     │                     │                   ║
║           └─────────────────────┼─────────────────────┘                   ║
║                                 │                                         ║
║                    memgraph.ts (API Client)                               ║
║                 (Makes HTTP requests to backend)                          ║
║                                 │                                         ║
╠═════════════════════════════════╪═════════════════════════════════════════╣
║                                 ▼                                         ║
║                      FASTAPI BACKEND SERVER                               ║
║                    (uvicorn on port 8000)                                 ║
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │                        routes.py                                 │   ║
║  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   ║
║  │  │ /agents      │  │ /memories    │  │ /chat        │            │   ║
║  │  │ endpoints    │  │ endpoints    │  │ endpoint     │            │   ║
║  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │   ║
║  │         │                 │                 │                    │   ║
║  │         └─────────────────┼─────────────────┘                    │   ║
║  │                           │                                       │   ║
║  │                 memory.py (Business Logic)                        │   ║
║  │                 MemoryGraph class                                 │   ║
║  │          .add(), .retrieve(), .relate(), etc.                    │   ║
║  │                           │                                       │   ║
║  │                 graph.py (Database Layer)                         │   ║
║  │            Neo4j query execution                                  │   ║
║  │          .add_memory(), .get_related(), etc.                     │   ║
║  └──────────────────────────┬───────────────────────────────────────┘   ║
║                             │                                             ║
╠═════════════════════════════╪═════════════════════════════════════════════╣
║                             ▼                                             ║
║                      NEO4J DATABASE                                       ║
║                   (Knowledge Graph Storage)                               ║
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │  Agents (Nodes)                                                  │   ║
║  │  ├─ Agent: research_assistant                                    │   ║
║  │  └─ Agent: writing_assistant                                     │   ║
║  │                                                                   │   ║
║  │  Relationships (Edges)                                           │   ║
║  │  ├─ CREATED: Agent -> Memory                                     │   ║
║  │  ├─ RELATES_TO: Memory -> Memory                                 │   ║
║  │  ├─ PART_OF: Memory -> Context                                   │   ║
║  │  └─ ACCESSED: Agent -> Memory (shared)                           │   ║
║  │                                                                   │   ║
║  │  Memories (Nodes)                                                │   ║
║  │  ├─ Memory: "User prefers concise answers"                       │   ║
║  │  ├─ Memory: "User is researching neural nets"                    │   ║
║  │  └─ ... (thousands of memories)                                  │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Request Flow - Adding a Memory

### Scenario: User types "Remember John is my boss"

```
┌─ FRONTEND (React Component) ─────────────────────────────────────┐
│                                                                    │
│  User types: "Remember John is my boss"                          │
│  Clicks: "Add Memory" button                                     │
│                                                                    │
│  Component: ChatInterface.tsx                                    │
│    └─> memgraphClient.addMemory({                               │
│           agent_id: "research_001",                             │
│           content: "John is my boss",                           │
│           memory_type: "fact",                                  │
│           importance: 0.8                                       │
│        })                                                        │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP POST /memories
                             │ {agent_id, content, memory_type, importance}
                             ▼
┌─ API LAYER (fastapi/routes.py) ──────────────────────────────────┐
│                                                                    │
│  @router_memories.post("")                                       │
│  async def add_memory(                                           │
│      agent_id: str,                                             │
│      content: str,                                              │
│      memory_type: str,                                          │
│      importance: float,                                         │
│      memory_graph: MemoryGraph = Depends(get_memory_graph)      │
│  ):                                                             │
│      try:                                                        │
│          memory = memory_graph.add(                             │
│              agent_id=agent_id,                                 │
│              content=content,                                   │
│              memory_type=memory_type,                           │
│              importance=importance                              │
│          )                                                       │
│          return memory                                           │
│      except Exception as e:                                     │
│          raise HTTPException(...)                               │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Calls memory_graph.add(...)
                             ▼
┌─ BUSINESS LOGIC (core/memory.py) ────────────────────────────────┐
│                                                                    │
│  class MemoryGraph:                                              │
│      def add(self, agent_id, content, memory_type, ...):         │
│          # Check agent exists                                   │
│          agent = self.graph.get_agent(agent_id)                 │
│          if not agent:                                          │
│              raise ValueError("Agent not found")                │
│                                                                    │
│          # Create Memory object                                 │
│          memory = Memory(                                        │
│              content=content,                                   │
│              memory_type=MemoryType(memory_type),               │
│              importance=importance                              │
│          )                                                       │
│                                                                    │
│          # Store to database                                    │
│          return self.graph.add_memory(agent_id, memory)         │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Calls graph.add_memory(...)
                             ▼
┌─ DATABASE LAYER (core/graph.py) ─────────────────────────────────┐
│                                                                    │
│  def add_memory(self, agent_id: str, memory: Memory):            │
│      query = """                                                 │
│      MATCH (a:Agent {id: $agent_id})                            │
│      CREATE (m:Memory {                                          │
│          id: $id,                                               │
│          content: $content,                                     │
│          memory_type: $memory_type,                             │
│          importance: $importance,                               │
│          created_at: datetime($created_at),                     │
│          updated_at: datetime($updated_at),                     │
│          metadata: $metadata                                    │
│      })                                                          │
│      CREATE (a)-[:CREATED {at: datetime($created_at)}]->(m)     │
│      RETURN m                                                    │
│      """                                                         │
│                                                                    │
│      with self.driver.session() as session:                     │
│          result = session.run(query, id=memory.id, ...)         │
│          return memory                                           │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Executes Cypher query
                             ▼
┌─ NEO4J DATABASE ──────────────────────────────────────────────────┐
│                                                                    │
│  BEFORE: Agent "research_001" exists                             │
│          ┌────────────────┐                                      │
│          │ Agent          │                                      │
│          │ research_001   │                                      │
│          └────────────────┘                                      │
│                                                                    │
│  EXECUTE: MATCH → CREATE Memory → CREATE CREATED relationship    │
│                                                                    │
│  AFTER: Memory created with relationship                         │
│          ┌────────────────┐                                      │
│          │ Agent          │                                      │
│          │ research_001   │                                      │
│          └────────┬───────┘                                      │
│                   │ :CREATED                                    │
│                   │ {at: 2026-05-11T10:30:00}                  │
│                   ▼                                              │
│          ┌────────────────┐                                      │
│          │ Memory         │                                      │
│          │ mem_abc123...  │                                      │
│          │ content:       │                                      │
│          │ "John is boss" │                                      │
│          │ importance: 0.8│                                      │
│          └────────────────┘                                      │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Returns: memory object
                             ▼
┌─ API RESPONSE ────────────────────────────────────────────────────┐
│                                                                    │
│  HTTP 201 Created                                                │
│  {                                                               │
│    "id": "mem_abc123def456789",                                 │
│    "content": "John is my boss",                                │
│    "memory_type": "fact",                                       │
│    "importance": 0.8,                                           │
│    "created_at": "2026-05-11T10:30:00",                        │
│    "metadata": {}                                               │
│  }                                                               │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Response travels back
                             ▼
┌─ FRONTEND ────────────────────────────────────────────────────────┐
│                                                                    │
│  ChatInterface.tsx receives response                             │
│    ├─ Memory saved successfully!                                │
│    ├─ Update UI                                                 │
│    └─ Show confirmation: "Memory added"                        │
│                                                                    │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Request Flow - Retrieving Memories

### Scenario: User asks "Who is important in my work?"

```
┌─ FRONTEND ────────────────────────────────────────────────────────┐
│                                                                    │
│  User types: "Who is important in my work?"                      │
│  Clicks: "Send" button                                           │
│                                                                    │
│  ChatInterface.tsx calls:                                        │
│    memgraphClient.chat({                                         │
│      agent_id: "research_001",                                  │
│      message: "Who is important in my work?"                    │
│    })                                                            │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP POST /chat
                             │ {agent_id, message}
                             ▼
┌─ API LAYER (routes.py) ───────────────────────────────────────────┐
│                                                                    │
│  @chat_router.post("/chat")                                      │
│  async def chat(agent_id: str, message: str, ...):               │
│      # 1. Get agent                                              │
│      agent = memory_graph.get_agent(agent_id)                    │
│                                                                    │
│      # 2. Retrieve relevant memories                             │
│      context = memory_graph.retrieve(                            │
│          agent_id=agent_id,                                      │
│          query=message,  # "Who is important?"                  │
│          limit=5,                                                │
│          min_importance=0.3                                      │
│      )                                                            │
│                                                                    │
│      # 3. Generate LLM response                                  │
│      response = generate_chat_response(                          │
│          message=message,                                        │
│          agent_name=agent.name,                                  │
│          memory_context=formatted_memories                       │
│      )                                                            │
│                                                                    │
│      # 4. Store interaction                                      │
│      memory_graph.add(                                            │
│          agent_id=agent_id,                                      │
│          content=f"User asked: {message[:100]}",                │
│          memory_type="interaction",                              │
│          importance=0.6                                          │
│      )                                                            │
│                                                                    │
│      return {"response": response, ...}                          │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ Step 2: Retrieve
                             ▼
┌─ BUSINESS LOGIC (memory.py) ──────────────────────────────────────┐
│                                                                    │
│  def retrieve(self, agent_id, query, limit, ...):                │
│      # Get agent's memories with filters                         │
│      memories = self.graph.get_agent_memories(                   │
│          agent_id=agent_id,                                      │
│          limit=limit,                                            │
│          memory_types=type_enums,                                │
│          time_range_days=time_range_days                         │
│      )                                                            │
│                                                                    │
│      # Filter by importance                                      │
│      memories = [m for m in memories                             │
│                  if m.memory.importance >= min_importance]       │
│                                                                    │
│      # Sort by importance + recency                              │
│      memories.sort(                                              │
│          key=lambda m: (m.memory.importance,                     │
│                         m.memory.created_at),                    │
│          reverse=True                                            │
│      )                                                            │
│                                                                    │
│      return ContextResponse(                                      │
│          memories=memories[:limit],                              │
│          total_found=len(memories),                              │
│          query=query                                             │
│      )                                                            │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ Step 2: Query DB
                             ▼
┌─ DATABASE LAYER (graph.py) ───────────────────────────────────────┐
│                                                                    │
│  def get_agent_memories(self, agent_id, limit, ...):             │
│      query = """                                                 │
│      MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory)    │
│      WHERE m.memory_type IN $memory_types                        │
│        AND c.at > datetime() - duration('P' + $days + 'D')       │
│      RETURN m, a.name as agent_name, c.at as created_at          │
│      ORDER BY c.at DESC                                          │
│      LIMIT $limit                                                │
│      """                                                          │
│                                                                    │
│      with self.driver.session() as session:                     │
│          result = session.run(query, ...)                        │
│          # Build MemoryResponse objects                          │
│          return responses                                        │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─ NEO4J DATABASE ──────────────────────────────────────────────────┐
│                                                                    │
│  QUERY: Find all memories created by agent                       │
│                                                                    │
│  Graph Structure:                                                │
│      Agent (research_001)                                        │
│      ├─── :CREATED ──→ Memory: "John is my boss" (imp: 0.8)    │
│      ├─── :CREATED ──→ Memory: "Prefer technical answers"       │
│      ├─── :CREATED ──→ Memory: "Working on AI project"          │
│      └─── :CREATED ──→ Memory: "Budget approved" (imp: 0.9)     │
│                                                                    │
│  Matching query: Find 5 most recent with importance > 0.3        │
│  Results: [                                                       │
│      {memory: "Budget approved", created: 2026-05-11 10:00},     │
│      {memory: "John is my boss", created: 2026-05-11 09:30},     │
│      {memory: "Working on AI", created: 2026-05-11 09:00},       │
│      ...                                                          │
│  ]                                                                │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Returns memories
                             ▼
┌─ LLM GENERATION (llm.py) ────────────────────────────────────────┐
│                                                                    │
│  generate_chat_response(                                         │
│      message="Who is important in my work?",                    │
│      agent_name="Research Assistant",                            │
│      memory_context=                                             │
│          "- Budget approved\n                                    │
│           - John is my boss\n                                    │
│           - Working on AI project"                               │
│  )                                                               │
│                                                                    │
│  Builds prompt:                                                  │
│  """                                                              │
│  You are Research Assistant.                                     │
│  Relevant memories:                                              │
│  - Budget approved                                               │
│  - John is my boss                                               │
│  - Working on AI project                                         │
│                                                                    │
│  User: Who is important in my work?                             │
│  Assistant:                                                      │
│  """                                                              │
│                                                                    │
│  Calls: genai.GenerativeModel("gemini-2.5-flash")               │
│  Response: "Based on your memories, John (your boss) and        │
│           the AI project team are key stakeholders..."          │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─ RESPONSE TO FRONTEND ────────────────────────────────────────────┐
│                                                                    │
│  HTTP 200 OK                                                     │
│  {                                                               │
│    "response": "Based on your memories, John (your boss)        │
│                and the AI project team are key...",             │
│    "agent_id": "research_001",                                  │
│    "context_memories": "3"                                      │
│  }                                                               │
│                                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─ FRONTEND DISPLAY ────────────────────────────────────────────────┐
│                                                                    │
│  ChatInterface.tsx receives response                             │
│    ├─ Display AI response in chat bubble                        │
│    ├─ Show "Based on 3 memories"                                │
│    └─ User can click to see which memories were used            │
│                                                                    │
│  Chat window shows:                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ You: Who is important in my work?                       │   │
│  │                                                          │   │
│  │ Assistant: Based on your memories, John (your boss)     │   │
│  │ and the AI project team are key stakeholders. Your      │   │
│  │ budget was also recently approved for this project.     │   │
│  │ [Based on 3 memories] 📊                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                    │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema (Neo4j)

```
┌─────────────────────────────────────────────────────────────────┐
│                     NEO4J GRAPH STRUCTURE                        │
│                                                                   │
│  Node Types:                                                     │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐   │
│  │ :Agent      │  │ :Memory  │  │ :Context │  │ :Entity   │   │
│  ├─────────────┤  ├──────────┤  ├──────────┤  ├───────────┤   │
│  │ id*         │  │ id*      │  │ id*      │  │ id*       │   │
│  │ name        │  │ content  │  │ name     │  │ name      │   │
│  │ type        │  │ type     │  │ started_ │  │ type      │   │
│  │ created_at  │  │ import   │  │ at       │  │ descr.    │   │
│  │ metadata    │  │ created_ │  │ ended_at │  │ metadata  │   │
│  │             │  │ at       │  │ summary  │  │           │   │
│  │             │  │ metadata │  │ metadata │  │           │   │
│  └─────────────┘  └──────────┘  └──────────┘  └───────────┘   │
│                                                                   │
│  Relationship Types:                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ :CREATED (Agent -> Memory)                              │   │
│  │   └─ at: timestamp                                       │   │
│  │                                                          │   │
│  │ :PART_OF (Memory -> Context)                            │   │
│  │   └─ at: timestamp                                       │   │
│  │                                                          │   │
│  │ :RELATES_TO (Memory -> Memory)                          │   │
│  │   ├─ type: supports|contradicts|elaborates|...          │   │
│  │   ├─ strength: 0.0-1.0                                  │   │
│  │   ├─ reason: string                                     │   │
│  │   └─ created_at: timestamp                              │   │
│  │                                                          │   │
│  │ :ACCESSED (Agent -> Memory, for sharing)                │   │
│  │   ├─ at: timestamp                                       │   │
│  │   ├─ permission: read|write                             │   │
│  │   └─ shared_by: agent_id                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Example Graph:                                                  │
│  ┌──────────────────┐                                           │
│  │ Agent            │                                           │
│  │ research_001     │                                           │
│  └─────────┬────────┘                                           │
│            │ :CREATED (2026-05-11 09:00)                        │
│            ├──────────────┬──────────────┬──────────────┐       │
│            ▼              ▼              ▼              ▼       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌───────┐  │
│  │ Memory       │  │ Memory       │  │ Memory   │  │Memory │  │
│  │ john_boss    │  │ tech_answer  │  │ context1 │  │budget │  │
│  │ imp: 0.8     │  │ imp: 0.7     │  │ imp: 0.5 │  │imp:0.9│  │
│  └──────────────┘  └──────────────┘  └──────────┘  └───────┘  │
│            │              │                                      │
│            └──:RELATES_TO─┘ (type: elaborates, strength: 0.7)  │
│                                                                   │
│            john_boss ──:PART_OF──→ ┌──────────────┐            │
│                                    │ Context      │            │
│                                    │ session_123  │            │
│                                    └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Component Hierarchy (Frontend)

```
┌──────────────────────────────────────────────┐
│ Navigation.tsx                               │
│ (Top bar with navigation links)              │
└─────────────────────────────────────────────┬┘
                                              │
                    ┌─────────────────────────┴─────────────────────┐
                    │                                                │
                    ▼                                                ▼
        ┌──────────────────────────────┐         ┌──────────────────────────────┐
        │ ChatInterface.tsx            │         │ GraphView.tsx                │
        ├──────────────────────────────┤         ├──────────────────────────────┤
        │ - Message input              │         │ - ReactFlow diagram          │
        │ - Message display            │         │ - Node visualization         │
        │ - Send button                │         │ - Relationship edges         │
        │ - Context memories display   │         │ - Legend                     │
        │ - Calls /chat endpoint       │         │ - Calls /memories/graph      │
        └──────────────────────────────┘         └──────────────────────────────┘
                    │
                    │ Uses
                    ▼
        ┌──────────────────────────────┐
        │ src/lib/memgraph.ts          │
        │ (API Client)                 │
        ├──────────────────────────────┤
        │ - addMemory()                │
        │ - getMemories()              │
        │ - chat()                     │
        │ - getGraphData()             │
        │ - All HTTP methods           │
        └──────────────────────────────┘
                    │
                    │ HTTP Requests
                    ▼
        ┌──────────────────────────────┐
        │ FastAPI Backend              │
        │ (memgraph/api/routes.py)     │
        └──────────────────────────────┘
```

---

## 6. Key Classes & Methods

```
MemoryGraph (memgraph/core/memory.py)
├── __init__(neo4j_uri, neo4j_user, neo4j_password)
├── Agents
│   ├── register_agent(agent_id, name, agent_type, metadata)
│   ├── get_agent(agent_id)
│   └── get_stats(agent_id)
├── Memories
│   ├── add(agent_id, content, memory_type, importance, ...)
│   ├── get(memory_id)
│   ├── retrieve(agent_id, query, limit, time_range_days, ...)
│   └── get_agent_memories(agent_id, limit, memory_types, ...)
├── Relationships
│   ├── relate(from_memory_id, to_memory_id, relation_type, strength)
│   └── get_related(memory_id, max_depth, min_strength)
├── Sharing
│   ├── share(from_agent_id, to_agent_id, memory_ids, permission)
│   └── get_shared_memories(agent_id, limit)
└── Utils
    ├── health_check()
    └── clear_all()

MemGraphDB (memgraph/core/graph.py)
├── Agent Operations
│   ├── create_agent(agent)
│   ├── get_agent(agent_id)
│   └── get_or_create_agent(agent)
├── Memory Operations
│   ├── add_memory(agent_id, memory, context_id)
│   ├── get_memory(memory_id)
│   └── get_agent_memories(agent_id, limit, types, time_range)
├── Relationship Operations
│   ├── create_memory_relationship(relationship)
│   └── get_related_memories(memory_id, max_depth, min_strength)
├── Sharing Operations
│   ├── share_memory(from_agent, to_agent, memory_id, permission)
│   └── get_shared_memories(agent_id, limit)
└── DB Utils
    ├── health_check()
    └── clear_database()
```

---

## 7. Environment Variables

```
.env or .env.local
│
├── NEO4J_URI
│   └─ Connection string to Neo4j database
│   └─ Example: neo4j://localhost:7687
│
├── NEO4J_USER
│   └─ Database username
│   └─ Example: neo4j
│
├── NEO4J_PASSWORD
│   └─ Database password
│   └─ Example: 12345678
│
└── GOOGLE_API_KEY (or GEMINI_API_KEY)
    └─ API key for Google Generative AI (Gemini)
    └─ Example: sk-abc123...
```

---

## Summary

This architecture follows a clean layered pattern:

1. **Frontend** (React/Next.js) - User interface
2. **API** (FastAPI) - HTTP endpoints
3. **Business Logic** (MemoryGraph class) - Core operations
4. **Database Layer** (Neo4j operations) - Persistence
5. **Neo4j** - Graph storage

Each layer has a specific responsibility and communicates with the next layer. Data flows:
- **Down** for operations (User action → Frontend → API → Logic → DB)
- **Up** for responses (DB → Logic → API → Frontend → Display)

