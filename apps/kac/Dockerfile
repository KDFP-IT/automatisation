FROM node:24-alpine AS ui
WORKDIR /app
COPY apps/kac/ui/package.json apps/kac/ui/package-lock.json ./apps/kac/ui/
RUN npm ci --prefix apps/kac/ui
COPY apps/kac/ui/index.html apps/kac/ui/vite.config.mjs ./apps/kac/ui/
COPY apps/kac/ui/src ./apps/kac/ui/src
COPY packages/kac-ui ./packages/kac-ui
RUN npm run build --prefix apps/kac/ui

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
COPY apps/kac/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/kac/app.py apps/kac/serve.py apps/kac/assemble.py apps/kac/export-libreoffice.py ./
COPY --from=ui /app/apps/kac/static/ui ./static/ui

USER 10001:10001
EXPOSE 8080
CMD ["python", "serve.py", "--host", "0.0.0.0"]
