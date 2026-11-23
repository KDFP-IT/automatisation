FROM python:3.12-slim
WORKDIR /srv/gesn-match
COPY apps/gesn-match/requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt \
 && adduser --disabled-password --uid 1000 app && mkdir /data && chown app:app /data
COPY apps/gesn-match/ .
USER app
EXPOSE 8080
ENV PORT=8080 GESN_DATA_DIR=/data
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health')"
CMD ["python", "serve.py"]
