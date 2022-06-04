FROM node:16 as builder
RUN mkdir /app
COPY ./frontend/package.json /app
WORKDIR /app
RUN npm i
COPY ./frontend /app
RUN npm run build

FROM nginx
COPY --from=builder /app/build /usr/share/nginx/html
COPY --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
