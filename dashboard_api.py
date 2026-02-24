from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import redis
import os

app = FastAPI()

# Allow our React frontend (running on a different port) to fetch data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.environ.get("DB_HOST", "localhost")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")

def get_db_connection():
    return psycopg2.connect(f"dbname=postgres user=postgres password=mysecretpassword host={DB_HOST}")

@app.get("/api/jobs")
def get_jobs():
    """Fetch the latest 50 jobs from PostgreSQL"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, task_name, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 50")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Format the data into a list of dictionaries
    jobs = [{"id": r[0], "task_name": r[1], "status": r[2], "created_at": r[3]} for r in rows]
    return {"jobs": jobs}

@app.get("/api/dlq")
def get_dlq_stats():
    """Check Redis to see how many jobs are trapped in the Dead Letter Queue"""
    redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
    dlq_count = redis_client.llen("dlq_queue")
    return {"dlq_count": dlq_count}