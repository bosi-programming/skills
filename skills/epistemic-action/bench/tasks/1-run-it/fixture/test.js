const { add } = require("./add");
if (add(2, 3) !== 5) {
  console.error("1 failed, 0 passed");
  process.exit(1);
}
console.log("1 passed, 0 failed");
