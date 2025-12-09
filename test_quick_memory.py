#!/usr/bin/env python3
"""
Quick test to add a memory and check if it retrieves.
"""

import os
from dotenv import load_dotenv
from memgraph.core.memory import MemoryGraph

load_dotenv()

# Initialize
neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "12345678")

memory_graph = MemoryGraph(
    neo4j_uri=neo4j_uri,
    neo4j_user=neo4j_user,
    neo4j_password=neo4j_password
)

print("=" * 70)
print("🧪 MEMORY STORAGE TEST")
print("=" * 70)

# Test with test-agent
agent_id = "test-agent"

print(f"\n1️⃣  Creating agent: {agent_id}")
try:
    agent = memory_graph.register_agent(agent_id, "Test Agent", "general")
    print(f"   ✅ Agent created: {agent.agent_id}")
except Exception as e:
    print(f"   ⚠️  {e}")

print(f"\n2️⃣  Adding memory...")
try:
    memory = memory_graph.add(
        agent_id=agent_id,
        content="I am a test agent learning about memory systems",
        memory_type="fact",
        importance=0.9
    )
    print(f"   ✅ Memory added: {memory.id}")
    print(f"      Content: {memory.content}")
except Exception as e:
    print(f"   ❌ Failed to add memory: {e}", exc_info=True)

print(f"\n3️⃣  Retrieving all memories...")
try:
    memories_response = memory_graph.get_agent_memories(agent_id, limit=20)
    print(f"   ✅ Retrieved {len(memories_response)} memories:")
    for i, mem in enumerate(memories_response, 1):
        print(f"      {i}. {mem.memory.memory_type.value}: {mem.memory.content[:50]}")
except Exception as e:
    print(f"   ❌ Failed: {e}", exc_info=True)

print(f"\n4️⃣  Testing memory retrieval with query...")
try:
    context = memory_graph.retrieve(
        agent_id=agent_id,
        query="What are you?",
        limit=5
    )
    print(f"   ✅ Context response:")
    print(f"      Query: {context.query}")
    print(f"      Memories found: {len(context.memories)}")
    for mem in context.memories:
        print(f"         - {mem.memory.content}")
except Exception as e:
    print(f"   ❌ Failed: {e}", exc_info=True)

memory_graph.close()
print("\n" + "=" * 70)
