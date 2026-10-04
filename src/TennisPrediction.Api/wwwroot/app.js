const player1Search = document.querySelector("#player1Search");
const player2Search = document.querySelector("#player2Search");
const player1Options = document.querySelector("#player1Options");
const player2Options = document.querySelector("#player2Options");
const surface = document.querySelector("#surface");
const matchDate = document.querySelector("#matchDate");
const predictButton = document.querySelector("#predictButton");
const statusText = document.querySelector("#status");

const selectedPlayers = new Map();

matchDate.valueAsDate = new Date();

async function fetchPlayers(search = "") {
  const response = await fetch(`/players?limit=12&search=${encodeURIComponent(search)}`);
  if (!response.ok) {
    throw new Error("Não foi possível carregar as jogadoras.");
  }

  return response.json();
}

function renderPlayerOptions(container, input, players) {
  container.replaceChildren();
  container.hidden = players.length === 0 || document.activeElement !== input;

  for (const player of players) {
    const option = document.createElement("button");
    option.type = "button";
    option.className = "player-option";
    option.dataset.playerId = player.id;
    option.setAttribute("role", "option");

    const name = document.createElement("span");
    name.textContent = player.name;

    const meta = document.createElement("small");
    meta.textContent = `${player.matches} jogos · rank ${player.last_rank ?? "s/r"} · ${Math.round(player.win_rate * 100)}% vitórias`;

    option.append(name, meta);
    option.addEventListener("click", () => {
      selectedPlayers.set(input.id, player);
      input.value = player.name;
      container.hidden = true;
      input.classList.add("has-selection");
    });
    container.appendChild(option);
  }
}

async function loadPlayerOptions(input, container) {
  const players = await fetchPlayers(input.value.trim());
  renderPlayerOptions(container, input, players);
}

function resolvePlayer(input) {
  const selected = selectedPlayers.get(input.id);
  if (selected && selected.name === input.value.trim()) {
    return selected.id;
  }

  return input.value.trim();
}

function pct(value) {
  return `${Math.round(value * 100)}%`;
}

function getFeatureEntries(features) {
  const fields = [
    "rank_diff",
    "points_diff",
    "recent_form_diff",
    "surface_win_rate_diff",
    "head_to_head_diff",
    "experience_diff"
  ];

  return fields
    .filter(field => features[field] !== undefined)
    .map(field => [field, features[field]]);
}

function setFeatureList(features, player1 = "Jogadora 1", player2 = "Jogadora 2") {
  const config = {
    rank_diff: { label: "Ranking melhor", suffix: "pos.", decimals: 0, invertAdvantage: true },
    points_diff: { label: "Pontos WTA", suffix: "pts", decimals: 0 },
    recent_form_diff: { label: "Forma recente", suffix: "p.p.", decimals: 1, multiplier: 100 },
    surface_win_rate_diff: { label: "Vitórias no piso", suffix: "p.p.", decimals: 1, multiplier: 100 },
    head_to_head_diff: { label: "Confronto direto", suffix: "p.p.", decimals: 1, multiplier: 100 },
    experience_diff: { label: "Experiência", suffix: "escala log", decimals: 2 }
  };

  const featureItems = getFeatureEntries(features).map(([key, value]) => {
    const item = document.createElement("div");
    item.className = "feature-card";

    const feature = config[key];
    const rawValue = Number(value);
    const displayValue = Math.abs(rawValue * (feature.multiplier ?? 1));
    const advantageValue = rawValue * (feature.invertAdvantage ? -1 : 1);
    const advantageLabel = Math.abs(advantageValue) < 0.0001
      ? "Equilibrado"
      : `Vantagem ${advantageValue > 0 ? player1 : player2}`;

    const label = document.createElement("b");
    label.textContent = feature.label;

    const number = document.createElement("strong");
    number.textContent = displayValue.toFixed(feature.decimals);

    const suffix = document.createElement("small");
    suffix.textContent = `${feature.suffix} · ${advantageLabel}`;

    item.append(label, number, suffix);
    return item;
  });

  document.querySelector("#features").replaceChildren(...featureItems);
}

async function predict() {
  statusText.textContent = "";
  predictButton.disabled = true;

  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        player_1_id: resolvePlayer(player1Search),
        player_2_id: resolvePlayer(player2Search),
        surface: surface.value,
        match_date: matchDate.value
      })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error ?? "Não foi possível calcular a previsão.");
    }

    const winner = data.win_probability_p1 >= data.win_probability_p2 ? data.player_1 : data.player_2;
    document.querySelector("#winner").textContent = `Vencedora prevista: ${winner}`;
    document.querySelector("#barP1").style.width = pct(data.win_probability_p1);
    document.querySelector("#p1Name").textContent = data.player_1;
    document.querySelector("#p2Name").textContent = data.player_2;
    document.querySelector("#p1Probability").textContent = pct(data.win_probability_p1);
    document.querySelector("#p2Probability").textContent = pct(data.win_probability_p2);
    document.querySelector("#powerP1").textContent = data.power_index.player_1.toFixed(1);
    document.querySelector("#powerP2").textContent = data.power_index.player_2.toFixed(1);
    document.querySelector("#powerNameP1").textContent = data.player_1;
    document.querySelector("#powerNameP2").textContent = data.player_2;

    const drivers = data.key_drivers.map(driver => {
      const item = document.createElement("li");
      const factor = document.createElement("b");
      factor.textContent = driver.factor;
      const impact = document.createElement("span");
      impact.textContent = driver.impact;
      item.append(factor, impact);
      return item;
    });
    document.querySelector("#drivers").replaceChildren(...drivers);
    setFeatureList(data.features, data.player_1, data.player_2);
  } catch (error) {
    statusText.textContent = error.message;
  } finally {
    predictButton.disabled = false;
  }
}

let searchTimer;
function scheduleSearch(input, container) {
  selectedPlayers.delete(input.id);
  input.classList.remove("has-selection");
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadPlayerOptions(input, container), 160);
}

function setupPlayerPicker(input, container) {
  input.addEventListener("focus", () => loadPlayerOptions(input, container));
  input.addEventListener("input", () => scheduleSearch(input, container));
  input.closest(".player-picker").querySelector(".clear-player").addEventListener("click", () => {
    selectedPlayers.delete(input.id);
    input.value = "";
    input.classList.remove("has-selection");
    input.focus();
    loadPlayerOptions(input, container);
  });
}

document.addEventListener("click", event => {
  for (const [input, container] of [[player1Search, player1Options], [player2Search, player2Options]]) {
    if (!input.closest(".player-picker").contains(event.target)) {
      container.hidden = true;
    }
  }
});

setupPlayerPicker(player1Search, player1Options);
setupPlayerPicker(player2Search, player2Options);
predictButton.addEventListener("click", predict);
