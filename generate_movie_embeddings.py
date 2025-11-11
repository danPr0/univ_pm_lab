import json
import os

import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


model = SentenceTransformer('all-MiniLM-L6-v2')

load_dotenv()
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

batch_size = 50 
count = 0

while True:
    rows = cur.fetchmany(batch_size)
    if not rows:
        break

    for movie_id, desc in rows:
        if not desc:
            continue 

        emb = model.encode(desc).tolist()
        conn.cursor().execute(
            """
            INSERT INTO embeddings (movie_id, embedding)
            VALUES (%s, %s)
            """,
            [movie_id, json.dumps(emb)]
        )
        count += 1
    print(f"Batch done\n")
    conn.commit()

cur.close()
conn.close()