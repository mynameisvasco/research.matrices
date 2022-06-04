FROM node:16 as builder
RUN mkdir /app
COPY ./frontend /app
WORKDIR /app
RUN npm i
RUN npm run build

FROM nginx
COPY --from=build /app/build /usr/share/nginx/html
COPY --from=build /app/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
