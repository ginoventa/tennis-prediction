# Tennis Match Predictor

Aplicação full-stack para prever a probabilidade de vitória em partidas WTA. O treinamento do modelo é feito em Python com scikit-learn, e a API de inferência foi implementada em C# com ASP.NET Core.

O objetivo do projeto é demonstrar um fluxo completo de Machine Learning: dados históricos, criação de features, treino, avaliação, exportação do modelo e consumo por uma aplicação web.

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

O treino processa as partidas em ordem cronológica para evitar data leakage. Isso significa que, ao criar as features de uma partida, o modelo só usa informações que já existiam antes dela.

### 2. Treinamento

O arquivo `src/training/train_model.py`:

- carrega e limpa os dados;
- cria features comparando jogadora 1 contra jogadora 2;
- atualiza o histórico das jogadoras partida por partida;
- treina uma regressão logística;
- separa treino e teste por tempo;
- exporta `artifacts/model.json`.

O modelo é propositalmente simples e interpretável. A regressão logística facilita explicar quais fatores empurraram a previsão para cada jogadora.

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

O projeto inclui um benchmark local e reprodutível:

```bash
python src/evaluation/benchmark_model.py
```

O benchmark usa o mesmo recorte temporal de teste do treinamento e compara:

- nosso modelo;
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

O mercado por odds é um benchmark forte. O objetivo não é necessariamente superá-lo, mas verificar se o modelo melhora em relação a regras simples e produz probabilidades coerentes.

## Retreinamento automático

A API possui um `BackgroundService` preparado para retreinar o modelo periodicamente. Ele fica desativado por padrão em `src/TennisPrediction.Api/appsettings.json`:

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

Quando ativado, o worker chama o script Python, gera um novo `model.json` e recarrega o modelo na API se o treino terminar com sucesso.

## Observações

- O modelo não usa odds no treinamento principal. As odds aparecem apenas no benchmark.
- O treino evita data leakage processando as partidas em ordem cronológica.
- As métricas podem mudar quando os datasets forem atualizados.
- O Match Charting Project exige atribuição e uso não comercial.
