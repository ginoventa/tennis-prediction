# Tennis Match Predictor

## Browser release — GitHub Pages

The public version lives in `web/` and runs entirely in the browser. It loads
`artifacts/model.json` for player search, feature generation, and predictions.
There is no hosted API, database, Python runtime, or live data feed.

The **C# reference application is maintained** in
`src/TennisPrediction.Api/`, including its original frontend. It remains runnable
with the commands below and serves as the reference implementation.

## Preview locally

```bash
node --test tests/model.test.mjs
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

Training requires the Python dependencies in `requirements.txt`; browser checks use Node.js 22.

```bash
python3 -m pip install -r requirements.txt
python3 src/training/train_model.py
python3 src/evaluation/benchmark_model.py
```

Review benchmark changes before publishing a new model. The parity fixtures in
`tests/csharp-predictions.json` capture predictions from the C# reference service
for the current artifact; regenerate them against C# when replacing that artifact.
With the .NET 8 SDK, regenerate fixtures from the repository root:

```bash
dotnet run --project tests/reference/Parity.csproj -- "$PWD" > /tmp/tennis-csharp-output.txt
python3 -c 'import json; from pathlib import Path; lines=Path("/tmp/tennis-csharp-output.txt").read_text().splitlines(); data=json.loads(next(s for s in reversed(lines) if s.startswith("[{"))); Path("tests/csharp-predictions.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")'
node --test tests/model.test.mjs
```

After regenerating fixtures, run the browser tests and static build before publishing.
Commit the updated model, benchmark, and fixtures, then redeploy Pages. C# automatic
retraining does not update the deployed browser snapshot.

Keep browser feature generation synchronized with `TennisModelService.cs`.
The interface displays the model generation date and historical cutoff. The
browser version omits the date selector because inference uses a fixed snapshot. Match Charting Project
attribution and its noncommercial, share-alike license are displayed in the UI.

---

## Treinamento e aplicação C# de referência

O treinamento usa Python com scikit-learn e exporta um modelo compartilhado pela aplicação pública no navegador e pela API de referência em C# com ASP.NET Core.

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
        +--> web/model.mjs --> Interface pública no navegador (GitHub Pages)
        |
        +--> src/TennisPrediction.Api/TennisModelService.cs --> API + interface de referência

src/evaluation/benchmark_model.py compara o modelo com odds, ranking e pontos WTA.
```

## Como cada parte funciona

### 1. Dados

O projeto usa dois grupos principais de dados:

- `data-kaggle/wta.csv`: partidas WTA históricas, rankings, pontos, vencedora, superfície e odds.
- `data/charting-w-matches.csv` e `data/charting-w-stats-Overview.csv`: metadados e estatísticas agregadas do Tennis Abstract Match Charting Project usados no treinamento atual. Os demais arquivos de `data/` são dados-fonte e documentação do projeto original.

### 2. Treinamento

O arquivo `src/training/train_model.py`:

- carrega e limpa os dados;
- cria features comparando jogadora 1 contra jogadora 2;
- atualiza o histórico das jogadoras partida por partida;
- treina uma regressão logística;
- separa treino e teste por tempo;
- exporta `artifacts/model.json`.

### 3. Artefato do modelo

O arquivo `artifacts/model.json` guarda tudo que o navegador e a API precisam para prever sem depender do Python em tempo de execução:

- nomes das features;
- médias e escalas do `StandardScaler`;
- coeficientes da regressão logística;
- intercepto;
- métricas do treinamento;
- dados históricos das jogadoras para inferência.

Esse arquivo é o contrato entre Python, C# e JavaScript. O treinamento atual lê os CSVs diretamente e exporta `artifacts/model.json`.

### 4. API C#

A API ASP.NET Core carrega o `model.json` no `TennisModelService`.

Ela:

- valida se a ordem das features do artefato é a esperada;
- monta o vetor de features da partida solicitada;
- aplica a mesma padronização usada no treino;
- calcula a probabilidade com a fórmula da regressão logística;
- retorna probabilidade, Power Index, principais fatores e snapshot das features.

### 5. Interfaces web

A interface pública em `web/` busca jogadoras e calcula previsões localmente com `web/model.mjs`, usando o histórico fixo do modelo.

Os arquivos em `src/TennisPrediction.Api/wwwroot` formam uma interface simples para:

- buscar jogadoras;
- escolher superfície e preencher o campo de data legado;
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

## Endpoints da API C#

Estes endpoints pertencem à aplicação de referência; o site no GitHub Pages executa a inferência no navegador.

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
  "surface": "Hard"
}
```

O campo opcional `match_date` é aceito por compatibilidade, mas não altera a previsão. A inferência usa o histórico fixo e a rodada e o torneio padrão do artefato.

## Como executar a referência C#

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

Depois acesse a URL mostrada no terminal. Exemplo (a porta pode variar):

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

Resultado registrado em `artifacts/benchmark.json`:

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
