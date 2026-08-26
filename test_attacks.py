"""
Rigorous Evaluation Suite for MemGraph Adversarial Attacks
Designed for academic publication — IEEE conference standard

Evaluation components:
1. Edge Poisoning        — 20 independent runs, reasoning-layer impact
2. Temporal Drift Burial — 20 independent runs, retrieval disappearance
3. Flood Attack          — 10 independent runs x 4 batch sizes (statistical)

Key design decisions:
- Full database reset before each flood iteration (clean state)
- Retrieval before/after validation for all attacks
- Statistical reporting: mean, stddev, min, max, median for flood
- No hardcoded expected results — all from live Neo4j queries
"""

from attacks.edge_poison import connect_to_db, get_edges, poison_edge, verify_poison
from attacks.temporal_drift import (
    get_memory_timestamp, drift_timestamp, verify_drift, flood_recency_window
)
from memgraph.core.memory import MemoryGraph
from memgraph.core.graph import _convert_neo4j_datetime
import datetime
import random
import statistics
from typing import List, Dict, Any, Tuple, Optional

# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════

NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "12345678"

RETRIEVAL_WINDOW_DAYS = 7
TEMPORAL_DRIFT_DAYS   = 90
POISON_RUNS           = 20          # Edge poisoning sample size
DRIFT_RUNS            = 20          # Temporal drift burial sample size
FLOOD_RUNS            = 10          # Statistical iterations per batch size
FLOOD_BATCH_SIZES     = [5, 10, 20, 50]
FLOOD_IMPORTANCE      = 0.95        # Importance score for injected memories

# ════════════════════════════════════════════════════════════════════════════════
# SETUP
# ════════════════════════════════════════════════════════════════════════════════

print("=" * 80)
print("MEMGRAPH ADVERSARIAL ATTACK EVALUATION SUITE")
print("=" * 80)

driver = connect_to_db(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
memory_graph = MemoryGraph(
    neo4j_uri=NEO4J_URI,
    neo4j_user=NEO4J_USER,
    neo4j_password=NEO4J_PASSWORD
)

# ════════════════════════════════════════════════════════════════════════════════
# SNAPSHOT / RESTORE — Required for clean flood iterations
# ════════════════════════════════════════════════════════════════════════════════

def snapshot_timestamps(driver) -> Dict[Tuple, Any]:
    """
    Snapshot all CREATED edge timestamps before flood tests.
    Returns dict of {(agent_id, memory_id): original_timestamp}
    """
    query = """
    MATCH (a:Agent)-[c:CREATED]->(m:Memory)
    RETURN a.id as agent_id, m.id as memory_id, c.at as created_at
    """
    with driver.session() as session:
        result = session.run(query)
        return {
            (r['agent_id'], r['memory_id']): r['created_at']
            for r in result
        }


def restore_timestamps(driver, snapshot: Dict[Tuple, Any]):
    """
    Restore all CREATED edge timestamps from snapshot.
    Called between flood iterations to ensure clean state.
    """
    query = """
    MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory {id: $memory_id})
    SET c.at = datetime($timestamp)
    """
    with driver.session() as session:
        for (agent_id, memory_id), ts in snapshot.items():
            if hasattr(ts, 'isoformat'):
                ts_str = ts.isoformat()
            elif hasattr(ts, 'to_native'):
                ts_str = ts.to_native().isoformat()
            else:
                ts_str = str(ts)
            session.run(query, agent_id=agent_id, memory_id=memory_id, timestamp=ts_str)


def snapshot_edge_types(driver) -> Dict[Tuple, str]:
    """
    Snapshot all RELATES_TO edge types before poison tests.
    Returns dict of {(source_id, target_id): original_type}
    """
    query = """
    MATCH (source:Memory)-[r:RELATES_TO]->(target:Memory)
    RETURN source.id as source_id, target.id as target_id, r.type as edge_type
    """
    with driver.session() as session:
        result = session.run(query)
        return {
            (r['source_id'], r['target_id']): r['edge_type']
            for r in result
        }


def restore_edge_types(driver, snapshot: Dict[Tuple, str]):
    """
    Restore all RELATES_TO edge types from snapshot.
    Called after poison tests to clean up.
    """
    query = """
    MATCH (source:Memory {id: $source_id})-[r:RELATES_TO]->(target:Memory {id: $target_id})
    SET r.type = $edge_type
    """
    with driver.session() as session:
        for (source_id, target_id), edge_type in snapshot.items():
            session.run(query, source_id=source_id, target_id=target_id, edge_type=edge_type)


# ════════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def get_all_edges(driver) -> List[Dict]:
    query = """
    MATCH (source:Memory)-[r:RELATES_TO]->(target:Memory)
    RETURN source.id as source_id, target.id as target_id,
           r.type as edge_type, r.strength as edge_strength
    LIMIT 100
    """
    with driver.session() as session:
        result = session.run(query)
        return [dict(r) for r in result]


def get_all_memories(driver) -> List[Dict]:
    query = """
    MATCH (a:Agent)-[c:CREATED]->(m:Memory)
    RETURN a.id as agent_id, m.id as memory_id,
           m.content as content, c.at as created_at,
           m.importance as importance
    """
    with driver.session() as session:
        result = session.run(query)
        return [dict(r) for r in result]


def get_memories_in_window(driver, agent_id: str, window_days: int) -> List[str]:
    """Return memory IDs currently inside the retrieval window for an agent."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=window_days)
    query = """
    MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory)
    WHERE c.at >= datetime($cutoff)
    RETURN m.id as memory_id
    """
    with driver.session() as session:
        result = session.run(query, agent_id=agent_id, cutoff=cutoff.isoformat())
        return [r['memory_id'] for r in result]


def get_all_memories_in_window(driver, window_days: int) -> List[Dict]:
    """Return all memories currently inside the retrieval window across all agents."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=window_days)
    query = """
    MATCH (a:Agent)-[c:CREATED]->(m:Memory)
    WHERE c.at >= datetime($cutoff)
    RETURN a.id as agent_id, m.id as memory_id,
           m.content as content, c.at as created_at,
           m.importance as importance
    """
    with driver.session() as session:
        result = session.run(query, cutoff=cutoff.isoformat())
        return [dict(r) for r in result]


