from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import accuracy_score, f1_score, log_loss, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data-kaggle" / "wta.csv"
CHARTING_MATCHES_PATH = ROOT / "data" / "charting-w-matches.csv"
CHARTING_OVERVIEW_PATH = ROOT / "data" / "charting-w-stats-Overview.csv"
ARTIFACT_PATH = ROOT / "artifacts" / "model.json"

FEATURE_NAMES = [
    "rank_diff",
    "points_diff",
    "recent_form_diff",
    "surface_win_rate_diff",
    "head_to_head_diff",
    "experience_diff",
    "chart_serve_win_diff",
    "chart_total_points_won_diff",
    "chart_return_win_diff",
    "chart_bp_saved_diff",
    "chart_winner_rate_diff",
    "chart_unforced_rate_diff",
    "chart_experience_diff",
    "round",
    "is_slam",
]

ROUNDS = {
    "1st Round": 1,
    "2nd Round": 2,
    "3rd Round": 3,
    "4th Round": 4,
    "Quarterfinals": 5,
    "Semifinals": 6,
    "The Final": 7,
}

SLAMS = {"Australian Open", "French Open", "Wimbledon", "US Open"}


@dataclass
class PlayerState:
    matches: int = 0
    wins: int = 0
    last_rank: int | None = None
    last_points: float | None = None
    recent: deque[bool] = field(default_factory=lambda: deque(maxlen=5))
    surface: dict[str, list[int]] = field(default_factory=lambda: defaultdict(lambda: [0, 0]))

    @property
    def overall_win_rate(self) -> float:
        return 0.5 if self.matches == 0 else self.wins / self.matches

    @property
    def recent_win_rate(self) -> float:
        return self.overall_win_rate if not self.recent else sum(self.recent) / len(self.recent)

    def surface_win_rate(self, surface: str) -> float:
        wins, matches = self.surface.get(surface, [0, 0])
        return self.overall_win_rate if matches == 0 else wins / matches

    def add_match(self, surface: str, won: bool, rank: int, points: float) -> None:
        self.matches += 1
        self.wins += int(won)
        self.last_rank = rank
        self.last_points = points
        self.recent.append(won)
        stats = self.surface[surface]
        stats[0] += int(won)
        stats[1] += 1


@dataclass
class ChartingState:
    matches: int = 0
    serve_pts: int = 0
    serve_won: int = 0
    first_won: int = 0
    first_in: int = 0
    second_won: int = 0
    second_in: int = 0
    break_points: int = 0
    break_points_saved: int = 0
    return_pts: int = 0
    return_won: int = 0
    winners: int = 0
    unforced: int = 0

    @property
    def serve_win_rate(self) -> float:
        return safe_divide(self.serve_won, self.serve_pts, 0.5)

    @property
    def return_win_rate(self) -> float:
        return safe_divide(self.return_won, self.return_pts, 0.5)

    @property
    def total_points_won_rate(self) -> float:
        return safe_divide(self.serve_won + self.return_won, self.serve_pts + self.return_pts, 0.5)

    @property
    def break_points_saved_rate(self) -> float:
        return safe_divide(self.break_points_saved, self.break_points, 0.5)

    @property
    def winner_rate(self) -> float:
        return safe_divide(self.winners, self.serve_pts + self.return_pts, 0.0)

    @property
    def unforced_rate(self) -> float:
        return safe_divide(self.unforced, self.serve_pts + self.return_pts, 0.0)

    def add_stats(self, row: pd.Series) -> None:
        serve_pts = int(row["serve_pts"])
        first_won = int(row["first_won"])
        second_won = int(row["second_won"])
        self.matches += 1
        self.serve_pts += serve_pts
        self.serve_won += first_won + second_won
        self.first_won += first_won
        self.first_in += int(row["first_in"])
        self.second_won += second_won
        self.second_in += int(row["second_in"])
        self.break_points += int(row["bk_pts"])
        self.break_points_saved += int(row["bp_saved"])
        self.return_pts += int(row["return_pts"])
        self.return_won += int(row["return_pts_won"])
        self.winners += int(row["winners"])
        self.unforced += int(row["unforced"])


