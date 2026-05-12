# Codebase Guide: What Each File Does

**MemGraph** - A persistent memory layer for AI agents using Neo4j knowledge graphs.

---

## Quick Navigation

- **Backend Core** (`memgraph/core/`) - Data models and core logic
- **API Layer** (`memgraph/api/`) - REST endpoints and integrations  
- **Frontend Components** (`src/components/`) - React UI components
- **Configuration Files** - Next.js, TypeScript, Node.js setup
- **Test Files** (`tests/`) - Integration and manual tests
- **Scripts** (`scripts/`) - Utility scripts for development

---

## Backend Core Layer

### `memgraph/core/models.py` (307 lines)

**What it does:** Defines all data structures used throughout the application with Pydantic validation.

**Key Classes:**
- `Agent` - Represents an AI agent (id, name, type, metadata)
- `Memory` - A single memory unit (content, type, importance, timestamps)
- `Context` - Groups related memories into sessions/conversations
- `Entity` - Extracted entities from memory content (person, place, concept, etc.)
- `MemoryType` (Enum) - 6 types: PREFERENCE, FACT, ACTION, CONVERSATION, DECISION, OBSERVATION
- `RelationType` (Enum) - 6 types: SUPPORTS, CONTRADICTS, ELABORATES, FOLLOWS, RELATES_TO, SUPERSEDES
- `MemoryRelationship` - Links between two memories with relationship type and strength

**Why it matters:**
- **Source of truth** for data structures
- Ensures data validation before database operations
- All API responses use these models
- Provides type safety for the entire application

**How to use it:**
```python
from memgraph.core.models import Memory, MemoryType, Agent

# Creating a memory
memory = Memory(
    content="John is my boss",
    memory_type=MemoryType.FACT,
    importance=0.8
)

# Creating an agent
agent = Agent(name="research_assistant", agent_type="researcher")
```

---

### `memgraph/core/memory.py` (551 lines)

**What it does:** High-level API for all memory operations. This is the main interface users interact with.

**Key Methods:**
- `register_agent()` - Create/register a new AI agent
- `add()` - Store a new memory with automatic importance scoring
- `retrieve()` - Query memories with filters (time range, type, importance level)
- `get_agent_memories()` - List all memories for an agent
- `create_context()` - Group memories into sessions
- `relate()` - Create relationships between memories
- `get_related()` - Find connected memories via graph traversal
- `share()` - Share memories between agents with permissions
- `get_shared_memories()` - Retrieve shared memories
- `health_check()` - Verify the system is working
- `get_stats()` - Get statistics about memory usage

**How it works:**
1. Validates input using Pydantic models
2. Delegates to `MemGraphDB` (lower layer) for database operations
3. Returns structured responses

**Example usage:**
```python
from memgraph.core.memory import MemoryGraph

# Initialize
mem_graph = MemoryGraph()

# Add a memory
memory = mem_graph.add(
    agent_id="research_001",
    content="User prefers concise answers",
    memory_type="preference",
    importance=0.7
)

# Retrieve memories
context = mem_graph.retrieve(
    agent_id="research_001",
    query="preferences",  # Free-text search
    limit=5,
    min_importance=0.5
)
```

**Key Pattern:** Acts as a **facade** - simplifies the complex database layer for API consumers

---

### `memgraph/core/graph.py` (617 lines)

**What it does:** Direct Neo4j database operations using Cypher queries. Low-level database abstraction.

**Key Methods:**
- **Agent Operations:**
  - `create_agent()` - Write an agent to database
  - `get_agent()` - Read an agent from database
  - `get_or_create_agent()` - Create if doesn't exist

- **Memory Operations:**
  - `add_memory()` - Create a memory node and CREATED relationship
  - `get_memory()` - Retrieve a single memory
  - `get_agent_memories()` - Query all memories for an agent with filtering

- **Relationship Operations:**
  - `create_memory_relationship()` - Link two memories
  - `get_related_memories()` - Find connected memories via graph traversal

