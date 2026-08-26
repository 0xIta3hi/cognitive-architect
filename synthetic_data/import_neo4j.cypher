// ═══════════════════════════════════════════════════════════════
// Neo4j Desktop Import Script: Synthetic Agent Data
// ═══════════════════════════════════════════════════════════════

// Step 1: Create Indices (Required for performance with MERGE)
CREATE INDEX agent_id_idx IF NOT EXISTS FOR (a:Agent) ON (a.id);
CREATE INDEX memory_id_idx IF NOT EXISTS FOR (m:Memory) ON (m.id);

// Step 2: Import Agents
LOAD CSV WITH HEADERS FROM "file:///agents.csv" AS row
MERGE (a:Agent {id: row.id})
SET a.name = row.name,
    a.type = row.type,
    a.description = row.description,
    a.created_at = datetime(row.created_at);

// Step 3: Import Memories
LOAD CSV WITH HEADERS FROM "file:///memories.csv" AS row
MERGE (m:Memory {id: row.id})
SET m.content = row.content,
    m.memory_type = row.memory_type,
    m.importance = toFloat(row.importance),
    m.created_at = datetime(row.created_at);

// Step 4: Create Agent->Memory Relationships (CREATED)
// This links the memories to the agents that own them
LOAD CSV WITH HEADERS FROM "file:///memories.csv" AS row
MATCH (a:Agent {id: row.agent_id})
MATCH (m:Memory {id: row.id})
MERGE (a)-[c:CREATED]->(m)
SET c.at = m.created_at;

// Step 5: Create Memory->Memory Relationships (RELATES_TO)
// This establishes the graph structure between memories
LOAD CSV WITH HEADERS FROM "file:///relationships.csv" AS row
MATCH (source:Memory {id: row.source_id})
MATCH (target:Memory {id: row.target_id})
MERGE (source)-[r:RELATES_TO {type: row.type}]->(target)
SET r.strength = toFloat(row.strength),
    r.reason = row.reason,
    r.created_at = datetime(row.created_at);

// Verification Queries
MATCH (a:Agent) RETURN count(a) as Total_Agents;
MATCH (m:Memory) RETURN count(m) as Total_Memories;
MATCH ()-[r:RELATES_TO]->() RETURN count(r) as Memory_Relationships;
MATCH ()-[r:CREATED]->() RETURN count(r) as Agent_Memory_Links;
