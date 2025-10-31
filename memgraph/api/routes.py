"""
MemGraph REST API endpoints.

Organized by resource type: agents, memories, contexts, relationships, sharing.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional, Dict, Any
import logging

from memgraph.core.memory import MemoryGraph
from memgraph.core.models import (
    Agent, Memory, Context, MemoryType, RelationType,
    AddMemoryRequest, RetrieveContextRequest, ShareMemoryRequest,
    MemoryResponse, ContextResponse, MemoryRelationship
)
from memgraph.api.main import get_memory_graph

logger = logging.getLogger(__name__)

# Create routers for different resource groups
router_agents = APIRouter(prefix="/agents", tags=["Agents"])
router_memories = APIRouter(prefix="/memories", tags=["Memories"])
router_contexts = APIRouter(prefix="/contexts", tags=["Contexts"])
router_relationships = APIRouter(prefix="/relationships", tags=["Relationships"])
router_sharing = APIRouter(prefix="/sharing", tags=["Cross-Agent Sharing"])


# ══════════════════════════════════════════════════════════════
# AGENT ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router_agents.post("", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def register_agent(
    agent_id: str = Query(..., min_length=1, description="Unique agent identifier"),
    name: str = Query(..., min_length=1, description="Human-readable agent name"),
    agent_type: str = Query("general", description="Type of agent (research, writing, coding, etc.)"),
    memory_graph: MemoryGraph = Depends(get_memory_graph)
):
    """
    Register a new agent or get existing one.
    
    **Example:**
    ```
    POST /agents?agent_id=research_001&name=Research Assistant&agent_type=research
    ```
    """
    try:
        agent = memory_graph.register_agent(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type
        )
        logger.info(f"✓ Registered agent: {agent_id}")
        return agent
    except Exception as e:
        logger.error(f"✗ Failed to register agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router_agents.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    memory_graph: MemoryGraph = Depends(get_memory_graph)
):
    """
    Retrieve an agent by ID.
    
    **Example:**
    ```
    GET /agents/research_001
    ```
    """
    try:
        agent = memory_graph.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Failed to get agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router_agents.get("/{agent_id}/stats", response_model=Dict[str, Any])
async def get_agent_stats(
    agent_id: str,
    memory_graph: MemoryGraph = Depends(get_memory_graph)
):
    """
    Get statistics about an agent's memory usage.
    
    **Example:**
    ```
    GET /agents/research_001/stats
    ```
    
    Returns:
        - total_memories: Total number of memories
        - average_importance: Average importance score
        - memory_types: Count by memory type
        - oldest_memory: Oldest memory timestamp
        - newest_memory: Newest memory timestamp
    """
    try:
        agent = memory_graph.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        stats = memory_graph.get_stats(agent_id)
        logger.info(f"✓ Retrieved stats for agent: {agent_id}")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Failed to get agent stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ══════════════════════════════════════════════════════════════
# MEMORY ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router_memories.post("", response_model=Memory, status_code=status.HTTP_201_CREATED)
async def add_memory(
    agent_id: str = Query(..., min_length=1, description="Agent ID"),
    content: str = Query(..., min_length=1, max_length=10000, description="Memory content"),
    memory_type: str = Query("fact", description="Type: preference, fact, action, conversation, decision, observation"),
    importance: float = Query(0.5, ge=0.0, le=1.0, description="Importance score 0.0-1.0"),
    context_id: Optional[str] = Query(None, description="Optional context/session ID"),
    memory_graph: MemoryGraph = Depends(get_memory_graph)
):
    """
    Add a new memory to the graph.
    
    **Example:**
    ```
    POST /memories?agent_id=research_001&content=User prefers technical explanations&memory_type=preference&importance=0.8
    ```
    """
    try:
        memory = memory_graph.add(
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            context_id=context_id
        )
        logger.info(f"✓ Added memory: {memory.id}")
        return memory
    except ValueError as e:
        logger.error(f"✗ Invalid memory request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"✗ Failed to add memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router_memories.get("/{memory_id}", response_model=Memory)
async def get_memory(
    memory_id: str,
    memory_graph: MemoryGraph = Depends(get_memory_graph)
):
    """
    Retrieve a specific memory by ID.
    
    **Example:**
    ```
    GET /memories/mem_abc123def456
    ```
    """
    try:
        memory = memory_graph.get(memory_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory {memory_id} not found"
            )
        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Failed to get memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router_memories.get("/agent/{agent_id}", response_model=List[MemoryResponse])
async def get_agent_memories(
    agent_id: str,
    limit: int = Query(10, ge=1, le=100, description="Max memories to return"),
    memory_types: Optional[str] = Query(None, description="Comma-separated memory types to filter"),
    time_range_days: Optional[int] = Query(None, ge=1, description="Only return memories from last N days"),
    memory_graph: MemoryGraph = Depends(get_memory_graph)
):
    """
    Get all memories for an agent.
    
    **Example:**
    ```
    GET /memories/agent/research_001?limit=20&memory_types=fact,preference&time_range_days=30
    ```
    """
    try:
        # Parse memory types if provided
        type_list = None
        if memory_types:
            type_list = [t.strip() for t in memory_types.split(",")]
        
        memories = memory_graph.get_agent_memories(
            agent_id=agent_id,
            limit=limit,
            memory_types=type_list,
            time_range_days=time_range_days
        )
        logger.info(f"✓ Retrieved {len(memories)} memories for agent: {agent_id}")
        return memories
    except ValueError as e:
        logger.error(f"✗ Invalid filter: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"✗ Failed to get agent memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ══════════════════════════════════════════════════════════════
# CONTEXT ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router_contexts.post("", response_model=Context, status_code=status.HTTP_201_CREATED)
async def create_context(
    name: str = Query(..., min_length=1, max_length=300, description="Context name"),
    summary: Optional[str] = Query(None, max_length=5000, description="Optional summary"),
    memory_graph: MemoryGraph = Depends(get_memory_graph)
):
    """
    Create a new context/session.
    
    Contexts group related memories together (e.g., a conversation, research session).
    
    **Example:**
    ```
    POST /contexts?name=Literature Review - Neural Networks&summary=Reviewing recent papers
    ```
    """
    try:
        context = memory_graph.create_context(
            name=name,
            summary=summary
        )
        logger.info(f"✓ Created context: {context.id}")
        return context
    except Exception as e:
        logger.error(f"✗ Failed to create context: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ══════════════════════════════════════════════════════════════
# RETRIEVAL ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router_memories.post("/retrieve")
async def retrieve_context(
    agent_id: str = Query(..., min_length=1, description="Agent ID"),
    query: str = Query(..., min_length=1, max_length=1000, description="Natural language query"),
    limit: int = Query(5, ge=1, le=50, description="Max memories to return"),
    time_range_days: Optional[int] = Query(None, ge=1, description="Only recent memories (N days)"),
    memory_types: Optional[str] = Query(None, description="Comma-separated memory types"),
    min_importance: float = Query(0.0, ge=0.0, le=1.0, description="Minimum importance threshold"),
    memory_graph: MemoryGraph = Depends(get_memory_graph)
) -> ContextResponse:
    """
    Retrieve relevant context for a query.
    
    This is the core retrieval method agents use to get relevant past memories.
    
    **Example:**
    ```
    POST /memories/retrieve?agent_id=research_001&query=What do I know about the user&limit=10&min_importance=0.5
    ```
    
    Returns:
        - memories: List of relevant MemoryResponse objects
        - total_found: Total memories matching criteria
        - query: Echo of the query
        - retrieved_at: Timestamp
    """
    try:
        type_list = None
        if memory_types:
            type_list = [t.strip() for t in memory_types.split(",")]
        
        context = memory_graph.retrieve(
            agent_id=agent_id,
            query=query,
            limit=limit,
            time_range_days=time_range_days,
            memory_types=type_list,
            min_importance=min_importance
        )
        logger.info(f"✓ Retrieved context for query: '{query}' ({len(context.memories)} results)")
        return context
    except ValueError as e:
        logger.error(f"✗ Invalid retrieval request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"✗ Failed to retrieve context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ══════════════════════════════════════════════════════════════
# RELATIONSHIP ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router_relationships.post("", response_model=MemoryRelationship, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    from_memory_id: str = Query(..., min_length=1, description="Source memory ID"),
    to_memory_id: str = Query(..., min_length=1, description="Target memory ID"),
    relation_type: str = Query("relates_to", description="Type: supports, contradicts, elaborates, follows, relates_to, supersedes"),
    strength: float = Query(0.5, ge=0.0, le=1.0, description="Relationship strength 0.0-1.0"),
    reason: Optional[str] = Query(None, max_length=500, description="Optional explanation"),
    memory_graph: MemoryGraph = Depends(get_memory_graph)
):
    """
    Create a relationship between two memories.
    
    **Example:**
    ```
    POST /relationships?from_memory_id=mem_abc&to_memory_id=mem_def&relation_type=supports&strength=0.8
    ```
    """
    try:
        relationship = memory_graph.relate(
            from_memory_id=from_memory_id,
            to_memory_id=to_memory_id,
            relation_type=relation_type,
            strength=strength,
            reason=reason
        )
        logger.info(f"✓ Created relationship: {from_memory_id} → {to_memory_id}")
        return relationship
    except Exception as e:
        logger.error(f"✗ Failed to create relationship: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router_relationships.get("/{memory_id}")
async def get_related_memories(
    memory_id: str,
    max_depth: int = Query(2, ge=1, le=3, description="Max traversal depth"),
    min_strength: float = Query(0.0, ge=0.0, le=1.0, description="Minimum relationship strength"),
    memory_graph: MemoryGraph = Depends(get_memory_graph)
) -> List[MemoryResponse]:
    """
    Get memories related to a given memory.
    
    Traverses relationship graph to find connected memories.
    
    **Example:**
    ```
    GET /relationships/mem_abc123?max_depth=2&min_strength=0.5
    ```
    """
    try:
        related = memory_graph.get_related(
            memory_id=memory_id,
            max_depth=max_depth,
            min_strength=min_strength
        )
        logger.info(f"✓ Found {len(related)} related memories for: {memory_id}")
        return related
    except Exception as e:
        logger.error(f"✗ Failed to get related memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ══════════════════════════════════════════════════════════════
# CROSS-AGENT SHARING ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router_sharing.post("/grant")
async def share_memories(
    from_agent_id: str = Query(..., min_length=1, description="Source agent ID"),
    to_agent_id: str = Query(..., min_length=1, description="Target agent ID"),
    memory_ids: str = Query(..., min_length=1, description="Comma-separated memory IDs to share"),
    permission: str = Query("read", regex="^(read|write)$", description="Access permission: read or write"),
    memory_graph: MemoryGraph = Depends(get_memory_graph)
):
    """
    Share memories from one agent to another.
    
    **Example:**
    ```
    POST /sharing/grant?from_agent_id=research_001&to_agent_id=writing_001&memory_ids=mem_abc,mem_def&permission=read
    ```
    
    Returns:
        - shared_count: Number of memories successfully shared
    """
    try:
        ids = [id.strip() for id in memory_ids.split(",")]
        
        shared_count = memory_graph.share(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            memory_ids=ids,
            permission=permission
        )
        logger.info(f"✓ Shared {shared_count} memories: {from_agent_id} → {to_agent_id}")
        return {
            "shared_count": shared_count,
            "from_agent_id": from_agent_id,
            "to_agent_id": to_agent_id,
            "permission": permission
        }
    except ValueError as e:
        logger.error(f"✗ Invalid sharing request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"✗ Failed to share memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router_sharing.get("/{agent_id}")
async def get_shared_memories(
    agent_id: str,
    limit: int = Query(10, ge=1, le=100, description="Max memories to return"),
    memory_graph: MemoryGraph = Depends(get_memory_graph)
) -> List[MemoryResponse]:
    """
    Get memories shared with an agent.
    
    **Example:**
    ```
    GET /sharing/writing_001?limit=20
    ```
    """
    try:
        memories = memory_graph.get_shared_memories(
            agent_id=agent_id,
            limit=limit
        )
        logger.info(f"✓ Retrieved {len(memories)} shared memories for agent: {agent_id}")
        return memories
    except Exception as e:
        logger.error(f"✗ Failed to get shared memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
