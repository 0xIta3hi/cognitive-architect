// ═══════════════════════════════════════════════════════════════
// Import Synthetic Agent Data into Neo4j
// Generated for research on graph attacks and temporal drift
// ═══════════════════════════════════════════════════════════════

// Step 1: Create Indices (for performance)
CREATE INDEX agent_id IF NOT EXISTS FOR (a:Agent) ON (a.id);
CREATE INDEX memory_id IF NOT EXISTS FOR (m:Memory) ON (m.id);

// Step 2: Import Agents
LOAD CSV WITH HEADERS FROM "file:///agents.csv" AS row
CREATE (a:Agent {
    id: row.id,
    name: row.name,
    type: row.type,
    description: row.description,
    created_at: datetime(row.created_at)
});

// Step 3: Import Memories
LOAD CSV WITH HEADERS FROM "file:///memories.csv" AS row
CREATE (m:Memory {
    id: row.id,
    content: row.content,
    memory_type: row.memory_type,
    importance: toFloat(row.importance),
    created_at: datetime(row.created_at)
});

// Step 4: Create Agent->Memory Relationships (CREATED)
LOAD CSV WITH HEADERS FROM "file:///memories.csv" AS row
MATCH (a:Agent {id: row.agent_id})
MATCH (m:Memory {id: row.id})
CREATE (a)-[c:CREATED {at: m.created_at}]->(m);

// Step 5: Create Memory->Memory Relationships (RELATES_TO)
LOAD CSV WITH HEADERS FROM "file:///relationships.csv" AS row
MATCH (source:Memory {id: row.source_id})
MATCH (target:Memory {id: row.target_id})
CREATE (source)-[r:RELATES_TO {
    type: row.type,
    strength: toFloat(row.strength),
    reason: row.reason,
    created_at: datetime(row.created_at)
}]->(target);

// Verification
MATCH (a:Agent) RETURN count(a) as agents;
MATCH (m:Memory) RETURN count(m) as memories;
MATCH ()-[r:RELATES_TO]->() RETURN count(r) as relationships;
MATCH ()-[r:CREATED]->() RETURN count(r) as created_edges;
