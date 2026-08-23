"""Optional Neo4j sync for the graph built by knowledge_graph.py.

Fully optional and off by default: without NEO4J_URI set (or without the
`neo4j` driver installed), sync_to_neo4j() is a documented no-op that
returns False rather than raising — the graph JSON export
(build_user_graph().to_dict()) is useful on its own regardless of whether
anyone ever points this at a real database.
"""
from __future__ import annotations

import os

from src.graph.knowledge_graph import UserGraph

_MERGE_NODE = "MERGE (n:{label} {{id: $id}}) SET n += $properties"
_MERGE_RELATIONSHIP = "MATCH (a {{id: $start_id}}), (b {{id: $end_id}}) MERGE (a)-[:{type}]->(b)"


def neo4j_configured() -> bool:
    return bool(os.getenv("NEO4J_URI"))


def sync_to_neo4j(graph: UserGraph) -> bool:
    """Returns True if it actually wrote to Neo4j, False if skipped (not
    configured, or the driver isn't installed)."""
    if not neo4j_configured():
        return False

    try:
        from neo4j import GraphDatabase
    except ImportError:
        return False

    uri = os.environ["NEO4J_URI"]
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            for node in graph.nodes:
                session.run(_MERGE_NODE.format(label=node.label), id=node.id, properties=node.properties)
            for rel in graph.relationships:
                session.run(_MERGE_RELATIONSHIP.format(type=rel.type), start_id=rel.start_id, end_id=rel.end_id)
    finally:
        driver.close()

    return True
