function parseAmount(input) {
  const digits = String(input).replace(/[^0-9]/g, '');
  return Number.parseInt(digits, 10);
}

module.exports = { parseAmount };
