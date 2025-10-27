# MemGraph
### Open-Source memory layer for AI agents with persistant context graphs.

# Features
- Persistant Memory: Context survives beyond single conversation.
- knowledge Graphs: Relationships between memories for better recall
- Cross-Agent sharing: Multiple Agents access shared knowledge.
- Temporal awareness: Trace how context evolves over time.
- Simple API: 2-3 lines to add memory to any LangChain agent.

## Quick Start
```python
from memgraph import MemoryGraph

memory = MemoryGraph()
memory.add(agent_id="assistant", content="User prefers brief answers")
context = memory.retrieve(agent_id="assistant", query="How to respond?")
```

## Status
🚧 **Early Development** - MVP launching Nov 12, 2025

## Roadmap
- [x] Core architecture design
- [ ] Neo4j integration
- [ ] Basic memory storage/retrieval
- [ ] LangChain integration
- [ ] Cross-agent sharing
- [ ] Visual graph viewer
- [ ] Documentation

## Contributing
Built for university research labs and open source contributors. 
PRs welcome!

## License
MIT

---
Built by a college student who believes AI agents deserve better memory 🚀
