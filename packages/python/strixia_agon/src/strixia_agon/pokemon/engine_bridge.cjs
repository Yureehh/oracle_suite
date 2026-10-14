// Only engine operations live here; policies and training belong in Python.
const path = require('node:path');
const readline = require('node:readline');
const {Battle, Teams, TeamValidator} = require(path.join(process.argv[2], 'dist/sim'));
const {extractChannelMessages} = require(path.join(process.argv[2], 'dist/sim/battle'));
const FORMAT = 'gen9championsvgc2026regmcbo3';
let battle;
let errors = [];
let updates = new Map();
function send(type, data) {
  if (type === 'sideupdate') {
    const [player, ...lines] = (Array.isArray(data) ? data.join('\n') : data).split('\n');
    for (const line of lines) {
      if (line.startsWith('|error|')) errors.push(line);
      if (line.startsWith('|request|')) updates.set(player, JSON.parse(line.slice(9)));
    }
  }
}
function frame(start = 0) {
  const events = extractChannelMessages(battle.log.slice(start).join('\n'), [0])[0].filter(line => !line.startsWith('|t:|'));
  // Wall-clock markers are transport metadata, not reproducible player evidence.
  const sheets = battle.log.filter(l => l.startsWith('|showteam|')).map(l => ({
    player: l.split('|')[2], team: Teams.unpack(l.split('|').slice(3).join('|')),
  }));
  return {turn: battle.turn, phase: battle.ended ? 'end' : battle.requestState,
    ended: battle.ended, winner: battle.winner || null, events, sheets,
    requests: battle.sides.map(s => ({...s.activeRequest, side: s.getRequestData()}))};
}
function command(input) {
  if (input.op === 'start') {
    if (battle) throw new Error('Battle already initialized');
    const teams = input.teams;
    for (const [i, team] of teams.entries()) {
      const reasons = TeamValidator.get(FORMAT).validateTeam(team);
      if (reasons) throw new Error(`p${i + 1}: ${reasons.join('\n')}`);
    }
    battle = new Battle({formatid: FORMAT, seed: input.seed, send,
      p1: {name: 'p1', team: teams[0]}, p2: {name: 'p2', team: teams[1]}});
    return frame();
  }
  if (!battle || battle.ended) throw new Error('Battle is not active');
  if (input.op !== 'step') throw new Error('Unknown operation');
  const snapshot = JSON.stringify(battle.toJSON());
  const requests = battle.sides.map(side => structuredClone(side.activeRequest));
  const start = battle.log.length;
  errors = [];
  updates = new Map();
  try {
    for (const [i, side] of battle.sides.entries()) {
      const choice = input.choices[i];
      if (side.activeRequest?.wait) {
        if (choice !== null) throw new Error(`p${i + 1} must wait`);
      } else {
        if (typeof choice !== 'string' || !choice.trim()) throw new Error(`p${i + 1} needs a choice`);
        if (!side.choose(choice) || !side.isChoiceDone()) {
          throw new Error(errors.join('\n') || side.choice.error || `Incomplete p${i + 1} choice`);
        }
      }
    }
    battle.commitChoices();
    return frame(start);
  } catch (error) {
    const revealed = errors.some(e => e.includes("[Unavailable choice]")) ? updates : new Map();
    battle.destroy();
    battle = Battle.fromJSON(snapshot);
    battle.send = send;
    for (const [i, side] of battle.sides.entries()) {
      // fromJSON regenerates requests; retain facts revealed by earlier retries.
      side.activeRequest = revealed.has(side.id) ? revealed.get(side.id) : requests[i];
    }
    if (revealed.size) {
      error.updated = true;
      error.frame = frame(battle.log.length);
    }
    throw error;
  }
}
const input = readline.createInterface({input: process.stdin, crlfDelay: Infinity});
input.on('line', line => {
  try { process.stdout.write(JSON.stringify({ok: true, frame: command(JSON.parse(line))}) + '\n'); }
  catch (error) { process.stdout.write(JSON.stringify({ok: false, error: error.message, updated: !!error.updated, frame: error.frame}) + '\n'); }
});
input.on('close', () => { if (battle) battle.destroy(); });
