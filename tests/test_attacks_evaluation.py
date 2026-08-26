"""
Rigorous Evaluation Suite for MemGraph Adversarial Attacks

This script extends the attack demonstrations with:
1. Multiple attack runs (5 edge poisons, 5 temporal burials, 3 flood batches)
2. Retrieval before/after validation for each attack
3. Diff analysis showing actual impact on retrieved context
4. Summary statistics and verification rates

Requirements:
- Neo4j at bolt://localhost:7687, user=neo4j, password=12345678
- Synthetic data already loaded (see synthetic_data/import_synthetic_data.cypher)
- 7-day retrieval window for temporal drift cutoff
"""

from attacks.edge_poison import connect_to_db, get_edges, poison_edge, verify_poison
from attacks.temporal_drift import (
    get_memory_timestamp, drift_timestamp, verify_drift, flood_recency_window
)
from memgraph.core.memory import MemoryGraph
from memgraph.core.graph import _convert_neo4j_datetime
import datetime
import json
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

# ════════════════════════════════════════════════════════════════════════════════
# SETUP: Database connections
# ════════════════════════════════════════════════════════════════════════════════

print("=" * 80)
print("MEMGRAPH ADVERSARIAL ATTACK EVALUATION SUITE")
print("=" * 80)

# Connect to Neo4j for low-level operations
driver = connect_to_db("bolt://localhost:7687", "neo4j", "12345678")

# Connect to MemoryGraph for high-level retrieval
memory_graph = MemoryGraph(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="12345678"
)

RETRIEVAL_WINDOW_DAYS = 7
TEMPORAL_DRIFT_DAYS = 90

# ════════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════


def query_random_edges_by_type(driver, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query for edges with different types across the graph.
    Returns edges grouped by type to ensure diversity.
    """
    query = """
    MATCH (source:Memory)-[r:RELATES_TO]->(target:Memory)
    RETURN 
        source.id as source_id,
        target.id as target_id,
        r.type as edge_type,
        r.strength as edge_strength
    LIMIT $limit
    """
    
    with driver.session() as session:
        result = session.run(query, limit=limit)
        edges = []
        for record in result:
            edges.append({
                'source_id': record['source_id'],
                'target_id': record['target_id'],
                'edge_type': record['edge_type'],
                'edge_strength': record['edge_strength']
            })
    
    return edges


def query_random_memories_by_agent(driver, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query for random memories across different agents.
    Returns diverse memories from different agents.
    """
    query = """
    MATCH (a:Agent)-[c:CREATED]->(m:Memory)
    RETURN 
        a.id as agent_id,
        m.id as memory_id,
        m.content as content,
        c.at as created_at
    ORDER BY rand()
    LIMIT $limit
    """
    
    with driver.session() as session:
        result = session.run(query, limit=limit)
        memories = []
        for record in result:
            memories.append({
                'agent_id': record['agent_id'],
                'memory_id': record['memory_id'],
                'content': record['content'],
                'created_at': record['created_at']
            })
    
    return memories


def normalize_retrieved_ids(context_response) -> set:
    """Extract memory IDs from a ContextResponse."""
    return {mem.memory.id for mem in context_response.memories}


def describe_retrieved_subgraph(context_response) -> Dict[str, Any]:
    """Describe the retrieved subgraph: IDs, types, importance scores."""
    return {
        'ids': [mem.memory.id for mem in context_response.memories],
        'types': [mem.memory.memory_type.value for mem in context_response.memories],
        'importance': [mem.memory.importance for mem in context_response.memories],
        'count': len(context_response.memories)
    }


def memory_outside_window(timestamp: Any, window_days: int = RETRIEVAL_WINDOW_DAYS) -> bool:
    """Check if a timestamp is outside the retrieval window."""
    # Normalize timestamp
    if hasattr(timestamp, 'to_native'):  # Neo4j DateTime
        dt = timestamp.to_native()
    elif isinstance(timestamp, datetime.datetime):
        dt = timestamp
    else:
        dt = timestamp
    
    # Make timezone-aware if needed
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(days=window_days)
    
    return dt < cutoff


def format_table(title: str, headers: List[str], rows: List[List[str]]) -> str:
    """Format results as ASCII table."""
    col_widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) 
                   for i, h in enumerate(headers)]
    
    table = []
    table.append(f"\n{title}")
    table.append("─" * (sum(col_widths) + len(headers) * 3 + 1))
    
    # Header
    header_row = " │ ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    table.append(" │ " + header_row + " │")
    table.append("─" * (sum(col_widths) + len(headers) * 3 + 1))
    
    # Rows
    for row in rows:
        row_str = " │ ".join(str(r).ljust(col_widths[i]) for i, r in enumerate(row))
        table.append(" │ " + row_str + " │")
    
    table.append("─" * (sum(col_widths) + len(headers) * 3 + 1))
    
    return "\n".join(table)


