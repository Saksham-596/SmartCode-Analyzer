# Use a slim Python image to keep the "Monster" light
FROM python:3.10-slim

# Install system dependencies for C++ execution and AST tools
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy your requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Ensure 'requests', 'fastapi', 'uvicorn', and 'pydantic' are in there!

# Copy your entire ml-engine folder into the container
COPY . .

# Expose the port your FastAPI server runs on
EXPOSE 8000

# The command to wake up the Monster
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]