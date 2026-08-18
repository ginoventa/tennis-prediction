# Tennis Match Predictor 

## Objetivo

Projeto de **Machine Learning** capaz de prever a probabilidade de um jogador vencer uma partida de tênis levando em consideração seu histórico de desempenho

## Tecnologias
- Python (panda, NumPy, scikit-learn, matplotlib) - Tratamento de dados e ML
- Streamlit - Host 
- GitHub 

## Etapas
### 1. Dataset
O dataset utilizado é o https://github.com/JeffSackmann/tennis_MatchChartingProject, que contém dados da ATP e WTA de diversos anos. Também realizarei testes com um dataset do kaggle. 

### 2. Explorar os dados

Usar pandas para entender:

- quantidade de dados
- colunas
- valores nulos
- dados duplicados
- distribuição das informações

Fazer alguns gráficos para entender os dados.

### 3. Limpar os dados

- Tratar valores faltantes
- Remover informações desnecessárias
- Padronizar os dados
- Cuidar de **data leakage**

> Não usar informações que só seriam conhecidas depois da partida para tentar prevê-la.

### 4. Criar Features

Transformar os dados em informações que o modelo consiga utilizar.

Exemplos:

```text
ranking_difference
recent_win_rate_difference
surface_win_rate_difference
head_to_head_difference
age_difference
```

A ideia principal é comparar os dois jogadores.

### 5. Definir X e y

```text
X = características da partida
y = vencedor
```

Depois, dividir os dados em treino e teste.

### 6. Treinar modelos

Começar com dois modelos:

**Logistic Regression**

→ modelo simples e interpretável.

**Random Forest**

→ modelo mais complexo, baseado em árvores.

Não precisa testar vários algoritmos.

### 7. Avaliar

Comparar os modelos usando:

- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- Confusion Matrix

Perguntas importantes:

- Qual modelo foi melhor?
- Por quê?
- Onde ele erra?
- Quais features são mais importantes?

### 8. Escolher o modelo

Escolher o modelo que apresentar o melhor resultado **e entender por que ele foi escolhido**.

O objetivo não é simplesmente ter a maior accuracy.

### 9. Criar uma aplicação

Usar **Streamlit** para criar uma interface simples:

```text
TENNIS MATCH PREDICTOR

Jogador A: ______
Jogador B: ______
Superfície: ______

[ PREVER ]

Jogador A: 43%
Jogador B: 57%

Vencedor previsto: Jogador B
```

### 10. GitHub

O projeto precisa ter:

```text
README.md
requirements.txt
src/
notebooks/
data/
app/
```

O README deve explicar:

1. Qual problema você resolveu
2. Qual dataset utilizou
3. Como tratou os dados
4. Quais features criou
5. Quais modelos testou
6. Resultados
7. Limitações
8. Como executar o projeto

---

## O que preciso saber para explicar o projeto

- O que é Machine Learning
- O que são features e target
- Como funciona treino/teste
- O que é Logistic Regression
- O que é Random Forest
- O que significa overfitting
- O que é data leakage
- Para que servem Accuracy, Precision, Recall e F1
- Como avaliar um modelo
- Por que meu modelo pode errar
- Como transformar um modelo em uma aplicação

---

## Fluxo

```text
Dados
 ↓
Exploração
 ↓
Limpeza
 ↓
Features
 ↓
Treino
 ↓
Avaliação
 ↓
Comparação
 ↓
Melhor modelo
 ↓
Aplicação
 ↓
GitHub
```

## Regra principal

**Faça algo pequeno o suficiente para entender tudo.**

O projeto não precisa ser revolucionário. O importante é conseguir mostrar que você sabe passar por um problema de **ponta a ponta em Machine Learning**.
