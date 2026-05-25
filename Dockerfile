#Stage 1: Builder 
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

#  Install dependencies into a custom prefix (/install)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


#Stage 2: Final
FROM python:3.11-slim

#Prevent Python from writing .pyc files and enable real-time logs
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-root user for security best practice
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser
    
# Copy installed dependencies from builder stage
# IMPORTANT: /usr/local is where Python expects packages
COPY --from=builder /install /usr/local 

COPY src/ ./src/

# Switch to non-root user for security
USER appuser

EXPOSE 5000

CMD ["python", "src/app.py"]
