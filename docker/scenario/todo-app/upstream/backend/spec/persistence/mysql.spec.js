const fs = require('fs');
const path = require('path');

jest.mock('wait-port', () => jest.fn().mockResolvedValue(true));
jest.mock('mysql2', () => ({ createPool: jest.fn() }));

// MySQL is not available on this host. Check the driver boundary, not a fake DB.
test('file-based connection settings reach mysql2 as strings', async () => {
    const validation = path.join(__dirname, '../../.validation.local');
    fs.mkdirSync(validation, { recursive: true });
    const dir = fs.mkdtempSync(path.join(validation, 'settings-'));
    const settings = { HOST: 'localhost', USER: 'todo', PASSWORD: 'test-only', DB: 'todos' };
    const previous = { ...process.env };
    try {
        for (const [key, value] of Object.entries(settings)) {
            const file = path.join(dir, key);
            fs.writeFileSync(file, value);
            process.env[`MYSQL_${key}_FILE`] = file;
        }
        jest.resetModules();
        const mysql = require('mysql2');
        mysql.createPool.mockReturnValue({ query: (_sql, cb) => cb(null) });
        await require('../../src/persistence/mysql').init();
        expect(mysql.createPool).toHaveBeenCalledWith(expect.objectContaining({
            host: 'localhost', user: 'todo', password: 'test-only', database: 'todos',
        }));
    } finally {
        process.env = previous;
    }
});
