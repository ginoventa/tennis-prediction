import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# 1. Carregar base limpa
df = pd.read_parquet("data-kaggle/wta_clean.parquet")

# 2. Holdout
data_train = df[df["Date"] <= "2025-04-15"].copy()
data_test = df[df["Date"] > "2025-04-15"].copy()

# 3. Seleção dos Atributos
features = [
    "Rank_Diff",
    "Pts_Diff",
    "Odd_Diff",
    "isSlam",
    "Win_Rate_10_Diff",  
    "Win_Rate_Surface_Diff",
    "Elo_Diff",
    "Elo_Surf_Diff",
]

X_train = data_train[features].fillna(0)
Y_train = data_train["Player_1_Wins"]

X_test = data_test[features].fillna(0)
Y_test = data_test["Player_1_Wins"]

# 4. Treinar o Random Forest (CRIANDO O MODELO)
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    min_samples_leaf=10,
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, Y_train)

# 5. Avaliar no conjunto de Teste
y_pred = model.predict(X_test)
print("--- DESEMPENHO NO TESTE ---")
print(f"Acurácia: {accuracy_score(Y_test, y_pred):.4f}\n")
print(classification_report(Y_test, y_pred))

# 6. Salva modelo treinado 
joblib.dump(model, "data-kaggle/modelo_wta_rf.pkl")