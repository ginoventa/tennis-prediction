# Tennis Match Predictor

An application for predicting win probabilities in WTA matches. The public interface in `web/` runs inference in the browser using a model trained in Python. The ASP.NET Core application in `src/TennisPrediction.Api/` provides the C# reference API and interface.

Predictions use the fixed historical snapshot in `artifacts/model.json`. The model and player history are public; there are no live data updates.

## Run the browser interface

Requires Python 3 to build and serve the static files:

```bash
python3 scripts/build_pages.py
python3 -m http.server 8000 --directory dist
```

Open `http://localhost:8000`. The build generates `dist/` with the interface files and model, excluding raw datasets.

## Tests

With Node.js 22:

```bash
node --test tests/model.test.mjs
```

The tests verify browser inference, including 240 parity cases against the C# implementation. The fixtures in `tests/csharp-predictions.json` correspond to the current model; `tests/reference/` contains the .NET 8 fixture generator.

## Project flow

```text
data-kaggle/wta.csv
data/charting-w-matches.csv
data/charting-w-stats-Overview.csv
        |
        v
src/training/train_model.py
        |
        v
artifacts/model.json
        |
        +--> web/model.mjs --> Public browser interface (GitHub Pages)
        |
        +--> src/TennisPrediction.Api/TennisModelService.cs --> Reference API and interface

src/evaluation/benchmark_model.py compares the model against odds, rankings, and WTA points.
```

## How each part works

### 1. Data

The project uses two main groups of data:

- `data-kaggle/wta.csv`: historical WTA matches, rankings, points, winners, surfaces, and odds.
- `data/charting-w-matches.csv` and `data/charting-w-stats-Overview.csv`: match metadata and aggregate statistics from the Tennis Abstract Match Charting Project used in current training. The remaining files in `data/` are source data and documentation from the original project.

### 2. Training

The script `src/training/train_model.py`:

- loads and cleans the data;
- creates features comparing player 1 against player 2;
- updates player history match by match;
- trains a logistic regression model;
- splits training and test data chronologically;
- exports `artifacts/model.json`.

### 3. Model artifact

The file `artifacts/model.json` stores everything the browser and API need to predict without Python at runtime:

- feature names;
- `StandardScaler` means and scales;
- logistic regression coefficients;
- intercept;
- training metrics;
- historical player data for inference.

This file is the contract between Python, C#, and JavaScript. Current training reads the CSV files directly and exports `artifacts/model.json`.

### 4. C# API

The ASP.NET Core API loads `model.json` through `TennisModelService`.

It:

- validates the artifact's feature order;
- builds the feature vector for the requested match;
- applies the same standardization used during training;
- calculates the probability using the logistic regression formula;
- returns probabilities, Power Index, key drivers, and a feature snapshot.

### 5. Web interfaces

The public interface in `web/` searches players and calculates predictions locally through `web/model.mjs`, using the model's fixed historical snapshot.

The files in `src/TennisPrediction.Api/wwwroot` provide a reference interface to:

- search players;
- choose a surface and fill in the legacy date field;
- call `POST /predict`;
- display probabilities, Power Index, key drivers, and calculated features.

## Features

The model uses differences between the two players:

- ranking;
- WTA points;
- recent form;
- surface win rate;
- head-to-head record;
- historical experience;
- charted serve win rate;
- charted total points won rate;
- charted return win rate;
- charted break points saved rate;
- charted winner rate;
- charted unforced error rate;
- charted experience;
- tournament round;
- Grand Slam indicator.

## C# API endpoints

These endpoints belong to the reference application; the GitHub Pages site runs inference in the browser.

- `GET /health`: API status and model version.
- `GET /players?search=iga`: available players.
- `GET /metrics`: metrics from the chronological test set.
- `GET /accuracy`: accuracy summary.
- `POST /predict`: probabilities, Power Index, and key drivers.

Example request:

```json
{
  "player_1_id": "swiatek-i",
  "player_2_id": "sabalenka-a",
  "surface": "Hard"
}
```

The optional `match_date` field is accepted for compatibility but does not affect predictions. Inference uses the fixed history and the artifact's default round and tournament.

## Run the C# reference application

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Train or update the model:

```bash
python src/training/train_model.py
```

Start the C# backend:

```bash
dotnet run --project src/TennisPrediction.Api
```

Open the URL printed in the terminal. Example (the port may vary):

```text
http://localhost:5000
```

Swagger:

```text
http://localhost:5000/swagger
```

## Benchmark

The benchmark uses the same chronological test split as training and compares:

- the model;
- market implied probabilities calculated from `Odd_1` and `Odd_2`;
- a ranking baseline;
- a WTA points baseline.

Results recorded in `artifacts/benchmark.json`:

```text
Model                   Rows Coverage  Accuracy  LogLoss    Brier  ROC-AUC
Our model               9054   100.0%    0.6516   0.6177   0.2149   0.7132
Market odds             9043    99.9%    0.6792   0.5848   0.2009   0.7543
Ranking baseline        9054   100.0%    0.6333   0.6785   0.2301   0.6764
WTA points baseline     9054   100.0%    0.6292   0.7285   0.2357   0.6823
```

## Automatic retraining

The API includes a `BackgroundService` that periodically retrains the model. It is disabled by default in `src/TennisPrediction.Api/appsettings.json`:

```json
{
  "ModelTraining": {
    "Enabled": false,
    "IntervalDays": 7,
    "RunOnStartup": false,
    "PythonExecutable": "python",
    "ScriptPath": "src/training/train_model.py"
  }
}
```

When enabled, the worker calls the Python script, generates a new `model.json`, and reloads the API model after successful training. API retraining does not update the model published on the static site.

## Notes

- The main model does not use odds during training. Odds are used only in the benchmark.
- Training prevents future-data leakage by processing matches chronologically.
- Metrics may change when datasets are updated.
- **The Match Charting Project requires attribution and noncommercial use.**