# ════════════════════════════════════════════════════════════════════════════════
# 1. EDGE POISONING EVALUATION
# ════════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("1. EDGE POISONING EVALUATION")
print("=" * 80)

poison_results = []

try:
    # Query diverse edges across the graph
    available_edges = query_random_edges_by_type(driver, limit=20)
    
    if len(available_edges) < 5:
        print(f"⚠️  Only {len(available_edges)} edges found, need 5 for evaluation")
        poison_targets = available_edges
    else:
        poison_targets = available_edges[:5]
    
    print(f"\nFound {len(poison_targets)} target edges for poisoning")
    
    for idx, edge in enumerate(poison_targets, 1):
        source_id = edge['source_id']
        target_id = edge['target_id']
        original_type = edge['edge_type']
        
        print(f"\n[POISON {idx}/{len(poison_targets)}] {source_id} → {target_id}")
        print(f"  Original type: {original_type}")
        
        # Determine new type (avoid same type)
        edge_types = ["SUPPORTS", "CONTRADICTS", "ELABORATES", "FOLLOWS", "RELATES_TO", "SUPERSEDES"]
        new_type = next((t for t in edge_types if t != original_type), "RELATES_TO")
        
        try:
            # BEFORE: Retrieve context (if possible - query based on source memory content)
            before_response = None
            try:
                before_response = memory_graph.retrieve(
                    agent_id="agent_000",  # Use a known agent
                    query="memory relationships context",
                    limit=10
                )
                before_retrieved = normalize_retrieved_ids(before_response)
            except Exception as e:
                print(f"  ⚠️  Before retrieval failed: {e}")
                before_retrieved = set()
            
            # EXECUTE POISON
            poison_result = poison_edge(driver, source_id, target_id, new_type)
            print(f"  New type: {new_type}")
            
            # VERIFY poison
            verified = verify_poison(driver, source_id, target_id, new_type)
            print(f"  Verified: {verified}")
            
            # AFTER: Retrieve same context
            after_response = None
            try:
                after_response = memory_graph.retrieve(
                    agent_id="agent_000",
                    query="memory relationships context",
                    limit=10
                )
                after_retrieved = normalize_retrieved_ids(after_response)
            except Exception as e:
                print(f"  ⚠️  After retrieval failed: {e}")
                after_retrieved = set()
            
            # DIFF: Did retrieved set change?
            context_changed = before_retrieved != after_retrieved
            print(f"  Retrieved context changed: {context_changed}")
            
            poison_results.append({
                'index': idx,
                'source_id': source_id,
                'target_id': target_id,
                'original_type': original_type,
                'new_type': new_type,
                'verified': verified,
                'context_changed': context_changed
            })
        
        except Exception as e:
            print(f"  ❌ Attack failed: {e}")
            poison_results.append({
                'index': idx,
                'source_id': source_id,
                'target_id': target_id,
                'original_type': original_type,
                'new_type': new_type,
                'verified': False,
                'context_changed': False,
                'error': str(e)
            })

except Exception as e:
    print(f"❌ Edge poisoning evaluation failed: {e}")

# Print edge poisoning summary
poison_verified_count = sum(1 for r in poison_results if r['verified'])
poison_context_changed = sum(1 for r in poison_results if r['context_changed'])

print(format_table(
    "EDGE POISONING RESULTS",
    ["Run", "Source", "Target", "Old Type", "New Type", "Verified", "Context Changed"],
    [[
        str(r['index']),
        r['source_id'][-8:],
        r['target_id'][-8:],
        r['original_type'],
        r['new_type'],
        "✓" if r['verified'] else "✗",
        "✓" if r['context_changed'] else "✗"
    ] for r in poison_results]
))

print(f"\nPOISON SUMMARY: {poison_verified_count}/{len(poison_results)} mutations verified")
print(f"RETRIEVAL IMPACT: {poison_context_changed}/{len(poison_results)} showed context change")

# ════════════════════════════════════════════════════════════════════════════════
# 2. TEMPORAL DRIFT BURIAL EVALUATION
# ════════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("2. TEMPORAL DRIFT BURIAL EVALUATION")
print("=" * 80)

drift_results = []

