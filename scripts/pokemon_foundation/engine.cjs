// Research harness only. Engine defaults are deliberately not a competitive policy.
const fs = require('node:fs');
const path = require('node:path');
const {performance} = require('node:perf_hooks');
const started = performance.now();
const root = path.resolve(__dirname, '../..');
const upstream = path.join(root, 'tmp/pokemon-foundation/showdown');
const {Battle, Dex, Teams, TeamValidator} = require(path.join(upstream, 'dist/sim'));
const loadMs = performance.now() - started;
const format = 'gen9championsvgc2026regmcbo3';
const fixtures = JSON.parse(fs.readFileSync(path.join(root, 'docs/planning/pokemon/foundation/teams.json')));
const clone = value => structuredClone(value);
const validate = team => TeamValidator.get(format).validateTeam(team);
const validation = fixtures.map(team => validate(clone(team)));
if (validation.some(Boolean)) throw new Error(JSON.stringify(validation));
function create(seed = [1, 2, 3, 4]) {
  const teams = clone(fixtures);
  teams.forEach(team => { if (validate(team)) throw new Error('Invalid fixture'); });
  return new Battle({formatid: format, seed, p1: {name: 'ProbeA', team: teams[0]}, p2: {name: 'ProbeB', team: teams[1]}});
}
function finish(battle) {
  let decisions = 0;
  while (!battle.ended && decisions++ < 500) battle.makeChoices();
  if (!battle.ended) throw new Error('500 decision bound exceeded');
  return {winner: battle.winner, turns: battle.turn, log: battle.log};
}
function digest(value) { return require('node:crypto').createHash('sha256').update(JSON.stringify(value)).digest('hex'); }
const firstStart = performance.now();
const original = create();
const startupMs = performance.now() - firstStart;
const preview = clone(original.sides.map(s => s.activeRequest));
const sheets = original.log.filter(line => line.startsWith('|showteam|')).map(line => Teams.unpack(line.split('|').slice(3).join('|')));
original.makeChoices('team 1234', 'team 1234');
const requests = clone(original.sides.map(s => s.activeRequest));
const snapshot = JSON.stringify(original.toJSON());
const restored = Battle.fromJSON(snapshot);
const resultA = finish(original), resultB = finish(restored);
const repeat = create(); repeat.makeChoices('team 1234', 'team 1234');
const repeatResult = finish(repeat);
const branchA = Battle.fromJSON(snapshot), branchB = Battle.fromJSON(snapshot);
const before = JSON.stringify(branchB.toJSON());
branchA.makeChoices('switch 3, switch 4', 'default');
const isolated = before === JSON.stringify(branchB.toJSON());
branchB.makeChoices();
const differentBranch = digest(branchA.log) !== digest(branchB.log);
const invalid = clone(fixtures[0]); invalid[1].species = invalid[0].species;
const rejection = validate(invalid);
const times = [], hashes = [];
for (let i = 0; i < 100; i++) {
  const start = performance.now();
  const battle = create([1, 2, 3, i + 1]);
  battle.makeChoices('team 1234', 'team 1234');
  hashes.push(digest(finish(battle)));
  times.push(performance.now() - start);
  battle.destroy();
}
const stat = original.sides[0].pokemon[0];
const output = {
  task: '001', format, node: process.version, showdown: require(path.join(upstream, 'package.json')).version,
  validation, cases: {format: Dex.formats.get(format), preview, requests, sheets,
    invalid_team: rejection, identical_seed: digest(resultA) === digest(repeatResult),
    snapshot_continuation: digest(resultA) === digest(resultB), branch_isolation: isolated, distinct_branch: differentBranch,
    termination: {winner: resultA.winner, turns: resultA.turns},
    single_engine_games: 1, best_of_rule: original.ruleTable.valueRules.get('bestof'),
    champions_stats: {species: stat.species.name, base: stat.species.baseStats, allocation: stat.set.evs, stats: stat.baseStoredStats, hp: stat.maxhp}},
  timings: {load_ms: loadMs, first_battle_start_ms: startupMs, warm_battles: 100,
    total_ms: times.reduce((a,b)=>a+b,0), median_ms: [...times].sort((a,b)=>a-b)[50], samples_ms: times},
  trace: resultA.log, batch_hashes: hashes,
  packed_teams: fixtures.map(team => Teams.pack(team))
};
if (!output.cases.identical_seed || !output.cases.snapshot_continuation || !isolated || !differentBranch || !rejection) throw new Error('Invariant failed');
process.stdout.write(JSON.stringify(output));
