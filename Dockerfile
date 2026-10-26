FROM node:22-slim AS console
WORKDIR /console
COPY console/package.json console/package-lock.json ./
RUN npm ci
COPY console/ ./
RUN npm run build

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY paperweight/ paperweight/
RUN uv sync --frozen --no-dev
COPY tasks/ tasks/
COPY recordings/ recordings/
COPY eval/corpus/ eval/corpus/
COPY --from=console /console/dist console/dist
# note: the hosted demo replays recorded calls and never needs an api key
ENV PAPERWEIGHT_PUBLIC=1 PAPERWEIGHT_MODE=replay PAPERWEIGHT_LEDGER=/tmp/ledger.jsonl STATION_PORT=
EXPOSE 8080
CMD ["uv", "run", "--no-dev", "uvicorn", "paperweight.server.app:app", "--host", "0.0.0.0", "--port", "8080"]