- **Sharing Operations:**
  - `share_memory()` - Grant access to another agent
  - `get_shared_memories()` - Retrieve shared memories

- **Database Utilities:**
  - `health_check()` - Verify Neo4j connectivity
  - `clear_database()` - Wipe all data (development only)

**Cypher Examples Inside:**
```cypher
# Create a memory node and link to agent
MATCH (a:Agent {id: $agent_id})
CREATE (m:Memory {id: $id, content: $content, ...})
CREATE (a)-[:CREATED]->(m)
RETURN m

# Find related memories with depth
MATCH path=(m1:Memory {id: $memory_id})-[r*1..3]->(m2:Memory)
WHERE r.type IN $relation_types
RETURN m2, length(path) as distance
```

**Why it matters:**
- **Separation of concerns** - keeps database code isolated
- Easy to test database logic independently
- All Neo4j queries in one place for maintenance
- Can optimize queries here without touching business logic

---

## API Layer

### `memgraph/api/main.py` (182 lines)

**What it does:** FastAPI application setup, configuration, and server initialization.

**Key Functions:**
- `lifespan()` - Async context manager for startup/shutdown
  - Initializes `MemoryGraph` instance at startup
  - Cleans up at shutdown
  
- `get_memory_graph()` - Dependency injection function
  - Returns the singleton `MemoryGraph` instance
  - Used by all route handlers via `Depends()`

- `health_check()` - GET `/health` endpoint
  - Returns server status
  - Calls `memory_graph.health_check()` to verify database

- `root()` - GET `/` endpoint
  - Welcome message with API info

**Configuration:**
- CORS: Currently allows all origins (`*`) - **TODO: Restrict in production**
- Logging: INFO level with structured output
- Environment variables: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`

**Why it matters:**
- **Single entry point** for the entire API
- Dependency injection ensures only one `MemoryGraph` instance
- Lifespan management handles connection pooling

**Server startup:**
```bash
uvicorn memgraph.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### `memgraph/api/routes.py` (672 lines)

**What it does:** RESTful API endpoints organized into 6 routers. This is what the frontend calls.

**Routers & Endpoints:**

#### **Agents Router**
- `POST /agents` - Create new agent
  - Input: `{agent_id, name, agent_type, metadata}`
  - Returns: Agent object
  
- `GET /agents/{agent_id}` - Get agent details
  
- `GET /agents/{agent_id}/stats` - Get agent statistics
  - Returns: Memory count by type, total importance, etc.

#### **Memories Router**
- `POST /memories` - Add new memory
  - Input: `{agent_id, content, memory_type, importance}`
  - Returns: Memory object with ID

- `GET /memories/{memory_id}` - Get specific memory

- `GET /memories/agent/{agent_id}` - List all agent memories
  - Query params: `limit`, `memory_types`, `min_importance`, `time_range_days`

- `POST /memories/retrieve` - Search memories
  - Input: `{agent_id, query, limit, min_importance, time_range_days}`
  - Returns: Ranked list of relevant memories

- `GET /memories/graph` - Get graph visualization data
  - Returns: Nodes and edges for ReactFlow
  - Input: `agent_id`

#### **Contexts Router**
- `POST /contexts` - Create context (session grouping)
  - Input: `{name, agent_id}`
  - Returns: Context object

#### **Relationships Router**
- `POST /relationships` - Link two memories
  - Input: `{from_memory_id, to_memory_id, relation_type, strength}`
  - Returns: Relationship object

- `GET /relationships/{rel_id}` - Get relationship details

#### **Sharing Router**
- `POST /sharing/grant` - Share memory with another agent
  - Input: `{from_agent_id, to_agent_id, memory_ids, permission}`
  - Returns: Sharing record

- `GET /sharing/{agent_id}` - List shared memories
  - Returns: Memories shared with this agent

#### **Chat Router**
- `POST /chat` - Chat with LLM
  - Input: `{agent_id, message}`
  - Process:
    1. Retrieve agent's memories
    2. Build system prompt with context
    3. Call Gemini API
    4. Store interaction as memory
  - Returns: `{response, context_used}`