def normalize_surface(value: object) -> str:
    if pd.isna(value) or not str(value).strip():
        return "Hard"
    return str(value).strip().lower().title()


def safe_divide(numerator: float, denominator: float, default: float) -> float:
    return default if denominator == 0 else numerator / denominator


def abbreviate_player_name(name: str) -> str:
    parts = [part for part in re.split(r"\s+", name.replace("_", " ").strip()) if part]
    if len(parts) < 2:
        return name.strip()
    last_name = parts[-1]
    initials = "".join(part[0].upper() + "." for part in parts[:-1] if part)
    return f"{last_name} {initials}"


def make_id(name: str) -> str:
    normalized = unicodedata.normalize("NFD", name)
    without_marks = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", without_marks.lower()).strip("-")


def pair_key(a: str, b: str) -> tuple[tuple[str, str], bool]:
    reversed_pair = a.lower() > b.lower()
    return ((b, a), True) if reversed_pair else ((a, b), False)


def load_matches() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH, low_memory=False)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Rank_1"] = pd.to_numeric(data["Rank_1"], errors="coerce")
    data["Rank_2"] = pd.to_numeric(data["Rank_2"], errors="coerce")
    data["Pts_1"] = pd.to_numeric(data["Pts_1"], errors="coerce")
    data["Pts_2"] = pd.to_numeric(data["Pts_2"], errors="coerce")
    data = data.dropna(subset=["Date", "Player_1", "Player_2", "Winner", "Rank_1", "Rank_2", "Pts_1", "Pts_2"])
    data = data.drop_duplicates().copy()
    data["Surface"] = data["Surface"].map(normalize_surface)
    data["RoundValue"] = data["Round"].map(ROUNDS).fillna(3).astype(int)
    data["Rank_1"] = data["Rank_1"].astype(int)
    data["Rank_2"] = data["Rank_2"].astype(int)
    return data.sort_values("Date").reset_index(drop=True)


def load_charting_events() -> pd.DataFrame:
    if not CHARTING_MATCHES_PATH.exists() or not CHARTING_OVERVIEW_PATH.exists():
        return pd.DataFrame()

    matches = pd.read_csv(CHARTING_MATCHES_PATH, low_memory=False)
    overview = pd.read_csv(CHARTING_OVERVIEW_PATH, low_memory=False)
    matches["DateValue"] = pd.to_datetime(matches["Date"].astype(str), format="%Y%m%d", errors="coerce")
    overview = overview[overview["set"].astype(str).str.lower() == "total"].copy()

    numeric_columns = [
        "serve_pts",
        "first_won",
        "first_in",
        "second_won",
        "second_in",
        "bk_pts",
        "bp_saved",
        "return_pts",
        "return_pts_won",
        "winners",
        "unforced",
    ]
    for column in numeric_columns:
        overview[column] = pd.to_numeric(overview[column], errors="coerce").fillna(0).astype(int)

    data = overview.merge(matches[["match_id", "DateValue"]], on="match_id", how="inner")
    data = data.dropna(subset=["DateValue", "player"]).copy()
    data["PlayerAlias"] = data["player"].astype(str).map(abbreviate_player_name)
    return data.sort_values("DateValue").reset_index(drop=True)


