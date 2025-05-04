FROM python:3.11-slim

# Install espeak and dependencies
RUN apt-get update && \
    apt-get install -y espeak libespeak1 libespeak-dev && \
    pip install --upgrade pip

# Set environment variable for library path
ENV LD_LIBRARY_PATH=/usr/lib:/usr/local/lib

# Set the working directory
WORKDIR /app

# Copy your project files into the container
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
