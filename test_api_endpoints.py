"""
Test suite for MemGraph FastAPI endpoints.

Run with: pytest test_api_endpoints.py -v
Or: python test_api_endpoints.py
"""

import requests
import json
import time
from typing import Dict, Any
import sys

BASE_URL = "http://127.0.0.1:8000"


class APITester:
    """Helper class for testing MemGraph API endpoints."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.agent_id_1 = "test_agent_research"
        self.agent_id_2 = "test_agent_writing"
        self.memory_ids = []
        self.context_id = None
    
    def test_health(self) -> bool:
        """Test health check endpoint."""
        print("\n🧪 Testing Health Check...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✅ Health check passed")
                    return True
                else:
                    print(f"❌ Service unhealthy: {data.get('status')}")
                    return False
            else:
                print(f"❌ Expected 200, got {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            print(f"❌ Health check timeout")
            return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def test_register_agents(self) -> bool:
        """Test agent registration."""
        print("\n🧪 Testing Agent Registration...")
        try:
            # Register first agent
            response1 = requests.post(
                f"{self.base_url}/agents",
                params={
                    "agent_id": self.agent_id_1,
                    "name": "Test Research Agent",
                    "agent_type": "research"
                }
            )
            assert response1.status_code == 201, f"Expected 201, got {response1.status_code}"
            agent1 = response1.json()
            assert agent1["id"] == self.agent_id_1, "Agent ID mismatch"
            print(f"✅ Registered agent 1: {agent1['name']}")
            
            # Register second agent
            response2 = requests.post(
                f"{self.base_url}/agents",
                params={
                    "agent_id": self.agent_id_2,
                    "name": "Test Writing Agent",
                    "agent_type": "writing"
                }
            )
            assert response2.status_code == 201, f"Expected 201, got {response2.status_code}"
            agent2 = response2.json()
            print(f"✅ Registered agent 2: {agent2['name']}")
            return True
        except Exception as e:
            print(f"❌ Agent registration failed: {e}")
            return False
    
    def test_get_agent(self) -> bool:
        """Test getting agent."""
        print("\n🧪 Testing Get Agent...")
        try:
            response = requests.get(f"{self.base_url}/agents/{self.agent_id_1}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            agent = response.json()
            assert agent["id"] == self.agent_id_1, "Agent ID mismatch"
            print(f"✅ Retrieved agent: {agent['name']}")
            return True
        except Exception as e:
            print(f"❌ Get agent failed: {e}")
            return False
    
    def test_create_context(self) -> bool:
        """Test context creation."""
        print("\n🧪 Testing Context Creation...")
        try:
            response = requests.post(
                f"{self.base_url}/contexts",
                params={
                    "name": "Test Research Session",
                    "summary": "Testing MemGraph API"
                }
            )
            assert response.status_code == 201, f"Expected 201, got {response.status_code}"
            context = response.json()
            self.context_id = context["id"]
            print(f"✅ Created context: {context['name']}")
            return True
        except Exception as e:
            print(f"❌ Context creation failed: {e}")
            return False
    
    def test_add_memories(self) -> bool:
        """Test adding memories."""
        print("\n🧪 Testing Add Memories...")
        try:
            memories_data = [
                {
                    "content": "User is a PhD student working on graph neural networks",
                    "memory_type": "fact",
                    "importance": 0.9
                },
                {
                    "content": "User prefers technical explanations with code examples",
                    "memory_type": "preference",
                    "importance": 0.8
                },
                {
                    "content": "User is interested in transformer architectures",
                    "memory_type": "observation",
                    "importance": 0.7
                }
            ]
            
            for i, mem_data in enumerate(memories_data):
                params = {
                    "agent_id": self.agent_id_1,
                    **mem_data,
                    "context_id": self.context_id
                }
                response = requests.post(f"{self.base_url}/memories", params=params)
                assert response.status_code == 201, f"Expected 201, got {response.status_code}"
                memory = response.json()
                self.memory_ids.append(memory["id"])
                print(f"✅ Added memory {i+1}: {memory['id']}")
            
            return True
        except Exception as e:
            print(f"❌ Add memories failed: {e}")
            return False
    
    def test_get_memory(self) -> bool:
        """Test getting a memory."""
        print("\n🧪 Testing Get Memory...")
        try:
            if not self.memory_ids:
                print("⚠️  No memories to retrieve")
                return False
            
            response = requests.get(f"{self.base_url}/memories/{self.memory_ids[0]}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            memory = response.json()
            assert memory["id"] == self.memory_ids[0], "Memory ID mismatch"
            print(f"✅ Retrieved memory: {memory['content'][:50]}...")
            return True
        except Exception as e:
            print(f"❌ Get memory failed: {e}")
            return False
    
    def test_get_agent_memories(self) -> bool:
        """Test getting agent's memories."""
        print("\n🧪 Testing Get Agent Memories...")
        try:
            response = requests.get(
                f"{self.base_url}/memories/agent/{self.agent_id_1}",
                params={"limit": 10}
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            memories = response.json()
            assert len(memories) > 0, "Expected memories but got none"
            print(f"✅ Retrieved {len(memories)} agent memories")
            return True
        except Exception as e:
            print(f"❌ Get agent memories failed: {e}")
            return False
    
    def test_retrieve_context(self) -> bool:
        """Test retrieving context with query."""
        print("\n🧪 Testing Retrieve Context...")
        try:
            response = requests.post(
                f"{self.base_url}/memories/retrieve",
                params={
                    "agent_id": self.agent_id_1,
                    "query": "What do I know about the user's research?",
                    "limit": 5,
                    "min_importance": 0.5
                }
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            context = response.json()
            assert "memories" in context, "Missing memories in response"
            print(f"✅ Retrieved context with {len(context['memories'])} memories")
            for mem_resp in context["memories"]:
                print(f"   - {mem_resp['memory']['content'][:40]}... (importance: {mem_resp['memory']['importance']})")
            return True
        except Exception as e:
            print(f"❌ Retrieve context failed: {e}")
            return False
    
    def test_create_relationship(self) -> bool:
        """Test creating memory relationship."""
        print("\n🧪 Testing Create Relationship...")
        try:
            if len(self.memory_ids) < 2:
                print("⚠️  Need at least 2 memories for relationship")
                return False
            
            response = requests.post(
                f"{self.base_url}/relationships",
                params={
                    "from_memory_id": self.memory_ids[0],
                    "to_memory_id": self.memory_ids[1],
                    "relation_type": "supports",
                    "strength": 0.8,
                    "reason": "Both memories discuss user expertise"
                }
            )
            assert response.status_code == 201, f"Expected 201, got {response.status_code}"
            relationship = response.json()
            print(f"✅ Created relationship: {relationship['from_memory_id'][:8]}... → {relationship['to_memory_id'][:8]}...")
            return True
        except Exception as e:
            print(f"❌ Create relationship failed: {e}")
            return False
    
    def test_get_related_memories(self) -> bool:
        """Test getting related memories."""
        print("\n🧪 Testing Get Related Memories...")
        try:
            if not self.memory_ids:
                print("⚠️  No memories available")
                return False
            
            response = requests.get(
                f"{self.base_url}/relationships/{self.memory_ids[0]}",
                params={"max_depth": 2, "min_strength": 0.5}
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            related = response.json()
            print(f"✅ Found {len(related)} related memories")
            return True
        except Exception as e:
            print(f"❌ Get related memories failed: {e}")
            return False
    
    def test_share_memories(self) -> bool:
        """Test sharing memories between agents."""
        print("\n🧪 Testing Share Memories...")
        try:
            if not self.memory_ids:
                print("⚠️  No memories to share")
                return False
            
            memory_ids_str = ",".join(self.memory_ids[:2])
            response = requests.post(
                f"{self.base_url}/sharing/grant",
                params={
                    "from_agent_id": self.agent_id_1,
                    "to_agent_id": self.agent_id_2,
                    "memory_ids": memory_ids_str,
                    "permission": "read"
                }
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            result = response.json()
            print(f"✅ Shared {result['shared_count']} memories: {self.agent_id_1} → {self.agent_id_2}")
            return True
        except Exception as e:
            print(f"❌ Share memories failed: {e}")
            return False
    
    def test_get_shared_memories(self) -> bool:
        """Test getting shared memories."""
        print("\n🧪 Testing Get Shared Memories...")
        try:
            response = requests.get(
                f"{self.base_url}/sharing/{self.agent_id_2}",
                params={"limit": 10}
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            memories = response.json()
            print(f"✅ Retrieved {len(memories)} shared memories for {self.agent_id_2}")
            return True
        except Exception as e:
            print(f"❌ Get shared memories failed: {e}")
            return False
    
    def test_get_agent_stats(self) -> bool:
        """Test getting agent statistics."""
        print("\n🧪 Testing Agent Statistics...")
        try:
            response = requests.get(f"{self.base_url}/agents/{self.agent_id_1}/stats")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            stats = response.json()
            print(f"✅ Agent Statistics:")
            print(f"   - Total memories: {stats['total_memories']}")
            print(f"   - Average importance: {stats['average_importance']}")
            print(f"   - Memory types: {stats['memory_types']}")
            return True
        except Exception as e:
            print(f"❌ Get agent stats failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        print("\n" + "="*60)
        print("🧪 MemGraph API Test Suite")
        print("="*60)
        
        tests = [
            ("Health Check", self.test_health),
            ("Register Agents", self.test_register_agents),
            ("Get Agent", self.test_get_agent),
            ("Create Context", self.test_create_context),
            ("Add Memories", self.test_add_memories),
            ("Get Memory", self.test_get_memory),
            ("Get Agent Memories", self.test_get_agent_memories),
            ("Retrieve Context", self.test_retrieve_context),
            ("Create Relationship", self.test_create_relationship),
            ("Get Related Memories", self.test_get_related_memories),
            ("Share Memories", self.test_share_memories),
            ("Get Shared Memories", self.test_get_shared_memories),
            ("Agent Statistics", self.test_get_agent_stats),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                results[test_name] = False
            time.sleep(0.1)  # Small delay between tests
        
        # Print summary
        print("\n" + "="*60)
        print("📊 Test Summary")
        print("="*60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
        
        print("="*60)
        print(f"✅ Passed: {passed}/{total}")
        print("="*60 + "\n")
        
        return passed == total


if __name__ == "__main__":
    # Check if server is running
    print(f"🔗 Connecting to {BASE_URL}...")
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=3)
            print(f"✅ Connected to MemGraph API (Status: {response.status_code})")
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt < max_retries - 1:
                print(f"⏳ Waiting for server... (attempt {attempt + 1}/{max_retries})")
                time.sleep(1)
            else:
                print("❌ ERROR: MemGraph API server is not running!")
                print(f"   Make sure the server is running on {BASE_URL}")
                print("   Start with: python -m uvicorn memgraph.api.main:app --reload")
                sys.exit(1)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            sys.exit(1)
    
    # Run tests
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