def build_features(
    row: pd.Series,
    players: dict[str, PlayerState],
    h2h: dict[tuple[str, str], list[int]],
    charting: dict[str, ChartingState],
) -> list[float]:
    p1 = str(row["Player_1"]).strip()
    p2 = str(row["Player_2"]).strip()
    surface = str(row["Surface"])
    state1 = players.get(p1, PlayerState())
    state2 = players.get(p2, PlayerState())
    chart1 = charting.get(p1, ChartingState())
    chart2 = charting.get(p2, ChartingState())

    key, reversed_pair = pair_key(p1, p2)
    h2h_stats = h2h.get(key, [0, 0])
    p1_wins, p2_wins = (h2h_stats[1], h2h_stats[0]) if reversed_pair else (h2h_stats[0], h2h_stats[1])
    h2h_diff = 0.0 if p1_wins + p2_wins == 0 else (p1_wins - p2_wins) / (p1_wins + p2_wins)

    return [
        float(row["Rank_1"] - row["Rank_2"]),
        float(row["Pts_1"] - row["Pts_2"]),
        state1.recent_win_rate - state2.recent_win_rate,
        state1.surface_win_rate(surface) - state2.surface_win_rate(surface),
        h2h_diff,
        math.log1p(state1.matches) - math.log1p(state2.matches),
        chart1.serve_win_rate - chart2.serve_win_rate,
        chart1.total_points_won_rate - chart2.total_points_won_rate,
        chart1.return_win_rate - chart2.return_win_rate,
        chart1.break_points_saved_rate - chart2.break_points_saved_rate,
        chart1.winner_rate - chart2.winner_rate,
        chart1.unforced_rate - chart2.unforced_rate,
        math.log1p(chart1.matches) - math.log1p(chart2.matches),
        float(row["RoundValue"]),
        1.0 if str(row["Tournament"]).strip() in SLAMS else 0.0,
    ]


def update_history(row: pd.Series, players: dict[str, PlayerState], h2h: dict[tuple[str, str], list[int]]) -> None:
    p1 = str(row["Player_1"]).strip()
    p2 = str(row["Player_2"]).strip()
    p1_won = str(row["Winner"]).strip().lower() == p1.lower()
    players.setdefault(p1, PlayerState()).add_match(str(row["Surface"]), p1_won, int(row["Rank_1"]), float(row["Pts_1"]))
    players.setdefault(p2, PlayerState()).add_match(str(row["Surface"]), not p1_won, int(row["Rank_2"]), float(row["Pts_2"]))

    key, reversed_pair = pair_key(p1, p2)
    stats = h2h.setdefault(key, [0, 0])
    if reversed_pair:
        stats[1 if p1_won else 0] += 1
    else:
        stats[0 if p1_won else 1] += 1


