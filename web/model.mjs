// Browser port of TennisModelService and LogisticModel. Keep feature order in sync.
export const FEATURE_NAMES = ['rank_diff', 'points_diff', 'recent_form_diff',
  'surface_win_rate_diff', 'head_to_head_diff', 'experience_diff',
  'chart_serve_win_diff', 'chart_total_points_won_diff', 'chart_return_win_diff',
  'chart_bp_saved_diff', 'chart_winner_rate_diff', 'chart_unforced_rate_diff',
  'chart_experience_diff', 'round', 'is_slam'];

// .NET Math.Round uses ties-to-even, unlike Math.round.
function round(value, digits) {
  const scale = 10 ** digits;
  const scaled = value * scale;
  const lower = Math.floor(scaled);
  return (scaled - lower === 0.5 ? lower + Math.abs(lower % 2) : Math.round(scaled)) / scale;
}
const key = value => value.toUpperCase();

export class TennisModel {
  constructor(artifact) {
    if (JSON.stringify(artifact.feature_names) !== JSON.stringify(FEATURE_NAMES)) {
      throw new Error('O modelo não usa as features esperadas.');
    }
    for (const field of ['means', 'scales', 'coefficients']) {
      if (!Array.isArray(artifact[field]) || artifact[field].length !== FEATURE_NAMES.length ||
          !artifact[field].every(Number.isFinite)) throw new Error('Modelo inválido.');
    }
    if (!Number.isFinite(artifact.intercept) || artifact.scales.some(x => x <= 0) ||
        !artifact.inference?.players?.length) throw new Error('Modelo inválido.');
    this.artifact = artifact;
    this.players = new Map();
    this.ids = new Map();
    for (const p of [...artifact.inference.players].sort((a, b) => b.matches - a.matches)) {
      if (!this.players.has(key(p.name))) this.players.set(key(p.name), p);
      this.ids.set(key(p.id), key(p.name));
    }
    this.pairs = new Map();
    for (const p of artifact.inference.head_to_head) {
      this.pairs.set(JSON.stringify([key(p.player_1), key(p.player_2)]), [p.player_1_wins, p.player_2_wins]);
      this.pairs.set(JSON.stringify([key(p.player_2), key(p.player_1)]), [p.player_2_wins, p.player_1_wins]);
    }
  }

  searchPlayers(search = '', limit = 12) {
    return [...this.players.values()]
      .filter(p => key(p.name).includes(key(search)))
      .sort((a, b) => key(a.name) < key(b.name) ? -1 : key(a.name) > key(b.name) ? 1 : 0)
      .slice(0, Math.max(1, Math.min(300, limit)));
  }

  resolve(value) {
    const name = key((value ?? '').trim().replace(/\s+\(\d+\s+jogos\)$/i, '').trim());
    return this.players.get(this.ids.get(name) ?? name);
  }

  features(p1, p2, surface) {
    const [w1, w2] = this.pairs.get(JSON.stringify([key(p1.name), key(p2.name)])) ?? [0, 0];
    return [
      (p1.last_rank ?? 100) - (p2.last_rank ?? 100),
      (p1.last_points ?? 800) - (p2.last_points ?? 800),
      p1.recent_win_rate - p2.recent_win_rate,
      (p1.surface_win_rates[surface] ?? p1.win_rate) - (p2.surface_win_rates[surface] ?? p2.win_rate),
      w1 + w2 === 0 ? 0 : (w1 - w2) / (w1 + w2),
      Math.log(1 + p1.matches) - Math.log(1 + p2.matches),
      ...['chart_serve_win_rate', 'chart_total_points_won_rate', 'chart_return_win_rate',
        'chart_bp_saved_rate', 'chart_winner_rate', 'chart_unforced_rate'].map(f => p1[f] - p2[f]),
      Math.log(1 + p1.chart_matches) - Math.log(1 + p2.chart_matches),
      this.artifact.inference.default_round,
      ['AUSTRALIAN OPEN', 'FRENCH OPEN', 'WIMBLEDON', 'US OPEN']
        .includes(key(this.artifact.inference.default_tournament)) ? 1 : 0
    ];
  }

  predict(request) {
    const p1 = this.resolve(request.player_1_id);
    const p2 = this.resolve(request.player_2_id);
    if (!p1 || !p2) throw new Error('Selecione duas jogadoras disponíveis na lista.');
    if (p1 === p2) throw new Error('Escolha duas jogadoras diferentes.');
    const rawSurface = (request.surface ?? '').trim().toLowerCase() || 'hard';
    const surface = rawSurface[0].toUpperCase() + rawSurface.slice(1);
    const x = this.features(p1, p2, surface);
    const a = this.artifact;
    const contributions = x.map((v, i) => a.coefficients[i] * ((v - a.means[i]) / a.scales[i]));
    const z = contributions.reduce((sum, v) => sum + v, a.intercept);
    const exp = Math.exp(z >= 0 ? -z : z);
    const probability = z >= 0 ? 1 / (1 + exp) : exp / (1 + exp);
    const labels = ['Ranking atual', 'Pontuação WTA', 'Momento recente',
      `Aproveitamento no piso (${surface})`, 'Confronto direto (H2H)', 'Experiência histórica',
      'Saque charted', 'Total de pontos vencidos charted', 'Devolução charted',
      'Break points salvos charted', 'Winners charted', 'Erros não forçados charted',
      'Experiência charted', 'Fase do torneio', 'Grand Slam'];
    return {
      player_1: p1.name, player_2: p2.name,
      win_probability_p1: round(probability, 3), win_probability_p2: round(1 - probability, 3),
      power_index: { player_1: round(35 + 65 * probability, 1), player_2: round(35 + 65 * (1 - probability), 1) },
      key_drivers: contributions.map((impact, i) => ({ impact, factor: labels[i] }))
        .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact)).slice(0, 3)
        .map(({ impact, factor }) => ({ factor, impact: `${(Math.abs(impact) * 100).toFixed(1)}% para ${impact >= 0 ? p1.name : p2.name}` })),
      features: Object.fromEntries(FEATURE_NAMES.slice(0, 6).map((name, i) => [name, round(x[i], i < 2 ? 2 : 3)]))
    };
  }
}
