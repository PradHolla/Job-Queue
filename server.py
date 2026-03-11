import grpc
from concurrent import futures
import json
import uuid
import redis
import job_pb2
import job_pb2_grpc
import psycopg2

import os

# For Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

# For Postgres
DB_HOST = os.environ.get("DB_HOST", "localhost")

def get_db_connection():
    return psycopg2.connect(f"dbname=postgres user=postgres password=mysecretpassword host={DB_HOST}")

class JobQueueServicer(job_pb2_grpc.JobQueueServicer):
    def SubmitJob(self, request, context):
        # 1. GENERATE DETERMINISTIC ID
        # Combine the task name and payload into one string
        unique_string = f"{request.task_name}:{request.payload}"
        
        # Create a consistent UUID based on that string
        job_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
        
        # 2. SAVE TO DATABASE (With Conflict Handling)
        conn = get_db_connection()
        cur = conn.cursor()
        
        # If this exact ID already exists in the DB, do nothing!
        cur.execute(
            """
            INSERT INTO jobs (id, task_name, payload, status) 
            VALUES (%s, %s, %s, %s) 
            ON CONFLICT (id) DO NOTHING
            """,
            (job_id, request.task_name, request.payload, "QUEUED")
        )
        conn.commit()
        cur.close()
        conn.close()
        
        # 3. PUSH TO REDIS
        job_data = {"job_id": job_id, "task_name": request.task_name, "payload": request.payload}
        target_queue = "high_priority_queue" if request.priority == "HIGH" else "default_queue"
        
        redis_client.lpush(target_queue, json.dumps(job_data))
        
        print(f"--> Saved Job {job_id} and pushed to {target_queue}.")
        return job_pb2.JobResponse(job_id=job_id, status="QUEUED")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    job_pb2_grpc.add_JobQueueServicer_to_server(JobQueueServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC API Server running on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()