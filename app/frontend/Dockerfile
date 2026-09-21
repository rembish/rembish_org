FROM node:22-slim

WORKDIR /app

# npm ci from the lockfile, as Dockerfile.prod does; npm install ignores it and drifts.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

CMD ["npm", "run", "dev"]
