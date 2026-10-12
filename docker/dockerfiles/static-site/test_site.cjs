const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const root = path.join(__dirname, 'site');
assert.ok(fs.existsSync(path.join(root, 'index.html')), 'Homepage must exist');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
assert.match(html, /href="style.css"/);
assert.match(html, /src="script.js"/);
assert.match(html, /id="greet"/);
assert.match(html, /id="message"/);
const button = { addEventListener(event, handler) {
  assert.equal(event, 'click'); this.click = handler;
}};
const message = { textContent: '' };
vm.runInNewContext(fs.readFileSync(path.join(root, 'script.js'), 'utf8'), {
  document: { querySelector(selector) {
    return { '#greet': button, '#message': message }[selector];
  } }
});
button.click();
assert.equal(message.textContent, 'Hello from JavaScript!');
assert.ok(fs.readFileSync(path.join(root, 'style.css'), 'utf8').length > 0);
console.log('Static-site markup and button behavior passed.');