**Query Parameters Pattern:**
```python
# Standard filtering across endpoints
GET /memories/agent/{agent_id}?
  limit=10
  &memory_types=fact,preference
  &min_importance=0.3
  &time_range_days=30
```

**Error Handling:**
All endpoints return proper HTTP status codes:
- 200 OK - Success
- 201 Created - Resource created
- 400 Bad Request - Invalid input
- 404 Not Found - Resource not found
- 500 Internal Server Error - Database error

---

### `memgraph/api/llm.py` (~200 lines)

**What it does:** Google Gemini API integration for chat responses.

**Key Functions:**
- `get_gemini_model()` - Lazy initialization of Gemini model
  - Reads `GOOGLE_API_KEY` or `GEMINI_API_KEY` from environment
  - Uses `gemini-2.5-flash` model (fast and capable)

- `generate_chat_response()` - Create contextual responses
  - Takes: `message`, `agent_name`, `memory_context`
  - Builds system prompt with memory
  - Includes last 4 messages for conversation history
  - Has fallback responses if API not configured

**Prompt Structure:**
```
System: You are {agent_name}.
Context from your memory:
{formatted_memories}

Recent messages:
{last_4_messages}

User: {current_message}
```

**Fallback Behavior:**
If Gemini API is not available, provides basic responses:
- Recognizes simple math operations
- Returns default helpful responses
- Prevents chat from breaking

**Why it matters:**
- Makes memories **contextually relevant** in conversations
- Agent "remembers" preferences and past interactions
- Personalized responses based on memory

---

## Integration Layer

### `memgraph/integrations/langchain_agent.py` (482 lines)

**What it does:** LangChain-compatible memory backend and toolkit. Enables integration with LangChain agents.

**Key Classes:**

#### **MemGraphMemory**
Implements LangChain's `BaseChatMemory` interface:
- `save_context(inputs, outputs)` - Store human/AI messages with automatic relationships
- `load_memory_variables(inputs)` - Retrieve relevant memories for context
- `_format_memories()` - Format memories as readable text for LLM prompts
- `clear()` - Reset memory for new session

#### **MemGraphToolkit**
Provides tools for agents to use MemGraph:
- `add_memory()` - Store a memory during agent execution
- `retrieve_memories()` - Query memories by criteria
- `relate_memories()` - Create relationships between memories

**Example Usage:**
```python
from langchain.memory import MemGraphMemory
from langchain.agents import AgentExecutor, create_react_agent

# Initialize MemGraph memory
memory = MemGraphMemory(
    agent_id="my_agent",
    memory_graph=mem_graph
)

# Create LangChain agent with MemGraph memory
agent = create_react_agent(
    llm=llm_model,
    tools=tools,
    memory=memory  # Uses MemGraph for memory
)

# Run agent
executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    memory=memory
)

result = executor.invoke({"input": "Remember this fact"})
```

**Why it matters:**
- Bridges MemGraph and LangChain ecosystems
- Agents can use MemGraph as their memory backend
- Enables complex multi-step agent workflows with persistent context

---

## Frontend Components

### `src/components/ChatInterface.tsx`

**What it does:** Chat UI component for interacting with agents.

**Features:**
- Message input field
- Conversation history display
- Send button with loading state
- Context memory display (shows which memories were used)
- Auto-scroll to latest message

**Key Functions:**
- `sendMessage()` - POST to `/chat` endpoint
- `retrieveContext()` - GET `/memories/agent/{id}` for context
- `formatMemories()` - Format memories for display

**Data Flow:**
```
User types → Input field → Click Send → POST /chat
                                           ↓
                                    LLM generates response
                                           ↓
                                    Display in chat bubble
```

---

### `src/components/GraphView.tsx`

**What it does:** Visualizes the memory graph using ReactFlow library.

