// Capture actual protocol channels; omniscient payloads are research evidence only.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const upstream = path.join(root, 'tmp/pokemon-foundation/showdown/dist/sim');
const {Battle, Teams, TeamValidator} = require(upstream);
const {extractChannelMessages} = require(path.join(upstream, 'battle'));
const fixture = JSON.parse(fs.readFileSync(path.join(root, 'docs/planning/pokemon/foundation/teams.json')));
const format = 'gen9championsvgc2026regmcbo3';
function world(hidden) {
  const teams = structuredClone(fixture);
  // Hold visible gender constant while varying hidden allocation, seed and choice.
  teams.flat().forEach(set => { set.gender = "M"; });
  if (hidden) teams[1][0].evs = {hp: 32, atk: 2, def: 0, spa: 0, spd: 0, spe: 32};
  teams.forEach(t => { const errors = TeamValidator.get(format).validateTeam(t); if (errors) throw new Error(JSON.stringify(errors)); });
  const battle = new Battle({formatid: format, seed: hidden ? [4,3,2,1] : [1,2,3,4], p1: {name:'A',team:teams[0]},p2:{name:'B',team:teams[1]}});
  const preview = extractChannelMessages(battle.log.join('\n'), [0,1,2]);
  const sheets = preview[0].filter(l=>l.startsWith('|showteam|')).map(l=>({player:l.split('|')[2], team:Teams.unpack(l.split('|').slice(3).join('|'))}));
  const previewRequests = structuredClone(battle.sides.map(s=>s.activeRequest));
  battle.makeChoices('team 1234', 'team 1234');
  if (hidden) battle.sides[1].choose('switch 3, switch 4');
  else battle.sides[1].autoChoose();
  const boundary = extractChannelMessages(battle.log.join('\n'), [0,1,2]);
  const ownRequests = structuredClone(battle.sides.map(s=>s.activeRequest));
  const privileged = battle.toJSON();
  return {battle, preview, sheets, previewRequests, boundary, ownRequests, privileged};
}
const a = world(false), b = world(true);
const worlds = [a,b].map(w=>({preview:w.preview, sheets:w.sheets, preview_requests:w.previewRequests, boundary:w.boundary, own_requests:w.ownRequests, omniscient:w.privileged}));
// Finish the baseline after capturing the submitted choice, then expose only channels.
a.battle.sides[0].autoChoose(); a.battle.commitChoices();
while (!a.battle.ended && a.battle.turn < 100) a.battle.makeChoices();
if (!a.battle.ended) throw new Error('Visibility fixture exceeded bound');
const resolved = extractChannelMessages(a.battle.log.join('\n'), [0,1,2]);
process.stdout.write(JSON.stringify({task:'003',node:process.version,format,worlds,resolved}));
