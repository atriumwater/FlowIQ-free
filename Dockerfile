FROM python:3.11-slim

WORKDIR /app

# Install required dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file (will create separately)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY FlowIQ-free.py .
COPY pipeRoughness.csv .
COPY steamTableRaw.csv .
COPY AtriumLogo.ico .

# Expose port for Gradio web interface
EXPOSE 7860

# Run the application
CMD ["python", "FlowIQ-free.py"]
