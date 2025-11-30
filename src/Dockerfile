# Stage 1: Runtime
# We use 'slim' to keep the image size small (~50MB) and secure
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency file first to leverage Docker Layer Caching
COPY requirements.txt.

# Install dependencies without storing cache (reduces image size)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the actual application code
COPY src/ src/

# Default command to execute the script
# We use module execution (-m) for better import handling
CMD ["python", "-m", "src.main"]