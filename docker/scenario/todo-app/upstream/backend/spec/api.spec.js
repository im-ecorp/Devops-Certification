const { spawn } = require('child_process');
const path = require('path');

// Exercise the actual startup file, Express routes, UUID generation and SQLite.
// A disposable in-memory DB never reads the lab's credentials or volume.
test('real HTTP API creates, completes and deletes a todo', async () => {
    const env = { ...process.env, NODE_ENV: 'test', SQLITE_DB_LOCATION: ':memory:' };
    for (const key of Object.keys(env)) if (key.startsWith('MYSQL_')) delete env[key];
    const child = spawn(process.execPath, [path.join(__dirname, '../src/index.js')], { env });
    let output = '';
    child.stdout.on('data', (chunk) => { output += chunk; });
    child.stderr.on('data', (chunk) => { output += chunk; });
    try {
        await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => reject(new Error(`Startup timeout: ${output}`)), 5000);
            child.once('exit', (code) => { clearTimeout(timeout); reject(new Error(`Startup exited ${code}: ${output}`)); });
            child.stdout.on('data', () => {
                if (output.includes('Listening on port 3000')) { clearTimeout(timeout); resolve(); }
            });
        });
        const base = 'http://127.0.0.1:3000/api';
        expect(await (await fetch(`${base}/greeting`)).json()).toEqual({ greeting: 'Hello world!' });
        expect(await (await fetch(`${base}/items`)).json()).toEqual([]);
        const response = await fetch(`${base}/items`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'API test' }),
        });
        expect(response.status).toBe(200);
        const item = await response.json();
        expect(item.id).toMatch(/^[0-9a-f-]{36}$/);
        expect(item.completed).toBe(false);
        const updated = await fetch(`${base}/items/${item.id}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: item.name, completed: true }),
        });
        expect(await updated.json()).toEqual({ ...item, completed: true });
        expect((await fetch(`${base}/items/${item.id}`, { method: 'DELETE' })).status).toBe(200);
        expect(await (await fetch(`${base}/items`)).json()).toEqual([]);
    } finally {
        if (child.exitCode === null) {
            const exited = new Promise((resolve) => child.once('exit', resolve));
            child.kill('SIGTERM');
            await exited;
        }
    }
}, 10000);
