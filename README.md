# Browser release — GitHub Pages

The public version lives in `web/` and runs entirely in the browser. It loads
`artifacts/model.json` for player search, feature generation, and predictions.
There is no hosted API, database, Python runtime, or live data feed.

The original **C# application is preserved unchanged** in
`src/TennisPrediction.Api/`, including its original frontend. It remains runnable
with the commands below and serves as the reference implementation.

## Preview locally

```bash
python3 scripts/build_pages.py
python3 -m http.server 8000 --directory dist
```

Open `http://localhost:8000`. Use HTTP rather than opening the HTML file directly.
The build publishes only the browser assets and model, excluding raw datasets.
The model and its player history are publicly downloadable.

## Publish on GitHub Pages

1. Push these changes to the repository's `main` branch.
2. In **Settings → Pages → Build and deployment**, select **GitHub Actions**.
3. Open **Actions → Deploy browser app to GitHub Pages** and run the workflow,
   or push another commit to `main`.
4. Open the URL reported by the deployment job, normally
   `https://<owner>.github.io/tennis-prediction/`.

The workflow checks browser inference, builds `dist/`, and publishes it. Relative
asset and model paths support the repository URL and custom domains.

## Model updates and checks

```bash
node --test tests/model.test.mjs
python3 src/training/train_model.py
python3 src/evaluation/benchmark_model.py
```

Review benchmark changes before publishing a new model. The parity fixtures in
`tests/csharp-predictions.json` capture predictions from the preserved C# service
for the current artifact; regenerate them against C# when replacing that artifact.
With the .NET 8 SDK, regenerate fixtures from the repository root:

```bash
dotnet run --project tests/reference/Parity.csproj -- "$PWD" > /tmp/tennis-csharp-output.txt
python3 -c 'import json; from pathlib import Path; lines=Path("/tmp/tennis-csharp-output.txt").read_text().splitlines(); data=json.loads(next(s for s in reversed(lines) if s.startswith("[{"))); Path("tests/csharp-predictions.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")'
node --test tests/model.test.mjs
```

Keep browser feature generation synchronized with `TennisModelService.cs`.
The interface displays the model generation date and historical cutoff. The
browser version omits the date selector because inference uses a fixed snapshot. Match Charting Project
attribution and its noncommercial, share-alike license are displayed in the UI.

---

# Tennis Match Predictor

Aplicação full-stack para prever a probabilidade de vitória em partidas WTA. O treinamento do modelo é feito em Python com scikit-learn, e a API de inferência foi implementada em C# com ASP.NET Core.

## Fluxo do projeto

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
        v
src/TennisPrediction.Api/TennisModelService.cs
        |
        v
Endpoints REST + interface web
        |
        v
src/evaluation/benchmark_model.py
```

## Como cada parte funciona

### 1. Dados

O projeto usa dois grupos principais de dados:

- `data-kaggle/wta.csv`: partidas WTA históricas, rankings, pontos, vencedora, superfície e odds.
- `data/charting-*.csv`: estatísticas do Tennis Abstract Match Charting Project, incluindo dados agregados de saque, devolução, winners, erros não forçados e pontos.

### 2. Treinamento

O arquivo `src/training/train_model.py`:

- carrega e limpa os dados;
- cria features comparando jogadora 1 contra jogadora 2;
- atualiza o histórico das jogadoras partida por partida;
- treina uma regressão logística;
- separa treino e teste por tempo;
- exporta `artifacts/model.json`.

### 3. Artefato do modelo

O arquivo `artifacts/model.json` guarda tudo que a API precisa para prever sem depender do Python em tempo de execução:

- nomes das features;
- médias e escalas do `StandardScaler`;
- coeficientes da regressão logística;
- intercepto;
- métricas do treinamento;
- dados históricos das jogadoras para inferência.

Esse arquivo é o contrato entre Python e C#.

### 4. API C#

A API ASP.NET Core carrega o `model.json` no `TennisModelService`.

Ela:

- valida se a ordem das features do artefato é a esperada;
- monta o vetor de features da partida solicitada;
- aplica a mesma padronização usada no treino;
- calcula a probabilidade com a fórmula da regressão logística;
- retorna probabilidade, Power Index, principais fatores e snapshot das features.

### 5. Interface web

Os arquivos em `src/TennisPrediction.Api/wwwroot` formam uma interface simples para:

- buscar jogadoras;
- escolher superfície e data;
- chamar `POST /predict`;
- exibir probabilidades, Power Index, fatores principais e features calculadas.

## Features usadas

O modelo usa diferenças entre as duas jogadoras:

- ranking;
- pontos WTA;
- forma recente;
- aproveitamento na superfície;
- confronto direto;
- experiência histórica;
- saque charted;
- total de pontos vencidos charted;
- devolução charted;
- break points salvos charted;
- winners charted;
- erros não forçados charted;
- experiência charted;
- rodada;
- indicador de Grand Slam.

## Endpoints

- `GET /health`: status da API e versão do modelo.
- `GET /players?search=iga`: lista jogadoras disponíveis.
- `GET /metrics`: métricas calculadas no conjunto de teste temporal.
- `GET /accuracy`: resumo simples de acurácia.
- `POST /predict`: retorna probabilidades, Power Index e principais fatores.

Exemplo de request:

```json
{
  "player_1_id": "swiatek-i",
  "player_2_id": "sabalenka-a",
  "surface": "Hard",
  "match_date": "2026-10-15"
}
```

## Como executar

Instale as dependências Python:

```bash
pip install -r requirements.txt
```

Treine ou atualize o modelo:

```bash
python src/training/train_model.py
```

Inicie o backend C#:

```bash
dotnet run --project src/TennisPrediction.Api
```

Depois acesse a URL mostrada no terminal. Normalmente será algo como:

```text
http://localhost:5000
```

Swagger:

```text
http://localhost:5000/swagger
```

## Benchmark

O benchmark usa o mesmo recorte temporal de teste do treinamento e compara:

- modelo;
- probabilidade implícita do mercado, calculada a partir de `Odd_1` e `Odd_2`;
- baseline por ranking;
- baseline por pontos WTA.

Resultado atual:

```text
Modelo                   Rows Cobertura  Accuracy  LogLoss    Brier  ROC-AUC
Nosso modelo             9054    100.0%    0.6516   0.6177   0.2149   0.7132
Mercado por odds         9043     99.9%    0.6792   0.5848   0.2009   0.7543
Baseline ranking         9054    100.0%    0.6333   0.6785   0.2301   0.6764
Baseline pontos WTA      9054    100.0%    0.6292   0.7285   0.2357   0.6823
```

## Retreinamento automático

A API possui um `BackgroundService` para retreinar o modelo periodicamente. Ele fica desativado por padrão em `src/TennisPrediction.Api/appsettings.json`:

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

Quando ativado, o worker chama o script Python, gera um novo `model.json` e recarrega o modelo na API se o treino terminar com sucesso. A ideia é dar sync nisso com a atualização das tabelas de dados usadas.

## Observações

- O modelo não usa odds no treinamento principal. As odds aparecem apenas no benchmark.
- O treino evita data leakage processando as partidas em ordem cronológica.
- As métricas podem mudar quando os datasets forem atualizados.
- **O Match Charting Project exige atribuição e uso não comercial.**
