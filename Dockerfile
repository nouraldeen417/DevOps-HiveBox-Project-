FROM python:3.11-alpine    

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "jaraco.context>=6.1.0" "wheel>=0.46.2"

COPY src/ ./src/

RUN useradd -m appuser
USER appuser

CMD ["python", "src/app.py"]