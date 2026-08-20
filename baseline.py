#Contado apenas o ranking 
import sklearn as sk 
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

data = pd.read_parquet('data-kaggle/wta_clean.parquet')

data_train = data[data["Date"] <= '2025-06-15']
data_test = data[data["Date"] > '2025-06-15']

X_train = data_train[["Rank_Diff"]]
Y_train = data_train["Player_1_Wins"]
X_test = data_test[["Rank_Diff"]]
Y_test = data_test["Player_1_Wins"]

model = LogisticRegression()
model.fit(X_train, Y_train) # Aprende relação entre rank-vitória 
prediction = model.predict(X_test) # Faz predição de vitória com base no rank

acuracia = accuracy_score(Y_test, prediction)
print(classification_report(Y_test, prediction))
probabilities = model.predict_proba([["Rank_Diff"]])

print(probabilities)