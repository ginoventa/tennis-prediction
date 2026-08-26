import joblib
import pandas as pd

# 1. Carregar base de dados e o modelo salvo
df = pd.read_parquet("data-kaggle/wta_clean.parquet")
model = joblib.load("modelos/modelo_wta_rf.pkl")
features = ["Rank_Diff", "Pts_Diff", "Odd_Diff", "isSlam", "Win_Rate_10_Diff"]
  
# 2. Função para buscar as últimas estatísticas registradas de uma jogadora
def get_latest_player_full_stats(player_name, df):
  player_clean = player_name.strip().lower()

  # Busca partidas em que a jogadora esteve presente
  player_games = df[
      df["Player_1"].astype(str).str.lower().str.contains(player_clean)
      | df["Player_2"].astype(str).str.lower().str.contains(player_clean)
  ].sort_values("Date")

  if len(player_games) == 0:
    raise ValueError(
        f"Jogadora '{player_name}' não encontrada no histórico!"
    )

  last_game = player_games.iloc[-1]

  # Verifica se ela jogou como P1 ou P2 na última partida e extrai os valores
  if player_clean in str(last_game["Player_1"]).lower():
    win_rate = last_game["Win_Rate_10_P1"]
    rank = last_game.get("Rank_1", None)
    pts = last_game.get("Pts_1", None)
    odd = last_game.get("Odd_1", None)
    exact_name = str(last_game["Player_1"])
  else:
    win_rate = last_game["Win_Rate_10_P2"]
    rank = last_game.get("Rank_2", None)
    pts = last_game.get("Pts_2", None)
    odd = last_game.get("Odd_2", None)
    exact_name = str(last_game["Player_2"])

  return {
      "name": exact_name,
      "win_rate": win_rate,
      "rank": rank if pd.notnull(rank) else 0,
      "pts": pts if pd.notnull(pts) else 0,
      "odd": odd if pd.notnull(odd) else 0,
  }


# 3. ENTRADA DO USUÁRIO (Apenas nomes e se é Grand Slam)
p1_input = input("Digite o nome da Jogadora 1 (ex: Swiatek): ").strip()
p2_input = input("Digite o nome da Jogadora 2 (ex: Sabalenka): ").strip()
slam_input = (input("É um torneio de Grand Slam? (s/n): ").strip().lower() == "s")

try:
  # Busca automática no histórico
  p1 = get_latest_player_full_stats(p1_input, df)
  p2 = get_latest_player_full_stats(p2_input, df)

  # Cálculo automático de todos os diferenciais
  rank_diff = p1["rank"] - p2["rank"]
  pts_diff = p1["pts"] - p2["pts"]
  odd_diff = p1["odd"] - p2["odd"]
  win_rate_diff = p1["win_rate"] - p2["win_rate"]

  # Monta o DataFrame de entrada
  input_data = pd.DataFrame([[rank_diff, pts_diff, odd_diff, slam_input, win_rate_diff]],columns=features,)

  # 4. PREDIÇÃO
  probs = model.predict_proba(input_data)[0]

  print("\n--- RESUMO DOS DADOS RECUPERADOS ---")
  print(f"{p1['name']}: WinRate10={p1['win_rate']:.0%} | Rank={p1['rank']} |"f" Pts={p1['pts']}")
  print(f"{p2['name']}: WinRate10={p2['win_rate']:.0%} | Rank={p2['rank']} |"f" Pts={p2['pts']}")

  print("\n--- RESULTADO DA PREDIÇÃO ---")
  print(f"Probabilidade de {p1['name']} vencer: {probs[1]:.2%}")
  print(f"Probabilidade de {p2['name']} vencer: {probs[0]:.2%}")

  if probs[1] > probs[0]:
    print(f"\nPalpite: {p1['name']} Vence!")
  else:
    print(f"\nPalpite: {p2['name']} Vence!")

except ValueError as e:
  print(e)