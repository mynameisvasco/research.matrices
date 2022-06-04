FROM python:3.8-alpine
RUN mkdir /app
ADD ./backend /app
WORKDIR /app
RUN apk add --update --no-cache --virtual .tmp gcc libc-dev linux-headers
RUN apk add --no-cache jpeg-dev zlib-dev
RUN apk add --no-cache hdf5-dev
RUN pip install -r requirements.txt
CMD ["python", "app.py"]