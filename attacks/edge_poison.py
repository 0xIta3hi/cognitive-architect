# this file handles the functionality for edge poisoning.
# imports
from neo4j import GraphDatabase as Neo4jDriver, Driver
from neo4j.exceptions import ServiceUnavailable
import datetime

def connect_to_db(uri:str, user:str, passwd: str):
    try:
        driver = Neo4jDriver.driver(uri, auth=(user,passwd))
        driver.verify_connectivity()
    except ServiceUnavailable as e:
        raise ConnectionError(f"Cannot connect to Neo4j at {uri}:{e}")
    except Exception as e:
        raise ConnectionError(f"Neo4j connection Error: {e}")
    print("Connected successfully at", datetime.datetime.now())
    return driver


def get_edges(driver, memory_id):
    """
    Reconnaissance: Enumerate all RELATES_TO edges pointing FROM a memory node.
    """
    # Existence check: verify the memory node exists before querying edges
    existence_query = "MATCH (m:Memory {id: $memory_id}) RETURN m"
    
    with driver.session() as session:
        # First, check if the memory node exists
        result = session.run(existence_query, memory_id=memory_id)
        if not result.single():
            raise ValueError(f"Memory node with ID '{memory_id}' does not exist in the graph")
        
        # Memory exists, now retrieve all outgoing edges
        edge_query = """
        MATCH (m:Memory {id: $memory_id})-[r:RELATES_TO]->(target:Memory)
        RETURN 
            target.id as target_id,
            target.content as target_content,
            target.memory_type as target_type,
            r.type as edge_type,
            r.strength as edge_strength,
            r.reason as edge_reason,
            r.created_at as edge_created_at
        """
        
        edges = []
        result = session.run(edge_query, memory_id=memory_id)
        for record in result:
            edges.append({
                'target_id': record['target_id'],
                'target_content': record['target_content'],
                'target_type': record['target_type'],
                'edge_type': record['edge_type'],
                'edge_strength': record['edge_strength'],
                'edge_reason': record['edge_reason'],
                'edge_created_at': record['edge_created_at']
            })
    
    return edges


def poison_edge(driver, source_id, target_id, new_type):
    """
    Core mutation: Change the type property of an existing RELATES_TO edge.
    """
    query = """
    MATCH (source:Memory {id: $source_id})-[r:RELATES_TO]->(target:Memory {id: $target_id})
    WITH r, r.type as old_type
    SET r.type = $new_type
    RETURN old_type, r
    """
    
    with driver.session() as session:
        result = session.run(
            query,
            source_id=source_id,
            target_id=target_id,
            new_type=new_type
        )
        record = result.single()
        
        # Edge must exist between these exact nodes, else fail loudly
        if not record:
            raise ValueError(
                f"Edge does not exist between source '{source_id}' and target '{target_id}'"
            )
        
        old_type = record['old_type']
        timestamp = datetime.datetime.now()
        
        # Log the poison event with full context
        print(f"[POISON] {source_id} → {target_id}: {old_type} → {new_type} at {timestamp}")
        
        return {
            'old_type': old_type,
            'new_type': new_type,
            'source_id': source_id,
            'target_id': target_id,
            'timestamp': timestamp
        }


def verify_poison(driver, source_id, target_id, expected_type):
    """
    Verification: Confirm that an edge mutation landed as expected.
    """
    query = """
    MATCH (source:Memory {id: $source_id})-[r:RELATES_TO]->(target:Memory {id: $target_id})
    RETURN r.type as current_type
    """
    
    with driver.session() as session:
        result = session.run(
            query,
            source_id=source_id,
            target_id=target_id
        )
        record = result.single()
        
        # Edge must exist, else it's a different failure mode
        if not record:
            raise ValueError(
                f"Edge does not exist between source '{source_id}' and target '{target_id}' — cannot verify poison"
            )
        
        current_type = record['current_type']
        match = current_type == expected_type
        
        # Log verification result
        status = "VERIFIED" if match else "MISMATCH"
        print(f"[VERIFY] {source_id} → {target_id}: expected={expected_type}, actual={current_type} {status}")
        
        return match


