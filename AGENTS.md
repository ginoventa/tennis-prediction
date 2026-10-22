# Repository Guidelines

## Project Structure & Module Organization

This project predicts WTA match outcomes through Python training and a browser app deployed to GitHub Pages. An ASP.NET Core (.NET 8) application remains the inference reference.

- `web/`: public browser interface and ES module inference (`model.mjs`).
- `scripts/build_pages.py`: copies browser assets and the exported model into `dist/`.
- `tests/`: browser model tests, C# parity fixtures, and the .NET fixture generator.
- `.github/workflows/pages.yml`: validates, builds, and deploys Pages on pushes to `main` or manual runs.
- `src/training/train_model.py`: feature generation, logistic regression training, and model export.
- `src/evaluation/benchmark_model.py`: comparisons against market odds, ranking, and WTA points.
- `src/TennisPrediction.Api/`: C# endpoints, inference services, and background retraining.
- `src/TennisPrediction.Api/wwwroot/`: API-backed reference interface.
- `data-kaggle/` and `data/`: WTA records and Match Charting Project datasets.
- `artifacts/model.json`: shared Python/C#/browser model contract.

## Build, Test, and Development Commands

Run commands from the repository root:

- `node --test tests/model.test.mjs`: run browser inference and C# parity checks (Node.js 22).
- `python3 scripts/build_pages.py`: build the public site from the existing model.
- `python3 -m http.server 8000 --directory dist`: preview the built site over HTTP.
- `pip install -r requirements.txt`: install Python dependencies, preferably in a virtual environment.
- `python src/training/train_model.py`: train and export the model; requires input datasets.
- `python src/evaluation/benchmark_model.py`: evaluate the temporal holdout and write `artifacts/benchmark.json`.
- `dotnet build src/TennisPrediction.Api`: compile the API.
- `dotnet run --project src/TennisPrediction.Api`: serve the API and interface. Use the printed URL; Swagger is at `/swagger`.

Use `python3` if your environment does not provide `python`.

## Coding Style & Naming Conventions

Follow existing formatting: four spaces in Python and C#, two spaces in JavaScript. Use Python `snake_case`, C# `PascalCase` for types and methods, and JavaScript `camelCase`. Preserve snake_case JSON fields. No repository-wide formatter or linter configuration is present.

## Testing Guidelines

Run `node --test tests/model.test.mjs` for browser inference changes and `python3 scripts/build_pages.py` for site changes. The 240 preserved C# cases check parity against the current artifact; regenerate them with `tests/reference/Parity.csproj` when changing the model (see README.md). No coverage threshold is configured. Build API changes and check `/health`, player search, and valid and invalid `/predict` requests. Verify interface changes in the browser. For model changes, rerun training and benchmarking; report accuracy, log loss, Brier score, and ROC-AUC. Preserve chronological splits, prevent future-data leakage, and keep feature order and scaling consistent between Python, C#, and the browser.

## Commit & Pull Request Guidelines

History uses short descriptive subjects in Portuguese and English without consistent prefixes. Keep commits focused. PRs should explain behavior changes, link relevant issues, and list validation performed. Include screenshots for interface changes and metric comparisons for model changes. Explain dataset and artifact updates.

## Data & Configuration

Preserve attribution and noncommercial, share-alike requirements documented in `data/README.md`. Automatic retraining applies only to the C# API and is disabled by default; configure it explicitly in `src/TennisPrediction.Api/appsettings.json`. The Pages app uses a fixed model snapshot: after retraining, update benchmarks and parity fixtures, commit the model, and redeploy. Keep raw source datasets and upstream attribution documents when removing obsolete generated files.
