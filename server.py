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
        job_id = str(uuid.uuid4())
        
        # 1. SAVE TO DATABASE FIRST
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO jobs (id, task_name, payload, status) VALUES (%s, %s, %s, %s)",
            (job_id, request.task_name, request.payload, "QUEUED")
        )
        conn.commit()
        cur.close()
        conn.close()
        
        # 2. PUSH TO REDIS SECOND
        job_data = {"job_id": job_id, "task_name": request.task_name, "payload": request.payload}
        redis_client.lpush("task_queue", json.dumps(job_data))
        
        print(f"--> Saved Job {job_id} to DB and pushed to Redis.")
        return job_pb2.JobResponse(job_id=job_id, status="QUEUED")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    job_pb2_grpc.add_JobQueueServicer_to_server(JobQueueServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC API Server running on port 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()