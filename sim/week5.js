// Loads the Week 5 bucket-brigade engine for the cross-check test.
// Reads week5/build_opim639_deck.py and evaluates only its simulation part
// (rng, Brigade, Loop, measure). The reference file is never modified.

const fs = require("node:fs");
const path = require("node:path");

function loadWeek5Brigade() {
  const src = fs.readFileSync(path.join(__dirname, "..", "week5", "build_opim639_deck.py"), "utf8");
  const engine = src.match(/ENGINE = r"""([\s\S]*?)"""/);
  if (!engine) throw new Error("ENGINE block not found in week5/build_opim639_deck.py");
  const simPart = engine[1].split("/* ================= drawing helpers")[0];
  return new Function(`${simPart}; return { Brigade, measure };`)();
}

module.exports = { loadWeek5Brigade };
