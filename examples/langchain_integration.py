"""
Example: Using MemGraph with LangChain Agents

This example demonstrates how to integrate MemGraph as a memory backend
for LangChain agents, enabling persistent context across conversations.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.tools import tool

from memgraph.integrations.langchain_agent import (
    create_langchain_memory,
    create_toolkit,
    MemGraphToolkit
)

# Configure LLM
llm = ChatOpenAI(temperature=0, model="gpt-4")


# ══════════════════════════════════════════════════════════════
# EXAMPLE 1: Research Agent with Memory
# ══════════════════════════════════════════════════════════════

def example_research_agent():
    """
    Create a research agent that remembers facts between conversations.
    """
    print("\n" + "="*60)
    print("📚 Research Agent with MemGraph Memory")
    print("="*60)
    
    # Create memory backend
    memory = create_langchain_memory(
        agent_id="research_agent",
        session_id="research_20231031_001",
        context_window_size=10,
        min_importance=0.6
    )
    
    # Define search tool
    @tool
    def search_wikipedia(query: str) -> str:
        """Search Wikipedia for information."""
        # Simulated search result
        return f"Wikipedia search for '{query}': [simulation result]"
    
    # Create agent
    tools = [search_wikipedia]
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        max_iterations=3
    )
    
    # Use the agent
    print("\n🤖 Agent: What can you tell me about neural networks?")
    response = agent.run(
        "What are the key components of neural networks? "
        "Remember this for future conversations."
    )
    print(f"\nAgent Response:\n{response}")
    
    # Second query (should use memory)
    print("\n🤖 Agent: Based on what you know, explain backpropagation")
    response = agent.run(
        "Using what you remember about neural networks, "
        "can you explain how backpropagation works?"
    )
    print(f"\nAgent Response:\n{response}")


# ══════════════════════════════════════════════════════════════
# EXAMPLE 2: Multi-Turn Conversation with Context
# ══════════════════════════════════════════════════════════════

def example_conversational_agent():
    """
    Create a conversational agent that maintains context across turns.
    """
    print("\n" + "="*60)
    print("💬 Conversational Agent with Persistent Context")
    print("="*60)
    
    # Create memory
    memory = create_langchain_memory(
        agent_id="chat_agent",
        session_id="chat_20231031_001",
        context_window_size=5
    )
    
    # Simple tools
    @tool
    def get_time() -> str:
        """Get current time."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    @tool
    def calculate(expression: str) -> str:
        """Calculate a math expression."""
        try:
            result = eval(expression)
            return str(result)
        except:
            return "Invalid expression"
    
    # Create agent
    tools = [get_time, calculate]
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        max_iterations=2
    )
    
    # Multi-turn conversation
    queries = [
        "Hello! My name is Alice. I'm interested in machine learning.",
        "What's the current time?",
        "Can you calculate 42 * 3?",
        "Based on what you know about me, what topics should I study?"
    ]
    
    for query in queries:
        print(f"\n👤 User: {query}")
        response = agent.run(query)
        print(f"🤖 Agent: {response}")


# ══════════════════════════════════════════════════════════════
# EXAMPLE 3: Agent with Memory Toolkit
# ══════════════════════════════════════════════════════════════

def example_agent_with_toolkit():
    """
    Create an agent that can programmatically manage its own memories.
    """
    print("\n" + "="*60)
    print("🧠 Agent with Memory Management Tools")
    print("="*60)
    
    # Create toolkit
    toolkit = create_toolkit(agent_id="memory_agent")
    
    # Agent can use toolkit methods
    print("\n📝 Agent stores a memory:")
    result = toolkit.add_memory(
        content="Python is a versatile language suitable for AI/ML",
        memory_type="fact",
        importance=0.9,
        tags=["python", "programming", "ai"]
    )
    print(f"   Result: {result}")
    
    print("\n📝 Agent stores another memory:")
    result = toolkit.add_memory(
        content="Tensorflow and PyTorch are popular ML frameworks",
        memory_type="fact",
        importance=0.85,
        tags=["ml", "frameworks"]
    )
    print(f"   Result: {result}")
    
    print("\n🔍 Agent retrieves relevant memories:")
    result = toolkit.retrieve_memories(
        query="What do I know about Python and ML?",
        limit=5,
        min_importance=0.7
    )
    print(f"   Found {result['count']} memories:")
    for mem in result['memories']:
        print(f"   - {mem['content']} (importance: {mem['importance']})")
    
    print("\n📊 Agent checks memory statistics:")
    result = toolkit.get_agent_stats()
    print(f"   Total memories: {result['total_memories']}")
    print(f"   Average importance: {result['average_importance']:.2f}")
    print(f"   Memory types: {result['memory_types']}")
    
    print("\n🔗 Agent creates memory relationships:")
    result = toolkit.relate_memories(
        from_content="Python is a versatile language suitable for AI/ML",
        to_content="Tensorflow and PyTorch are popular ML frameworks",
        relation_type="RELATES_TO",
        strength=0.9
    )
    print(f"   Relationship created: {result['success']}")


# ══════════════════════════════════════════════════════════════
# EXAMPLE 4: Specialized Domain Agent (Code Assistant)
# ══════════════════════════════════════════════════════════════

def example_code_assistant():
    """
    Create a code assistant that remembers coding patterns and preferences.
    """
    print("\n" + "="*60)
    print("💻 Code Assistant with Memory")
    print("="*60)
    
    # Create memory
    memory = create_langchain_memory(
        agent_id="code_assistant",
        session_id="coding_20231031_001",
        context_window_size=8,
        min_importance=0.5
    )
    
    # Code tools
    @tool
    def check_syntax(code: str) -> str:
        """Check Python syntax."""
        try:
            compile(code, '<string>', 'exec')
            return "Syntax OK"
        except SyntaxError as e:
            return f"Syntax Error: {e}"
    
    @tool
    def suggest_improvement(code: str) -> str:
        """Suggest code improvements."""
        # Simulated suggestions
        suggestions = []
        if "for i in range(len(" in code:
            suggestions.append("Consider using 'enumerate()' instead of 'range(len())'")
        if "except:" in code:
            suggestions.append("Avoid bare 'except:' clauses - specify exception type")
        return "\n".join(suggestions) if suggestions else "Code looks good!"
    
    # Create agent
    tools = [check_syntax, suggest_improvement]
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        max_iterations=2
    )
    
    # Code review conversation
    code_samples = [
        "for i in range(len(items)):\n    print(items[i])",
        "try:\n    result = risky_operation()\nexcept:\n    print('Error')"
    ]
    
    for i, code in enumerate(code_samples, 1):
        query = f"Review this code:\n```python\n{code}\n```\nRemember this pattern."
        print(f"\n👤 User: Please review code sample {i}")
        response = agent.run(query)
        print(f"🤖 Assistant:\n{response}")


if __name__ == "__main__":
    """
    Run examples (uncomment to run specific examples)
    """
    
    # Note: Requires OpenAI API key in environment
    # Set: OPENAI_API_KEY=your_key
    
    print("\n" + "="*60)
    print("🚀 MemGraph + LangChain Integration Examples")
    print("="*60)
    
    try:
        # Uncomment examples to run:
        
        # example_research_agent()
        # example_conversational_agent()
        example_agent_with_toolkit()
        # example_code_assistant()
        
        print("\n" + "="*60)
        print("✅ Examples completed")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
