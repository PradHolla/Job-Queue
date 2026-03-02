import grpc
import job_pb2
import job_pb2_grpc
import time

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = job_pb2_grpc.JobQueueStub(channel)
        
        print("Sending 5 DEFAULT priority jobs...")
        for i in range(5):
            request = job_pb2.JobRequest(
                task_name=f"background_sync_{i}",
                payload='{"data": "bulk"}',
                priority="DEFAULT"
            )
            stub.SubmitJob(request)
            
        print("Sending 1 HIGH priority job...")
        request = job_pb2.JobRequest(
            task_name="PASSWORD_RESET_EMAIL",
            payload='{"user": "admin"}',
            priority="HIGH"
        )
        stub.SubmitJob(request)

if __name__ == '__main__':
    run()