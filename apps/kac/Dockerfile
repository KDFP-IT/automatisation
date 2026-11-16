FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    KAC_LOCAL_EXPORT=1 PDF_WEB_DATA_DIR=/data HOME=/tmp
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer python3-uno fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea \
    tesseract-ocr tesseract-ocr-osd tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 portal \
    && useradd --uid 10001 --gid portal --no-create-home portal \
    && install -d -o 10001 -g 10001 /data
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py serve.py assemble.py export-libreoffice.py ./
COPY static/ ./static/

USER 10001:10001
EXPOSE 8080
CMD ["python", "serve.py", "--host", "0.0.0.0"]