def build_dataset(matches: pd.DataFrame, charting_events: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    players: dict[str, PlayerState] = {}
    h2h: dict[tuple[str, str], list[int]] = {}
    charting: dict[str, ChartingState] = {}
    x_rows: list[list[float]] = []
    y_rows: list[int] = []
    chart_index = 0

    for _, row in matches.iterrows():
        while chart_index < len(charting_events) and charting_events.iloc[chart_index]["DateValue"] < row["Date"]:
            chart_row = charting_events.iloc[chart_index]
            alias = str(chart_row["PlayerAlias"]).strip()
            charting.setdefault(alias, ChartingState()).add_stats(chart_row)
            chart_index += 1

        x_rows.append(build_features(row, players, h2h, charting))
        y_rows.append(int(str(row["Winner"]).strip().lower() == str(row["Player_1"]).strip().lower()))
        update_history(row, players, h2h)

    return np.array(x_rows, dtype=float), np.array(y_rows, dtype=int)


def build_player_ids(names: pd.Series) -> dict[str, str]:
    ids: dict[str, str] = {}
    for name in sorted(set(names.dropna().astype(str))):
        base_id = make_id(name)
        player_id = base_id
        suffix = 2
        while player_id in ids:
            player_id = f"{base_id}-{suffix}"
            suffix += 1
        ids[player_id] = name
    return ids


def build_inference_payload(matches: pd.DataFrame, charting_events: pd.DataFrame, player_ids: dict[str, str]) -> dict:
    players: dict[str, PlayerState] = {}
    h2h: dict[tuple[str, str], list[int]] = {}
    charting: dict[str, ChartingState] = {}

    for _, row in matches.iterrows():
        update_history(row, players, h2h)

    for _, row in charting_events.iterrows():
        alias = str(row["PlayerAlias"]).strip()
        charting.setdefault(alias, ChartingState()).add_stats(row)

    name_to_id = {name: player_id for player_id, name in player_ids.items()}
    player_rows = []
    for name in sorted(players):
        state = players[name]
        chart = charting.get(name, ChartingState())
        player_rows.append(
            {
                "id": name_to_id[name],
                "name": name,
                "matches": state.matches,
                "wins": state.wins,
                "win_rate": round(state.overall_win_rate, 3),
                "last_rank": state.last_rank,
                "last_points": round(state.last_points) if state.last_points is not None else None,
                "recent_win_rate": round(state.recent_win_rate, 6),
                "surface_win_rates": {
                    surface: round(wins / matches_count, 6)
                    for surface, (wins, matches_count) in sorted(state.surface.items())
                    if matches_count > 0
                },
                "chart_serve_win_rate": round(chart.serve_win_rate, 6),
                "chart_return_win_rate": round(chart.return_win_rate, 6),
                "chart_total_points_won_rate": round(chart.total_points_won_rate, 6),
                "chart_bp_saved_rate": round(chart.break_points_saved_rate, 6),
                "chart_winner_rate": round(chart.winner_rate, 6),
                "chart_unforced_rate": round(chart.unforced_rate, 6),
                "chart_matches": chart.matches,
            }
        )

    h2h_rows = [
        {
            "player_1": pair[0],
            "player_2": pair[1],
            "player_1_wins": wins[0],
            "player_2_wins": wins[1],
        }
        for pair, wins in sorted(h2h.items())
    ]

    return {
        "players": player_rows,
        "head_to_head": h2h_rows,
        "default_round": 3,
        "default_tournament": "",
    }


def main():
    matches = load_matches()
    charting_events = load_charting_events()
    x, y = build_dataset(matches, charting_events)
    split_index = max(1, int(len(x) * 0.8))
    x_train, x_test = x[:split_index], x[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    model = LogisticRegressionCV(
        Cs=[0.01, 0.03, 0.1, 0.3, 1.0],
        cv=TimeSeriesSplit(n_splits=5),
        scoring="roc_auc",
        max_iter=1000,
        random_state=42,
        n_jobs=None,
        l1_ratios=(0.0,),
        use_legacy_attributes=False,
    )
    model.fit(x_train_scaled, y_train)

    probabilities = model.predict_proba(x_test_scaled)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    player_ids = build_player_ids(pd.concat([matches["Player_1"], matches["Player_2"]]))
    artifact = {
        "version": "1.0.0",
        "model_type": "sklearn-logistic-regression",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_names": FEATURE_NAMES,
        "means": scaler.mean_.round(12).tolist(),
        "scales": scaler.scale_.round(12).tolist(),
        "coefficients": model.coef_[0].round(12).tolist(),
        "intercept": float(round(model.intercept_[0], 12)),
        "regularization_c": float(np.ravel(model.C_)[0]),
        "validation": "TimeSeriesSplit(n_splits=5), scoring=roc_auc",
        "data_sources": [
            str(DATA_PATH.relative_to(ROOT)),
            str(CHARTING_MATCHES_PATH.relative_to(ROOT)),
            str(CHARTING_OVERVIEW_PATH.relative_to(ROOT)),
        ],
        "metrics": {
            "total_matches": int(len(matches)),
            "training_rows": int(len(x_train)),
            "test_rows": int(len(x_test)),
            "accuracy": round(float(accuracy_score(y_test, predictions)), 3),
            "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 3),
            "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 3),
            "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 3),
            "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 3),
            "log_loss": round(float(log_loss(y_test, probabilities)), 3),
            "first_match": matches["Date"].iloc[0].date().isoformat(),
            "last_match": matches["Date"].iloc[-1].date().isoformat(),
            "charting_stat_rows": int(len(charting_events)),
        },
        "players": player_ids,
        "inference": build_inference_payload(matches, charting_events, player_ids),
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Modelo treinado e salvo em {ARTIFACT_PATH}")
    print(json.dumps(artifact["metrics"], indent=2))


if __name__ == "__main__":
    main()
