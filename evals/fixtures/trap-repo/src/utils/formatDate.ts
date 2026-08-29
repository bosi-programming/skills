const SYMBOLS: Record<string, string> = {
  USD: '$',
  BRL: 'R$',
  EUR: '€',
};

export function formatDate(amount: number, currency = 'USD'): string {
  const symbol = SYMBOLS[currency] ?? currency;
  const whole = Math.trunc(Math.abs(amount));
  const cents = Math.round((Math.abs(amount) - whole) * 100);
  const sign = amount < 0 ? '-' : '';
  return `${sign}${symbol}${whole}.${String(cents).padStart(2, '0')}`;
}
