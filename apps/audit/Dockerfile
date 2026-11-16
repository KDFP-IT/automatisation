FROM python:3.12-alpine
WORKDIR /srv/audit
COPY apps/audit/server.py .
RUN adduser -D -u 1000 app && mkdir /data && chown app:app /data
USER app
EXPOSE 8080
ENV PORT=8080 AUDIT_DB_PATH=/data/audit.sqlite3
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/audit/health')"
CMD ["python", "server.py"]
