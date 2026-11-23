FROM python:3.12-slim
WORKDIR /srv/gesn-match
COPY apps/gesn-match/requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt \
 && useradd -m -u 1000 app && mkdir -p /data && chown app:app /data
COPY apps/gesn-match/ .
USER app
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/gesn-match/api/health')"
CMD ["python", "serve.py", "--host", "0.0.0.0"]
