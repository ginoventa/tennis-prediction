import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { TennisModel } from '../web/model.mjs';
const artifact = JSON.parse(readFileSync(new URL('../artifacts/model.json', import.meta.url)));
const model = new TennisModel(artifact);

test('browser predictions match the preserved C# service fixtures', () => {
  const cases = JSON.parse(readFileSync(new URL('./csharp-predictions.json', import.meta.url)));
  for (const { request, expected } of cases) {
    const actual = model.predict(request);
    // C# formats explanatory strings with the server culture; compare their numbers separately.
    const drivers = actual.key_drivers;
    const expectedDrivers = expected.key_drivers;
    assert.deepEqual({ ...actual, key_drivers: [] }, { ...expected, key_drivers: [] });
    assert.deepEqual(drivers.map(d => d.factor), expectedDrivers.map(d => d.factor));
    drivers.forEach((d, i) => assert.equal(d.impact.replace(',', '.'), expectedDrivers[i].impact.replace(',', '.')));
  }
});

test('lookup accepts IDs, names and case; rejects unknown or identical players', () => {
  const p = artifact.inference.players[0];
  assert.equal(model.resolve(p.id.toUpperCase()).name, p.name);
  assert.equal(model.resolve(`${p.name} (${p.matches} jogos)`).name, p.name);
  assert.ok(model.searchPlayers(p.name.toLowerCase()).some(x => x.id === p.id));
  assert.throws(() => model.predict({ player_1_id: p.id, player_2_id: p.id }));
  assert.throws(() => model.predict({ player_1_id: 'unknown', player_2_id: p.id }));
});

test('fallbacks and reversed head-to-head are handled consistently', () => {
  const copy = structuredClone(artifact);
  const [a, b] = copy.inference.players;
  a.last_rank = null; b.last_rank = null;
  a.last_points = null; b.last_points = null;
  a.surface_win_rates = {}; b.surface_win_rates = {};
  copy.inference.head_to_head = [{ player_1: a.name, player_2: b.name, player_1_wins: 3, player_2_wins: 1 }];
  const instance = new TennisModel(copy);
  const forward = instance.features(a, b, 'Carpet');
  const reverse = instance.features(b, a, 'Carpet');
  assert.equal(forward[0], 0); assert.equal(forward[1], 0);
  assert.equal(forward[3], a.win_rate - b.win_rate);
  assert.equal(forward[4], 0.5); assert.equal(reverse[4], -0.5);
});

test('incompatible or corrupt artifacts fail before inference', () => {
  assert.throws(() => new TennisModel({ ...artifact, feature_names: [] }));
  assert.throws(() => new TennisModel({ ...artifact, scales: artifact.scales.map(() => 0) }));
});
