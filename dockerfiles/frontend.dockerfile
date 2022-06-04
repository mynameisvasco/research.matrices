FROM node:alpine
COPY ./frontend /app
RUN npm i
CMD ["npm", "run", "start"]