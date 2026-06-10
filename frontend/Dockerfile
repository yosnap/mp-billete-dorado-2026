FROM node:22-slim AS builder

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .
RUN npm run build

FROM node:22-slim AS runner

WORKDIR /app

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json .

EXPOSE 4321

CMD ["node", "dist/server/entry.mjs"]
