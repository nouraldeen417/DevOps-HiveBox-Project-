FROM python:3.11-alpine    

WORKDIR /app

# 1. Patch OS
RUN apk update && apk upgrade --no-cache

# 2. Install your application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. THE KILL SWITCH: Destroy pip, setuptools, and wheel. 
# They are not needed at runtime, and removing them destroys the vendored vulnerabilities.
RUN pip uninstall -y pip setuptools wheel jaraco.context || true

# 4. Copy app code
COPY src/ ./src/

# 5. Secure user context
RUN adduser -D appuser
USER appuser

CMD ["python", "src/app.py"]