**Features:**
- Interactive node display (Agents, Memories, Contexts)
- Edge relationships with labels
- Zoom and pan controls
- Color-coded node types
- Legend explaining colors

**Data Source:**
- GET `/memories/graph?agent_id={id}`
- Returns: `{nodes: [...], edges: [...]}`

**Visualization:**
- Nodes: Circles representing agents/memories
- Edges: Lines showing relationships (CREATED, RELATES_TO, etc.)
- Colors: Different color per node type

---

### `src/components/AgentCreationForm.tsx`

**What it does:** Form for registering new AI agents.

**Fields:**
- `agent_id` - Unique identifier
- `name` - Display name
- `agent_type` - Category (researcher, writer, assistant, etc.)
- `metadata` - JSON object for custom properties

**On Submit:**
- POST `/agents` with form data
- Returns: Created agent object
- Redirects to agent details view

---

### `src/components/AgentDetails.tsx`

**What it does:** Display agent information and statistics.

**Data Displayed:**
- Agent name, ID, type
- Memory statistics (count by type)
- Total importance score
- Creation date
- List of recent memories

**Data Sources:**
- GET `/agents/{id}` - Agent info
- GET `/agents/{id}/stats` - Statistics

---

### `src/components/AgentLoader.tsx`

**What it does:** Agent selection and loading UI.

**Features:**
- Dropdown or list of all agents
- Select agent to view details
- Quick actions (delete, edit, stats)

**Data Source:**
- GET `/agents` - List all agents

---

### `src/components/Navigation.tsx`

**What it does:** Top-level navigation component.

**Links:**
- Agents - View all agents
- Memories - View all memories
- Graph - View memory graph
- Chat - Chat with agent
- Settings - Configuration

---

## Configuration Files

### `package.json`

**What it does:** Node.js/npm package configuration for frontend build.

**Key Sections:**
- `dependencies` - React, Next.js, Tailwind CSS, ReactFlow
- `devDependencies` - TypeScript, ESLint, PostCSS
- `scripts` - Build, dev server, test commands
- `next.config.js` - Next.js specific configuration

