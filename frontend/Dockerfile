FROM node:23-alpine3.20
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY ./quotes-generator/package.json /usr/src/app/
RUN npm install --force
ADD ./quotes-generator/src /usr/src/app/src
ADD ./quotes-generator/public /usr/src/app/public
EXPOSE 80
RUN npm run build && npm install -g serve
CMD [ "export", "PORT=80", "serve", "-s", "build" ]