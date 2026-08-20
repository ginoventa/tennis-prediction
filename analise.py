import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt

path_file = 'data-kaggle/wta_clean.parquet'

data = pd.read_parquet(path_file)

# 2. Verificar proporção do Target (Player_1_Wins)
print("--- Distribuição de Vitórias ---")
print(data['Player_1_Wins'].value_counts(normalize=True))

# 3. Taxa de vitória do favorito segundo as Odds
favorito_venceu = (data['Odd_Diff'] < 0) == (data['Player_1_Wins'] == 1)
print(f"\nTaxa de vitória do favorito (Odd menor): {favorito_venceu.mean():.2%}")

# 4. Visualização: Distribuição do Rank_Diff por Resultado
plt.figure(figsize=(8, 5))
sns.boxplot(data=data, x='Player_1_Wins', y='Rank_Diff')
plt.title('Diferença de Ranking vs Vitória do Player 1')
plt.xlabel('Player 1 Venceu? (0 = Não, 1 = Sim)')
plt.ylabel('Rank_Diff (Rank_1 - Rank_2)')
plt.show()