**Key Scripts:**
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Run production build
npm run lint     # Run ESLint
```

---

### `requirements.txt`

**What it does:** Python package dependencies for backend.

**Key Packages:**
- `fastapi==0.104.1` - Web framework
- `uvicorn==0.24.0` - ASGI server
- `neo4j==5.14.1` - Database driver
- `pydantic==2.5.0` - Data validation
- `python-dotenv` - Environment variables
- `google-generativeai` - Gemini API
- `langchain==0.1.0` - LLM agent framework

---

### `tsconfig.json`

**What it does:** TypeScript compiler configuration.

**Key Settings:**
- `target: ES2020` - JavaScript version
- `lib: ["ES2020", "DOM", "DOM.Iterable"]` - Type definitions
- `jsx: "preserve"` - Keep JSX for Next.js
- `moduleResolution: "node"` - Module resolution
- `strict: true` - Strict type checking

---

### `tailwind.config.js`

**What it does:** Tailwind CSS customization.

**Configuration:**
- Content paths for CSS generation
- Color palette customization
- Font configuration
- Plugin configuration

---

### `.env` / `.env.local`

**What it does:** Environment variables for local development.

**Variables:**
```
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
GOOGLE_API_KEY=your_gemini_api_key
```

---

## Test Files

### `tests/test_agent_state.py`

**Purpose:** Diagnostic script to verify agent state and memory operations.

**What it tests:**
- Can retrieve agents from database
- Can list agent memories
- Memory retrieval with filters works
- Stats calculation is correct

**Output:** Structured diagnostic output with success/error indicators

**Run:** `python tests/test_agent_state.py`

---

### `tests/test_backend_manual.py`

**Purpose:** Manual testing of API endpoints during development.

**What it tests:**
- Agent creation via `/agents` endpoint
- Memory addition via `/memories` endpoint
- Relationship creation
- Error handling

**Use case:** Verify backend changes before frontend integration

---

### `tests/test_chat_debug.py`

**Purpose:** Debug chat endpoint and Gemini integration.

**What it tests:**
- Chat endpoint response format
- Gemini API calls
- Fallback responses when API unavailable
- Context memory inclusion

**Use case:** Troubleshoot chat functionality

---

### `tests/test_quick_memory.py`

**Purpose:** Quick verification of memory operations.

**What it tests:**
- Add memory operation
- Retrieve memory operation
- Basic query filtering

**Use case:** Quick smoke test before deployment

---

## Script Files

### `scripts/list_models.py`

**Purpose:** List available LLM models from Google Generative AI.

**What it does:**
- Connects to Google Generative AI
- Lists all available models
- Shows model capabilities (input/output tokens, etc.)

**Run:** `python scripts/list_models.py`

**Output:** Formatted table of available models

---

### `scripts/init-agents.js`

**Purpose:** Initialize test agents for development/demo.

**What it does:**
- Connects to backend API
- Creates sample agents
- Adds sample memories
- Creates relationships between memories

**Run:** `npm run init-agents` or `node scripts/init-agents.js`

**Use case:** Quick setup for demo/testing

---

### `scripts/generate-api-client.js`

**Purpose:** Generate TypeScript API client from OpenAPI spec.

**What it does:**
- Reads `openapi.json` spec
- Generates `src/lib/api/client.ts`
- Includes proper TypeScript types

**Run:** `node scripts/generate-api-client.js`

**Use case:** Keep frontend API client in sync with backend

---

## Documentation Files

### `README.md`

**Purpose:** Project overview and quick start guide.

**Covers:**
- What is MemGraph?
- Problem it solves
- Quick start instructions
- Architecture overview
- API documentation links

---

### `PROJECT_STRUCTURE.md`

**Purpose:** Detailed guide to directory organization.

**Explains:**
- Why each directory exists
- What files belong in each directory
- How to add new files

---

### `CLEANUP_SUMMARY.md`

**Purpose:** Summary of codebase cleanup and reorganization.

**Documents:**
- Files deleted
- Files moved
- Directories created
- Git commit information

---

### `DIRECTORY_TREE.md`

**Purpose:** ASCII tree visualization of project structure.

**Shows:**
- Full directory hierarchy
- All files organized by folder
- Helpful for navigation

---

### `scripts/README.md`

**Purpose:** Documentation for utility scripts.

**Explains:**
- Purpose of each script
- How to run each script
- What environment variables are needed
- Example outputs

---

## How Files Work Together

```
User Action (Frontend)
    ↓
React Component (ChatInterface.tsx)
    ↓
API Client (src/lib/memgraph.ts)
    ↓
HTTP Request to FastAPI
    ↓
Route Handler (routes.py)
    ↓
Business Logic (memory.py)
    ↓
Database Operations (graph.py)
    ↓
Neo4j Queries
    ↓
Data returned through layers
    ↓
