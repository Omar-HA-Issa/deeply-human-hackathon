FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* /app/
RUN npm install --include=dev

COPY frontend /app

ENV NODE_ENV=development

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
