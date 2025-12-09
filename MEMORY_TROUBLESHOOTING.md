# Memory Storage Troubleshooting Guide

## Issue: Memories Not Showing in Chat

You add memories through the frontend, but the chat endpoint says "Retrieved 0 relevant memories".

## Root Cause Analysis

The backend memory system is working correctly (verified via `test_quick_memory.py`).
The issue is that memories added through the frontend aren't actually being sent to the backend properly.

### Possible Causes:

1. **Agent ID mismatch** - Frontend sends to one agent ID, but you're chatting with a different agent
   - Example: Created "test-agent-1" but loading "test-agent"

2. **Frontend form not submitting** - The "Add Memory" form might not be sending the request

3. **Agent doesn't exist yet** - Must create agent BEFORE adding memories

## Solution Steps

### Step 1: Verify Agent Exists
Use the AgentLoader to load an agent:
1. Go to Dashboard (http://localhost:3000)
2. Scroll to "Load Existing Agent"
3. Enter agent ID and click "Load Agent"
4. Check browser console - should see: `✅ Agent loaded: {agent_id}`

### Step 2: Add Memory Manually (Verification)
Run this test to verify the memory system works:

```bash
python test_quick_memory.py
```

Expected output:
```
1️⃣  Creating agent: test-agent
   ✅ Agent created: test-agent
2️⃣  Adding memory...
   ✅ Memory added: mem_xxxxx
3️⃣  Retrieving all memories...
   ✅ Retrieved 1 memories:
      1. fact: I am a test agent learning about memory systems
```

### Step 3: Add Memory Through Frontend
1. Load an agent first (use AgentLoader)
2. Fill in "Add Memory" form:
   - Memory Content: (any text)
   - Type: Select a type
   - Importance: slider
3. Click "Add Memory"
4. Check browser console for errors
5. Check backend logs for: `✓ Added memory: mem_xxxxx`

### Step 4: Verify Memory Stored
1. Go to Playground (http://localhost:3000/playground)
2. Make sure agent ID matches the one you added memory to
3. Send a chat message
4. Check backend logs:
   - Should see: `📝 Retrieved 1 relevant memories`
   - Should see: `🤖 Calling Gemini API`

## Expected Behavior

### Before Adding Memory:
```
POST /chat
📝 Retrieved 0 relevant memories
(Gemini falls back to generic response)
```

### After Adding Memory:
```
POST /chat
📝 Retrieved 1 relevant memories
🤖 Calling Gemini API
(Gemini uses memory in response)
```

## Debugging Checklist

- [ ] Backend running? (`python -m uvicorn memgraph.api.main:app --reload`)
- [ ] Frontend running? (`npm run dev`)
- [ ] Agent created? (check `/agents/{agent_id}` returns 200)
- [ ] Agent loaded in Frontend? (AgentLoader shows it was loaded)
- [ ] Memory added? (check POST /memories returns 201)
- [ ] Memory retrievable? (`test_quick_memory.py` shows memory stored)
- [ ] Gemini API key set? (check `GOOGLE_API_KEY` in `.env`)

## Chrome DevTools Debugging

Open F12 in browser and check:

1. **Network tab** - See requests sent
   - POST /agents - should return agent data
   - POST /memories - should return memory data
   - POST /chat - should return response

2. **Console tab** - Check for logs
   - Look for `✅` messages showing successful operations
   - Look for `❌` errors explaining what went wrong

3. **Application tab** - Check stored data
   - Check `.env.local` is set correctly

## Example: Full Memory Flow

```
1. Create Agent
   POST /agents?agent_id=test-1&name=Test+Agent&agent_type=general
   ✅ Returns: {"agent_id": "test-1", "name": "Test Agent", ...}

2. Add Memory
   POST /memories?agent_id=test-1&content=I+am+a+test+agent&memory_type=fact&importance=0.9
   ✅ Returns: {"id": "mem_abc123", "content": "I am a test agent", ...}

3. Retrieve in Chat
   POST /chat {"agent_id": "test-1", "message": "Who are you?"}
   Backend: 📝 Retrieved 1 relevant memories
   Backend: 🤖 Calling Gemini API
   ✅ Returns: {"response": "I am a test agent...", ...}
```

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Agent not found" | Agent ID doesn't exist | Create agent first with AgentCreationForm |
| "Failed to get response: Internal Server Error" | Backend error | Check backend logs, restart server |
| "Retrieved 0 memories" | No memories for agent | Add memories first, then chat |
| "Failed to fetch graph" | No agent memories yet | This is normal for new agents |

Still stuck? Check backend logs:
```bash
# Watch backend logs
# Should see messages like:
# ✓ Added memory: mem_xxxxx
# 📝 Retrieved 1 relevant memories
# 🤖 Calling Gemini API
# ✅ Gemini response received
```
