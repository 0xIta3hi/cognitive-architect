"""
LangChain integration for MemGraph.

Provides memory backends and tools for LangChain agents to use MemGraph
as their persistent memory layer.

Example usage:
    from memgraph.integrations.langchain_agent import MemGraphMemory
    from langchain.agents import initialize_agent, AgentType
    from langchain.llms import OpenAI
    
    memory = MemGraphMemory(agent_id="research_agent")
    llm = OpenAI()
    
    agent = initialize_agent(
        tools=[...],
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True
    )
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from pydantic import Field

from memgraph.core.memory import MemoryGraph
from memgraph.core.models import MemoryType

logger = logging.getLogger(__name__)


class MemGraphMemory(BaseChatMemory):
    """
    LangChain memory backend using MemGraph for persistence.
    
    This memory backend stores conversation history and agent context
    in MemGraph's knowledge graph, enabling:
    - Persistent memory across sessions
    - Relationship tracking between memories
    - Cross-agent memory sharing
    - Rich context retrieval based on importance and relevance
    
    Attributes:
        memory_graph: MemoryGraph instance for persistence
        agent_id: Unique identifier for the agent using this memory
        session_id: Optional session identifier for grouping conversations
        return_messages: Whether to return message objects or strings
        human_prefix: Prefix for human messages
        ai_prefix: Prefix for AI messages
        context_window_size: Maximum memories to retrieve as context
        min_importance: Minimum importance threshold for memory retrieval
    """
    
    memory_graph: Any = Field(default=None)
    agent_id: str = Field(default="default_agent")
    session_id: Optional[str] = Field(default=None)
    return_messages: bool = Field(default=True)
    human_prefix: str = Field(default="Human")
    ai_prefix: str = Field(default="AI")
    context_window_size: int = Field(default=5)
    min_importance: float = Field(default=0.5)
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Save context from this conversation to MemGraph.
        
        Stores both human and AI messages as memories with relationships
        tracking the conversation flow.
        
        Args:
            inputs: Input dictionary containing user query
            outputs: Output dictionary containing agent response
        """
        try:
            # Extract input and output
            input_str = inputs.get("input", "")
            output_str = outputs.get("output", "")
            
            if not input_str or not output_str:
                logger.warning("Empty input or output, skipping save")
                return
            
            # Create context name
            context_name = f"Session: {self.session_id}" if self.session_id else "Default Session"
            
            # Save human message as memory
            human_memory = self.memory_graph.add(
                agent_id=self.agent_id,
                content=f"User: {input_str}",
                memory_type=MemoryType.CONVERSATION,
                importance=0.8,
                context_id=context_name,
                metadata={
                    "message_type": "human",
                    "session_id": self.session_id or "default",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Save AI response as memory
            ai_memory = self.memory_graph.add(
                agent_id=self.agent_id,
                content=f"Assistant: {output_str}",
                memory_type=MemoryType.CONVERSATION,
                importance=0.8,
                context_id=context_name,
                metadata={
                    "message_type": "ai",
                    "session_id": self.session_id or "default",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Create relationship between human and AI messages
            if human_memory and ai_memory:
                self.memory_graph._memory_graph.db.create_memory_relationship(
                    from_memory_id=human_memory.id,
                    to_memory_id=ai_memory.id,
                    relation_type="RESPONSE_TO",
                    strength=0.9,
                    reason="AI response to user query"
                )
            
            logger.info(f"✓ Saved conversation to MemGraph for agent {self.agent_id}")
            
        except Exception as e:
            logger.error(f"✗ Failed to save context: {e}")
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load memory variables for the agent.
        
        Retrieves relevant context from MemGraph to include in the prompt.
        
        Args:
            inputs: Input dictionary (typically contains current query)
            
        Returns:
            Dictionary with memory variables
        """
        try:
            query = inputs.get("input", "")
            
            if not query:
                return {self.memory_variables[0]: ""}
            
            # Retrieve relevant context from MemGraph
            context = self.memory_graph.retrieve(
                agent_id=self.agent_id,
                query=query,
                limit=self.context_window_size,
                min_importance=self.min_importance
            )
            
            # Format memories for the agent
            memory_text = self._format_memories(context)
            
            logger.info(f"✓ Retrieved {len(context.get('memories', []))} memories for context")
            
            return {self.memory_variables[0]: memory_text}
            
        except Exception as e:
            logger.error(f"✗ Failed to load memory variables: {e}")
            return {self.memory_variables[0]: ""}
    
    def _format_memories(self, context: Dict[str, Any]) -> str:
        """
        Format retrieved memories for inclusion in agent prompt.
        
        Args:
            context: Context dictionary from MemGraph.retrieve()
            
        Returns:
            Formatted string with relevant memories
        """
        if not context or not context.get("memories"):
            return ""
        
        formatted_memories = []
        for mem_resp in context["memories"]:
            memory = mem_resp.get("memory", {})
            importance = memory.get("importance", 0)
            content = memory.get("content", "")
            
            # Format with importance indicator
            formatted_memories.append(
                f"[Importance: {importance:.1f}] {content}"
            )
        
        if not formatted_memories:
            return ""
        
        return "Relevant Context:\n" + "\n".join(formatted_memories)
    
    @property
    def memory_variables(self) -> List[str]:
        """Return memory variable names."""
        return ["history"]
    
    def clear(self) -> None:
        """
        Clear memory for this agent.
        
        Note: This doesn't delete memories from MemGraph (for audit trail),
        but resets the session state.
        """
        logger.info(f"Cleared memory for agent {self.agent_id}")


class MemGraphToolkit:
    """
    Toolkit providing LangChain tools for MemGraph operations.
    
    Allows agents to programmatically interact with MemGraph during execution.
    """
    
    def __init__(self, memory_graph: MemoryGraph, agent_id: str):
        """
        Initialize the toolkit.
        
        Args:
            memory_graph: MemoryGraph instance
            agent_id: Agent identifier
        """
        self.memory_graph = memory_graph
        self.agent_id = agent_id
    
    def add_memory(
        self,
        content: str,
        memory_type: str = "fact",
        importance: float = 0.7,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Tool for agent to add memories.
        
        Args:
            content: Memory content
            memory_type: Type of memory (fact, observation, preference)
            importance: Importance score 0-1
            tags: Optional tags for organization
            
        Returns:
            Memory creation result
        """
        try:
            memory = self.memory_graph.add(
                agent_id=self.agent_id,
                content=content,
                memory_type=MemoryType[memory_type.upper()],
                importance=importance,
                metadata={"tags": tags or []}
            )
            
            return {
                "success": True,
                "memory_id": memory.id,
                "content": memory.content
            }
        except Exception as e:
            logger.error(f"✗ Failed to add memory: {e}")
            return {"success": False, "error": str(e)}
    
    def retrieve_memories(
        self,
        query: str,
        limit: int = 5,
        min_importance: float = 0.5
    ) -> Dict[str, Any]:
        """
        Tool for agent to retrieve memories.
        
        Args:
            query: Query string
            limit: Maximum memories to retrieve
            min_importance: Minimum importance threshold
            
        Returns:
            Retrieved memories
        """
        try:
            context = self.memory_graph.retrieve(
                agent_id=self.agent_id,
                query=query,
                limit=limit,
                min_importance=min_importance
            )
            
            memories = []
            for mem_resp in context.get("memories", []):
                memory = mem_resp.get("memory", {})
                memories.append({
                    "id": memory.get("id"),
                    "content": memory.get("content"),
                    "importance": memory.get("importance"),
                    "type": memory.get("type")
                })
            
            return {
                "success": True,
                "count": len(memories),
                "memories": memories
            }
        except Exception as e:
            logger.error(f"✗ Failed to retrieve memories: {e}")
            return {"success": False, "error": str(e)}
    
    def relate_memories(
        self,
        from_content: str,
        to_content: str,
        relation_type: str = "RELATES_TO",
        strength: float = 0.7
    ) -> Dict[str, Any]:
        """
        Tool for agent to create relationships between memories.
        
        Args:
            from_content: Content of first memory
            to_content: Content of second memory
            relation_type: Type of relationship
            strength: Relationship strength 0-1
            
        Returns:
            Relationship creation result
        """
        try:
            # Find memories by content
            from_memories = self.memory_graph.retrieve(
                agent_id=self.agent_id,
                query=from_content,
                limit=1
            ).get("memories", [])
            
            to_memories = self.memory_graph.retrieve(
                agent_id=self.agent_id,
                query=to_content,
                limit=1
            ).get("memories", [])
            
            if not from_memories or not to_memories:
                return {"success": False, "error": "Could not find memories"}
            
            from_memory_id = from_memories[0]["memory"]["id"]
            to_memory_id = to_memories[0]["memory"]["id"]
            
            self.memory_graph._memory_graph.db.create_memory_relationship(
                from_memory_id=from_memory_id,
                to_memory_id=to_memory_id,
                relation_type=relation_type,
                strength=strength,
                reason=f"Relationship created by agent {self.agent_id}"
            )
            
            return {
                "success": True,
                "from_memory_id": from_memory_id,
                "to_memory_id": to_memory_id,
                "relation_type": relation_type
            }
        except Exception as e:
            logger.error(f"✗ Failed to relate memories: {e}")
            return {"success": False, "error": str(e)}
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the agent's memories.
        
        Returns:
            Agent statistics
        """
        try:
            stats = self.memory_graph.get_stats(self.agent_id)
            return {
                "success": True,
                "total_memories": stats.get("total_memories", 0),
                "average_importance": stats.get("average_importance", 0),
                "memory_types": stats.get("memory_types", {})
            }
        except Exception as e:
            logger.error(f"✗ Failed to get stats: {e}")
            return {"success": False, "error": str(e)}


def create_langchain_memory(
    agent_id: str,
    session_id: Optional[str] = None,
    neo4j_uri: str = "neo4j://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "12345678",
    **kwargs
) -> MemGraphMemory:
    """
    Factory function to create a MemGraphMemory instance.
    
    Args:
        agent_id: Unique agent identifier
        session_id: Optional session identifier
        neo4j_uri: Neo4j connection URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
        **kwargs: Additional memory configuration
        
    Returns:
        MemGraphMemory instance ready for use
        
    Example:
        memory = create_langchain_memory(
            agent_id="research_agent",
            session_id="session_20231031_001"
        )
    """
    try:
        # Create MemoryGraph instance
        memory_graph = MemoryGraph(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password
        )
        
        # Create and return MemGraphMemory
        return MemGraphMemory(
            memory_graph=memory_graph,
            agent_id=agent_id,
            session_id=session_id,
            **kwargs
        )
    except Exception as e:
        logger.error(f"✗ Failed to create MemGraphMemory: {e}")
        raise


def create_toolkit(
    agent_id: str,
    neo4j_uri: str = "neo4j://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "12345678"
) -> MemGraphToolkit:
    """
    Factory function to create a MemGraphToolkit instance.
    
    Args:
        agent_id: Unique agent identifier
        neo4j_uri: Neo4j connection URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
        
    Returns:
        MemGraphToolkit instance with tools for agent use
        
    Example:
        toolkit = create_toolkit(agent_id="coding_agent")
        memory_result = toolkit.add_memory(
            content="Python is a great language",
            importance=0.8
        )
    """
    try:
        # Create MemoryGraph instance
        memory_graph = MemoryGraph(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password
        )
        
        # Create and return toolkit
        return MemGraphToolkit(
            memory_graph=memory_graph,
            agent_id=agent_id
        )
    except Exception as e:
        logger.error(f"✗ Failed to create MemGraphToolkit: {e}")
        raise
