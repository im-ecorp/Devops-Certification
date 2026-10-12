const express = require('express');

const app = express();
app.get('/', (_request, response) => response.json({ message: 'Hello from Node.js in Docker!' }));
app.get('/health', (_request, response) => response.json({ status: 'ok' }));

function listen(port = 3000, host = '0.0.0.0') {
  return app.listen(port, host);
}

if (require.main === module) {
  listen(Number(process.env.PORT || 3000));
}

module.exports = { app, listen };
