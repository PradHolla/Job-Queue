import grpc
import job_pb2
import job_pb2_grpc

def run():
    # 1. Open a channel to the server
    with grpc.insecure_channel('localhost:50051') as channel:
        # 2. Create a stub (this is what gRPC calls a client)
        stub = job_pb2_grpc.JobQueueStub(channel)
        
        # 3. Create and send the request using our generated classes
        print("Sending mock job to the server...")
        request = job_pb2.JobRequest(
            task_name="process_video",
            payload='{"file_id": "vid_123", "resolution": "1080p"}'
        )
        response = stub.SubmitJob(request)
        
        # 4. Read the response
        print(f"Success! Server assigned Job ID: {response.job_id}")
        print(f"Current Status: {response.status}")

if __name__ == '__main__':
    run()