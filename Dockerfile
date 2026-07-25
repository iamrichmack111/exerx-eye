FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir fastapi uvicorn textual rich
RUN mkdir -p /data
ENV EXERCISE_DB_PATH=/data/exercises.db
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
