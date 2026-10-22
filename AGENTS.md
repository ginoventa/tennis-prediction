# Repository Guidelines

## Project Structure & Module Organization

This project predicts WTA match outcomes through Python training and an ASP.NET Core (.NET 8) inference API.

- `src/training/train_model.py`: feature generation, logistic regression training, and model export.
- `src/evaluation/benchmark_model.py`: comparisons against market odds, ranking, and WTA points.
- `src/TennisPrediction.Api/`: C# endpoints, inference services, and background retraining.
- `src/TennisPrediction.Api/wwwroot/`: HTML, CSS, and JavaScript interface.
- `data-kaggle/` and `data/`: WTA records and Match Charting Project datasets.
- `artifacts/model.json`: shared Python/C# model contract. `baseline.py` and `modelos/` contain earlier model work.

## Build, Test, and Development Commands

Run commands from the repository root:

- `pip install -r requirements.txt`: install Python dependencies, preferably in a virtual environment.
- `python src/training/train_model.py`: train and export the model; requires input datasets.
- `python src/evaluation/benchmark_model.py`: evaluate the temporal holdout and write `artifacts/benchmark.json`.
- `dotnet build src/TennisPrediction.Api`: compile the API.
- `dotnet run --project src/TennisPrediction.Api`: serve the API and interface. Use the printed URL; Swagger is at `/swagger`.

Use `python3` if your environment does not provide `python`.

## Coding Style & Naming Conventions

Follow existing formatting: four spaces in Python and C#, two spaces in JavaScript. Use Python `snake_case`, C# `PascalCase` for types and methods, and JavaScript `camelCase`. Preserve snake_case JSON fields. No repository-wide formatter or linter configuration is present.

## Testing Guidelines

No automated test suite or coverage threshold is configured. Build API changes and check `/health`, player search, and valid and invalid `/predict` requests. Verify interface changes in the browser. For model changes, rerun training and benchmarking; report accuracy, log loss, Brier score, and ROC-AUC. Preserve chronological splits, prevent future-data leakage, and keep feature order and scaling consistent between Python and C#.

## Commit & Pull Request Guidelines

History uses short descriptive subjects in Portuguese and English without consistent prefixes. Keep commits focused. PRs should explain behavior changes, link relevant issues, and list validation performed. Include screenshots for interface changes and metric comparisons for model changes. Explain dataset and artifact updates.

## Data & Configuration

Preserve attribution and noncommercial, share-alike requirements documented in `data/README.md`. Automatic retraining is disabled by default; configure it explicitly in `src/TennisPrediction.Api/appsettings.json`.
