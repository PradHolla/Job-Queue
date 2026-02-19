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
    
    # Update DB to show we are working on it
    update_job_status(job_id, "PROCESSING")
    print(f"\n[x] Processing Job {job_id}")
    
    try:
        # Simulate heavy work
        time.sleep(3) 
        
        # Success! Update DB
        update_job_status(job_id, "COMPLETED")
        print(f"    [✔] Completed Job {job_id}")
        
    except Exception as e:
        # Failure! Update DB
        update_job_status(job_id, "FAILED")
        print(f"    [!] Failed Job {job_id}: {e}")

def start_worker():
    print(f"[*] Worker started. Waiting for jobs in '{QUEUE_NAME}'...")
    
    while True:
        # BRPOP blocks until a job is available.
        # It returns a tuple: (queue_name, popped_value)
        # We use timeout=0 to block indefinitely.
        result = redis_client.brpop(QUEUE_NAME, timeout=0)
        
        if result:
            queue, job_json = result
            job_data = json.loads(job_json)
            
            try:
                process_job(job_data)
            except Exception as e:
                # In a real system, this is where you'd send the job to a Dead Letter Queue
                print(f"    [!] Error processing job {job_data.get('job_id')}: {e}")

if __name__ == '__main__':
    start_worker()