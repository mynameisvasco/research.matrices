FROM node:alpine
EXPOSE 3000
COPY ./frontend /app
WORKDIR /app
RUN npm i
CMD ["npm", "run", "start"]

FROM nginx:alpine
EXPOSE 80
COPY ./nginx.conf /etc/nginx/conf.d/default.conf