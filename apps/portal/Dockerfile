FROM nginx:stable-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html /usr/share/nginx/html/index.html
COPY app.js style.css embedded.css /usr/share/nginx/html/portal/
COPY brand/ /usr/share/nginx/html/brand/
USER nginx
EXPOSE 8090
HEALTHCHECK --interval=15s --timeout=3s --start-period=3s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8090/api/health || exit 1
ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]
