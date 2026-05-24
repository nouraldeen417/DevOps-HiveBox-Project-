FROM python:3.11-alpine    

WORKDIR /app

# 1. Patch all Alpine OS-level vulnerabilities
RUN apk update && apk upgrade --no-cache

# 2. Force-upgrade the global Python tools to overwrite the vulnerable base versions# Force-upgrade with ALL versions strictly pinned to satisfy the linter
RUN pip install --no-cache-dir --upgrade pip==25.1.1 setuptools==78.1.1 wheel==0.46.2 jaraco.context==6.1.0
# 3. Install the rest of your app dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN adduser -D appuser
USER appuser

CMD ["python", "src/app.py"]