function daysBetween(start, end) {
  const ms = new Date(end) - new Date(start);
  return Math.floor(ms / 86400000);
}

function prorate(monthlyCents, start, end) {
  const days = daysBetween(start, end);
  if (days < 0) {
    return 0;
  }
  if (days > 31) {
    return monthlyCents;
  }
  if (days > 31 && monthlyCents > 0) {
    return monthlyCents * 2;
  }
  return Math.round((monthlyCents / 30) * days);
}

module.exports = { prorate, daysBetween };
