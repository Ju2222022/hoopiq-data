import pandas as pd
import json
import uuid
import kagglehub
import os

# 1. CONFIGURATION
# J'ai ajouté quelques légendes des 70s dans la liste blanche par sécurité
FAN_FAVORITES = ["Robert Horry", "Steve Kerr", "Alex Caruso", "Udonis Haslem", "JJ Redick", "Brian Scalabrine", "Pete Maravich", "Julius Erving"]
TOP_PLAYERS_PER_FRANCHISE = 30

# 2. FONCTIONS DE MAPPING
def get_decade(year):
    # NOUVEAU : Ajout des années 70
    if 1970 <= year <= 1979: return "seventies"
    elif 1980 <= year <= 1989: return "eighties"
    elif 1990 <= year <= 1999: return "nineties"
    elif 2000 <= year <= 2009: return "thousands"
    elif 2010 <= year <= 2019: return "tens"
    elif 2020 <= year <= 2029: return "twenties"
    return None

def map_positions(pos_string):
    if not isinstance(pos_string, str): return ["SF"]
    # On conserve les initiales brutes de Kaggle au lieu de les traduire
    pos_map = {
        "PG": "PG", "SG": "SG",
        "SF": "SF", "PF": "PF", "C": "C"
    }
    positions = pos_string.split('-')
    mapped = [pos_map[p] for p in positions if p in pos_map]
    return mapped if mapped else ["SF"]

# 3. TRAITEMENT DES DONNÉES
def build_database():
    print("🏀 Téléchargement des données depuis Kaggle...")
    
    path = kagglehub.dataset_download("drgilermo/nba-players-stats")
    csv_path = os.path.join(path, "Seasons_Stats.csv")
    
    print(f"📊 Fichier trouvé : {csv_path}. Début du traitement...")
    df = pd.read_csv(csv_path)
    
    # NOUVEAU : Filtre descendu à 1970
    df = df[(df['Year'] >= 1970) & (df['Year'] <= 2024)]
    df = df[df['G'] >= 40]
    df['Decade'] = df['Year'].apply(get_decade)
    df = df.dropna(subset=['Decade'])
    
    # SÉCURITÉ 70s : Remplacement des cases vides par des 0 pour éviter les crashs
    df['PTS'] = df['PTS'].fillna(0)
    df['TRB'] = df['TRB'].fillna(0)
    df['AST'] = df['AST'].fillna(0)
    df['STL'] = df['STL'].fillna(0)
    df['BLK'] = df['BLK'].fillna(0)
    
    # Création de l'Impact Score
    df['Impact_Score'] = df['PTS'] + (df['TRB'] * 1.2) + (df['AST'] * 1.5) + (df['STL'] * 2.5) + (df['BLK'] * 2.5)
    
    # Isolation de la meilleure saison par décennie
    df = df.sort_values('Impact_Score', ascending=False)
    best_seasons = df.drop_duplicates(subset=['Player', 'Decade'], keep='first')
    
    # Filtre d'équilibrage (Top 12)
    top_franchise_players = best_seasons.groupby(['Decade', 'Tm']).head(TOP_PLAYERS_PER_FRANCHISE)
    favorites_df = best_seasons[best_seasons['Player'].isin(FAN_FAVORITES)]
    final_df = pd.concat([top_franchise_players, favorites_df]).drop_duplicates(subset=['Player', 'Decade'])
    
    # 4. CONSTRUCTION DU JSON
    players_list = []
    for index, row in final_df.iterrows():
        players_list.append({
            "id": str(uuid.uuid4()),
            "name": str(row['Player']).replace("*", ""), 
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
