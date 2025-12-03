# MemGraph Next.js Frontend

A modern Next.js + TypeScript frontend for the MemGraph AI Agent Memory System.

## Features

- ✅ **Type-Safe API**: Auto-generated TypeScript client from OpenAPI spec
- ✅ **Real-time Dashboard**: Load agents and manage their memories
- ✅ **Responsive UI**: Built with Tailwind CSS
- ✅ **Error Handling**: Graceful error states and backend connection detection
- ✅ **Production Ready**: ESLint, TypeScript strict mode, optimized builds

## Prerequisites

- **Node.js 18+** and npm/yarn
- **MemGraph Backend** running on `http://localhost:8000`
  - See root `README.md` for backend setup

## Installation

### 1. Install Dependencies

```bash
npm install
```

### 2. Generate TypeScript API Client

If not already generated:

```bash
node generate-api-client.js
```

This generates:
- `src/lib/api/index.ts` - OpenAPI types
- `src/lib/api/client.ts` - Client wrapper

### 3. Configure Environment

Copy or create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
MEMGRAPH_API_URL=http://localhost:8000
```

## Running the Frontend

### Development Mode

```bash
npm run dev
```

Visit: http://localhost:3000

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
.
├── app/
│   ├── layout.tsx              # Root layout with metadata
│   ├── page.tsx                # Dashboard/home page
│   └── globals.css             # Global styles
├── src/
│   └── lib/
│       ├── memgraph.ts         # API client initialization & helpers
│       └── api/
│           ├── client.ts       # Generated client wrapper
│           └── index.ts        # Generated OpenAPI types
├── package.json                # Dependencies
├── tsconfig.json               # TypeScript config
├── next.config.js              # Next.js config
├── tailwind.config.js          # Tailwind CSS config
└── postcss.config.js           # PostCSS config
```

## Usage

### In Components

```typescript
import { api, fetchAgent, addMemory } from '@/lib/memgraph';

// Load an agent
const { data: agent, error } = await fetchAgent('research-agent');

// Add a memory
const { data: memory } = await addMemory(
  'agent-id',
  'Important fact about something',
  'fact',
  0.8 // importance score
);

// Check backend health
const health = await checkHealth();
```

### Available Helper Functions

```typescript
// Check if backend is running
checkHealth()

// Fetch an agent by ID
fetchAgent(agentId)

// Get agent memories
fetchAgentMemories(agentId, limit?)

// Retrieve relevant context
retrieveContext(agentId, query, limit?, minImportance?)

// Add a new memory
addMemory(agentId, content, memoryType?, importance?)

// Get the raw API client
useMemGraphAPI()
```

## API Endpoints

The TypeScript client wraps these REST endpoints:

### Agents
- `GET /agents/{agent_id}` - Get agent details
- `POST /agents` - Register new agent
- `GET /agents/{agent_id}/stats` - Get agent statistics

### Memories
- `GET /memories/{memory_id}` - Get memory
- `GET /memories/agent/{agent_id}` - List agent memories
- `POST /memories` - Add new memory
- `POST /memories/retrieve` - Semantic search

### Relationships
- `POST /relationships` - Create relationship
- `GET /relationships/{memory_id}` - Get related memories

### Sharing
- `POST /sharing/grant` - Grant memory access
- `GET /sharing/{agent_id}` - Get shared memories

### Health
- `GET /health` - Backend health check
- `GET /` - Root info endpoint

## Environment Variables

### Required
- `NEXT_PUBLIC_API_URL` - Backend URL (exposed to client)

### Optional
- `MEMGRAPH_API_URL` - Server-side backend URL (can be internal DNS)

## Troubleshooting

### "Backend is not available" error
- Ensure FastAPI server is running: `python -m uvicorn memgraph.api.main:app --reload`
- Check `NEXT_PUBLIC_API_URL` matches backend URL
- Verify Neo4j is running (required by backend)

### Type errors on `api.agents.get()`
- Run `npm run generate-api` to regenerate types from OpenAPI spec
- Clear `.next` folder: `rm -rf .next`
- Restart dev server

### CORS errors
- Backend is configured with CORS support
- Verify backend is on the same URL as `NEXT_PUBLIC_API_URL`

## API Client Generation

The TypeScript client is auto-generated from the FastAPI OpenAPI spec using `openapi-typescript`.

To regenerate after backend changes:

```bash
npm run generate-api
```

Or manually:

```bash
node generate-api-client.js
```

## Building for Production

```bash
npm run build
npm start
```

The frontend will connect to the backend URL specified in `NEXT_PUBLIC_API_URL` environment variable.

## Next Steps

1. ✅ Install dependencies: `npm install`
2. ✅ Start backend: `python -m uvicorn memgraph.api.main:app --reload`
3. ✅ Run frontend: `npm run dev`
4. 🎯 Create additional pages and components using the API
5. 🎯 Deploy to production (Vercel, AWS, etc.)

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [Tailwind CSS](https://tailwindcss.com)
- [MemGraph Backend API](../../README.md)

## License

See root LICENSE file