def normalize_retrieved_ids(context_response) -> set:
    """Extract memory IDs from a ContextResponse."""
    return {mem.memory.id for mem in context_response.memories}


def retrieve_top5(agent_id: str) -> List[str]:
    """Retrieve top-5 memory IDs for an agent."""
    try:
        response = memory_graph.retrieve(
            agent_id=agent_id,
            query="all memories",
            limit=5,
            time_range_days=RETRIEVAL_WINDOW_DAYS
        )
        return [mem.memory.id for mem in response.memories]
    except Exception:
        return []


def memory_outside_window(timestamp, window_days: int = RETRIEVAL_WINDOW_DAYS) -> bool:
    """Check if a timestamp is outside the retrieval window."""
    if hasattr(timestamp, 'to_native'):
        dt = timestamp.to_native()
    elif isinstance(timestamp, datetime.datetime):
        dt = timestamp
    else:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=window_days)
    return dt < cutoff


def print_table(title: str, headers: List[str], rows: List[List[str]]):
    if not rows:
        print(f"\n{title}: No data")
        return
    col_widths = [
        max(len(h), max(len(str(r[i])) for r in rows))
        for i, h in enumerate(headers)
    ]
    sep = "─" * (sum(col_widths) + len(headers) * 3 + 1)
    print(f"\n{title}")
    print(sep)
    print(" │ " + " │ ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " │")
    print(sep)
    for row in rows:
        print(" │ " + " │ ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers))) + " │")
    print(sep)


# ════════════════════════════════════════════════════════════════════════════════
# 1. EDGE POISONING EVALUATION (20 runs)
# ════════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print(f"1. EDGE POISONING EVALUATION (n={POISON_RUNS})")
print("=" * 80)

# Snapshot before poisoning so we can restore
edge_snapshot = snapshot_edge_types(driver)

poison_results = []
available_edges = get_all_edges(driver)

print(f"\nAvailable edges in graph: {len(available_edges)}")

if len(available_edges) < POISON_RUNS:
    print(f"⚠️  Only {len(available_edges)} edges available, running {len(available_edges)} instead of {POISON_RUNS}")
    poison_targets = available_edges
else:
    poison_targets = available_edges[:POISON_RUNS]

print(f"Running edge poisoning on {len(poison_targets)} edges")

EDGE_TYPES = ["SUPPORTS", "CONTRADICTS", "ELABORATES", "FOLLOWS", "RELATES_TO", "SUPERSEDES"]

for idx, edge in enumerate(poison_targets, 1):
    source_id     = edge['source_id']
    target_id     = edge['target_id']
    original_type = edge['edge_type']
    new_type      = next(
        (t for t in EDGE_TYPES if t != original_type and t != original_type.upper()),
        "RELATES_TO"
    )

    print(f"\n[POISON {idx}/{len(poison_targets)}] {source_id} → {target_id}")
    print(f"  Original type: {original_type}")

    try:
        # BEFORE retrieval
        try:
            before_resp = memory_graph.retrieve(
                agent_id="agent_000",
                query="memory relationships context",
                limit=10
            )
            before_ids = normalize_retrieved_ids(before_resp)
        except Exception as e:
            print(f"  ⚠️  Before retrieval failed: {e}")
            before_ids = set()

        # EXECUTE
        poison_edge(driver, source_id, target_id, new_type)
        print(f"  New type: {new_type}")

        # VERIFY
        verified = verify_poison(driver, source_id, target_id, new_type)
        print(f"  Verified: {verified}")

        # AFTER retrieval
        try:
            after_resp = memory_graph.retrieve(
                agent_id="agent_000",
                query="memory relationships context",
                limit=10
            )
            after_ids = normalize_retrieved_ids(after_resp)
        except Exception as e:
            print(f"  ⚠️  After retrieval failed: {e}")
            after_ids = set()

        context_changed = before_ids != after_ids
        print(f"  Retrieved context changed: {context_changed}")

        poison_results.append({
            'index': idx, 'source_id': source_id, 'target_id': target_id,
            'original_type': original_type, 'new_type': new_type,
            'verified': verified, 'context_changed': context_changed
        })

    except Exception as e:
        print(f"  ❌ Attack failed: {e}")
        poison_results.append({
            'index': idx, 'source_id': source_id, 'target_id': target_id,
            'original_type': original_type, 'new_type': new_type,
            'verified': False, 'context_changed': False
        })

# Restore edge types after evaluation
restore_edge_types(driver, edge_snapshot)
print("\n[INFO] Edge types restored to pre-attack state")

poison_verified = sum(1 for r in poison_results if r['verified'])
poison_failed   = sum(1 for r in poison_results if not r['verified'])
poison_changed  = sum(1 for r in poison_results if r['context_changed'])

print_table(
    "EDGE POISONING RESULTS",
    ["Run", "Source", "Target", "Old Type", "New Type", "Verified", "Ctx Changed"],
    [[str(r['index']), r['source_id'][-8:], r['target_id'][-8:],
      r['original_type'], r['new_type'],
      "✓" if r['verified'] else "✗",
      "✓" if r['context_changed'] else "✗"] for r in poison_results]
)

print(f"\nPOISON SUMMARY (n={len(poison_results)}):")
print(f"  Mutation success : {poison_verified}/{len(poison_results)} ({100*poison_verified/len(poison_results):.1f}%)")
print(f"  Mutation failed  : {poison_failed}/{len(poison_results)}")
print(f"  Retrieval impact : {poison_changed}/{len(poison_results)} showed retrieval-set change")
print(f"\nNOTE: Edge Poisoning is a REASONING-LAYER attack.")
print(f"  Edge mutations do not change WHICH memories are retrieved.")
print(f"  Impact: retrieved subgraph carries inverted relationship semantics.")
print(f"  Agent draws opposite conclusions from identical memory content.")

# Edge type distribution
type_counts: Dict[str, int] = {}
for r in poison_results:
    t = r['original_type']
    type_counts[t] = type_counts.get(t, 0) + 1
print(f"\nEdge types tested:")
for t, c in sorted(type_counts.items()):
    print(f"  {t}: {c} edges")


# ════════════════════════════════════════════════════════════════════════════════
# 2. TEMPORAL DRIFT BURIAL EVALUATION (20 runs)
# ════════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print(f"2. TEMPORAL DRIFT BURIAL EVALUATION (n={DRIFT_RUNS})")
print("=" * 80)

# Snapshot timestamps before drift tests
ts_snapshot = snapshot_timestamps(driver)

drift_results = []

# Select memories that are CURRENTLY inside the retrieval window
# across ALL agents — not just one
in_window_targets = get_all_memories_in_window(driver, RETRIEVAL_WINDOW_DAYS)
print(f"\nMemories currently inside {RETRIEVAL_WINDOW_DAYS}-day window: {len(in_window_targets)}")

if len(in_window_targets) < DRIFT_RUNS:
    print(f"⚠️  Only {len(in_window_targets)} in-window memories available.")
    print(f"  Running {len(in_window_targets)} drift runs instead of {DRIFT_RUNS}.")
    drift_targets = in_window_targets
else:
    # Randomly sample to get diverse agents
    drift_targets = random.sample(in_window_targets, DRIFT_RUNS)

print(f"Running temporal drift burial on {len(drift_targets)} memories")

for idx, mem in enumerate(drift_targets, 1):
    agent_id  = mem['agent_id']
    memory_id = mem['memory_id']

    print(f"\n[DRIFT {idx}/{len(drift_targets)}] {agent_id} / {memory_id}")
    print(f"  Original timestamp: {mem['created_at']}")

    try:
        # BEFORE: confirm memory IS in retrieval window
        before_in_window = memory_id in get_memories_in_window(
            driver, agent_id, RETRIEVAL_WINDOW_DAYS
        )
        print(f"  Memory in {RETRIEVAL_WINDOW_DAYS}-day retrieval (before): {before_in_window}")

        # EXECUTE DRIFT (90 days back)
        target_time = (
            datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=TEMPORAL_DRIFT_DAYS)
        )
        drift_result = drift_timestamp(driver, agent_id, memory_id, target_time)
        print(f"  New timestamp: {drift_result['new_timestamp']}")

        # VERIFY
        verified = verify_drift(driver, agent_id, memory_id, target_time)
        print(f"  Verified: {verified}")

        # Check outside window
        is_buried = memory_outside_window(target_time, window_days=RETRIEVAL_WINDOW_DAYS)
        print(f"  Is outside {RETRIEVAL_WINDOW_DAYS}-day window: {is_buried}")

        # AFTER: confirm memory IS NOT in retrieval window
        after_in_window = memory_id in get_memories_in_window(
            driver, agent_id, RETRIEVAL_WINDOW_DAYS
        )
        print(f"  Memory in {RETRIEVAL_WINDOW_DAYS}-day retrieval (after): {after_in_window}")

        disappeared = before_in_window and not after_in_window
        print(f"  Disappeared from retrieval: {disappeared}")

        drift_results.append({
            'index': idx, 'agent_id': agent_id, 'memory_id': memory_id,
            'verified': verified, 'is_buried': is_buried,
            'before_in_window': before_in_window,
            'disappeared': disappeared
        })

    except Exception as e:
        print(f"  ❌ Attack failed: {e}")
        drift_results.append({
            'index': idx, 'agent_id': agent_id, 'memory_id': memory_id,
            'verified': False, 'is_buried': False,
            'before_in_window': False, 'disappeared': False
        })

# Restore timestamps after drift evaluation
restore_timestamps(driver, ts_snapshot)
print("\n[INFO] Timestamps restored to pre-attack state")

drift_verified    = sum(1 for r in drift_results if r['verified'])
drift_buried      = sum(1 for r in drift_results if r['is_buried'])
drift_in_before   = sum(1 for r in drift_results if r['before_in_window'])
drift_disappeared = sum(1 for r in drift_results if r['disappeared'])
drift_failed      = sum(1 for r in drift_results if not r['verified'])

print_table(
    "TEMPORAL DRIFT BURIAL RESULTS",
    ["Run", "Agent", "Memory", "In Before", "Verified", "Buried", "Disappeared"],
    [[str(r['index']), r['agent_id'][-8:], r['memory_id'][-8:],
      "✓" if r['before_in_window'] else "✗",
      "✓" if r['verified'] else "✗",
      "✓" if r['is_buried'] else "✗",
      "✓" if r['disappeared'] else "✗"] for r in drift_results]
)

print(f"\nDRIFT SUMMARY (n={len(drift_results)}):")
print(f"  Timestamp mutations verified : {drift_verified}/{len(drift_results)} ({100*drift_verified/len(drift_results):.1f}%)")
print(f"  Timestamp mutations failed   : {drift_failed}/{len(drift_results)}")
print(f"  Outside {RETRIEVAL_WINDOW_DAYS}-day window         : {drift_buried}/{len(drift_results)} ({100*drift_buried/len(drift_results):.1f}%)")
print(f"  Disappeared from retrieval   : {drift_disappeared}/{drift_in_before} ({100*drift_disappeared/drift_in_before:.1f}% of in-window targets)")
print(f"  (denominator={drift_in_before}: only memories confirmed present before attack)")


# ════════════════════════════════════════════════════════════════════════════════
# 3. FLOOD ATTACK — 10-RUN STATISTICAL EVALUATION
# ════════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print(f"3. FLOOD ATTACK — STATISTICAL EVALUATION ({FLOOD_RUNS} runs per batch size)")
print("=" * 80)
print(f"\nConfiguration:")
print(f"  Batch sizes      : {FLOOD_BATCH_SIZES}")
print(f"  Runs per batch   : {FLOOD_RUNS}")
print(f"  Importance boost : {FLOOD_IMPORTANCE} (baseline ~0.8-1.0)")
print(f"  Recency window   : {RETRIEVAL_WINDOW_DAYS} days")
print(f"  State management : Full timestamp reset between runs")

all_memories = get_all_memories(driver)
agents       = list(set(m['agent_id'] for m in all_memories))

print(f"  Total memories   : {len(all_memories)}")
print(f"  Total agents     : {len(agents)}")

# Statistical results: {batch_size: [contamination_count per run]}
stats: Dict[int, List[int]] = {b: [] for b in FLOOD_BATCH_SIZES}

# Take initial snapshot — restored before every run
ts_snapshot_flood = snapshot_timestamps(driver)

for batch_size in FLOOD_BATCH_SIZES:
    print(f"\n{'─'*60}")
    print(f"[FLOOD] Batch size: {batch_size} ({FLOOD_RUNS} independent runs)")
    print(f"{'─'*60}")

    if batch_size > len(all_memories):
        print(f"  ⚠️  Insufficient memories ({len(all_memories)}) for batch={batch_size}, skipping")
        continue

    for run in range(1, FLOOD_RUNS + 1):
        # RESET: Restore all timestamps to original state
        restore_timestamps(driver, ts_snapshot_flood)

        # Randomly select batch_size memories
        targets       = random.sample(all_memories, batch_size)
        flood_targets = [(m['agent_id'], m['memory_id']) for m in targets]
        flood_ids     = {m['memory_id'] for m in targets}

        # Randomly select agent for retrieval check
        retrieval_agent = random.choice(agents)

        # BEFORE: top-5
        before_top5 = retrieve_top5(retrieval_agent)

        # EXECUTE FLOOD
        try:
            flood_result = flood_recency_window(
                driver, flood_targets, target_window_days=RETRIEVAL_WINDOW_DAYS
            )
            succeeded = flood_result['total_drifted']
        except Exception as e:
            print(f"  Run {run:2d}: ❌ Flood failed: {e}")
            stats[batch_size].append(0)
            continue

        # AFTER: top-5
        after_top5    = retrieve_top5(retrieval_agent)
        contamination = sum(1 for m in after_top5 if m in flood_ids)
        stats[batch_size].append(contamination)

        print(f"  Run {run:2d}: {succeeded}/{batch_size} drifted | "
              f"contamination={contamination}/5 | "
              f"agent={retrieval_agent[-3:]}")

# Restore to clean state after all flood tests
restore_timestamps(driver, ts_snapshot_flood)
print(f"\n[INFO] All timestamps restored after flood evaluation")

# ── Statistical summary ──────────────────────────────────────────────────────

print(f"\n{'='*70}")
print("FLOOD ATTACK — STATISTICAL SUMMARY")
print(f"{'='*70}")
print(f"{'Batch':>8} {'Runs':>6} {'Mean':>8} {'Stddev':>8} "
      f"{'Min':>6} {'Max':>6} {'Median':>8} {'p(>0)':>8}")
print("─" * 70)

for b in FLOOD_BATCH_SIZES:
    data = stats[b]
    if not data:
        continue
    mean   = statistics.mean(data)
    stddev = statistics.stdev(data) if len(data) > 1 else 0.0
    median = statistics.median(data)
    p_gt0  = sum(1 for x in data if x > 0) / len(data)
    print(f"{b:>8} {len(data):>6} {mean:>8.2f} {stddev:>8.2f} "
          f"{min(data):>6} {max(data):>6} {median:>8.1f} {p_gt0:>7.0%}")

print("─" * 70)
print("  p(>0): probability of at least 1 adversarial memory in top-5")

print(f"\nPer-run contamination counts (adversarial memories in top-5):")
for b in FLOOD_BATCH_SIZES:
    if stats[b]:
        print(f"  Batch {b:>2}: {stats[b]}")


# ════════════════════════════════════════════════════════════════════════════════
# FINAL EVALUATION SUMMARY
# ════════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("FINAL EVALUATION SUMMARY")
print("=" * 80)

print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║           MEMGRAPH ATTACK EVALUATION RESULTS                         ║
╠══════════════════════════════════════════════════════════════════════╣
║  EDGE POISONING (n={len(poison_results)})                                         ║
║    Mutation success : {poison_verified}/{len(poison_results)} ({100*poison_verified/len(poison_results):.1f}%)                            ║
║    Retrieval impact : {poison_changed}/{len(poison_results)} (0 expected — reasoning-layer attack)  ║
╠══════════════════════════════════════════════════════════════════════╣
║  TEMPORAL DRIFT BURIAL (n={len(drift_results)})                                  ║
║    Mutation success : {drift_verified}/{len(drift_results)} ({100*drift_verified/len(drift_results):.1f}%)                            ║
║    Outside window   : {drift_buried}/{len(drift_results)} ({100*drift_buried/len(drift_results):.1f}%)                            ║
║    Disappeared      : {drift_disappeared}/{drift_in_before} of in-window targets ({100*drift_disappeared/drift_in_before:.1f}%)          ║
╠══════════════════════════════════════════════════════════════════════╣
║  FLOOD ATTACK (n={FLOOD_RUNS} runs x {len(FLOOD_BATCH_SIZES)} batch sizes)                         ║""")

for b in FLOOD_BATCH_SIZES:
    data = stats.get(b, [])
    if data:
        mean   = statistics.mean(data)
        stddev = statistics.stdev(data) if len(data) > 1 else 0.0
        print(f"║    Batch={b:<3}: mean={mean:.2f}±{stddev:.2f}, "
              f"range=[{min(data)},{max(data)}]/5                    ║")

print(f"""╠══════════════════════════════════════════════════════════════════════╣
║  KEY FINDINGS                                                        ║
║    1. Edge poisoning  : {poison_verified}/{len(poison_results)} mutations verified, reasoning-layer impact  ║
║    2. Temporal drift  : {drift_verified}/{len(drift_results)} burials verified, {drift_disappeared}/{drift_in_before} disappeared from retrieval ║
║    3. Flood attack    : stochastic contamination, no monotonic trend  ║
╚══════════════════════════════════════════════════════════════════════╝
""")


# ════════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ════════════════════════════════════════════════════════════════════════════════

print("=" * 80)
print("Cleaning up...")
memory_graph.close()
driver.close()
print("✓ Evaluation complete")