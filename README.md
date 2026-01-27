# MemGraph 🕸️🧠

### _Open-Source Persistent Context Layer for Autonomous AI Agents_

MemGraph is a specialized memory infrastructure designed to solve the "Goldfish Memory" problem in LLM agents. Unlike traditional vector databases that store flat embeddings, MemGraph builds a **dynamic knowledge graph** of user interactions, allowing agents to understand not just _what_ was said, but the _relationships_ and _temporal evolution_ of context over time.

## 🚀 The Problem: Flat Memory vs. Graph Context

Standard RAG (Retrieval-Augmented Generation) often fails to capture complex relationships. If a user says "My boss is John" and later "He is traveling," a vector search might not link "He" to "John" effectively. **MemGraph** uses a graph-based approach to ensure that:

1. **Context Survives:** Memories persist across infinite sessions.
    
2. **Relationships are First-Class:** Agents can query "Who are the key stakeholders mentioned in the last month?"
    
3. **Temporal Tracking:** The agent understands when a fact was true and how it changed.
    

## ✨ Key Features

- **🌲 Knowledge Graph Architecture:** Built on **Neo4j** (or similar graph DBs) to map entities and actions as nodes and edges.
    
- **📂 Multi-Agent Shared Context:** Allows different specialized agents (e.g., a "Research Agent" and a "Writing Agent") to read from the same evolving memory pool.
    
- **🔗 LangChain & CrewAI Ready:** A developer-friendly API that integrates into existing agentic frameworks with minimal boilerplate.
    
- **🛰️ Temporal Awareness:** Every memory node is timestamped, allowing for "Time-Travel" debugging of an agent's reasoning process.
    

## 🏗️ Technical Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   Agent Query   │      │   MemGraph API   │      │   Neo4j/Cypher   │
│ (LangChain/etc) │────▶ │  (Uvicorn/Fast)  │────▶ │  (Graph Store)   │
└─────────────────┘      └──────────────────┘      └──────────────────┘
        │                         │                         │
  - User Intent             - Entity Extraction       - Relationship Map
  - Task Context            - Relationship Logic      - Pattern Matching
  - History Request         - Query Construction      - Persistent Graph
```

## 🛠️ Implementation Details

- **Backend:** Python 3.11+ using **FastAPI** for high-performance async API endpoints.
    
- **Graph Logic:** Optimized **Cypher** queries for fast traversal of deeply nested relationships.
    
- **NLP Pipeline:** Uses `spaCy` or small local LLMs for Entity-Relationship extraction before committing to the graph.
    
- **Persistence:** Designed to interface with local or cloud-hosted Neo4j instances.
    

## 📖 Quick Start

### 1. Start the API Server

```
python -m uvicorn memgraph.api.main:app --reload
```

### 2. Add Memory via Python

```
from memgraph import MemoryGraph

memory = MemoryGraph(api_url="http://localhost:8000")
memory.add(
    agent_id="travel_agent", 
    content="User prefers window seats and is allergic to peanuts",
    metadata={"importance": "high"}
)
```

## 🗺️ Engineering Roadmap

- [x] Core API & Architecture Design
    
- [ ] **Neo4j Integration:** Mapping Python objects to Cypher nodes/edges.
    
- [ ] **Agentic Entity Extraction:** Using LLMs to automatically identify entities in chat logs.
    
- [ ] **Graph Visualization:** A built-in dashboard to see the agent's "brain" in real-time.
    

_Built by 0xIta3hi to give AI agents the memory they deserve._