try:
    # Query diverse memories across agents
    available_memories = query_random_memories_by_agent(driver, limit=15)
    
    if len(available_memories) < 5:
        print(f"⚠️  Only {len(available_memories)} memories found, need 5 for evaluation")
        drift_targets = available_memories
    else:
        drift_targets = available_memories[:5]
    
    print(f"\nFound {len(drift_targets)} target memories for burial")
    
    for idx, mem in enumerate(drift_targets, 1):
        agent_id = mem['agent_id']
        memory_id = mem['memory_id']
        original_timestamp = mem['created_at']
        
        print(f"\n[DRIFT {idx}/{len(drift_targets)}] {agent_id} / {memory_id}")
        print(f"  Original timestamp: {original_timestamp}")
        
        try:
            # BEFORE: Retrieve and check if memory is in results
            before_response = memory_graph.retrieve(
                agent_id=agent_id,
                query="all memories",
                limit=100,
                time_range_days=RETRIEVAL_WINDOW_DAYS
            )
            before_retrieved = normalize_retrieved_ids(before_response)
            memory_in_before = memory_id in before_retrieved
            print(f"  Memory in 7-day retrieval (before): {memory_in_before}")
            
            # EXECUTE DRIFT (90 days back)
            target_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=TEMPORAL_DRIFT_DAYS)
            drift_result = drift_timestamp(driver, agent_id, memory_id, target_time)
            print(f"  New timestamp: {drift_result['new_timestamp']}")
            
            # VERIFY drift
            verified = verify_drift(driver, agent_id, memory_id, target_time)
            print(f"  Verified: {verified}")
            
            # Check if buried (outside window)
            is_buried = memory_outside_window(target_time, window_days=RETRIEVAL_WINDOW_DAYS)
            print(f"  Is outside 7-day window: {is_buried}")
            
            # AFTER: Retrieve same query
            after_response = memory_graph.retrieve(
                agent_id=agent_id,
                query="all memories",
                limit=100,
                time_range_days=RETRIEVAL_WINDOW_DAYS
            )
            after_retrieved = normalize_retrieved_ids(after_response)
            memory_in_after = memory_id in after_retrieved
            print(f"  Memory in 7-day retrieval (after): {memory_in_after}")
            
            # DIFF: Did memory disappear from retrieval?
            disappeared = memory_in_before and not memory_in_after
            print(f"  Disappeared from retrieval: {disappeared}")
            
            drift_results.append({
                'index': idx,
                'agent_id': agent_id,
                'memory_id': memory_id,
                'original_timestamp': original_timestamp,
                'new_timestamp': drift_result['new_timestamp'],
                'verified': verified,
                'is_buried': is_buried,
                'disappeared_from_retrieval': disappeared
            })
        
        except Exception as e:
            print(f"  ❌ Attack failed: {e}")
            drift_results.append({
                'index': idx,
                'agent_id': agent_id,
                'memory_id': memory_id,
                'original_timestamp': original_timestamp,
                'new_timestamp': None,
                'verified': False,
                'is_buried': False,
                'disappeared_from_retrieval': False,
                'error': str(e)
            })

except Exception as e:
    print(f"❌ Temporal drift evaluation failed: {e}")

# Print drift summary
drift_verified_count = sum(1 for r in drift_results if r['verified'])
drift_buried_count = sum(1 for r in drift_results if r['is_buried'])
drift_disappeared_count = sum(1 for r in drift_results if r['disappeared_from_retrieval'])

print(format_table(
    "TEMPORAL DRIFT BURIAL RESULTS",
    ["Run", "Agent", "Memory", "Verified", "Buried", "Disappeared"],
    [[
        str(r['index']),
        r['agent_id'][-8:],
        r['memory_id'][-8:],
        "✓" if r['verified'] else "✗",
        "✓" if r['is_buried'] else "✗",
        "✓" if r['disappeared_from_retrieval'] else "✗"
    ] for r in drift_results]
))

print(f"\nDRIFT SUMMARY: {drift_verified_count}/{len(drift_results)} drifts verified")
print(f"BURIAL VERIFICATION: {drift_buried_count}/{len(drift_results)} outside 7-day window")
print(f"RETRIEVAL IMPACT: {drift_disappeared_count}/{len(drift_results)} disappeared from retrieval")

# ════════════════════════════════════════════════════════════════════════════════
# 3. FLOOD ATTACK EVALUATION
# ════════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("3. FLOOD ATTACK EVALUATION")
print("=" * 80)

flood_results_by_batch = {}
batch_sizes = [5, 10, 20]

