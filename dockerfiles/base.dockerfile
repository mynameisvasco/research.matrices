FROM python:3.9-slim
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN mkdir /app
COPY ./backend /app
WORKDIR /app