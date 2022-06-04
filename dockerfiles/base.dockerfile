FROM python:3.9
RUN mkdir /app
COPY ./backend /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt