"""
Attack demonstration script
Tests edge poisoning and temporal drift on the synthetic data
"""
from attacks.edge_poison import connect_to_db, get_edges, poison_edge, verify_poison
from attacks.temporal_drift import get_memory_timestamp, drift_timestamp, verify_drift, flood_recency_window
import datetime

# Connect to database
driver = connect_to_db("bolt://localhost:7687", "neo4j", "12345678")

print("ATTACK DEMONSTRATIONS")


# ═══════════════════════════════════════════════════════════════
# EDGE POISONING ATTACK
# ═══════════════════════════════════════════════════════════════
print("\n[EDGE POISONING] Testing reconnaissance and mutation")


try:
    memory_id = "mem_agent_000_0000"
    
    # Step 1: Reconnaissance — what edges exist?
    print(f"\n1. Reconnaissance: Getting edges FROM {memory_id}")
    edges = get_edges(driver, memory_id)
    print(f"   Found {len(edges)} outgoing edges:")
    for i, edge in enumerate(edges[:3]):  # Show first 3
        print(f"   - {edge['target_id']}: type={edge['edge_type']}, strength={edge['edge_strength']}")
    
    if edges:
        # Step 2: Pick a target and mutate
        target_edge = edges[0]
        source_id = memory_id
        target_id = target_edge['target_id']
        old_type = target_edge['edge_type']
        new_type = "CONTRADICTS" if old_type != "CONTRADICTS" else "SUPPORTS"
        
        print(f"\n2. Mutation: Changing edge type {old_type} → {new_type}")
        result = poison_edge(driver, source_id, target_id, new_type)
        print(f"   ✓ Mutation timestamp: {result['timestamp']}")
        
        # Step 3: Verify the poison landed
        print(f"\n3. Verification: Confirming mutation")
        verified = verify_poison(driver, source_id, target_id, new_type)
        if verified:
            print(f"POISON SUCCESSFUL: Edge type is now {new_type}")
        else:
            print(f"POISON FAILED: Type mismatch")
    
except Exception as e:
    print(f"ERROR: {e}")

# ═══════════════════════════════════════════════════════════════
# TEMPORAL DRIFT ATTACK
# ═══════════════════════════════════════════════════════════════
print("\n\n[TEMPORAL DRIFT] Testing timestamp manipulation")


try:
    agent_id = "agent_000"
    memory_id = "mem_agent_000_0001"
    
    # Step 1: Reconnaissance — what's the current timestamp?
    print(f"\n1. Reconnaissance: Getting timestamp for {agent_id}/{memory_id}")
    ts_info = get_memory_timestamp(driver, agent_id, memory_id)
    print(f"   Current timestamp: {ts_info['created_at']}")
    
    # Step 2: Drift the timestamp backward 30 days
    print(f"\n2. Drift attack: Moving timestamp back 30 days")
    target_time = datetime.datetime.now() - datetime.timedelta(days=30)
    result = drift_timestamp(driver, agent_id, memory_id, target_time)
    print(f"   Old: {result['old_timestamp']}")
    print(f"   New: {result['new_timestamp']}")
    
    # Step 3: Verify the drift landed
    print(f"\n3. Verification: Confirming drift")
    verified = verify_drift(driver, agent_id, memory_id, target_time)
    if verified:
        print(f"DRIFT SUCCESSFUL: Timestamp is now {target_time}")
    else:
        print(f"DRIFT FAILED: Timestamp mismatch")

except Exception as e:
    print(f"ERROR: {e}")

# ═══════════════════════════════════════════════════════════════
# BATCH ATTACK: FLOOD RECENCY WINDOW
# ═══════════════════════════════════════════════════════════════
print("\n\n[TEMPORAL DRIFT] Batch attack: Flood recency window")

try:
    # Get a batch of memories to inject into recent window
    agent_id = "agent_000"
    memory_targets = [
        (agent_id, "mem_agent_000_0002"),
        (agent_id, "mem_agent_000_0003"),
        (agent_id, "mem_agent_000_0004"),
    ]
    
    print(f"\nFlooding {len(memory_targets)} memories into 7-day recency window")
    result = flood_recency_window(driver, memory_targets, target_window_days=7)
    
    print(f"\nResults:")
    print(f"  Total injected: {result['total_drifted']}")
    print(f"  Failed: {result['total_failed']}")
    print(f"  Target window: {result['target_window_days']} days")
    print(f"  Injection timestamp: {result['injection_timestamp']}")
    
except Exception as e:
    print(f"ERROR: {e}")

# ═══════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════
print("Attack demonstrations complete!")
driver.close()
