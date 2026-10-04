from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score


ROOT = Path(__file__).resolve().parents[2]
TRAINING_PATH = ROOT / "src" / "training"
ARTIFACT_PATH = ROOT / "artifacts" / "model.json"
OUTPUT_PATH = ROOT / "artifacts" / "benchmark.json"

sys.path.insert(0, str(TRAINING_PATH))

from train_model import (  # noqa: E402
    ChartingState,
    PlayerState,
    build_features,
    load_charting_events,
    load_matches,
    update_history,
)


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    rows: int
    coverage: float
    accuracy: float
    log_loss: float
    brier_score: float
    roc_auc: float


def sigmoid(value: float) -> float:
    if value >= 0:
        exp = math.exp(-value)
        return 1 / (1 + exp)

    exp = math.exp(value)
    return exp / (1 + exp)


def clip_probability(probability: float) -> float:
    return min(max(float(probability), 1e-6), 1 - 1e-6)


def model_probability(features: list[float], artifact: dict) -> float:
    x = np.array(features, dtype=float)
    means = np.array(artifact["means"], dtype=float)
    scales = np.array(artifact["scales"], dtype=float)
    coefficients = np.array(artifact["coefficients"], dtype=float)
    z = float(artifact["intercept"]) + float(np.dot(coefficients, (x - means) / scales))
    return clip_probability(sigmoid(z))


def market_probability(row: pd.Series) -> float | None:
    odd_1 = pd.to_numeric(row.get("Odd_1"), errors="coerce")
    odd_2 = pd.to_numeric(row.get("Odd_2"), errors="coerce")
    if pd.isna(odd_1) or pd.isna(odd_2) or odd_1 <= 1 or odd_2 <= 1:
        return None

    implied_1 = 1 / float(odd_1)
    implied_2 = 1 / float(odd_2)
    return clip_probability(implied_1 / (implied_1 + implied_2))


def ranking_probability(row: pd.Series) -> float:
    rank_diff = float(row["Rank_1"] - row["Rank_2"])
    return clip_probability(sigmoid(-rank_diff / 100))


def points_probability(row: pd.Series) -> float:
    points_diff = float(row["Pts_1"] - row["Pts_2"])
    return clip_probability(sigmoid(points_diff / 1000))


def evaluate(name: str, y_true: list[int], probabilities: list[float | None], total_rows: int) -> BenchmarkResult:
    paired = [(truth, probability) for truth, probability in zip(y_true, probabilities) if probability is not None]
    if not paired:
        raise ValueError(f"{name} nao tem previsoes validas para avaliar.")

    y = np.array([truth for truth, _ in paired], dtype=int)
    p = np.array([clip_probability(probability) for _, probability in paired], dtype=float)
    predictions = (p >= 0.5).astype(int)

    return BenchmarkResult(
        name=name,
        rows=int(len(y)),
        coverage=round(len(y) / total_rows, 4),
        accuracy=round(float(accuracy_score(y, predictions)), 4),
        log_loss=round(float(log_loss(y, p)), 4),
        brier_score=round(float(brier_score_loss(y, p)), 4),
        roc_auc=round(float(roc_auc_score(y, p)), 4),
    )


def build_benchmark_rows(matches: pd.DataFrame, charting_events: pd.DataFrame, artifact: dict) -> dict[str, list]:
    players: dict[str, PlayerState] = {}
    h2h: dict[tuple[str, str], list[int]] = {}
    charting: dict[str, ChartingState] = {}
    chart_index = 0
    split_index = max(1, int(len(matches) * 0.8))

    y_true: list[int] = []
    model_probs: list[float] = []
    market_probs: list[float | None] = []
    ranking_probs: list[float] = []
    points_probs: list[float] = []

    for index, row in matches.iterrows():
        while chart_index < len(charting_events) and charting_events.iloc[chart_index]["DateValue"] < row["Date"]:
            chart_row = charting_events.iloc[chart_index]
            alias = str(chart_row["PlayerAlias"]).strip()
            charting.setdefault(alias, ChartingState()).add_stats(chart_row)
            chart_index += 1

        features = build_features(row, players, h2h, charting)
        target = int(str(row["Winner"]).strip().lower() == str(row["Player_1"]).strip().lower())

        if index >= split_index:
            y_true.append(target)
            model_probs.append(model_probability(features, artifact))
            market_probs.append(market_probability(row))
            ranking_probs.append(ranking_probability(row))
            points_probs.append(points_probability(row))

        update_history(row, players, h2h)

    return {
        "y_true": y_true,
        "model": model_probs,
        "market_odds": market_probs,
        "ranking_baseline": ranking_probs,
        "points_baseline": points_probs,
    }


def main() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    matches = load_matches()
    charting_events = load_charting_events()
    rows = build_benchmark_rows(matches, charting_events, artifact)
    y_true = rows["y_true"]

    results = [
        evaluate("Nosso modelo", y_true, rows["model"], len(y_true)),
        evaluate("Mercado por odds", y_true, rows["market_odds"], len(y_true)),
        evaluate("Baseline ranking", y_true, rows["ranking_baseline"], len(y_true)),
        evaluate("Baseline pontos WTA", y_true, rows["points_baseline"], len(y_true)),
    ]

    output = {
        "description": "Benchmark no mesmo recorte temporal de teste usado no treinamento.",
        "test_rows": len(y_true),
        "metrics": [result.__dict__ for result in results],
        "notes": [
            "Mercado por odds usa Odd_1 e Odd_2 normalizadas para remover a margem da casa.",
            "Baselines de ranking e pontos usam funcoes logisticas heuristicas, sem treino adicional.",
            "Log loss e brier score avaliam qualidade probabilistica; menor e melhor.",
            "Accuracy e ROC-AUC avaliam acerto/diferenciacao; maior e melhor.",
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Benchmark salvo em", OUTPUT_PATH)
    print()
    print(f"{'Modelo':<22} {'Rows':>6} {'Cobertura':>9} {'Accuracy':>9} {'LogLoss':>8} {'Brier':>8} {'ROC-AUC':>8}")
    for result in results:
        print(
            f"{result.name:<22} "
            f"{result.rows:>6} "
            f"{result.coverage:>9.1%} "
            f"{result.accuracy:>9.4f} "
            f"{result.log_loss:>8.4f} "
            f"{result.brier_score:>8.4f} "
            f"{result.roc_auc:>8.4f}"
        )


if __name__ == "__main__":
    main()
