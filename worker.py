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
    
    # 1. THE IDEMPOTENCY CHECK
    # We try to set a key unique to this job. 
    # nx=True means "Set only if it does not exist"
    # ex=86400 means "Keep this lock for 24 hours to prevent old duplicates"
    lock_key = f"idempotency:{job_id}"
    acquired_lock = redis_client.set(lock_key, "locked", nx=True, ex=86400)
    
    if not acquired_lock:
        print(f"\n[!] Idempotency kick-in! Job {job_id} was already processed. Skipping.")
        return # Exit early, do not process!

    # 2. Proceed with normal processing
    update_job_status(job_id, "PROCESSING")
    print(f"\n[x] Processing Job {job_id}")
    
    if "explode" in payload:
        raise ValueError("Boom! Simulated processing error.")
        
    time.sleep(3) 
    
    update_job_status(job_id, "COMPLETED")
    print(f"    [✔] Completed Job {job_id}")

def start_worker():
    # Notice we list HIGH priority first!
    QUEUES = ["high_priority_queue", "default_queue"]
    print(f"[*] Worker started. Listening to: {QUEUES}...")
    
    while True:
        # BRPOP takes a list of keys. It will pop from 'high_priority_queue' 
        # as long as there are items. It only checks 'default_queue' if high is empty.
        result = redis_client.brpop(QUEUES, timeout=0)
        
        if result:
            queue_name, job_json = result
            job_data = json.loads(job_json)
            
            print(f"\n[!] Pulled from {queue_name.upper()}")
            
            try:
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