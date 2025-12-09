# MemGraph LLM Integration - Gemini Setup

## Overview
The chat endpoint now integrates with Google Gemini for intelligent, context-aware responses using agent memories.

## Setup Instructions

### 1. Get Your Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the API key

### 2. Update .env File
Add your API key to `.env` in the project root:

```env
GOOGLE_API_KEY=your-api-key-here
```

Alternatively, you can use:
```env
GEMINI_API_KEY=your-api-key-here
```

### 3. Restart Backend
The backend will automatically pick up the API key on restart:

```bash
# Kill current process (Ctrl+C) and restart
python -m uvicorn memgraph.api.main:app --reload
```

## How It Works

### Chat Flow
1. **User sends message** to `/chat` endpoint
2. **Retrieve memories** - System finds relevant memories for the agent based on the message
3. **Build context** - Combines relevant memories into context for the LLM
4. **Generate response** - Sends message + memory context to Gemini
5. **Store interaction** - Saves the user's question as a new memory
6. **Return response** - Sends Gemini's response back to frontend

### Memory Integration
- **Memories are passed to Gemini** - System memory helps Gemini understand the agent's history
- **Context is limited** - Only the most recent/relevant 5 memories are used to avoid token limits
- **Interactions are saved** - Each user question is saved as an interaction memory

## Testing

### Test in Browser
1. Go to http://localhost:3000/playground
2. Create or load an agent
3. Add some memories to the agent first
4. Send a chat message
5. Gemini will respond using the memories as context

### Manual Test
```bash
python test_quick_memory.py  # Verify memory system works
```

## Example Behavior

**Agent**: "test-agent"  
**Memory**: "I am a Python developer learning about Neo4j"  
**User**: "What do you know about yourself?"  

**Expected Response** (from Gemini):
> "I'm a Python developer learning about Neo4j. Based on my knowledge, I can help with Python development questions, especially related to graph databases and Neo4j."

Instead of the old hardcoded response:
> "I don't have specific memories about that yet..."

## Troubleshooting

### Gemini Returns Fallback Responses
- Check that `GOOGLE_API_KEY` is set correctly in `.env`
- Check backend logs: `🤖 Calling Gemini API` should appear
- If API key is missing: `⚠️  GOOGLE_API_KEY or GEMINI_API_KEY not set`

### Memory Not Being Used
- Make sure agent has memories - check `/memories/agent/{agent_id}`
- Memories must have `importance > 0.3` to be retrieved
- Check backend logs for `📝 Retrieved X relevant memories`

### Memory Not Saving from Frontend
- Check that the agent exists first
- Use the AgentLoader to verify agent ID matches
- Check browser console for API errors

## Features Added

✅ **Gemini LLM Integration** - Intelligent, context-aware responses  
✅ **Memory Context** - System memories inform Gemini responses  
✅ **Fallback Mode** - Works even if API key is missing  
✅ **Interaction Tracking** - User questions saved as memories  
✅ **Smart Prompting** - System prompt helps Gemini understand agent role  

## Cost Considerations

Google Gemini has a **free tier**:
- Free tier: 60 requests per minute
- No credit card required for free tier

See [Gemini API Pricing](https://ai.google.dev/pricing) for details.

## Next Steps

1. Add your Gemini API key to `.env`
2. Restart the backend server
3. Test in the Playground
4. Create agents, add memories, and chat!
