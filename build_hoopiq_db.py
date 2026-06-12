import pandas as pd
import requests
import json
import uuid
import time

# 1. CONFIGURATION
FAN_FAVORITES = ["Robert Horry", "Steve Kerr", "Alex Caruso", "Udonis Haslem", "JJ Redick", "Brian Scalabrine", "Pete Maravich", "Julius Erving"]
TOP_PLAYERS_PER_FRANCHISE = 15 # La limite a été augmentée ici !

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
    positions = pos_string.split('-')
    mapped = [pos_map[p] for p in positions if p in pos_map]
    return mapped if mapped else ["SF"]

# 3. TRAITEMENT DES DONNÉES (LE SCRAPER)
def build_database():
    print("🏀 Lancement du Scraper de données en direct...")
    
    all_seasons = []
    # On imite un vrai navigateur pour ne pas être bloqué par les serveurs
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    }
    
    # Scraping de 1970 à aujourd'hui (2024 inclus)
    for year in range(1970, 2025):
        print(f"📊 Récupération de la saison {year}...")
        url = f"https://www.basketball-reference.com/leagues/NBA_{year}_totals.html"
        
        try:
            response = requests.get(url, headers=headers)
            df = pd.read_html(response.text)[0]
            
            # Nettoyage des fausses lignes d'en-tête insérées dans les tableaux
            df = df[df['Player'] != 'Player']
            
            # Conversion sécurisée des statistiques en valeurs numériques
            numeric_cols = ['G', 'PTS', 'TRB', 'AST', 'STL', 'BLK']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    
            df['Year'] = year
            all_seasons.append(df)
            
            # ⚠️ SÉCURITÉ ANTI-BAN : Pause obligatoire de 3 secondes entre chaque page
            time.sleep(3)
            
        except Exception as e:
            print(f"⚠️ Erreur de scraping pour l'année {year} : {e}")
            
    # Fusion de toutes les années récoltées
    full_df = pd.concat(all_seasons, ignore_index=True)
    
    # Application des filtres de sélection
    full_df = full_df[full_df['G'] >= 40]
    full_df['Decade'] = full_df['Year'].apply(get_decade)
    full_df = full_df.dropna(subset=['Decade'])
    
    # Création de l'Impact Score
    full_df['Impact_Score'] = full_df['PTS'] + (full_df['TRB'] * 1.2) + (full_df['AST'] * 1.5) + (full_df['STL'] * 2.5) + (full_df['BLK'] * 2.5)
    
    # Isolation de la meilleure saison par décennie pour chaque joueur
    full_df = full_df.sort_values('Impact_Score', ascending=False)
    best_seasons = full_df.drop_duplicates(subset=['Player', 'Decade'], keep='first')
    
    # Filtre d'équilibrage final (Top 15 par franchise + Favoris)
    top_franchise_players = best_seasons.groupby(['Decade', 'Tm']).head(TOP_PLAYERS_PER_FRANCHISE)
    favorites_df = best_seasons[best_seasons['Player'].isin(FAN_FAVORITES)]
    final_df = pd.concat([top_franchise_players, favorites_df]).drop_duplicates(subset=['Player', 'Decade'])
    
    # 4. CONSTRUCTION DU JSON
    players_list = []
    for index, row in final_df.iterrows():
        players_list.append({
            "id": str(uuid.uuid4()),
            "name": str(row['Player']).replace("*", ""), 
            "eligiblePositions": map_positions(str(row['Pos'])),
            "franchiseId": str(row['Tm']).upper(),
            "decade": row['Decade'],
            "stats": {
                "points": round(float(row['PTS']), 1),
                "rebounds": round(float(row['TRB']), 1),
                "assists": round(float(row['AST']), 1),
                "steals": round(float(row['STL'])) if 'STL' in row else 0.0,
                "blocks": round(float(row['BLK'])) if 'BLK' in row else 0.0
            }
        })
    
    # 5. SAUVEGARDE
    with open('players.json', 'w', encoding='utf-8') as f:
        json.dump(players_list, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Terminé ! {len(players_list)} joueurs exportés avec la base de données live.")

if __name__ == "__main__":
    build_database()
