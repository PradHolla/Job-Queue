import redis
import json
import time
import psycopg2
import os

QUEUE_NAME = "task_queue"

# For Redis (in server.py and worker.py)
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

# For Postgres (in server.py, worker.py, and init_db.py)
DB_HOST = os.environ.get("DB_HOST", "localhost")
def get_db_connection():
    return psycopg2.connect(f"dbname=postgres user=postgres password=mysecretpassword host={DB_HOST}")

def update_job_status(job_id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET status = %s WHERE id = %s", (status, job_id))
    conn.commit()
    cur.close()
    conn.close()

def process_job(job_data):
    job_id = job_data.get("job_id")
    payload = job_data.get("payload")
    
    update_job_status(job_id, "PROCESSING")
    print(f"\n[x] Processing Job {job_id}")
    
    # Let's introduce an artificial way to test failures!
    # If the payload contains the word "explode", we will force a crash.
    if "explode" in payload:
        raise ValueError("Boom! Simulated processing error.")
        
    # Simulate heavy work
    time.sleep(3) 
    
    update_job_status(job_id, "COMPLETED")
    print(f"    [✔] Completed Job {job_id}")

def start_worker():
    print(f"[*] Worker started. Waiting for jobs in '{QUEUE_NAME}'...")
    
    while True:
        result = redis_client.brpop(QUEUE_NAME, timeout=0)
        
        if result:
            queue, job_json = result
            job_data = json.loads(job_json)
            
            try:
                # Try to process the job
                process_job(job_data)
                
            except Exception as e:
                job_id = job_data.get('job_id')
                # 1. Update the database state to FAILED
                update_job_status(job_id, "FAILED")
                
                # 2. Push the raw job data into the DLQ in Redis
                # We add the error message so we know WHY it failed
                dlq_entry = {
                    "original_job": job_data,
                    "error_message": str(e)
                }
                redis_client.lpush("dlq_queue", json.dumps(dlq_entry))
                
                print(f"    [!] Failed Job {job_id}. Moved to DLQ. Error: {e}")

if __name__ == '__main__':
    start_worker()