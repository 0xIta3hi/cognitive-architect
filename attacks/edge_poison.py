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

    