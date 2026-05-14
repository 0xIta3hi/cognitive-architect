# this file handles the functionality for temporal drift attacks.
# imports
from neo4j import GraphDatabase as Neo4jDriver, Driver
from neo4j.exceptions import ServiceUnavailable
import datetime
from typing import List, Tuple, Dict, Any

# Import connect_to_db from edge_poison module
from edge_poison import connect_to_db
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
    # Convert expected_timestamp to ISO format if needed for comparison
    if isinstance(expected_timestamp, datetime.datetime):
        expected_ts_str = expected_timestamp.isoformat()
    else:
        expected_ts_str = str(expected_timestamp)
    
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
                f"CREATED edge does not exist between agent '{agent_id}' and memory '{memory_id}' — cannot verify drift"
            )
        
        current_ts = record['current_timestamp']
        
        # Convert Neo4j datetime to Python datetime to handle timezone-aware comparisons
        current_ts_normalized = _convert_neo4j_datetime(current_ts) if current_ts else None
        
        # Normalize expected_timestamp to datetime for consistent comparison
        if isinstance(expected_timestamp, datetime.datetime):
            expected_ts_normalized = expected_timestamp
        else:
            # If it's a string, parse it
            try:
                expected_ts_normalized = datetime.datetime.fromisoformat(str(expected_timestamp))
            except (ValueError, AttributeError):
                expected_ts_normalized = expected_timestamp
        
        # Compare normalized datetime objects
        match = current_ts_normalized == expected_ts_normalized if (current_ts_normalized and expected_ts_normalized) else False
        
        # Log verification result
        status = "VERIFIED" if match else "MISMATCH"
        print(f"[VERIFY] agent={agent_id}, memory={memory_id}: expected={expected_ts_normalized}, actual={current_ts_normalized} {status}")
        
        return match


def flood_recency_window(driver, memory_list, target_window_days):
    """
    Batch attack: Drift multiple memories into a recency window simultaneously.
    
    Coordinated temporal attack — inject a list of memories into a target time window
    (e.g., "last 7 days") in a single operation. This is more powerful than individual
    drifts because it allows an attacker to:
    
    - Synchronize an injection strategy across multiple memories
    - Test recency-filtering behavior at scale
    - Evade per-operation detection
    
    Strategy:
    - Calculate a random timestamp within the target window
    - For each (agent_id, memory_id) pair, drift it to that timestamp
    - Return results of all drifts plus summary
    
    Args:
        driver: Neo4j driver instance
        memory_list: List of tuples: [(agent_id_1, memory_id_1), (agent_id_2, memory_id_2), ...]
        target_window_days: Number of days back to inject into (e.g., 7 for "last 7 days")
        
    Returns:
        Dict containing:
        - 'total_drifted': Number of memories successfully drifted
        - 'failed': List of (agent_id, memory_id) pairs that failed
        - 'drifts': List of drift result dicts (from drift_timestamp)
        - 'target_window_days': The window that was targeted
        - 'injection_timestamp': The specific timestamp all memories were drifted to
    """
    # Calculate target timestamp: random point within the window
    now = datetime.datetime.now()
    window_start = now - datetime.timedelta(days=target_window_days)
    
    # Use a point in the middle of the window for consistency
    injection_timestamp = window_start + datetime.timedelta(days=target_window_days / 2)
    
    drifts = []
    failed = []
    
    print(f"\n[FLOOD] Starting batch injection into {target_window_days}-day window")
    print(f"[FLOOD] Target timestamp: {injection_timestamp}")
    print(f"[FLOOD] Targets: {len(memory_list)} memories")
    
    for agent_id, memory_id in memory_list:
        try:
            result = drift_timestamp(driver, agent_id, memory_id, injection_timestamp)
            drifts.append(result)
        except ValueError as e:
            print(f"[FLOOD] FAILED: {agent_id}/{memory_id} — {e}")
            failed.append((agent_id, memory_id))
    
    flood_result = {
        'total_drifted': len(drifts),
        'total_failed': len(failed),
        'failed': failed,
        'drifts': drifts,
        'target_window_days': target_window_days,
        'injection_timestamp': injection_timestamp
    }
    
    print(f"[FLOOD] Complete: {len(drifts)} succeeded, {len(failed)} failed")
    
    return flood_result
