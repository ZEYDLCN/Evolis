"""Knowledge Graph — section 25 (explicitly optional per the spec: "MVP için
zorunlu değildir").

build_user_graph() is the part that matters regardless of whether Neo4j is
ever wired up: a deterministic, computed (not LLM-guessed) projection of a
user's data onto the node/relationship shape the spec sketches —

    USER -> LEARNS -> SKILL
    USER -> BUILDS -> PROJECT
    PROJECT -> USES -> SKILL
    ENTRY -> MENTIONS -> TOPIC

— returned as plain JSON. That's useful on its own (an export, a payload for
some other graph viewer) whether or not a Neo4j instance exists; syncing it
into an actual Neo4j database is a thin, optional addition in
src/graph/neo4j_sync.py.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.analytics.skills import skill_scores
from src.database.models import Activity, Entry, EntryTopic, Project


@dataclass
class GraphNode:
    id: str
    label: str  # Neo4j node label: User | Skill | Project | Topic
    properties: dict = field(default_factory=dict)


@dataclass
class GraphRelationship:
    start_id: str
    end_id: str
    type: str  # LEARNS | BUILDS | USES | MENTIONS


@dataclass
class UserGraph:
    nodes: list[GraphNode] = field(default_factory=list)
    relationships: list[GraphRelationship] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": [{"id": n.id, "label": n.label, "properties": n.properties} for n in self.nodes],
            "relationships": [{"start": r.start_id, "end": r.end_id, "type": r.type} for r in self.relationships],
        }


def build_user_graph(db: Session, user_id: str, start: dt.datetime, end: dt.datetime) -> UserGraph:
    graph = UserGraph()
    user_node_id = f"user:{user_id}"
    graph.nodes.append(GraphNode(id=user_node_id, label="User"))

    # USER -> LEARNS -> SKILL, computed from the same deterministic scoring
    # as GET /analytics/skills — no separate source of truth here.
    for skill in skill_scores(db, user_id, start, end):
        skill_node_id = f"skill:{skill['skill'].lower()}"
        graph.nodes.append(GraphNode(id=skill_node_id, label="Skill", properties={"name": skill["skill"], "activity_score": skill["activity_score"]}))
        graph.relationships.append(GraphRelationship(start_id=user_node_id, end_id=skill_node_id, type="LEARNS"))

    # USER -> BUILDS -> PROJECT, and PROJECT -> USES -> SKILL from that
    # project's own logged activities.
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    for project in projects:
        project_node_id = f"project:{project.id}"
        graph.nodes.append(GraphNode(id=project_node_id, label="Project", properties={"name": project.name}))
        graph.relationships.append(GraphRelationship(start_id=user_node_id, end_id=project_node_id, type="BUILDS"))

        used_skills = (
            db.query(Activity.topic)
            .filter(Activity.project_id == project.id, Activity.topic.is_not(None))
            .distinct()
            .all()
        )
        for (topic,) in used_skills:
            skill_node_id = f"skill:{topic.lower()}"
            if not any(n.id == skill_node_id for n in graph.nodes):
                graph.nodes.append(GraphNode(id=skill_node_id, label="Skill", properties={"name": topic}))
            graph.relationships.append(GraphRelationship(start_id=project_node_id, end_id=skill_node_id, type="USES"))

    # ENTRY -> MENTIONS -> TOPIC, within the requested window.
    entry_topic_rows = db.execute(
        select(Entry.id, EntryTopic.topic)
        .join(EntryTopic, EntryTopic.entry_id == Entry.id)
        .where(Entry.user_id == user_id, Entry.entry_date >= start, Entry.entry_date < end)
    ).all()
    for entry_id, topic in entry_topic_rows:
        entry_node_id = f"entry:{entry_id}"
        topic_node_id = f"topic:{topic.lower()}"
        if not any(n.id == entry_node_id for n in graph.nodes):
            graph.nodes.append(GraphNode(id=entry_node_id, label="Entry"))
        if not any(n.id == topic_node_id for n in graph.nodes):
            graph.nodes.append(GraphNode(id=topic_node_id, label="Topic", properties={"name": topic}))
        graph.relationships.append(GraphRelationship(start_id=entry_node_id, end_id=topic_node_id, type="MENTIONS"))

    return graph
