import pandas as pd
import json
import uuid
import kagglehub
import os

# 1. CONFIGURATION
# Ta liste blanche pour les joueurs cultes (Fan Favorites) qui doivent être là
FAN_FAVORITES = ["Robert Horry", "Steve Kerr", "Alex Caruso", "Udonis Haslem", "JJ Redick", "Brian Scalabrine"]
TOP_PLAYERS_PER_FRANCHISE = 12

# 2. FONCTIONS DE MAPPING
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

# 3. TRAITEMENT DES DONNÉES
def build_database():
    print("🏀 Téléchargement des données depuis Kaggle...")
    
    # Téléchargement dynamique via KaggleHub
    path = kagglehub.dataset_download("drgilermo/nba-players-stats")
    csv_path = os.path.join(path, "Seasons_Stats.csv")
    
    print(f"📊 Fichier trouvé : {csv_path}. Début du traitement...")
    df = pd.read_csv(csv_path)
    
    # Filtre de base : Depuis 1980, minimum 40 matchs
    df = df[(df['Year'] >= 1980) & (df['Year'] <= 2024)]
    df = df[df['G'] >= 40]
    df['Decade'] = df['Year'].apply(get_decade)
    df = df.dropna(subset=['Decade'])
    
    # Création de l'Impact Score (Valorisation de la polyvalence)
    df['Impact_Score'] = df['PTS'] + (df['TRB'] * 1.2) + (df['AST'] * 1.5) + (df['STL'] * 2.5) + (df['BLK'] * 2.5)
    
    # On isole la MEILLEURE saison de chaque joueur par décennie
    df = df.sort_values('Impact_Score', ascending=False)
    best_seasons = df.drop_duplicates(subset=['Player', 'Decade'], keep='first')
    
    # LE FILTRE D'ÉQUILIBRAGE (TOP 12)
    top_franchise_players = best_seasons.groupby(['Decade', 'Tm']).head(TOP_PLAYERS_PER_FRANCHISE)
    
    # Ajout de la Whitelist
    favorites_df = best_seasons[best_seasons['Player'].isin(FAN_FAVORITES)]
    
    # Fusion et nettoyage final
    final_df = pd.concat([top_franchise_players, favorites_df]).drop_duplicates(subset=['Player', 'Decade'])
    
    # 4. CONSTRUCTION DU JSON
    players_list = []
    for index, row in final_df.iterrows():
        players_list.append({
            "id": str(uuid.uuid4()),
            "name": str(row['Player']).replace("*", ""), # Retire l'astérisque du Hall of Fame
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
    
    # 5. SAUVEGARDE
    with open('players.json', 'w', encoding='utf-8') as f:
        json.dump(players_list, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Terminé ! {len(players_list)} joueurs premium exportés pour la draft.")

if __name__ == "__main__":
    build_database()
