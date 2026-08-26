import os
import csv
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Configuration - Update these if your Neo4j Desktop settings are different
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678") # <--- UPDATE THIS

# Path to the synthetic data folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "synthetic_data")

class Neo4jImporter:
    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            exit(1)

    def close(self):
        self.driver.close()

    def run_import(self):
        print(f"🚀 Starting import from {DATA_DIR} to Neo4j...")
        
        with self.driver.session() as session:
            # 1. Create Indices
            print("  Indexing nodes...")
            session.run("CREATE INDEX agent_id_idx IF NOT EXISTS FOR (a:Agent) ON (a.id)")
            session.run("CREATE INDEX memory_id_idx IF NOT EXISTS FOR (m:Memory) ON (m.id)")

            # 2. Import Agents
            agents_file = os.path.join(DATA_DIR, "agents.csv")
            print(f"  Importing Agents from {os.path.basename(agents_file)}...")
            with open(agents_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session.run("""
                        MERGE (a:Agent {id: $id})
                        SET a.name = $name,
                            a.type = $type,
                            a.description = $description,
                            a.created_at = datetime($created_at)
                    """, **row)

            # 3. Import Memories
            memories_file = os.path.join(DATA_DIR, "memories.csv")
            print(f"  Importing Memories from {os.path.basename(memories_file)}...")
            with open(memories_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['importance'] = float(row['importance'])
                    session.run("""
                        MERGE (m:Memory {id: $id})
                        SET m.content = $content,
                            m.memory_type = $memory_type,
                            m.importance = $importance,
                            m.created_at = datetime($created_at)
                    """, **row)

            # 4. Create Agent->Memory Relationships (CREATED)
            print("  Linking Agents to Memories...")
            with open(memories_file, mode='r', encoding='utf-8') as f:
                f.seek(0)
                reader = csv.DictReader(f)
                for row in reader:
                    session.run("""
                        MATCH (a:Agent {id: $agent_id})
                        MATCH (m:Memory {id: $id})
                        MERGE (a)-[c:CREATED]->(m)
                        SET c.at = datetime($created_at)
                    """, **row)

            # 5. Create Memory->Memory Relationships (RELATES_TO)
            rel_file = os.path.join(DATA_DIR, "relationships.csv")
            print(f"  Establishing Memory Relationships from {os.path.basename(rel_file)}...")
            with open(rel_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['strength'] = float(row['strength'])
                    session.run("""
                        MATCH (source:Memory {id: $source_id})
                        MATCH (target:Memory {id: $target_id})
                        MERGE (source)-[r:RELATES_TO {type: $type}]->(target)
                        SET r.strength = $strength,
                            r.reason = $reason,
                            r.created_at = datetime($created_at)
                    """, **row)

        print("\n✅ Import Complete!")
        print("Verification counts:")
        with self.driver.session() as session:
            agents = session.run("MATCH (a:Agent) RETURN count(a)").single()[0]
            memories = session.run("MATCH (m:Memory) RETURN count(m)").single()[0]
            rels = session.run("MATCH ()-[r:RELATES_TO]->() RETURN count(r)").single()[0]
            print(f"  Agents in DB: {agents}")
            print(f"  Memories in DB: {memories}")
            print(f"  Relationships in DB: {rels}")

if __name__ == "__main__":
    importer = Neo4jImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        importer.run_import()
    finally:
        importer.close()
