const assert = require('assert');
const { parseAmount } = require('../src/utils/parseAmount');

assert.strictEqual(parseAmount('1,00'), 1, 'parseAmount should read 1,00 as 1');

console.log('ok');
