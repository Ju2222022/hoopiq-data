import pandas as pd
import json
import uuid
import kagglehub
import os

# Liste blanche pour les joueurs cultes (Fan Favorites)
FAN_FAVORITES = ["Robert Horry", "Steve Kerr", "Alex Caruso", "Udonis Haslem", "JJ Redick"]

def get_decade(year):
    if 1980 <= year <= 1989: return "eighties"
    elif 1990 <= year <= 1999: return "nineties"
    elif 2000 <= year <= 2009: return "thousands"
    elif 2010 <= year <= 2019: return "tens"
    elif 2020 <= year <= 2029: return "twenties"
    return None

def map_positions(pos_string):
    if not isinstance(pos_string, str): return ["smallForward"]
    pos_map = {
        "PG": "pointGuard", "SG": "shootingGuard",
        "SF": "smallForward", "PF": "powerForward", "C": "center"
    }
    positions = pos_string.split('-')
    mapped = [pos_map[p] for p in positions if p in pos_map]
    return mapped if mapped else ["smallForward"]

def build_database():
    print("🏀 Téléchargement des données depuis Kaggle...")
    
    # TON INTÉGRATION : Téléchargement dynamique
    path = kagglehub.dataset_download("drgilermo/nba-players-stats")
    csv_path = os.path.join(path, "Seasons_Stats.csv")
    
    print(f"📊 Fichier trouvé : {csv_path}. Début du traitement...")
    
    # Chargement du CSV
    df = pd.read_csv(csv_path)
    
    # Filtrage global (Depuis 1980, minimum 40 matchs)
    df = df[(df['Year'] >= 1980) & (df['Year'] <= 2024)]
    df = df[df['G'] >= 40]
    
    # APPLICATION DU FILTRE "HOOPIQ CASTING"
    condition_stats = (df['PTS'] >= 12.0) | (df['TRB'] >= 7.0) | (df['AST'] >= 5.0) | (df['STL'] >= 1.5) | (df['BLK'] >= 1.5)
    condition_favorites = df['Player'].isin(FAN_FAVORITES)
    
    filtered_df = df[condition_stats | condition_favorites]
    
    # Formatage par décennie
    filtered_df['Decade'] = filtered_df['Year'].apply(get_decade)
    filtered_df = filtered_df.sort_values('PTS', ascending=False)
    final_df = filtered_df.drop_duplicates(subset=['Player', 'Decade'], keep='first')
    
    # CONSTRUCTION DU JSON
    players_list = []
    for index, row in final_df.iterrows():
        players_list.append({
            "id": str(uuid.uuid4()),
            "name": str(row['Player']).replace("*", ""), # Enlève l'étoile du Hall of Fame parfois présente
            "eligiblePositions": map_positions(row['Pos']),
            "franchiseId": str(row['Tm']).upper(),
            "decade": row['Decade'],
            "stats": {
                "points": round(float(row['PTS']), 1),
                "rebounds": round(float(row['TRB']), 1),
                "assists": round(float(row['AST']), 1),
                "steals": round(float(row['STL']), 1),
                "blocks": round(float(row['BLK']), 1)
            }
        })
    
    with open('players.json', 'w', encoding='utf-8') as f:
        json.dump(players_list, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Terminé ! {len(players_list)} joueurs exportés dans le JSON.")

if __name__ == "__main__":
    build_database()
