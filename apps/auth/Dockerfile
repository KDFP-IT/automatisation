FROM python:3.12-alpine
WORKDIR /srv/auth
COPY apps/auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/auth/server.py .
USER nobody
EXPOSE 8080
ENV PORT=8080 ACCESS_FILE=/etc/auth/access.toml
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/auth/mode')"
CMD ["python", "server.py"]
