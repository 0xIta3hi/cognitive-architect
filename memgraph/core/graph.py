"""
MemGraph Neo4j Operations

Handles all interactions with Neo4j graph database.
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from neo4j import GraphDatabase as Neo4jDriver, Driver, Session
from neo4j.exceptions import ServiceUnavailable, Neo4jError
from neo4j.time import DateTime as Neo4jDateTime

from .models import (
    Agent, Memory, Context, Entity, MemoryType, RelationType,
    MemoryRelationship, MemoryResponse
)


# ══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════

def _convert_neo4j_datetime(dt: Any) -> datetime:
    """
    Convert Neo4j DateTime to Python datetime.
    
    Args:
        dt: Neo4j DateTime object or Python datetime
        
    Returns:
        Python datetime object
    """
    if isinstance(dt, Neo4jDateTime):
        # Convert Neo4j DateTime to Python datetime
        return dt.to_native()
    elif isinstance(dt, datetime):
        return dt
    else:
        return dt


class MemGraphDB:
    """Neo4j graph database operations for MemGraph."""
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j bolt URI (e.g., bolt://localhost:7687)
            user: Database username
            password: Database password
        """
        try:
            self.driver: Driver = Neo4jDriver.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
        except ServiceUnavailable as e:
            raise ConnectionError(f"Cannot connect to Neo4j at {uri}: {e}")
        except Exception as e:
            raise ConnectionError(f"Neo4j connection error: {e}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.driver:
            self.driver.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    # ══════════════════════════════════════════════════════════════
    # AGENT OPERATIONS
    # ══════════════════════════════════════════════════════════════
    
    def create_agent(self, agent: Agent) -> Agent:
        """
        Create a new agent in the graph.
        
        Args:
            agent: Agent model to create
            
        Returns:
            Created Agent model
        """
        query = """
        CREATE (a:Agent {
            id: $id,
            name: $name,
            type: $type,
            created_at: datetime($created_at),
            metadata: $metadata
        })
        RETURN a
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                id=agent.id,
                name=agent.name,
                type=agent.type,
                created_at=agent.created_at.isoformat(),
                metadata=json.dumps(agent.metadata)
            )
            record = result.single()
            if not record:
                raise ValueError(f"Failed to create agent {agent.id}")
            return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Retrieve agent by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent model or None if not found
        """
        query = """
        MATCH (a:Agent {id: $id})
        RETURN a
        """
        
        with self.driver.session() as session:
            result = session.run(query, id=agent_id)
            record = result.single()
            if not record:
                return None
            
            node = record["a"]
            metadata = {}
            if node.get("metadata"):
                try:
                    metadata = json.loads(node["metadata"])
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            
            return Agent(
                id=node["id"],
                name=node["name"],
                type=node["type"],
                created_at=_convert_neo4j_datetime(node["created_at"]),
                metadata=metadata
            )
    
    def get_or_create_agent(self, agent: Agent) -> Agent:
        """Get existing agent or create if doesn't exist."""
        existing = self.get_agent(agent.id)
        if existing:
            return existing
        return self.create_agent(agent)
    
    # ══════════════════════════════════════════════════════════════
    # MEMORY OPERATIONS
    # ══════════════════════════════════════════════════════════════
    
    def add_memory(
        self,
        agent_id: str,
        memory: Memory,
        context_id: Optional[str] = None
    ) -> Memory:
        """
        Add a new memory to the graph.
        
        Args:
            agent_id: ID of agent creating the memory
            memory: Memory model to add
            context_id: Optional context ID to link memory to
            
        Returns:
            Created Memory model
        """
        query = """
        MATCH (a:Agent {id: $agent_id})
        CREATE (m:Memory {
            id: $id,
            content: $content,
            memory_type: $memory_type,
            importance: $importance,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at),
            embedding_id: $embedding_id,
            metadata: $metadata
        })
        CREATE (a)-[:CREATED {at: datetime($created_at)}]->(m)
        """
        
        # Add context relationship if provided
        if context_id:
            query += """
            WITH m
            MATCH (c:Context {id: $context_id})
            CREATE (m)-[:PART_OF {at: datetime($created_at)}]->(c)
            """
        
        query += """
        RETURN m
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                agent_id=agent_id,
                id=memory.id,
                content=memory.content,
                memory_type=memory.memory_type.value,
                importance=memory.importance,
                created_at=memory.created_at.isoformat(),
                updated_at=memory.updated_at.isoformat(),
                embedding_id=memory.embedding_id,
                metadata=json.dumps(memory.metadata),
                context_id=context_id
            )
            record = result.single()
            if not record:
                raise ValueError(f"Failed to create memory {memory.id}")
            return memory
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory model or None if not found
        """
        query = """
        MATCH (m:Memory {id: $id})
        RETURN m
        """
        
        with self.driver.session() as session:
            result = session.run(query, id=memory_id)
            record = result.single()
            if not record:
                return None
            
            node = record["m"]
            metadata = {}
            if node.get("metadata"):
                try:
                    metadata = json.loads(node["metadata"])
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            
            return Memory(
                id=node["id"],
                content=node["content"],
                memory_type=MemoryType(node["memory_type"]),
                importance=node["importance"],
                created_at=_convert_neo4j_datetime(node["created_at"]),
                updated_at=_convert_neo4j_datetime(node["updated_at"]),
                embedding_id=node.get("embedding_id"),
                metadata=metadata
            )
    
    def get_agent_memories(
        self,
        agent_id: str,
        limit: int = 10,
        memory_types: Optional[List[MemoryType]] = None,
        time_range_days: Optional[int] = None
    ) -> List[MemoryResponse]:
        """
        Get memories created by an agent.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of memories to return
            memory_types: Filter by memory types
            time_range_days: Only return memories from last N days
            
        Returns:
            List of MemoryResponse objects
        """
        query = """
        MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory)
        """
        
        # Add filters
        where_clauses = []
        if memory_types:
            types_list = [t.value for t in memory_types]
            where_clauses.append("m.memory_type IN $memory_types")
        
        if time_range_days:
            where_clauses.append("c.at > datetime() - duration('P' + $days + 'D')")
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += """
        RETURN m, a.name as agent_name, c.at as created_at
        ORDER BY c.at DESC
        LIMIT $limit
        """
        
        params: Dict[str, Any] = {
            "agent_id": agent_id,
            "limit": limit
        }
        
        if memory_types:
            params["memory_types"] = [t.value for t in memory_types]
        if time_range_days:
            params["days"] = str(time_range_days)
        
        with self.driver.session() as session:
            result = session.run(query, **params)
            
            responses = []
            for record in result:
                node = record["m"]
                metadata = {}
                if node.get("metadata"):
                    try:
                        metadata = json.loads(node["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}
                
                memory = Memory(
                    id=node["id"],
                    content=node["content"],
                    memory_type=MemoryType(node["memory_type"]),
                    importance=node["importance"],
                    created_at=_convert_neo4j_datetime(node["created_at"]),
                    updated_at=_convert_neo4j_datetime(node["updated_at"]),
                    embedding_id=node.get("embedding_id"),
                    metadata=metadata
                )
                
                responses.append(MemoryResponse(
                    memory=memory,
                    agent_name=record["agent_name"]
                ))
            
            return responses
    
    # ══════════════════════════════════════════════════════════════
    # CONTEXT OPERATIONS
    # ══════════════════════════════════════════════════════════════
    
    def create_context(self, context: Context) -> Context:
        """
        Create a new context in the graph.
        
        Args:
            context: Context model to create
            
        Returns:
            Created Context model
        """
        query = """
        CREATE (c:Context {
            id: $id,
            name: $name,
            started_at: datetime($started_at),
            ended_at: $ended_at,
            summary: $summary,
            metadata: $metadata
        })
        RETURN c
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                id=context.id,
                name=context.name,
                started_at=context.started_at.isoformat(),
                ended_at=context.ended_at.isoformat() if context.ended_at else None,
                summary=context.summary,
                metadata=json.dumps(context.metadata)
            )
            record = result.single()
            if not record:
                raise ValueError(f"Failed to create context {context.id}")
            return context
    
    # ══════════════════════════════════════════════════════════════
    # MEMORY RELATIONSHIPS
    # ══════════════════════════════════════════════════════════════
    
    def create_memory_relationship(
        self,
        relationship: MemoryRelationship
    ) -> MemoryRelationship:
        """
        Create a relationship between two memories.
        
        Args:
            relationship: MemoryRelationship model
            
        Returns:
            Created MemoryRelationship
        """
        query = """
        MATCH (m1:Memory {id: $from_id})
        MATCH (m2:Memory {id: $to_id})
        CREATE (m1)-[r:RELATES_TO {
            type: $type,
            strength: $strength,
            reason: $reason,
            created_at: datetime($created_at)
        }]->(m2)
        RETURN r
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                from_id=relationship.from_memory_id,
                to_id=relationship.to_memory_id,
                type=relationship.type.value,
                strength=relationship.strength,
                reason=relationship.reason,
                created_at=relationship.created_at.isoformat()
            )
            record = result.single()
            if not record:
                raise ValueError("Failed to create memory relationship")
            return relationship
    
    def get_related_memories(
        self,
        memory_id: str,
        max_depth: int = 2,
        min_strength: float = 0.0
    ) -> List[MemoryResponse]:
        """
        Get memories related to a given memory.
        
        Args:
            memory_id: Starting memory ID
            max_depth: Maximum traversal depth (1-3)
            min_strength: Minimum relationship strength
            
        Returns:
            List of related MemoryResponse objects
        """
        query = f"""
        MATCH (seed:Memory {{id: $memory_id}})
        MATCH path = (seed)-[r:RELATES_TO*1..{max_depth}]-(related:Memory)
        WHERE ALL(rel IN relationships(path) WHERE rel.strength >= $min_strength)
        WITH DISTINCT related, 
             relationships(path) as rels
        WITH related, 
             reduce(total = 0.0, rel IN rels | total + rel.strength) / size(rels) as avg_strength
        RETURN related, avg_strength
        ORDER BY avg_strength DESC, related.importance DESC
        LIMIT 10
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                memory_id=memory_id,
                min_strength=min_strength
            )
            
            responses = []
            for record in result:
                node = record["related"]
                metadata = {}
                if node.get("metadata"):
                    try:
                        metadata = json.loads(node["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}
                
                memory = Memory(
                    id=node["id"],
                    content=node["content"],
                    memory_type=MemoryType(node["memory_type"]),
                    importance=node["importance"],
                    created_at=_convert_neo4j_datetime(node["created_at"]),
                    updated_at=_convert_neo4j_datetime(node["updated_at"]),
                    embedding_id=node.get("embedding_id"),
                    metadata=metadata
                )
                
                responses.append(MemoryResponse(
                    memory=memory,
                    relevance_score=record["avg_strength"]
                ))
            
            return responses
    
    # ══════════════════════════════════════════════════════════════
    # CROSS-AGENT SHARING
    # ══════════════════════════════════════════════════════════════
    
    def share_memory(
        self,
        from_agent_id: str,
        to_agent_id: str,
        memory_id: str,
        permission: str = "read"
    ) -> bool:
        """
        Share a memory from one agent to another.
        
        Args:
            from_agent_id: Source agent ID
            to_agent_id: Target agent ID
            memory_id: Memory to share
            permission: Access permission (read/write)
            
        Returns:
            True if successful
        """
        query = """
        MATCH (from:Agent {id: $from_agent_id})
        MATCH (to:Agent {id: $to_agent_id})
        MATCH (from)-[:CREATED]->(m:Memory {id: $memory_id})
        MERGE (to)-[a:ACCESSED {
            at: datetime(),
            permission: $permission,
            shared_by: $from_agent_id
        }]->(m)
        RETURN a
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                memory_id=memory_id,
                permission=permission
            )
            return result.single() is not None
    
    def get_shared_memories(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[MemoryResponse]:
        """
        Get memories shared with an agent.
        
        Args:
            agent_id: Agent ID
            limit: Maximum number to return
            
        Returns:
            List of shared MemoryResponse objects
        """
        query = """
        MATCH (a:Agent {id: $agent_id})-[acc:ACCESSED]->(m:Memory)
        MATCH (creator:Agent)-[:CREATED]->(m)
        RETURN m, creator.name as source_agent, acc.at as accessed_at
        ORDER BY acc.at DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, agent_id=agent_id, limit=limit)
            
            responses = []
            for record in result:
                node = record["m"]
                metadata = {}
                if node.get("metadata"):
                    try:
                        metadata = json.loads(node["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}
                
                memory = Memory(
                    id=node["id"],
                    content=node["content"],
                    memory_type=MemoryType(node["memory_type"]),
                    importance=node["importance"],
                    created_at=_convert_neo4j_datetime(node["created_at"]),
                    updated_at=_convert_neo4j_datetime(node["updated_at"]),
                    embedding_id=node.get("embedding_id"),
                    metadata=metadata
                )
                
                responses.append(MemoryResponse(
                    memory=memory,
                    agent_name=record["source_agent"]
                ))
            
            return responses
    
    # ══════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ══════════════════════════════════════════════════════════════
    
    def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as health")
                return result.single()["health"] == 1
        except Exception:
            return False
    
    def clear_database(self) -> None:
        """
        DANGER: Clear all nodes and relationships.
        Only use in development/testing!
        """
        query = "MATCH (n) DETACH DELETE n"
        with self.driver.session() as session:
            session.run(query)