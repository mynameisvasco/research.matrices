FROM python:3.8-alpine
RUN mkdir /app
ADD ./backend /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "app.py"]