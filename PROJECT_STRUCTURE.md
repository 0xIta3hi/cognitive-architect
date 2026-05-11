# Project Structure

MemGraph - Open-source memory layer for AI agents with persistent context graphs.

## Directory Organization

```
cognitive-architect/
├── memgraph/                           # Core Python backend
│   ├── api/                           # FastAPI REST API
│   │   ├── main.py                   # FastAPI app initialization & lifespan
│   │   ├── routes.py                 # API endpoints (agents, memories, etc.)
│   │   ├── llm.py                    # LLM integration (Google Gemini)
│   │   └── __init__.py
│   ├── core/                         # Core business logic
│   │   ├── memory.py                 # Main MemoryGraph class interface
│   │   ├── graph.py                  # Neo4j database operations
│   │   ├── models.py                 # Pydantic data models & enums
│   │   └── __init__.py
│   ├── integrations/                 # Third-party integrations
│   │   ├── langchain_agent.py        # LangChain memory backend
│   │   └── __init__.py
│   ├── utils/                        # Utility functions
│   │   └── __init__.py
│   └── __init__.py
│
├── app/                               # Next.js application (frontend root)
│   ├── layout.tsx                    # Root layout component
│   ├── page.tsx                      # Home page
│   ├── globals.css                   # Global styles
│   └── playground/
│       └── page.tsx                  # Playground page
│
├── src/                               # Frontend source code
│   ├── components/                   # React components
│   │   ├── AgentCreationForm.tsx
│   │   ├── AgentDetails.tsx
│   │   ├── AgentLoader.tsx
│   │   ├── ChatInterface.tsx
│   │   ├── GraphView.tsx
│   │   └── Navigation.tsx
│   └── lib/                          # Frontend utilities & API client
│       ├── memgraph.ts               # API client
│       └── api/
│           ├── client.ts
│           └── index.ts
│
├── examples/                          # Example code & demos
│   └── langchain_integration.py      # LangChain integration example
│
├── tests/                             # Test suite
│   ├── unit/                         # Unit tests (empty - add as needed)
│   ├── integration/                  # Integration tests (empty - add as needed)
│   ├── test_agent_state.py           # Diagnostic: Check agent state & memories
│   ├── test_backend_manual.py        # Manual backend testing
│   ├── test_chat_debug.py            # Chat endpoint debugging
│   ├── test_quick_memory.py          # Quick memory operations test
│   └── __init__.py
│
├── scripts/                           # Utility scripts
│   ├── generate-api-client.js        # Generate TypeScript API client
│   ├── init-agents.js                # Initialize test agents
│   ├── list_models.py                # List available LLM models
│   └── README.md                     # Scripts documentation
│
├── Configuration Files (Root)
│   ├── package.json                  # Node.js dependencies
│   ├── requirements.txt               # Python dependencies
│   ├── tsconfig.json                 # TypeScript configuration
│   ├── next.config.js                # Next.js configuration
│   ├── tailwind.config.js            # Tailwind CSS configuration
│   ├── postcss.config.js             # PostCSS configuration
│   ├── .gitignore                    # Git ignore rules
│   ├── .env                          # Environment variables (git ignored)
│   ├── .env.local                    # Local environment overrides (git ignored)
│   └── openapi.json                  # OpenAPI specification
│
├── Documentation
│   ├── README.md                     # Project overview & quick start
│   ├── CODEBASE_ANALYSIS.md          # Detailed technical analysis
│   ├── PROJECT_STRUCTURE.md          # This file
│   └── LICENSE                       # MIT License
│
├── Version Control & Build
│   ├── .git/                         # Git repository
│   ├── .gitignore                    # Git ignore rules
│   └── node_modules/                 # Node dependencies (git ignored)
│
└── Virtual Environments & Build
    ├── venv/                         # Python virtual environment (git ignored)
    ├── .venv/                        # Alternative Python venv (git ignored)
    ├── .next/                        # Next.js build output (git ignored)
    └── .pytest_cache/                # Pytest cache (git ignored)
```

## Key Directories Explained

### `memgraph/` - Backend
The core Python package containing all business logic and API endpoints.

**Structure:**
- `api/` - REST API layer (FastAPI)
- `core/` - Business logic and data models
- `integrations/` - Third-party integrations (LangChain, etc.)
- `utils/` - Shared utility functions

### `app/` & `src/` - Frontend
Next.js frontend application and React components.

**Structure:**
- `app/` - Next.js App Router pages
- `src/components/` - Reusable React components
- `src/lib/` - API client and utilities

### `tests/` - Test Suite
Organized test code.

**Structure:**
- `unit/` - Unit tests (isolated component testing)
- `integration/` - Integration tests (multiple components)
- Root level files - Diagnostic/manual test scripts

**Test Files:**
- `test_agent_state.py` - Diagnose agent & memory state
- `test_backend_manual.py` - Manual backend testing
- `test_chat_debug.py` - Chat endpoint debugging
- `test_quick_memory.py` - Quick memory operation tests

### `scripts/` - Utilities
Development and setup utility scripts.

**Scripts:**
- `generate-api-client.js` - Generate TypeScript from OpenAPI
- `init-agents.js` - Initialize test agents
- `list_models.py` - List available LLM models

### `examples/` - Examples
Example implementations and usage patterns.

**Currently:**
- `langchain_integration.py` - LangChain agent examples

## Running the Application

### Backend (Python)
```bash
# Start FastAPI development server
python -m uvicorn memgraph.api.main:app --reload

# Or from project root
uvicorn memgraph.api.main:app --reload
```

Server runs on: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Frontend (Node.js)
```bash
# Development server
npm run dev

# Production build
npm run build
npm start
```

Frontend runs on: `http://localhost:3000`

### Running Tests
```bash
# Diagnostic tests
python tests/test_agent_state.py

# Manual backend test
python tests/test_backend_manual.py

# Chat debugging
python tests/test_chat_debug.py

# Quick memory test
python tests/test_quick_memory.py
```

## Environment Setup

Create `.env` file in project root:
```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=12345678
GOOGLE_API_KEY=your_gemini_api_key
```

## Development Workflow

1. **Start backend**: `uvicorn memgraph.api.main:app --reload`
2. **Start frontend**: `npm run dev`
3. **Run tests**: `python tests/test_*.py`
4. **Add scripts**: Place in `scripts/` with `README.md` entry
5. **Add tests**: Place in `tests/unit/` or `tests/integration/`

## Tech Stack

**Backend:**
- Python 3.8+
- FastAPI 0.104.1
- Neo4j 5.14.1
- Pydantic 2.5.0
- LangChain 0.1.0
- Google Generative AI (Gemini)

**Frontend:**
- Next.js 14.0
- React 18.2
- TypeScript 5.0
- TailwindCSS 3.3
- ReactFlow 11.10

## Next Steps for Development

1. **Add Unit Tests** → `tests/unit/`
2. **Add Integration Tests** → `tests/integration/`
3. **Add Documentation** → Consider `docs/` directory for detailed guides
4. **Extend Examples** → Add more integration examples to `examples/`
5. **Add Utilities** → Place helper modules in `memgraph/utils/`

## Notes

- `.env` files are git-ignored for security
- `venv/`, `node_modules/`, `.next/` are git-ignored (recreate locally)
- `__pycache__/` and `.pytest_cache/` are git-ignored
- Configuration files stay in root for tool discovery
