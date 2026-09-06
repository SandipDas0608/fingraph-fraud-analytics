import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver

load_dotenv()
logger = logging.getLogger("fingraph.database")

URI = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
PASSWORD = os.getenv('NEO4J_PASSWORD', 'neo4j')
MAX_CONNECTION_POOL_SIZE = int(os.getenv('NEO4J_MAX_POOL_SIZE', '50'))
CONNECTION_TIMEOUT = float(os.getenv('NEO4J_CONNECTION_TIMEOUT', '30.0'))

driver: Driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD),
    max_connection_pool_size=MAX_CONNECTION_POOL_SIZE,
    connection_timeout=CONNECTION_TIMEOUT
)


def verify_connection() -> bool:
    """Verify active connectivity to Neo4j graph cluster."""
    try:
        driver.verify_connectivity()
        logger.info(f"Neo4j database connection verified at {URI}")
        return True
    except Exception as exc:
        logger.error(f"Failed to connect to Neo4j at {URI}: {exc}")
        return False


def close_driver():
    """Gracefully close Neo4j connection pool on application shutdown."""
    if driver:
        driver.close()
        logger.info("Neo4j database driver connection closed gracefully.")