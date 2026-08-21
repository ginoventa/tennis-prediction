import pandas as pd
import numpy as np
import seaborn as sns 
import pyarrow.parquet as pa
import matplotlib.pyplot as plt 

player_name = "Sabalenka A."
# player_name = input("Coloque o nome da jogadora que deseja analisar: ")
data = pd.read_parquet('data-kaggle/wta_clean.parquet', engine='pyarrow')
data_sabalenka = data[(data['Player_1'] ==  player_name) | (data['Player_2'] == player_name)]

partidas_jogadas = data_sabalenka['Surface'].value_counts(normalize=True)
plt.pie(partidas_jogadas, labels=partidas_jogadas.index, autopct='%1.1f%%', startangle=90)
plt.title("Partidas jogadas")
# plt.show()
# print(partidas_jogadas)


partidas_ganhas = data_sabalenka[(data_sabalenka['Winner'] == player_name)]
partidas_ganhas = partidas_ganhas["Surface"].value_counts(normalize=True)
# print(partidas_ganhas)
plt.pie(partidas_ganhas, labels=partidas_ganhas.index, autopct='%1.1f%%', startangle=90)
plt.title("Partidas ganhas")
# plt.show()
