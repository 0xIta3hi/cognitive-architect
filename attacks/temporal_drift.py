# this file handles the functionality for temporal drift attacks.
# imports
from neo4j import GraphDatabase as Neo4jDriver, Driver
from neo4j.exceptions import ServiceUnavailable
import datetime
from typing import List, Tuple, Dict, Any

# Import connect_to_db from edge_poison module
from .edge_poison import connect_to_db
# Import datetime conversion utility to handle Neo4j timezone-aware datetimes
from memgraph.core.graph import _convert_neo4j_datetime

def get_memory_timestamp(driver, agent_id, memory_id):
    """
    Reconnaissance: Read the current c.at timestamp on a CREATED edge.
    
    Before drifting a memory's creation timestamp, you need to know what it
    currently is. This is the recon query for temporal attacks — enumerate
    the temporal properties of the target before mutation.
    
    Args:
        driver: Neo4j driver instance
        agent_id: ID of the agent that created the memory
        memory_id: ID of the memory node
        
    Returns:
        Dict containing:
        - 'memory_id': The memory ID
        - 'agent_id': The agent ID
        - 'created_at': Current c.at timestamp on the CREATED edge
        
    Raises:
        ValueError: If the CREATED edge does not exist between agent and memory
    """
    query = """
    MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory {id: $memory_id})
    RETURN c.at as created_at
    """
    
    with driver.session() as session:
        result = session.run(
            query,
            agent_id=agent_id,
            memory_id=memory_id
        )
        record = result.single()
        
        if not record:
            raise ValueError(
                f"CREATED edge does not exist between agent '{agent_id}' and memory '{memory_id}'"
            )
        
        return {
            'memory_id': memory_id,
            'agent_id': agent_id,
            'created_at': record['created_at']
        }


def drift_timestamp(driver, agent_id, memory_id, new_timestamp):
    """
    Core mutation: Change the c.at timestamp on a CREATED edge.
    
    This is temporal drift — moving a memory's creation timestamp to a different
    point in time without changing any other graph properties. By drifting timestamps
    forward or backward, an attacker can:
    
    - Evict recent memories from time-range queries (drift old)
    - Inject old memories into recency windows (drift recent)
    - Reorder time-based reasoning (causal confusion)
    
    The attack is stealthy because:
    - Graph topology unchanged (same nodes, same edge type)
    - No memory content is altered
    - No edges created or deleted
    - Only a timestamp property mutated — just a datetime value, looks legitimate
    
    Args:
        driver: Neo4j driver instance
        agent_id: ID of the agent
        memory_id: ID of the memory
        new_timestamp: Target datetime to set c.at to (datetime.datetime object or ISO string)
        
    Returns:
        Dict containing mutation details:
        - 'old_timestamp': The original c.at value
        - 'new_timestamp': The new c.at value
        - 'agent_id': Agent ID
        - 'memory_id': Memory ID
        - 'mutation_timestamp': When the drift was executed
        
    Raises:
        ValueError: If the CREATED edge does not exist

    """
    # Convert new_timestamp to ISO format if it's a datetime object
    if isinstance(new_timestamp, datetime.datetime):
        new_timestamp_str = new_timestamp.isoformat()
    else:
        new_timestamp_str = new_timestamp
    
    query = """
    MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory {id: $memory_id})
    WITH c, c.at as old_timestamp
    SET c.at = datetime($new_timestamp)
    RETURN old_timestamp, c.at as new_timestamp
    """
    
    with driver.session() as session:
        result = session.run(
            query,
            agent_id=agent_id,
            memory_id=memory_id,
            new_timestamp=new_timestamp_str
        )
        record = result.single()
        
        if not record:
            raise ValueError(
                f"CREATED edge does not exist between agent '{agent_id}' and memory '{memory_id}' — cannot drift"
            )
        
        old_timestamp = record['old_timestamp']
        new_ts = record['new_timestamp']
        mutation_time = datetime.datetime.now()
        
        # Log the drift event
        print(f"[DRIFT] agent={agent_id}, memory={memory_id}: {old_timestamp} → {new_ts} at {mutation_time}")
        
        return {
            'old_timestamp': old_timestamp,
            'new_timestamp': new_ts,
            'agent_id': agent_id,
            'memory_id': memory_id,
            'mutation_timestamp': mutation_time
        }


