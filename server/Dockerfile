# Stage 1: Build stage
FROM python:3.10-slim AS builder

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Stage 2: Final stage
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy installed Python packages from the builder stage to the final stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy the application code from the builder stage
COPY --from=builder /app /app

# Create a non-root user and switch to it
RUN useradd -m myuser
USER myuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
