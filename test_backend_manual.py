#!/usr/bin/env python3
"""
Test script to verify MemGraph backend is working correctly.
Run this to test all core functionality.
"""

import sys
import os
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

from memgraph.core.memory import MemoryGraph

def test_backend():
    """Test all backend functionality."""
    
    print("=" * 60)
    print("MemGraph Backend Testing")
    print("=" * 60)
    
    # Test 1: Connection
    print("\n1. Testing Neo4j connection...")
    try:
        mg = MemoryGraph(
            neo4j_uri=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "12345678")
        )
        print("   ✅ Connected to Neo4j")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        return
    
    # Test 2: Health check
    print("\n2. Testing health check...")
    try:
        health = mg.health_check()
        if health:
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 3: Register agent
    print("\n3. Testing agent registration...")
    try:
        agent = mg.register_agent(
            agent_id="test-agent-001",
            name="Test Agent",
            agent_type="testing"
        )
        print(f"   ✅ Registered agent: {agent.id}")
    except Exception as e:
        print(f"   ❌ Failed to register: {e}")
        return
    
    # Test 4: Add memory
    print("\n4. Testing memory creation...")
    try:
        memory = mg.add(
            agent_id="test-agent-001",
            content="This is a test memory",
            memory_type="fact",
            importance=0.8
        )
        print(f"   ✅ Added memory: {memory.id}")
    except Exception as e:
        print(f"   ❌ Failed to add memory: {e}")
        return
    
    # Test 5: Get agent
    print("\n5. Testing agent retrieval...")
    try:
        agent = mg.get_agent("test-agent-001")
        if agent:
            print(f"   ✅ Retrieved agent: {agent.id}")
        else:
            print("   ❌ Agent not found")
    except Exception as e:
        print(f"   ❌ Failed to retrieve: {e}")
        return
    
    # Test 6: Get agent memories
    print("\n6. Testing memory retrieval...")
    try:
        memories = mg.get_agent_memories("test-agent-001", limit=10)
        print(f"   ✅ Retrieved {len(memories)} memories")
    except Exception as e:
        print(f"   ❌ Failed to retrieve: {e}")
        return
    
    # Test 7: Retrieve context
    print("\n7. Testing context retrieval...")
    try:
        context = mg.retrieve(
            agent_id="test-agent-001",
            query="What test memories do I have?",
            limit=5
        )
        print(f"   ✅ Retrieved context with {len(context.memories)} memories")
    except Exception as e:
        print(f"   ❌ Failed to retrieve context: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    
    # Clean up
    try:
        mg.close()
        print("\n✅ Connection closed")
    except:
        pass

if __name__ == "__main__":
    test_backend()
