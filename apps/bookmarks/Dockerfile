FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PDF_WEB_DATA_DIR=/data
WORKDIR /app
COPY webapp/requirements-deploy.txt ./
RUN pip install --no-cache-dir -r requirements-deploy.txt \
    && groupadd --gid 10001 portal \
    && useradd --uid 10001 --gid portal --no-create-home portal \
    && install -d -o 10001 -g 10001 /data
COPY add_drawing_bookmarks.py serve.py ./
COPY webapp/app.py webapp/worker.py ./webapp/
COPY webapp/static/ ./webapp/static/
USER 10001:10001
EXPOSE 8080
CMD ["python", "serve.py"]
