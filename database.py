import os
from sqlalchemy import create_engine, text
from pgvector.sqlalchemy import Vector

# Success Criterion: 0.8 Threshold
THRESHOLD = 0.8

engine = create_engine(os.getenv("DATABASE_URL"))

async def get_memories(user_id: str, query_vector: list):
    """Retrieves top 3 memories only if they meet the similarity threshold."""
    query = text("""
        SELECT content, 1 - (embedding <=> :v) AS similarity 
        FROM memories 
        WHERE user_id = :uid AND 1 - (embedding <=> :v) > :t
        ORDER BY similarity DESC LIMIT 3
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"v": str(query_vector), "uid": user_id, "t": THRESHOLD})
        return [row.content for row in result]

async def save_fact(user_id: str, content: str, embedding: list):
    """LLM Tool to persist user facts."""
    query = text("INSERT INTO memories (user_id, content, embedding) VALUES (:uid, :c, :v)")
    with engine.connect() as conn:
        conn.execute(query, {"uid": user_id, "c": content, "v": str(embedding)})
