# Start with a lightweight Python image
FROM python:3.10-slim

# Install system dependencies for PDF processing and build tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cmake \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Set up directory structure
WORKDIR /app
COPY . .

# Run the application
CMD ["python", "app.py"]
