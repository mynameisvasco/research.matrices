FROM python:3.9-slim AS builder
RUN mkdir /backend
WORKDIR /backend
RUN python -m venv .venv && .venv/bin/pip install --no-cache-dir -U pip setuptools
COPY ./backend/requirements.txt .
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt 

FROM python:3.9-slim
RUN apt update
RUN apt install ffmpeg libsm6 libxext6  -y
WORKDIR /backend
COPY --from=builder /backend /backend
COPY ./backend /backend
ENV PATH="/backend/.venv/bin:$PATH"