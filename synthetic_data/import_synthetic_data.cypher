// ═══════════════════════════════════════════════════════════════
// Import Synthetic Agent Data into Memgraph
// Generated for research on graph attacks and temporal drift
// ═══════════════════════════════════════════════════════════════

// Step 1: Create Indices (for performance)
CREATE INDEX ON :Agent(id);
CREATE INDEX ON :Memory(id);

// Step 2: Import Agents
LOAD CSV FROM "/home/ita3hi/Projects/cognitive-architect/synthetic_data/agents.csv" WITH HEADER AS row
MERGE (a:Agent {id: row.id})
SET a.name = row.name,
    a.type = row.type,
    a.description = row.description,
    a.created_at = datetime(row.created_at);

// Step 3: Import Memories
LOAD CSV FROM "/home/ita3hi/Projects/cognitive-architect/synthetic_data/memories.csv" WITH HEADER AS row
MERGE (m:Memory {id: row.id})
SET m.content = row.content,
    m.memory_type = row.memory_type,
    m.importance = toFloat(row.importance),
    m.created_at = datetime(row.created_at);

// Step 4: Create Agent->Memory Relationships (CREATED)
LOAD CSV FROM "/home/ita3hi/Projects/cognitive-architect/synthetic_data/memories.csv" WITH HEADER AS row
MATCH (a:Agent {id: row.agent_id})
MATCH (m:Memory {id: row.id})
MERGE (a)-[c:CREATED]->(m)
SET c.at = m.created_at;

// Step 5: Create Memory->Memory Relationships (RELATES_TO)
LOAD CSV FROM "/home/ita3hi/Projects/cognitive-architect/synthetic_data/relationships.csv" WITH HEADER AS row
MATCH (source:Memory {id: row.source_id})
MATCH (target:Memory {id: row.target_id})
MERGE (source)-[r:RELATES_TO {type: row.type}]->(target)
SET r.strength = toFloat(row.strength),
    r.reason = row.reason,
    r.created_at = datetime(row.created_at);

// Verification
MATCH (a:Agent) RETURN count(a) as agents;
MATCH (m:Memory) RETURN count(m) as memories;
MATCH ()-[r:RELATES_TO]->() RETURN count(r) as relationships;
MATCH ()-[r:CREATED]->() RETURN count(r) as created_edges;
