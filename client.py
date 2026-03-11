import grpc
import job_pb2
import job_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = job_pb2_grpc.JobQueueStub(channel)
        
        # We define a job request
        request = job_pb2.JobRequest(
            task_name="charge_credit_card",
            payload='{"user_id": "999", "amount": "$50"}',
            priority="HIGH"
        )
        
        print("Sending the job")
        response1 = stub.SubmitJob(request)
        
        print("Sending the EXACT SAME job payload again")
        # In a real scenario, the API would generate the same deterministic ID based on the payload, 
        # but for our test, we'll just trust that the worker handles idempotency for any duplicate ID.
        response2 = stub.SubmitJob(request)

if __name__ == '__main__':
    run()