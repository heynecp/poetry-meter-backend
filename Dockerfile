FROM python:3.11-slim

# Install espeak-ng and dependencies
RUN apt-get update && \
    apt-get install -y espeak-ng libespeak-ng1 libespeak-ng-dev && \
    pip install --upgrade pip

# Set environment variable so prosodic can find espeak-ng
ENV PATH_ESPEAK=/usr/lib/libespeak-ng.so.1

# Set the working directory
WORKDIR /app

# Copy your project files into the container
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
