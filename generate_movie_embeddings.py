import json
import os

import psycopg2
from sentence_transformers import SentenceTransformer


model = SentenceTransformer('all-MiniLM-L6-v2')

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute(
    """
    SELECT id, description 
    FROM movies
    LEFT JOIN embeddings ON movies.id = embeddings.movie_id
    WHERE embeddings.movie_id IS NULL
    """
)

for movie_id, desc in cur.fetchall():
    emb = model.encode(desc).tolist()
    cur.execute(
        """
        INSERT INTO embeddings (movie_id, embedding) 
        VALUES (%s, %s)
        """,
        [movie_id, json.dumps(emb)]
    )

conn.commit()
