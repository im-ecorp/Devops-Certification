const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const http = require('node:http');
const express = require('express');

// Execute the real entrypoint, replacing only the database and Socket.IO boundaries.
async function start(options = {}) {
  const events = { connects: 0, releases: 0, queries: 0, broadcasts: [] };
  class Pool {
    connect(callback) {
      events.connects++;
      callback(null, { query: query, release: () => events.releases++ }, () => events.releases++);
    }
    on() {}
    query(sql, params, callback) { query(sql, params, callback); }
  }
  function query(sql, params, callback) {
    events.queries++;
    callback(options.queryError || null, { rows: [{ vote: 'a', count: '2' }] });
  }
  const mockExpress = (...args) => express(...args);
  Object.assign(mockExpress, express);
  // Disable static's automatic index serving so GET / reaches the actual root route.
  mockExpress.static = (dir, opts) => express.static(dir, { ...opts, index: false });
  const realRequire = require;
  const code = fs.readFileSync(path.join(__dirname, '../server.js'), 'utf8');
  const context = {
    require(name) {
      if (name === 'pg') return { Pool };
      if (name === 'express') return mockExpress;
      if (name === 'socket.io') return () => ({ on() {}, sockets: { emit: (...args) => events.broadcasts.push(args) } });
      return realRequire(name);
    },
    __dirname: path.join(__dirname, '..'),
    process: { env: { PORT: '0' } },
    console,
    setTimeout() {},
    clearTimeout() {},
  };
  vm.runInNewContext(code, context, { filename: 'server.js' });
  // A minimal testability seam: the application can be used without starting a second HTTP listener.
  return { events, server: context.server };
}

test('GET / serves the result page through its explicit route', async () => {
  const { server } = await start();
  try {
    const response = await new Promise((resolve, reject) => {
      http.get(`http://127.0.0.1:${server.address().port}/`, res => {
        let body = '';
        res.on('data', chunk => body += chunk);
        res.on('end', () => resolve({ status: res.statusCode, body }));
      }).on('error', reject);
    });
    assert.equal(response.status, 200);
    assert.match(response.body, /<html/i);
  } finally { await new Promise(resolve => server.close(resolve)); }
});

test('score polling does not retain a checked-out database client', async () => {
  const { events, server } = await start();
  try {
    assert.equal(events.queries, 1);
    assert.equal(events.connects, events.releases);
    assert.equal(JSON.parse(events.broadcasts[0][1]).a, 2);
  } finally { await new Promise(resolve => server.close(resolve)); }
});
