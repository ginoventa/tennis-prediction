import pandas as pd
import numpy as np
# import fastparquet

# Abertura e limpeza dos dados 
tennis_data = pd.read_csv('data-kaggle/wta.csv')
tennis_data['Odd_2'] = tennis_data['Odd_2'].replace('-', np.nan)
tennis_data['Odd_1'] = tennis_data['Odd_1'].replace('-', np.nan)
tennis_data_clean = tennis_data.dropna()
tennis_data_clean = tennis_data_clean.drop_duplicates()

string_columns = ['Tournament', 'Surface', 'Round', 'Court', 'Player_1', 'Player_2', 'Winner']
for col in string_columns:
    tennis_data_clean[col] = tennis_data_clean[col].astype('category') # Cria respectividade numérica para cada categoria, economizando memória

tennis_data_clean['Date'] = pd.to_datetime(tennis_data_clean['Date'], errors='coerce')

sets = tennis_data_clean['Score'].astype(str).str.strip().str.split(r'\s+', expand=True)
tennis_data_clean[['Set_1', 'Set_2', 'Set_3']] = sets[[0, 1, 2]]

int_columns = ['Rank_2', 'Rank_1', 'Pts_1', 'Pts_2']
for col in int_columns:
    tennis_data_clean[col] = pd.to_numeric(tennis_data_clean[col], errors='coerce').astype('Int64')

float_columns = ['Odd_1', 'Odd_2']
for col in float_columns:
    tennis_data_clean[col] = pd.to_numeric(tennis_data_clean[col], errors='coerce').astype('float64')

tennis_data_clean.to_parquet('data-kaggle/wta_clean.parquet', index=False)