FROM python:3.11-alpine    

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt \
    && pip install "jaraco.context>=6.1.0" "wheel>=0.46.2"

COPY src/ ./src/

RUN useradd -m appuser
USER appuser

CMD ["python", "src/app.py"]