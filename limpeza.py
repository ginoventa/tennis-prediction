import pandas as pd
import numpy as np
import pyarrow.parquet as pa 

file_path = 'data-kaggle/wta.csv'
# player_name = input("Coloque o nome da jogadora que deseja analisar: ")

# 1. Carregar o CSV
tennis_data = pd.read_csv(file_path, low_memory=False)

rounds = {'1st Round': 1, '2nd Round': 2, '3rd Round': 3, '4th Round': 4, 'Quarterfinals': 5, 'Semifinals': 6, 'The Final': 7}
surfaces = {'Hard': 1, 'Clay': 2, 'Grass': 3}
court = {'Outdoor': 1, 'Indoor': 2}
slams = ['Australian Open', 'French Open', 'Wimbledon', 'US Open']
string_columns = ['Player_1', 'Player_2', 'Winner']
int_columns = ['Rank_2', 'Rank_1', 'Pts_1', 'Pts_2']
float_columns = ['Odd_1', 'Odd_2']

# 2. Tratamento inicial de nulos e duplicatas
tennis_data[['Odd_2', 'Odd_1']] = tennis_data[['Odd_2', 'Odd_1']].replace('-', np.nan)
tennis_data['Surface'] = tennis_data['Surface'].replace('Carpet', np.nan)
tennis_data['Surface'] = tennis_data['Surface'].replace('Greenset', np.nan)
tennis_data_clean = tennis_data.dropna().copy()
tennis_data_clean = tennis_data_clean.drop_duplicates()
# 3. Mapeamentos e conversões de tipo
tennis_data_clean['Date'] = pd.to_datetime(tennis_data_clean['Date'], errors='coerce')
tennis_data_clean = tennis_data_clean.sort_values('Date').reset_index(drop=True)
tennis_data_clean['Round'] = tennis_data_clean['Round'].map(rounds).astype('Int64')
tennis_data_clean['Surface'] = tennis_data_clean['Surface'].map(surfaces).astype('Int64')
tennis_data_clean['Court'] = tennis_data_clean['Court'].map(court).astype('Int64')

tennis_data_clean['Player_1_Wins'] = (tennis_data_clean['Winner'] == tennis_data_clean['Player_1']).astype(int)
for col in string_columns:
    tennis_data_clean[col] = tennis_data_clean[col].astype('category')

for col in int_columns:
    tennis_data_clean[col] = pd.to_numeric(tennis_data_clean[col], errors='coerce').astype('Int64')

for col in float_columns:
    tennis_data_clean[col] = pd.to_numeric(tennis_data_clean[col], errors='coerce').astype('float64')

isSlam = tennis_data_clean['Tournament'].isin(slams)
tennis_data_clean['isSlam'] = isSlam.astype('bool')

# 3.1 - Cálculo da taxa de vitória dos últimos 10 jogos para cada jogadora
df_p1 = tennis_data_clean[["Date", "Player_1", "Player_1_Wins"]].rename(columns={"Player_1": "Player", "Player_1_Wins": "Win"})
df_p2 = tennis_data_clean[["Date", "Player_2", "Player_1_Wins"]].rename(columns={"Player_2": "Player"})
df_p2["Win"] = 1 - df_p2["Player_1_Wins"]
df_p2 = df_p2.drop(columns=["Player_1_Wins"])

df_history = pd.concat([df_p1, df_p2]).sort_values(["Player", "Date"])
df_history["Win_Rate_10"] = df_history.groupby("Player")["Win"].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
df_history["Win_Rate_10"] = df_history["Win_Rate_10"].fillna(0.5)
df_history = df_history.sort_index()

# 4. Criação das Features e Target (y)
total_linhas = len(tennis_data_clean)
tennis_data_clean["Win_Rate_10_P1"] = df_history.iloc[:total_linhas]["Win_Rate_10"].values
tennis_data_clean["Win_Rate_10_P2"] = df_history.iloc[total_linhas:]["Win_Rate_10"].values
tennis_data_clean["Win_Rate_10_Diff"] = (tennis_data_clean["Win_Rate_10_P1"] - tennis_data_clean["Win_Rate_10_P2"])
tennis_data_clean['Rank_Diff'] = tennis_data_clean['Rank_1'] - tennis_data_clean['Rank_2'].astype('Int64')
tennis_data_clean['Pts_Diff'] = tennis_data_clean['Pts_1'] - tennis_data_clean['Pts_2'].astype('Int64')
tennis_data_clean['Odd_Diff'] = (tennis_data_clean['Odd_1'] - tennis_data_clean['Odd_2']).round(2)

# 5. Drop final e salvamento
tennis_data_clean = tennis_data_clean.drop(columns=['Tournament', 'Score', 'Rank_1', 'Rank_2', 'Pts_1', 'Pts_2', 'Odd_1', 'Odd_2', 'Best of'], errors='ignore')
tennis_data_clean.to_parquet('data-kaggle/wta_clean.parquet', engine='pyarrow', index=False)

