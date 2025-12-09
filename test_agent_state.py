#!/usr/bin/env python3
"""
Diagnostic script to check agent state and memories.
"""

import os
from dotenv import load_dotenv
from memgraph.core.memory import MemoryGraph

load_dotenv()

# Initialize MemoryGraph
neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "12345678")

memory_graph = MemoryGraph(
    neo4j_uri=neo4j_uri,
    neo4j_user=neo4j_user,
    neo4j_password=neo4j_password
)

print("=" * 60)
print("🔍 AGENT STATE DIAGNOSTIC")
print("=" * 60)

# Check test-agent
try:
    agent = memory_graph.get_agent("test-agent")
    print(f"\n✅ Agent found: {agent}")
    print(f"   ID: {agent.agent_id}")
    print(f"   Name: {agent.name}")
    print(f"   Type: {agent.agent_type}")
except Exception as e:
    print(f"\n❌ Agent not found: {e}")

# Get all memories for test-agent
print("\n" + "=" * 60)
print("📝 MEMORIES FOR test-agent")
print("=" * 60)

try:
    memories_response = memory_graph.get_agent_memories("test-agent", limit=20)
    print(f"\n✅ Retrieved {len(memories_response)} memories:\n")
    
    for i, mem in enumerate(memories_response, 1):
        print(f"{i}. {mem.memory.memory_type.upper()}")
        print(f"   Content: {mem.memory.content[:100]}")
        print(f"   Importance: {mem.memory.importance}")
        print(f"   Created: {mem.memory.created_at}")
        print()
except Exception as e:
    print(f"\n❌ Failed to get memories: {e}", exc_info=True)

# Test retrieve with a query
print("\n" + "=" * 60)
print("🔎 MEMORY RETRIEVAL TEST")
print("=" * 60)

try:
    query = "What do you know about me?"
    print(f"\nQuery: '{query}'")
    
    context_response = memory_graph.retrieve(
        agent_id="test-agent",
        query=query,
        limit=5
    )
    
    print(f"\n✅ Context response received:")
    print(f"   Query: {context_response.query}")
    print(f"   Total found: {context_response.total_found}")
    print(f"   Memories returned: {len(context_response.memories)}\n")
    
    for i, mem in enumerate(context_response.memories, 1):
        print(f"{i}. {mem.memory.memory_type.upper()}")
        print(f"   Content: {mem.memory.content}")
        print(f"   Importance: {mem.memory.importance}\n")
        
except Exception as e:
    print(f"\n❌ Retrieval failed: {e}", exc_info=True)

memory_graph.close()
print("\n" + "=" * 60)
print("✓ Diagnostic complete")
print("=" * 60)