Frontend Display
```

---

## Key Takeaways

1. **Layered Architecture**: Separation between UI, API, business logic, and database
2. **Dependency Injection**: Single source of truth for `MemoryGraph` instance
3. **Type Safety**: Pydantic models validate all data
4. **Async/Await**: Efficient handling of I/O operations
5. **Integration**: LangChain compatibility for agent workflows
6. **Context**: Memories provide context to LLM responses

---

## See Also

For detailed data flow diagrams and architecture explanations, see **[DATA_FLOW_GUIDE.md](DATA_FLOW_GUIDE.md)**

#### 27. **`requirements.txt`** - Python Dependencies
**What it does:** Lists Python packages.

**Key Dependencies:**
- `fastapi` - Web framework
- `uvicorn` - Server
- `neo4j` - Database driver
- `pydantic` - Validation
- `langchain` - LLM framework
- `google-generativeai` - Gemini API

---

#### 28. **`tsconfig.json`** - TypeScript Config
**What it does:** TypeScript compiler settings for frontend.

**Configures:**
- Target ES version
- JSX support
- Module resolution

---

#### 29. **`next.config.js`** - Next.js Config
**What it does:** Next.js build and runtime settings.

**Configures:**
- API routes
- Static optimization
- Environment variables

---

#### 30. **`tailwind.config.js`** - Tailwind CSS Config
**What it does:** Tailwind styling configuration.

---

#### 31. **`.env` and `.env.local`** - Environment Variables
**What it does:** Stores secrets and configuration (NOT checked into git).

**Contains:**
- `NEO4J_URI` - Database connection
- `NEO4J_USER`, `NEO4J_PASSWORD`
- `GOOGLE_API_KEY` - Gemini API key

---

## 📖 DOCUMENTATION

#### 32. **`README.md`**
**What it does:** Project overview, quick start, key features.

#### 33. **`CODEBASE_ANALYSIS.md`**
**What it does:** Deep technical analysis of architecture, design patterns, TODO items.

#### 34. **`PROJECT_STRUCTURE.md`**
**What it does:** Directory structure guide and development workflow.

#### 35. **`DIRECTORY_TREE.md`**
**What it does:** Visual ASCII tree of all directories.

#### 36. **`CLEANUP_SUMMARY.md`**
**What it does:** Summary of codebase reorganization.

---

## 🔑 KEY FILES TO KNOW FOR DEVELOPMENT

### If you want to add a new feature:

**New Memory Type?** → Edit `memgraph/core/models.py` (add to `MemoryType` enum)

**New API Endpoint?** → Edit `memgraph/api/routes.py` (add new router)

**New Business Logic?** → Edit `memgraph/core/memory.py` (add method to `MemoryGraph` class)

**New Database Query?** → Edit `memgraph/core/graph.py` (add Neo4j Cypher query)

**New Frontend Page?** → Create in `app/` directory

**New Frontend Component?** → Create in `src/components/`

**New Integration?** → Create in `memgraph/integrations/`

### Most Important Files:

1. **`memgraph/core/memory.py`** - Main API (what developers import)
2. **`memgraph/core/graph.py`** - Database layer (where data actually goes)
3. **`memgraph/core/models.py`** - Data structures (defines everything)
4. **`memgraph/api/routes.py`** - REST endpoints (what frontend calls)
5. **`src/lib/memgraph.ts`** - Frontend API client (how frontend talks to backend)

---

## 📊 Data Flow Example

```
User types: "Remember that John is my boss"

1. Frontend (ChatInterface.tsx)
   └─> memgraphClient.addMemory()

2. API Client (src/lib/memgraph.ts)
   └─> POST /memories

3. Route Handler (memgraph/api/routes.py)
   └─> memory_graph.add()

4. Business Logic (memgraph/core/memory.py)
   └─> self.graph.add_memory()

5. Database Layer (memgraph/core/graph.py)
   └─> Neo4j Cypher Query:
       CREATE (a:Agent) -[:CREATED]-> (m:Memory)

6. Neo4j Database
   └─> Stores: Agent "User" -CREATED-> Memory "John is my boss"

Next Query: "Who is John?"

1. Frontend calls chat()
2. Backend retrieves memories with query
3. Returns: "John is your boss" (from graph)
4. LLM generates response
5. Frontend displays
```

---

## 🎯 Summary

| Layer | Files | Purpose |
|-------|-------|---------|
| **Backend API** | `memgraph/api/` | HTTP endpoints |
| **Business Logic** | `memgraph/core/memory.py` | Main interface |
| **Database Layer** | `memgraph/core/graph.py` | Neo4j operations |
| **Data Models** | `memgraph/core/models.py` | Validation & types |
| **Integrations** | `memgraph/integrations/` | LangChain, etc. |
| **Frontend** | `app/` + `src/` | React/Next.js UI |
| **Tests** | `tests/` | Validation scripts |
| **Scripts** | `scripts/` | Utilities |

Each file has a specific purpose. Start with understanding the flow from a user action → API → Core Logic → Database.

