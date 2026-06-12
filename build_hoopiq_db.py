import pandas as pd
import json
import uuid
import kagglehub
import os

# 1. CONFIGURATION
FAN_FAVORITES = ["Robert Horry", "Steve Kerr", "Alex Caruso", "Udonis Haslem", "JJ Redick", "Brian Scalabrine", "Pete Maravich", "Julius Erving"]
TOP_PLAYERS_PER_FRANCHISE = 15 # La limite a bien été augmentée ici !

# 2. FONCTIONS DE MAPPING
def get_decade(year):
    if 1970 <= year <= 1979: return "seventies"
    elif 1980 <= year <= 1989: return "eighties"
    elif 1990 <= year <= 1999: return "nineties"
    elif 2000 <= year <= 2009: return "thousands"
    elif 2010 <= year <= 2019: return "tens"
    elif 2020 <= year <= 2029: return "twenties"
    return None

def map_positions(pos_string):
    if not isinstance(pos_string, str): return ["SF"]
    pos_map = {"PG": "PG", "SG": "SG", "SF": "SF", "PF": "PF", "C": "C"}
    # Sécurité supplémentaire pour nettoyer le format des postes
    positions = str(pos_string).upper().split('-')
    mapped = [pos_map[p] for p in positions if p in pos_map]
    return mapped if mapped else ["SF"]

# 3. TRAITEMENT DES DONNÉES
def build_database():
    print("🏀 Téléchargement des données depuis Kaggle (Base de données moderne)...")
    
    # NOUVEAU DATASET : Toujours à jour avec les dernières saisons !
    path = kagglehub.dataset_download("sumitrodatta/nba-aba-baa-stats")
    csv_path = os.path.join(path, "Player Totals.csv")
    
    print(f"📊 Fichier trouvé : {csv_path}. Début du traitement...")
    df = pd.read_csv(csv_path)
    
    # Les colonnes sont en minuscules dans ce nouveau dataset
    df = df[(df['season'] >= 1970)]
    df = df[df['g'] >= 40]
    df['Decade'] = df['season'].apply(get_decade)
    df = df.dropna(subset=['Decade'])
    
    # Sécurité mathématique : on convertit bien tout en nombre
    for col in ['pts', 'trb', 'ast', 'stl', 'blk']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Création de l'Impact Score
    df['Impact_Score'] = df['pts'] + (df['trb'] * 1.2) + (df['ast'] * 1.5) + (df['stl'] * 2.5) + (df['blk'] * 2.5)
    
    # Isolation de la meilleure saison par décennie pour chaque joueur
    df = df.sort_values('Impact_Score', ascending=False)
    best_seasons = df.drop_duplicates(subset=['player', 'Decade'], keep='first')
    
    # Filtre d'équilibrage (Top 15 par franchise + Favoris)
    top_franchise_players = best_seasons.groupby(['Decade', 'tm']).head(TOP_PLAYERS_PER_FRANCHISE)
    favorites_df = best_seasons[best_seasons['player'].isin(FAN_FAVORITES)]
    final_df = pd.concat([top_franchise_players, favorites_df]).drop_duplicates(subset=['player', 'Decade'])
    
    # 4. CONSTRUCTION DU JSON
    players_list = []
    for index, row in final_df.iterrows():
        players_list.append({
            "id": str(uuid.uuid4()),
            "name": str(row['player']).replace("*", ""), 
            "eligiblePositions": map_positions(row['pos']),
            "franchiseId": str(row['tm']).upper(),
            "decade": row['Decade'],
            "stats": {
                "points": round(float(row['pts']), 1),
                "rebounds": round(float(row['trb']), 1),
                "assists": round(float(row['ast']), 1),
                "steals": round(float(row['stl']), 1),
                "blocks": round(float(row['blk']), 1)
            }
        })
    
    # 5. SAUVEGARDE
    with open('players.json', 'w', encoding='utf-8') as f:
        json.dump(players_list, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Terminé ! {len(players_list)} joueurs premium exportés pour la draft.")

if __name__ == "__main__":
    build_database()
