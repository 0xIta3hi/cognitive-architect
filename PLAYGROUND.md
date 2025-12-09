# MemGraph Frontend - Playground Feature

## What's New

Created an interactive **Playground** with real-time chat and memory graph visualization.

### Components Created

#### 1. **ChatInterface** (`src/components/ChatInterface.tsx`)
- Real-time chat interface with user/AI message styling
- Auto-scrolling message list
- Loading animations
- Error handling
- Posts to `/chat` endpoint with agent context

#### 2. **GraphView** (`src/components/GraphView.tsx`)
- ReactFlow-based memory graph visualization
- Animated edges with strength indicators
- Auto-refresh when new messages are added
- Fetches from `/memories/graph` endpoint
- Displays memory relationships as nodes and edges

#### 3. **Playground Page** (`app/playground/page.tsx`)
- Split-screen layout (50% chat, 50% graph)
- Shared `refreshKey` state to sync chat and graph
- Full-screen responsive design

#### 4. **Navigation** (`src/components/Navigation.tsx`)
- Top navigation bar with links to:
  - Dashboard (home)
  - Playground (interactive demo)
  - API Docs (FastAPI Swagger UI)

### Backend Endpoints Added

#### 1. **POST /chat**
```json
{
  "agent_id": "default-agent",
  "message": "Your message here"
}
```
Response:
```json
{
  "response": "AI response text",
  "agent_id": "default-agent",
  "context_memories": 5
}
```

Behavior:
- Retrieves relevant memories using semantic search
- Generates context-aware response
- Stores interaction as a memory
- Returns count of relevant memories used

#### 2. **GET /memories/graph?agent_id={agentId}**
Response:
```json
{
  "nodes": [
    {
      "id": "mem-123",
      "label": "Memory content preview",
      "type": "fact",
      "importance": 0.8
    }
  ],
  "edges": [
    {
      "source": "mem-123",
      "target": "mem-456",
      "type": "relates",
      "strength": 0.7
    }
  ],
  "agent_id": "default-agent",
  "stats": {
    "total_nodes": 10,
    "total_edges": 15
  }
}
```

Behavior:
- Fetches all memories for an agent
- Maps memories to graph nodes
- Finds relationships and creates edges
- Returns ReactFlow-compatible format

## How to Use

### Start the Playground

1. **Backend running:**
   ```bash
   python -m uvicorn memgraph.api.main:app --reload
   ```

2. **Frontend running:**
   ```bash
   npm run dev
   ```

3. **Visit playground:**
   ```
   http://localhost:3000/playground
   ```

### Interactive Demo Flow

1. Chat appears on the left side
2. Type a message and click "Send"
3. Agent responds with context-aware message
4. Memory graph updates on the right
5. Nodes represent memories, edges show relationships
6. Hover over nodes to see details

## Architecture

```
Frontend (Next.js)
├── app/playground/page.tsx (Layout & State)
├── src/components/
│   ├── ChatInterface.tsx (User interaction)
│   ├── GraphView.tsx (Visualization)
│   └── Navigation.tsx (Navigation)
└── (Uses generated API client from src/lib/api/)

Backend (FastAPI)
├── /chat (POST)
│   └── Retrieves memories → Generates response
├── /memories/graph (GET)
│   └── Builds node/edge structure for visualization
└── (All existing endpoints remain)
```

## Key Features

### Chat
- ✅ Real-time messaging
- ✅ Animated loading states
- ✅ Auto-scroll to latest message
- ✅ Error display
- ✅ User/AI message differentiation
- ✅ Timestamps

### Graph
- ✅ Interactive visualization
- ✅ Drag-to-pan nodes
- ✅ Zoom controls
- ✅ Edge strength visualization
- ✅ Auto-refresh on chat
- ✅ Node/edge statistics

### Integration
- ✅ Chat updates trigger graph refresh
- ✅ Shared agent ID across components
- ✅ Responsive split-screen layout
- ✅ Type-safe API communication

## Future Enhancements

- 🔄 WebSocket for real-time graph updates
- 🤖 LangChain integration for smarter responses
- 💾 Memory persistence visualization
- 🔍 Search/filter memories in graph
- 📊 Memory importance distribution chart
- 🎨 Customizable node styling
- 💬 Multi-agent conversation
- 📝 Memory editing interface

## Tech Stack

- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS, ReactFlow
- **Backend:** FastAPI, Pydantic, Neo4j
- **API:** REST, OpenAPI 3.0
- **Communication:** Fetch API (HTTP)

## Files Modified

- `app/layout.tsx` - Added Navigation
- `app/page.tsx` - Simplified to Dashboard
- `app/playground/page.tsx` - **NEW** Playground page
- `src/components/ChatInterface.tsx` - **NEW** Chat component
- `src/components/GraphView.tsx` - **NEW** Graph visualization
- `src/components/Navigation.tsx` - **NEW** Navigation bar
- `package.json` - Added reactflow dependency
- `memgraph/api/routes.py` - Added `/chat` and `/memories/graph` endpoints
- `memgraph/api/main.py` - Registered new chat router

## Testing

Visit http://localhost:3000/playground and:
1. Type "Tell me about Neo4j"
2. Click Send
3. Watch graph update on the right
4. Try "What do you remember?"
5. See how memories are organized