def verify_drift(driver, agent_id, memory_id, expected_timestamp):
    """
    Verification: Confirm that a timestamp drift landed as expected.
    
    Sanity check that drift_timestamp() succeeded. Query the CREATED edge and
    compare its current c.at to the expected value. Distinguishes between:
    
    - Edge nonexistence (something fundamentally wrong)
    - Timestamp mismatch (drift failed or partial write)
    - Successful drift (timestamp matches)
    
    Args:
        driver: Neo4j driver instance
        agent_id: ID of the agent
        memory_id: ID of the memory
        expected_timestamp: The timestamp value we expect to find (datetime or ISO string)
        
    Returns:
        bool: True if current c.at matches expected_timestamp, False if mismatch
        
    Raises:
        ValueError: If the CREATED edge does not exist
    """
    query = """
    MATCH (a:Agent {id: $agent_id})-[c:CREATED]->(m:Memory {id: $memory_id})
    RETURN c.at as current_timestamp
    """
    
    with driver.session() as session:
        result = session.run(
            query,
            agent_id=agent_id,
            memory_id=memory_id
        )
        record = result.single()
        
        if not record:
            raise ValueError(
                f"CREATED edge does not exist between agent '{agent_id}' "
                f"and memory '{memory_id}' — cannot verify drift"
            )
        
        current_ts = record['current_timestamp']
        
        # Convert Neo4j datetime to Python datetime
        current_ts_normalized = _convert_neo4j_datetime(current_ts) if current_ts else None
        
        # Normalize expected_timestamp to timezone-aware UTC datetime
        if isinstance(expected_timestamp, str):
            try:
                expected_ts_normalized = datetime.datetime.fromisoformat(expected_timestamp)
            except ValueError:
                expected_ts_normalized = expected_timestamp
        else:
            expected_ts_normalized = expected_timestamp
        
        # Make expected timezone-aware if it isn't — Neo4j always returns UTC-aware
        if isinstance(expected_ts_normalized, datetime.datetime):
            if expected_ts_normalized.tzinfo is None:
                expected_ts_normalized = expected_ts_normalized.replace(
                    tzinfo=datetime.timezone.utc
                )
        
        # Compare at second precision to avoid microsecond drift from
        # Neo4j storage rounding
        if current_ts_normalized and isinstance(expected_ts_normalized, datetime.datetime):
            current_truncated = current_ts_normalized.replace(microsecond=0)
            expected_truncated = expected_ts_normalized.replace(microsecond=0)
            match = current_truncated == expected_truncated
        else:
            match = current_ts_normalized == expected_ts_normalized
        
        # Log verification result
        status = "VERIFIED" if match else "MISMATCH"
        print(
            f"[VERIFY] agent={agent_id}, memory={memory_id}: "
            f"expected={expected_ts_normalized}, actual={current_ts_normalized} {status}"
        )
        
        return match


def _boost_memory_importance(driver, memory_id, target_importance):
    """
    Helper: Boost a memory's importance value to target level.
    
    This simulates an attacker injecting high-quality-looking memories by
    artificially inflating their importance scores. In practice, an attacker
    would:
    1. Craft fake memories with identical structure to high-importance ones
    2. Set their importance property to compete in ranking functions
    
    Args:
        driver: Neo4j driver instance
        memory_id: Memory to boost
        target_importance: Target importance value (0.0-1.0)
        
    Returns:
        bool: True if boost succeeded, False otherwise
    """
    query = """
    MATCH (m:Memory {id: $memory_id})
    SET m.importance = $importance
    RETURN m.importance as new_importance
    """
    
    with driver.session() as session:
        result = session.run(
            query,
            memory_id=memory_id,
            importance=target_importance
        )
        record = result.single()
        return record is not None


