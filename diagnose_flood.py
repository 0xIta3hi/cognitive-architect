#!/usr/bin/env python3
"""
Diagnostic script to understand why flood attacks aren't contaminating top-5
"""
import sys
from neo4j import GraphDatabase
from datetime import datetime, timedelta

# Connect to Neo4j
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "12345678")
)

# Target agent for analysis
AGENT_ID = "agent_004"

print("=" * 80)
print(f"FLOOD ATTACK DIAGNOSTIC - Analyzing {AGENT_ID}")
print("=" * 80)

# 1. Get all memories for agent with full details
query = """
MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory)
RETURN 
    m.id as memory_id,
    m.importance as importance,
    c.at as created_at,
    m.memory_type as memory_type,
    duration.between(c.at, datetime()) as age_duration
ORDER BY c.at DESC
LIMIT 30
"""

with driver.session() as session:
    result = session.run(query, agent_id=AGENT_ID)
    records = list(result)

print(f"\nAll memories for {AGENT_ID} (sorted by recency):\n")
print(f"{'Memory ID':<20} {'Importance':<12} {'Created At':<30}")
print("-" * 80)

for i, record in enumerate(records):
    mem_id = record['memory_id']
    importance = record['importance']
    created = record['created_at']
    
    # Parse the created_at datetime
    if hasattr(created, 'to_native'):
        created_str = str(created.to_native())
    else:
        created_str = str(created)
    
    print(f"{mem_id:<20} {importance:<12.2f} {created_str:<30}")
    
    if i == 4:
        print(f"                     ^^^ TOP-5 BASELINE ^^^")

# 2. Check what the retrieve function would return
print("\n" + "=" * 80)
print("SIMULATING RETRIEVE FUNCTION RANKING")
print("=" * 80)

# Parse all records and sort by (importance, created_at) as retrieve() does
memories_list = []
for record in records:
    mem_id = record['memory_id']
    importance = record['importance']
    created = record['created_at']
    
    if hasattr(created, 'to_native'):
        created_ts = created.to_native()
    else:
        created_ts = created
    
    memories_list.append({
        'id': mem_id,
        'importance': importance,
        'created_at': created_ts
    })

# Sort by (importance, created_at) descending - simulating memory.py retrieve()
sorted_memories = sorted(
    memories_list,
    key=lambda m: (m['importance'], m['created_at']),
    reverse=True
)

print(f"\nAfter retrieve() sorting by (importance, created_at):\n")
print(f"{'Rank':<6} {'Memory ID':<20} {'Importance':<12} {'Created At':<30}")
print("-" * 80)
for i, mem in enumerate(sorted_memories[:5]):
    print(f"{i+1:<6} {mem['id']:<20} {mem['importance']:<12.2f} {str(mem['created_at']):<30}")

# 3. Check recent timestamps in 7-day window
print("\n" + "=" * 80)
print("CHECKING 7-DAY RECENCY WINDOW")
print("=" * 80)

query_window = """
MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory)
WHERE c.at > datetime() - duration('P7D')
RETURN 
    m.id as memory_id,
    m.importance as importance,
    c.at as created_at
ORDER BY c.at DESC
"""

with driver.session() as session:
    result = session.run(query_window, agent_id=AGENT_ID)
    records_in_window = list(result)

print(f"\nMemories in 7-day window for {AGENT_ID}: {len(records_in_window)}")
print(f"\n{'Memory ID':<20} {'Importance':<12} {'Created At':<30}")
print("-" * 80)
for record in records_in_window[:10]:
    mem_id = record['memory_id']
    importance = record['importance']
    created = record['created_at']
    
    if hasattr(created, 'to_native'):
        created_str = str(created.to_native())
    else:
        created_str = str(created)
    
    print(f"{mem_id:<20} {importance:<12.2f} {created_str:<30}")

# 4. Find all memories with the SAME timestamp (likely the flood batch)
print("\n" + "=" * 80)
print("LOOKING FOR BATCH TIMESTAMPS")
print("=" * 80)

query_batch = """
MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory)
RETURN c.at as created_at, COUNT(*) as count
ORDER BY count DESC
LIMIT 10
"""

with driver.session() as session:
    result = session.run(query_batch, agent_id=AGENT_ID)
    batch_times = list(result)

print(f"\nTop timestamp frequencies for {AGENT_ID}:\n")
print(f"{'Timestamp':<40} {'Count':<10}")
print("-" * 80)
for record in batch_times:
    created = record['created_at']
    count = record['count']
    
    if hasattr(created, 'to_native'):
        created_str = str(created.to_native())
    else:
        created_str = str(created)
    
    print(f"{created_str:<40} {count:<10}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

# Check if baseline has higher importance
baseline_importance = sorted_memories[0]['importance']
print(f"\nBaseline (rank 1) importance: {baseline_importance}")

# Get importance distribution in 7-day window
if records_in_window:
    importances = [r['importance'] for r in records_in_window]
    print(f"Average importance in 7-day window: {sum(importances)/len(importances):.2f}")
    print(f"Min importance: {min(importances):.2f}")
    print(f"Max importance: {max(importances):.2f}")
    print(f"Importances in window: {set(importances)}")

driver.close()
print("\n✓ Diagnostic complete")
