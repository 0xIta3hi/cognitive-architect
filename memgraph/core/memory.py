"""
MemGraph Core Library

Main interface for developers to interact with the memory graph system.
This is the clean API that users will import and use.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from .graph import MemGraphDB
from .models import (
    Agent, Memory, Context, MemoryType, RelationType,
    AddMemoryRequest, RetrieveContextRequest, ShareMemoryRequest,
    MemoryResponse, ContextResponse, MemoryRelationship
)


class MemoryGraph:
    """
    Main interface for MemGraph - AI agent memory system.
    
    Usage:
        memory = MemoryGraph(neo4j_uri="bolt://localhost:7687")
        
        # Add a memory
        memory.add(
            agent_id="research_assistant",
            content="User prefers concise explanations",
            memory_type="preference"
        )
        
        # Retrieve context
        context = memory.retrieve(
            agent_id="research_assistant",
            query="How should I explain AI concepts?",
            limit=5
        )
    """
    
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "memgraph123"
    ):
        """
        Initialize MemoryGraph connection.
        
        Args:
            neo4j_uri: Neo4j database URI
            neo4j_user: Database username
            neo4j_password: Database password
        """
        self.graph = MemGraphDB(neo4j_uri, neo4j_user, neo4j_password)
    
    def close(self) -> None:
        """Close database connection."""
        self.graph.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    # ══════════════════════════════════════════════════════════════
    # AGENT MANAGEMENT
    # ══════════════════════════════════════════════════════════════
    
    def register_agent(
        self,
        agent_id: str,
        name: str,
        agent_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """
        Register a new agent or get existing one.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable agent name
            agent_type: Type of agent (research, writing, coding, etc.)
            metadata: Additional agent metadata
            
        Returns:
            Agent model
            
        Example:
            agent = memory.register_agent(
                agent_id="research_assistant_001",
                name="Research Assistant",
                agent_type="research",
                metadata={"version": "1.0"}
            )
        """
        agent = Agent(
            id=agent_id,
            name=name,
            type=agent_type,
            metadata=metadata or {}
        )
        return self.graph.get_or_create_agent(agent)
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent model or None if not found
        """
        return self.graph.get_agent(agent_id)
    
    # ══════════════════════════════════════════════════════════════
    # MEMORY OPERATIONS
    # ══════════════════════════════════════════════════════════════
    
    def add(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "fact",
        importance: float = 0.5,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Add a new memory to the graph.
        
        Args:
            agent_id: ID of agent creating the memory
            content: Memory content/text
            memory_type: Type of memory (preference, fact, action, conversation, etc.)
            importance: Importance score 0.0-1.0 (default 0.5)
            context_id: Optional context/session ID
            metadata: Additional metadata dictionary
            
        Returns:
            Created Memory model
            
        Example:
            memory.add(
                agent_id="research_assistant",
                content="User is working on a thesis about graph neural networks",
                memory_type="fact",
                importance=0.9,
                metadata={"topic": "research", "verified": True}
            )
        """
        # Ensure agent exists
        agent = self.graph.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found. Register agent first.")
        
        # Create memory
        memory = Memory(
            content=content,
            memory_type=MemoryType(memory_type),
            importance=importance,
            metadata=metadata or {}
        )
        
        return self.graph.add_memory(agent_id, memory, context_id)
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory model or None if not found
        """
        return self.graph.get_memory(memory_id)
    
    def retrieve(
        self,
        agent_id: str,
        query: str,
        limit: int = 5,
        time_range_days: Optional[int] = None,
        memory_types: Optional[List[str]] = None,
        min_importance: float = 0.0
    ) -> ContextResponse:
        """
        Retrieve relevant context for a query.
        
        This is the core retrieval method that agents use to get relevant
        past memories for their current task.
        
        Args:
            agent_id: Agent making the query
            query: Natural language query
            limit: Maximum number of memories to return
            time_range_days: Only return memories from last N days
            memory_types: Filter by memory types (list of strings)
            min_importance: Minimum importance threshold
            
        Returns:
            ContextResponse with relevant memories
            
        Example:
            context = memory.retrieve(
                agent_id="research_assistant",
                query="What do I know about the user's research?",
                limit=10,
                time_range_days=30,
                min_importance=0.5
            )
            
            for mem_response in context.memories:
                print(mem_response.memory.content)
        """
        # Convert memory types to enums
        type_enums = None
        if memory_types:
            type_enums = [MemoryType(t) for t in memory_types]
        
        # Get agent's memories with filters
        memories = self.graph.get_agent_memories(
            agent_id=agent_id,
            limit=limit,
            memory_types=type_enums,
            time_range_days=time_range_days
        )
        
        # Filter by importance
        if min_importance > 0.0:
            memories = [
                m for m in memories 
                if m.memory.importance >= min_importance
            ]
        
        # TODO: Add semantic search ranking when vector store is integrated
        # For now, return by recency and importance
        memories.sort(
            key=lambda m: (m.memory.importance, m.memory.created_at),
            reverse=True
        )
        
        return ContextResponse(
            memories=memories[:limit],
            total_found=len(memories),
            query=query
        )
    
    def get_agent_memories(
        self,
        agent_id: str,
        limit: int = 10,
        memory_types: Optional[List[str]] = None,
        time_range_days: Optional[int] = None
    ) -> List[MemoryResponse]:
        """
        Get all memories for an agent.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum memories to return
            memory_types: Filter by types
            time_range_days: Only recent memories
            
        Returns:
            List of MemoryResponse objects
        """
        type_enums = None
        if memory_types:
            type_enums = [MemoryType(t) for t in memory_types]
        
        return self.graph.get_agent_memories(
            agent_id=agent_id,
            limit=limit,
            memory_types=type_enums,
            time_range_days=time_range_days
        )
    
    # ══════════════════════════════════════════════════════════════
    # CONTEXT/SESSION MANAGEMENT
    # ══════════════════════════════════════════════════════════════
    
    def create_context(
        self,
        name: str,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Context:
        """
        Create a new context/session.
        
        Contexts group related memories together (e.g., a conversation,
        a research session, a coding task).
        
        Args:
            name: Context name
            summary: Optional summary
            metadata: Additional metadata
            
        Returns:
            Created Context model
            
        Example:
            ctx = memory.create_context(
                name="Literature Review - Neural Networks",
                summary="Reviewing recent papers on transformer architectures",
                metadata={"topic": "AI", "papers": 5}
            )
        """
        context = Context(
            name=name,
            summary=summary,
            metadata=metadata or {}
        )
        return self.graph.create_context(context)
    
    # ══════════════════════════════════════════════════════════════
    # MEMORY RELATIONSHIPS
    # ══════════════════════════════════════════════════════════════
    
    def relate(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relation_type: str = "relates_to",
        strength: float = 0.5,
        reason: Optional[str] = None
    ) -> MemoryRelationship:
        """
        Create a relationship between two memories.
        
        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            relation_type: Type of relationship (supports, contradicts, elaborates, etc.)
            strength: Relationship strength 0.0-1.0
            reason: Optional explanation for the relationship
            
        Returns:
            Created MemoryRelationship
            
        Example:
            memory.relate(
                from_memory_id="mem_abc123",
                to_memory_id="mem_def456",
                relation_type="supports",
                strength=0.8,
                reason="Both discuss the same research topic"
            )
        """
        relationship = MemoryRelationship(
            from_memory_id=from_memory_id,
            to_memory_id=to_memory_id,
            type=RelationType(relation_type),
            strength=strength,
            reason=reason
        )
        return self.graph.create_memory_relationship(relationship)
    
    def get_related(
        self,
        memory_id: str,
        max_depth: int = 2,
        min_strength: float = 0.0
    ) -> List[MemoryResponse]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: Starting memory ID
            max_depth: How many hops to traverse (1-3)
            min_strength: Minimum relationship strength
            
        Returns:
            List of related MemoryResponse objects
            
        Example:
            related = memory.get_related(
                memory_id="mem_abc123",
                max_depth=2,
                min_strength=0.5
            )
        """
        return self.graph.get_related_memories(
            memory_id=memory_id,
            max_depth=min(max_depth, 3),  # Cap at 3 for performance
            min_strength=min_strength
        )
    
    # ══════════════════════════════════════════════════════════════
    # CROSS-AGENT SHARING
    # ══════════════════════════════════════════════════════════════
    
    def share(
        self,
        from_agent_id: str,
        to_agent_id: str,
        memory_ids: List[str],
        permission: str = "read"
    ) -> int:
        """
        Share memories from one agent to another.
        
        This enables cross-agent knowledge sharing - a key feature of MemGraph.
        
        Args:
            from_agent_id: Source agent ID
            to_agent_id: Target agent ID
            memory_ids: List of memory IDs to share
            permission: Access permission (read or write)
            
        Returns:
            Number of memories successfully shared
            
        Example:
            memory.share(
                from_agent_id="research_assistant",
                to_agent_id="writing_assistant",
                memory_ids=["mem_abc123", "mem_def456"],
                permission="read"
            )
        """
        shared_count = 0
        for memory_id in memory_ids:
            success = self.graph.share_memory(
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                memory_id=memory_id,
                permission=permission
            )
            if success:
                shared_count += 1
        
        return shared_count
    
    def get_shared_memories(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[MemoryResponse]:
        """
        Get memories that have been shared with an agent.
        
        Args:
            agent_id: Agent ID
            limit: Maximum memories to return
            
        Returns:
            List of shared MemoryResponse objects
            
        Example:
            shared = memory.get_shared_memories(
                agent_id="writing_assistant",
                limit=20
            )
        """
        return self.graph.get_shared_memories(agent_id, limit)
    
    # ══════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ══════════════════════════════════════════════════════════════
    
    def health_check(self) -> bool:
        """
        Check if the memory system is healthy.
        
        Returns:
            True if connected and operational
        """
        return self.graph.health_check()
    
    def clear_all(self) -> None:
        """
        DANGER: Clear all data from the database.
        
        Only use in development/testing environments!
        This action cannot be undone.
        """
        self.graph.clear_database()
    
    # ══════════════════════════════════════════════════════════════
    # STATISTICS & INSIGHTS
    # ══════════════════════════════════════════════════════════════
    
    def get_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get statistics about an agent's memory usage.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary with statistics
            
        Example:
            stats = memory.get_stats("research_assistant")
            print(f"Total memories: {stats['total_memories']}")
        """
        memories = self.get_agent_memories(agent_id, limit=1000)
        
        type_counts = {}
        for mem_resp in memories:
            mem_type = mem_resp.memory.memory_type.value
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
        
        importances = [m.memory.importance for m in memories]
        avg_importance = sum(importances) / len(importances) if importances else 0.0
        
        return {
            "agent_id": agent_id,
            "total_memories": len(memories),
            "memory_types": type_counts,
            "average_importance": round(avg_importance, 2),
            "oldest_memory": memories[-1].memory.created_at if memories else None,
            "newest_memory": memories[0].memory.created_at if memories else None
        }


# ══════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION FOR QUICK START
# ══════════════════════════════════════════════════════════════


def create_memory_graph(
    uri: str = "neo4j://localhost:7687",
    user: str = "neo4j",
    password: str = "1234578"
) -> MemoryGraph:
    """
    Quick factory function to create a MemoryGraph instance.
    
    Args:
        uri: Neo4j URI
        user: Database user
        password: Database password
        
    Returns:
        Initialized MemoryGraph instance
        
    Example:
        from memgraph import create_memory_graph
        
        memory = create_memory_graph()
        memory.register_agent("my_agent", "My Agent")
    """
    return MemoryGraph(neo4j_uri=uri, neo4j_user=user, neo4j_password=password)