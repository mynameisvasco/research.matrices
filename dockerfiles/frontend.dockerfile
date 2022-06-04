FROM node:alpine
COPY ./frontend /app
RUN npm i
CMD ["npm", "run", "start"]

FROM nginx:alpine
COPY ./nginx.conf /etc/nginx/conf.d/default.conf