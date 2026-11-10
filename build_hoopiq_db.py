import pandas as pd
import json
import uuid
import kagglehub
import os

# 1. CONFIGURATION
FAN_FAVORITES = ["Robert Horry", "Steve Kerr", "Alex Caruso", "Udonis Haslem", "JJ Redick", "Brian Scalabrine", "Pete Maravich", "Julius Erving"]
TOP_PLAYERS_PER_FRANCHISE = 50

# NOUVEAU : Dictionnaire d'override manuel pour forcer la polyvalence historique des légendes
CUSTOM_POSITIONS = {
    "Tim Duncan": ["PF", "C"],
    "Allen Iverson": ["PG", "SG"],
    "LeBron James": ["SF", "PF", "PG"],
    "Magic Johnson": ["PG", "PF"],
    "Anthony Davis": ["PF", "C"],
    "Kevin Garnett": ["PF", "C"],
    "Giannis Antetokounmpo": ["PF", "SF", "C"],
    "Luka Doncic": ["PG", "SG"],
    "Kobe Bryant": ["SG", "SF"]
}

# 2. FONCTIONS DE MAPPING
def get_decade(year):
    if 1970 <= year <= 1979: return "seventies"
    elif 1980 <= year <= 1989: return "eighties"
    elif 1990 <= year <= 1999: return "nineties"
    elif 2000 <= year <= 2009: return "thousands"
    elif 2010 <= year <= 2019: return "tens"
    elif 2020 <= year <= 2029: return "twenties"
    return None

def map_positions(pos_string, player_name=None):
    # 1. Vérification de l'override manuel prioritaire
    if player_name and player_name in CUSTOM_POSITIONS:
        return CUSTOM_POSITIONS[player_name]
        
    # 2. Traitement dynamique des positions combinées
    if not isinstance(pos_string, str): return ["SF"]
    pos_map = {"PG": "PG", "SG": "SG", "SF": "SF", "PF": "PF", "C": "C"}
    positions = str(pos_string).upper().split('-')
    
    # Déduplication tout en conservant l'ordre
    mapped = []
    for p in positions:
        if p in pos_map and pos_map[p] not in mapped:
            mapped.append(pos_map[p])
            
    return mapped if mapped else ["SF"]

def get_all_positions(pos_series):
    all_pos = []
    for p in pos_series:
        if isinstance(p, str):
            all_pos.extend(p.upper().split('-'))
    seen = set()
    return '-'.join([x for x in all_pos if not (x in seen or seen.add(x))])

# 3. TRAITEMENT DES DONNÉES
def build_database():
    print("🏀 Téléchargement des données depuis Kaggle (Base de données moderne)...")
    
    path = kagglehub.dataset_download("sumitrodatta/nba-aba-baa-stats")
    csv_path = os.path.join(path, "Player Totals.csv")
    
    print(f"📊 Fichier trouvé : {csv_path}. Début du traitement...")
    df = pd.read_csv(csv_path)
    
    df.columns = df.columns.str.lower()
    
    team_col = 'tm'
    if 'team' in df.columns: team_col = 'team'
    elif 'team_id' in df.columns: team_col = 'team_id'
    elif 'team_abbreviation' in df.columns: team_col = 'team_abbreviation'
    
    df = df[(df['season'] >= 1970)]
    df = df[df['g'] >= 40]
    df['Decade'] = df['season'].apply(get_decade)
    df = df.dropna(subset=['Decade'])
   
    df = df[df[team_col].astype(str).str.upper() != 'TOT']
    
    for col in ['pts', 'trb', 'ast', 'stl', 'blk']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0.0
            
    df['Impact_Score'] = df['pts'] + (df['trb'] * 1.2) + (df['ast'] * 1.5) + (df['stl'] * 2.5) + (df['blk'] * 2.5)
    
    # ⚠️ NOUVEAUTÉ : Agrégation de TOUTES les positions jouées dans la décennie
    aggregated_positions = df.groupby(['player', 'Decade'])['pos'].agg(get_all_positions).reset_index()
    aggregated_positions.rename(columns={'pos': 'agg_pos'}, inplace=True)
    
    df = df.sort_values('Impact_Score', ascending=False)
    best_seasons = df.drop_duplicates(subset=['player', 'Decade'], keep='first')
    
    # Fusion pour injecter l'historique complet des positions
    best_seasons = pd.merge(best_seasons, aggregated_positions, on=['player', 'Decade'], how='left')
    
    top_franchise_players = best_seasons.groupby(['Decade', team_col]).head(TOP_PLAYERS_PER_FRANCHISE)
    favorites_df = best_seasons[best_seasons['player'].isin(FAN_FAVORITES)]
    final_df = pd.concat([top_franchise_players, favorites_df]).drop_duplicates(subset=['player', 'Decade'])
    
    # 4. CONSTRUCTION DU JSON
    players_list = []
    for index, row in final_df.iterrows():
        player_name_clean = str(row['player']).replace("*", "")
        players_list.append({
            "id": str(uuid.uuid4()),
            "name": player_name_clean, 
            # ⚠️ NOUVEAUTÉ : On utilise 'agg_pos' au lieu de 'pos' et on transmet le nom
            "eligiblePositions": map_positions(row['agg_pos'], player_name_clean),
            "franchiseId": str(row[team_col]).upper(),
            "decade": row['Decade'],
            "stats": {
                "points": round(float(row.get('pts', 0)), 1),
                "rebounds": round(float(row.get('trb', 0)), 1),
                "assists": round(float(row.get('ast', 0)), 1),
                "steals": round(float(row.get('stl', 0)), 1),
                "blocks": round(float(row.get('blk', 0)), 1)
            }
        })
    
    # 5. SAUVEGARDE
    with open('players.json', 'w', encoding='utf-8') as f:
        json.dump(players_list, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Terminé ! {len(players_list)} joueurs premium exportés avec leurs postes secondaires.")

if __name__ == "__main__":
    build_database()
