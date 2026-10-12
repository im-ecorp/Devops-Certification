const { test } = require('node:test');
const assert = require('node:assert/strict');
const { listen } = require('../src/server');

test('greeting and health respond over HTTP', async (t) => {
  const server = listen(0, '127.0.0.1');
  await new Promise((resolve) => server.once('listening', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const base = `http://127.0.0.1:${server.address().port}`;
  const greeting = await fetch(base + '/');
  assert.equal(greeting.status, 200);
  assert.deepEqual(await greeting.json(), { message: 'Hello from Node.js in Docker!' });
  const health = await fetch(base + '/health');
  assert.equal(health.status, 200);
  assert.deepEqual(await health.json(), { status: 'ok' });
  assert.equal((await fetch(base + '/missing')).status, 404);
});
