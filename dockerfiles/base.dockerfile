FROM python:3.9-slim AS builder
RUN mkdir /app
WORKDIR /app
RUN python -m venv .venv && .venv/bin/pip install --no-cache-dir -U pip setuptools
COPY ./backend/requirements.txt .
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt 

FROM python:3.9-alpine
WORKDIR /app
COPY --from=builder /app /app
COPY ./backend /app
ENV PATH="/app/.venv/bin:$PATH"