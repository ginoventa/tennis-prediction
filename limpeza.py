import pandas as pd
import numpy as np
import pyarrow.parquet as pa 

file_path = 'data-kaggle/wta.csv'

# 1. Carregar o CSV
tennis_data = pd.read_csv(file_path, low_memory=False)

rounds = {'1st Round': 1, '2nd Round': 2, '3rd Round': 3, '4th Round': 4, 'Quarterfinals': 5, 'Semifinals': 6, 'The Final': 7}
slams = ['Australian Open', 'French Open', 'Wimbledon', 'US Open']
string_columns = ['Surface', 'Court', 'Player_1', 'Player_2', 'Winner']
int_columns = ['Rank_2', 'Rank_1', 'Pts_1', 'Pts_2']
float_columns = ['Odd_1', 'Odd_2']

# 2. Tratamento inicial de nulos e duplicatas
tennis_data[['Odd_2', 'Odd_1']] = tennis_data[['Odd_2', 'Odd_1']].replace('-', np.nan)
tennis_data_clean = tennis_data.dropna(subset=['Winner', 'Rank_1', 'Rank_2']).copy()
tennis_data_clean = tennis_data_clean.drop_duplicates()

# 3. Mapeamentos e conversões de tipo
tennis_data_clean['Date'] = pd.to_datetime(tennis_data_clean['Date'], errors='coerce')
tennis_data_clean['Round'] = tennis_data_clean['Round'].map(rounds).astype('Int64')

tennis_data_clean['Player_1_Wins'] = (tennis_data_clean['Winner'] == tennis_data_clean['Player_1']).astype(int)
for col in string_columns:
    tennis_data_clean[col] = tennis_data_clean[col].astype('category')

for col in int_columns:
    tennis_data_clean[col] = pd.to_numeric(tennis_data_clean[col], errors='coerce').astype('Int64')

for col in float_columns:
    tennis_data_clean[col] = pd.to_numeric(tennis_data_clean[col], errors='coerce').astype('float64')

isSlam = tennis_data_clean['Tournament'].isin(slams)
tennis_data_clean['isSlam'] = isSlam.astype('bool')

# 4. Criação das Features e Target (y)
tennis_data_clean['Rank_Diff'] = tennis_data_clean['Rank_1'] - tennis_data_clean['Rank_2']
tennis_data_clean['Pts_Diff'] = tennis_data_clean['Pts_1'] - tennis_data_clean['Pts_2']
tennis_data_clean['Odd_Diff'] = (tennis_data_clean['Odd_1'] - tennis_data_clean['Odd_2']).round(2)

# 5. Drop final e salvamento
tennis_data_clean = tennis_data_clean.drop(columns=['Tournament', 'Score', 'Rank_1', 'Rank_2', 'Pts_1', 'Pts_2', 'Odd_1', 'Odd_2', 'Best of'], errors='ignore')
tennis_data_clean.to_parquet('data-kaggle/wta_clean.parquet', engine='pyarrow', index=False)