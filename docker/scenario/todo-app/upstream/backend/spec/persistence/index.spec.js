jest.mock('../../src/persistence/mysql', () => ({ adapter: 'mysql' }));
jest.mock('../../src/persistence/sqlite', () => ({ adapter: 'sqlite' }));

test('selects MySQL when only MYSQL_HOST_FILE is provided', () => {
    const previous = { ...process.env };
    try {
        delete process.env.MYSQL_HOST;
        process.env.MYSQL_HOST_FILE = '/unused/test-host';
        jest.resetModules();
        expect(require('../../src/persistence').adapter).toBe('mysql');
    } finally {
        process.env = previous;
    }
});
