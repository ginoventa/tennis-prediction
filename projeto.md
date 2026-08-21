# Tennis Prediction (WTA)

## Visao geral

Projeto em andamento para prever resultado de partidas femininas de tenis (WTA) usando dados historicos.

## Dados usados

- `data-kaggle/wta.csv` como base principal de treino.
- pasta `data/` com arquivos do Match Charting Project para estudos futuros e possiveis features mais ricas.

## Estado atual do codigo

### Limpeza (`limpeza.py`)

O script atual faz:
- leitura do CSV;
- tratamento inicial de nulos e duplicatas;
- conversoes de tipos (data, categorias, inteiros e floats);
- mapeamento de rodada para numero;
- criacao de target `Player_1_Wins`;
- criacao de features basicas:
	- `Rank_Diff`
	- `Pts_Diff`
	- `Odd_Diff`
	- `isSlam`
- exportacao para `data-kaggle/wta_clean.parquet`.

### Baseline (`baseline.py`)

Ja existe um primeiro modelo de classificacao com:
- separacao temporal treino/teste;
- uso de `Rank_Diff` como feature inicial;
- treino com Logistic Regression;
- metricas via `classification_report`.
