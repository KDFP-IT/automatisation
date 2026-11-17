FROM node:24-alpine AS build
WORKDIR /app
COPY apps/portal/package.json apps/portal/package-lock.json ./apps/portal/
RUN npm ci --prefix apps/portal
COPY apps/portal/index.html apps/portal/vite.config.mjs ./apps/portal/
COPY apps/portal/src ./apps/portal/src
COPY apps/portal/public ./apps/portal/public
COPY packages/kac-ui ./packages/kac-ui
COPY apps/signatures/dist/style.css ./apps/signatures/dist/style.css
RUN npm run build --prefix apps/portal

FROM nginx:stable-alpine

COPY apps/portal/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/apps/portal/dist /usr/share/nginx/html
USER nginx
EXPOSE 8090
HEALTHCHECK --interval=15s --timeout=3s --start-period=3s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8090/api/health || exit 1
ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]