def flood_recency_window(driver, memory_list, target_window_days, boost_importance=True, target_importance=0.95):
    """
    Batch attack: Drift multiple memories into a recency window simultaneously.
    
    Coordinated temporal attack — inject a list of memories into a target time window
    (e.g., "last 7 days") in a single operation. This is more powerful than individual
    drifts because it allows an attacker to:
    
    - Synchronize an injection strategy across multiple memories
    - Test recency-filtering behavior at scale
    - Evade per-operation detection
    
    ENHANCEMENT: Also boost importance of flooded memories to make them competitive
    in ranking. Real attackers would inject high-quality-looking content.
    
    Strategy:
    - Calculate a random timestamp within the target window
    - For each (agent_id, memory_id) pair:
      1. Drift it to that timestamp
      2. Optionally boost its importance to target_importance
    - Return results of all drifts plus summary
    
    Args:
        driver: Neo4j driver instance
        memory_list: List of tuples: [(agent_id_1, memory_id_1), (agent_id_2, memory_id_2), ...]
        target_window_days: Number of days back to inject into (e.g., 7 for "last 7 days")
        boost_importance: If True, elevate importance of flooded memories
        target_importance: What importance to set flooded memories to (0.0-1.0, default 0.95)
        
    Returns:
        Dict containing:
        - 'total_drifted': Number of memories successfully drifted
        - 'total_importance_boosted': Number of importance values updated
        - 'failed': List of (agent_id, memory_id) pairs that failed
        - 'drifts': List of drift result dicts (from drift_timestamp)
        - 'target_window_days': The window that was targeted
        - 'injection_timestamp': The specific timestamp all memories were drifted to
        - 'boost_importance': Whether importance was boosted
        - 'target_importance': The importance value set
    """
    # Calculate target timestamp: random point within the window
    now = datetime.datetime.now()
    window_start = now - datetime.timedelta(days=target_window_days)
    
    # Use a point in the middle of the window for consistency
    injection_timestamp = window_start + datetime.timedelta(days=target_window_days / 2)
    
    drifts = []
    failed = []
    importance_boosted = 0
    
    print(f"\n[FLOOD] Starting batch injection into {target_window_days}-day window")
    print(f"[FLOOD] Target timestamp: {injection_timestamp}")
    print(f"[FLOOD] Targets: {len(memory_list)} memories")
    if boost_importance:
        print(f"[FLOOD] Importance boost enabled: target={target_importance}")
    
    for agent_id, memory_id in memory_list:
        try:
            # Step 1: Drift timestamp
            result = drift_timestamp(driver, agent_id, memory_id, injection_timestamp)
            drifts.append(result)
            
            # Step 2: Optionally boost importance
            if boost_importance:
                try:
                    boost_success = _boost_memory_importance(driver, memory_id, target_importance)
                    if boost_success:
                        importance_boosted += 1
                except Exception as e:
                    print(f"[FLOOD] Warning: Failed to boost importance for {memory_id}: {e}")
                    
        except ValueError as e:
            print(f"[FLOOD] FAILED: {agent_id}/{memory_id} — {e}")
            failed.append((agent_id, memory_id))
    
    flood_result = {
        'total_drifted': len(drifts),
        'total_importance_boosted': importance_boosted if boost_importance else 0,
        'total_failed': len(failed),
        'failed': failed,
        'drifts': drifts,
        'target_window_days': target_window_days,
        'injection_timestamp': injection_timestamp,
        'boost_importance': boost_importance,
        'target_importance': target_importance
    }
    
    print(f"[FLOOD] Complete: {len(drifts)} succeeded, {len(failed)} failed")
    
    return flood_result
