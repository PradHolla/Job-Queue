# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install uv
RUN pip install uv

# Copy your dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy the rest of your application code
COPY . .

# We don't set a CMD here because docker-compose will dictate 
# whether this container runs server.py or worker.py