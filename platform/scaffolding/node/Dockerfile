FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD node -e "fetch('http://localhost:8000/health').then(r=>{if(!r.ok)process.exit(1)})"

CMD ["node", "server.js"]
