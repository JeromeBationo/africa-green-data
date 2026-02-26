import feedparser
import requests
import json
import base64
import os
from datetime import datetime

# --- CONFIGURATION VIA SECRETS GITHUB ---
# Remplacez "VOTRE_PSEUDO_GITHUB" par votre vrai nom d'utilisateur GitHub
GITHUB_TOKEN = os.environ.get('MY_GITHUB_TOKEN') 
REPO_OWNER = "VOTRE_PSEUDO_GITHUB" 
REPO_NAME = "africa-green-data"
FILE_PATH = "africa_green_data.json"

# --- SOURCES DE DONNÉES (NEWS & DATA) ---
RSS_SOURCES = {
    "AfDB_Environment": "https://www.afdb.org/fr/topics/environment/rss.xml",
    "UNECA_News": "https://archive.uneca.org/fr/rss-feeds",
    "Sustainability_Africa": "https://www.sustainabilitynewsafrica.com/feed/",
    "Green_Economy_Africa": "https://www.unep.org/news-and-stories/rss.xml"
}

# API Banque Mondiale : Émissions CO2 (en tonnes par habitant) pour l'Afrique Subsaharienne
WB_API_URL = "https://api.worldbank.org/v2/region/SSF/indicator/EN.ATM.CO2E.PC?format=json&per_page=10"

def fetch_green_news():
    """Récupère les news depuis les flux RSS africains."""
    all_news = []
    print("Extraction des actualités en cours...")
    for source, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # Top 5 par source
                all_news.append({
                    "source": source.replace('_', ' '),
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get('published', entry.get('updated', datetime.now().isoformat()))
                })
        except Exception as e:
            print(f"Erreur sur la source {source}: {e}")
    return all_news

def fetch_climate_data():
    """Récupère les indicateurs de la Banque Mondiale."""
    print("Récupération des données Banque Mondiale...")
    try:
        response = requests.get(WB_API_URL, timeout=10)
        data = response.json()
        # On filtre pour ne garder que les années avec des valeurs réelles
        return [
            {"year": item['date'], "value": item['value']} 
            for item in data[1] if item['value'] is not None
        ][:5]
    except Exception as e:
        print(f"Erreur API Banque Mondiale : {e}")
        return []

def push_to_github(content_dict):
    """Met à jour le fichier JSON sur le dépôt via l'API GitHub."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Étape A : Obtenir le SHA du fichier existant (si il existe)
    get_res = requests.get(url, headers=headers)
    sha = get_res.json().get('sha') if get_res.status_code == 200 else None

    # Étape B : Préparer le contenu en Base64
    json_string = json.dumps(content_dict, indent=4, ensure_ascii=False)
    content_base64 = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    # Étape C : Envoyer la mise à jour
    payload = {
        "message": f"Mise à jour Africa Green News : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "content": content_base64,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    put_res = requests.put(url, headers=headers, json=payload)
    
    if put_res.status_code in [200, 201]:
        print("✅ SUCCÈS : Données poussées sur GitHub.")
    else:
        print(f"❌ ÉCHEC : {put_res.status_code} - {put_res.text}")

def run_pipeline():
    """Lance le processus complet."""
    if not GITHUB_TOKEN:
        print("ERREUR : Le secret MY_GITHUB_TOKEN est manquant.")
        return

    data_payload = {
        "last_update": datetime.now().isoformat(),
        "news": fetch_green_news(),
        "climate_stats": fetch_climate_data()
    }
    
    push_to_github(data_payload)

if __name__ == "__main__":
    run_pipeline()
