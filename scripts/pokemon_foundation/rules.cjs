// Numeric limits were read from the pinned Champions validator before these cases.
const fs = require('node:fs');
const path = require('node:path');
const {performance} = require('node:perf_hooks');
const start = performance.now();
const root = path.resolve(__dirname, '../..');
const {Battle, Dex, TeamValidator} = require(path.join(root, 'tmp/pokemon-foundation/showdown/dist/sim'));
const format = 'gen9championsvgc2026regmcbo3';
const fixtures = JSON.parse(fs.readFileSync(path.join(root, 'docs/planning/pokemon/foundation/teams.json')));
const zero = {hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0};
const validator = TeamValidator.get(format);
function check(name, modify) {
  const team = structuredClone(fixtures[0]);
  modify(team);
  const submitted = structuredClone(team);
  const reasons = validator.validateTeam(team);
  return {name, status: reasons ? 'rejected' : 'accepted', reasons, submitted, normalized: team};
}
const cases = [
  check('zero_neutral', t => { t[0].evs = {...zero}; t[0].nature = 'Hardy'; }),
  check('zero_serious', t => { t[0].evs = {...zero}; t[0].nature = 'Serious'; }),
  check('max_total', t => { t[0].evs = {...zero, hp: 32, atk: 32, spe: 2}; }),
  check('over_stat', t => { t[0].evs = {...zero, hp: 33}; }),
  check('negative', t => { t[0].evs = {...zero, hp: -1}; }),
  check('fractional', t => { t[0].evs = {...zero, hp: 0.5}; }),
  check('over_total', t => { t[0].evs = {...zero, hp: 32, atk: 32, spe: 3}; }),
  check('nonmax_iv', t => { t[0].ivs = {...zero, hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 0}; }),
  check('unavailable_species', t => { t[0].species = 'Mew'; t[0].name = 'Mew'; }),
  check('invalid_ability', t => { t[0].ability = 'Wonder Guard'; }),
  check('invalid_move', t => { t[0].moves = ['Spore']; }),
  check('unavailable_item', t => { t[0].item = 'Ability Shield'; }),
  check('duplicate_item', t => { t[0].item = 'Sitrus Berry'; t[1].item = 'Sitrus Berry'; }),
  check('four_members', t => { t.splice(4); }),
  check('seven_members', t => { t.push(structuredClone(t[0])); }),
  ...[1, 50, 100, 101].map(level => check(`level_${level}`, t => { t[0].level = level; })),
];
const examples = [];
for (const nature of ['Hardy', 'Timid', 'Modest']) {
  const teams = structuredClone(fixtures);
  teams[0][0].nature = nature;
  teams.forEach(t => { const errors = validator.validateTeam(t); if (errors) throw new Error(JSON.stringify(errors)); });
  const battle = new Battle({formatid: format, seed: [1,2,3,4], p1: {name: 'A', team: teams[0]}, p2: {name: 'B', team: teams[1]}});
  const mon = battle.sides[0].pokemon[0];
  const expected = {hp: 72 + 2 + 75, atk: 95 + 32 + 20, def: 67 + 0 + 20, spa: 103 + 0 + 20, spd: 71 + 0 + 20, spe: 122 + 32 + 20};
  if (nature === 'Timid') { expected.spe = Math.floor(174 * 110 / 100); expected.atk = Math.floor(147 * 90 / 100); }
  if (nature === 'Modest') { expected.spa = Math.floor(123 * 110 / 100); expected.atk = Math.floor(147 * 90 / 100); }
  const actual = {...mon.baseStoredStats, hp: mon.maxhp};
  const matches = Object.entries(expected).every(([stat,value]) => actual[stat] === value);
  if (!matches) throw new Error(`Hand calculation mismatch: ${nature}`);
  examples.push({species: 'Greninja', nature, expected, actual, matches, level: mon.level});
  battle.destroy();
}
const rules = Dex.formats.getRuleTable(Dex.formats.get(format));
process.stdout.write(JSON.stringify({task: '002', node: process.version, format,
  boundaries: {per_stat: 32, total: rules.evLimit, min_team: rules.minTeamSize, max_team: rules.maxTeamSize, picked_team: rules.pickedTeamSize, adjust_level: rules.adjustLevel},
  cases, examples, rules: [...rules], value_rules: [...rules.valueRules], elapsed_ms: performance.now() - start}));
