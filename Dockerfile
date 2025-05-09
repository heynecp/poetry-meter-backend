FROM python:3.11-slim

# Install espeak and dependencies
RUN apt-get update && \
    apt-get install -y espeak libespeak1 libespeak-dev && \
    apt-get clean

# Set the environment variable so prosodic can find espeak
ENV PATH_ESPEAK=/usr/lib/x86_64-linux-gnu/libespeak.so.1

# Set working directory
WORKDIR /app

# Copy your app code
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