try:
    # Query memories for flooding
    available_flood_memories = query_random_memories_by_agent(driver, limit=50)
    
    if not available_flood_memories:
        print("⚠️  No memories available for flood attack")
    else:
        for batch_size in batch_sizes:
            print(f"\n[FLOOD] Batch size: {batch_size}")
            
            if batch_size > len(available_flood_memories):
                print(f"⚠️  Only {len(available_flood_memories)} memories available, skipping batch size {batch_size}")
                continue
            
            batch_targets = available_flood_memories[:batch_size]
            
            try:
                # Convert to (agent_id, memory_id) tuples
                flood_targets = [(m['agent_id'], m['memory_id']) for m in batch_targets]
                
                # BEFORE: Get baseline retrieval from first agent
                first_agent = flood_targets[0][0]
                before_response = memory_graph.retrieve(
                    agent_id=first_agent,
                    query="all memories",
                    limit=100,
                    time_range_days=RETRIEVAL_WINDOW_DAYS
                )
                before_top5 = [mem.memory.id for mem in before_response.memories[:5]]
                print(f"  Top-5 before flood (agent {first_agent[-4:]}): {[m[-8:] for m in before_top5]}")
                
                # EXECUTE FLOOD
                flood_result = flood_recency_window(driver, flood_targets, target_window_days=RETRIEVAL_WINDOW_DAYS)
                succeeded = flood_result['total_drifted']
                failed = flood_result['total_failed']
                
                print(f"  Flood executed: {succeeded} succeeded, {failed} failed")
                
                # AFTER: Get retrieval after flood
                after_response = memory_graph.retrieve(
                    agent_id=first_agent,
                    query="all memories",
                    limit=100,
                    time_range_days=RETRIEVAL_WINDOW_DAYS
                )
                after_top5 = [mem.memory.id for mem in after_response.memories[:5]]
                print(f"  Top-5 after flood:  {[m[-8:] for m in after_top5]}")
                
                # Count how many flood memories are in top-5 after
                flood_ids = {memory_id for _, memory_id in flood_targets}
                flood_in_top5 = sum(1 for m in after_top5 if m in flood_ids)
                print(f"  Flood memories in top-5 after: {flood_in_top5}/5")
                
                success_rate = (succeeded / batch_size * 100) if batch_size > 0 else 0
                
                flood_results_by_batch[batch_size] = {
                    'batch_size': batch_size,
                    'attempted': batch_size,
                    'succeeded': succeeded,
                    'failed': failed,
                    'success_rate': success_rate,
                    'flood_in_top5': flood_in_top5
                }
            
            except Exception as e:
                print(f"  ❌ Flood attack failed: {e}")
                flood_results_by_batch[batch_size] = {
                    'batch_size': batch_size,
                    'attempted': batch_size,
                    'succeeded': 0,
                    'failed': batch_size,
                    'success_rate': 0.0,
                    'error': str(e)
                }

except Exception as e:
    print(f"❌ Flood evaluation failed: {e}")

# Print flood summary
print(format_table(
    "FLOOD ATTACK RESULTS",
    ["Batch Size", "Attempted", "Succeeded", "Failed", "Success Rate", "In Top-5"],
    [[
        str(r['batch_size']),
        str(r['attempted']),
        str(r['succeeded']),
        str(r['failed']),
        f"{r['success_rate']:.1f}%",
        str(r.get('flood_in_top5', 'N/A'))
    ] for r in flood_results_by_batch.values()]
))

print("\nFLOOD SUMMARY:")
for batch_size, result in flood_results_by_batch.items():
    print(f"  Batch {batch_size}: {result['succeeded']}/{result['attempted']} succeeded ({result['success_rate']:.1f}%)")

# ════════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("FINAL EVALUATION SUMMARY")
print("=" * 80)

summary_lines = [
    "╔══════════════════════════════════════════════════════════════╗",
    "║                    EVALUATION RESULTS                        ║",
    "╠══════════════════════════════════════════════════════════════╣",
]

# Edge poisoning
summary_lines.append(f"║ Edge Poisoning (5 runs)                                    ║")
summary_lines.append(f"║   Verified mutations: {poison_verified_count}/5                              ║")
summary_lines.append(f"║   Retrieval impact: {poison_context_changed}/5 showed context change       ║")

# Temporal drift
summary_lines.append(f"║ Temporal Drift Burial (5 runs)                             ║")
summary_lines.append(f"║   Verified drifts: {drift_verified_count}/5                                 ║")
summary_lines.append(f"║   Buried (outside 7-day): {drift_buried_count}/5                       ║")
summary_lines.append(f"║   Disappeared from retrieval: {drift_disappeared_count}/5              ║")

# Flood attacks
for batch_size in batch_sizes:
    if batch_size in flood_results_by_batch:
        result = flood_results_by_batch[batch_size]
        summary_lines.append(f"║ Flood Attack (batch={batch_size})                              ║")
        summary_lines.append(f"║   Success rate: {result['succeeded']}/{result['attempted']} ({result['success_rate']:.1f}%)                 ║")
        if 'flood_in_top5' in result:
            summary_lines.append(f"║   In top-5 retrieval: {result['flood_in_top5']}/5                          ║")

summary_lines.append("╚══════════════════════════════════════════════════════════════╝")

for line in summary_lines:
    print(line)

# ════════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ════════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("Cleaning up...")
memory_graph.close()
driver.close()
print("✓ Evaluation complete")
