#!/usr/bin/env python3
"""
Scraping automatique des fiches DMC depuis l'annuaire DestiMaG / TourMaG.
Ce script :
1. Parcourt la page annuaire pour lister toutes les fiches DMC
2. Scrape chaque fiche pour extraire les données structurées
3. Génère un fichier dmc_data.json
"""

import json
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# =============================================================================
# CONFIGURATION
# =============================================================================

ANNUAIRE_URL = "https://www.tourmag.com/Annuaire-des-agences-touristiques-locales_r404.html"
BASE_URL = "https://www.tourmag.com"
OUTPUT_FILE = "data/dmc_data.json"
REQUEST_DELAY = 1.5  # Délai entre chaque requête (en secondes) pour ne pas surcharger le serveur
USER_AGENT = "Mozilla/5.0 (compatible; DMCMap-Scraper/1.0; TourMaG)"

# Coordonnées GPS centrales pour chaque pays/destination
COUNTRY_COORDS = {
    "Açores": (38.7222, -27.2206),
    "Afrique du Sud": (-30.5595, 22.9375),
    "Albanie": (41.1533, 20.1683),
    "Algérie": (28.0339, 1.6596),
    "Allemagne": (51.1657, 10.4515),
    "Arabie Saoudite": (23.8859, 45.0792),
    "Argentine": (-38.4161, -63.6167),
    "Autriche": (47.5162, 14.5501),
    "Belize": (17.1899, -88.4976),
    "Birmanie": (21.9162, 95.956),
    "Brésil": (-14.235, -51.9253),
    "Bulgarie": (42.7339, 25.4858),
    "Cambodge": (12.5657, 104.991),
    "Canada": (56.1304, -106.3468),
    "Cap-Vert": (16.5388, -23.0418),
    "Cap Vert": (16.5388, -23.0418),
    "Chine": (35.8617, 104.1954),
    "Chypre": (35.1264, 33.4299),
    "Colombie": (4.5709, -74.2973),
    "Corée du Nord": (40.3399, 127.5101),
    "Corée du Sud": (35.9078, 127.7669),
    "Costa Rica": (9.7489, -83.7534),
    "Croatie": (45.1, 15.2),
    "Cuba": (21.5218, -77.7812),
    "Danemark": (56.2639, 9.5018),
    "Ecosse": (56.4907, -4.2026),
    "Égypte": (26.8206, 30.8025),
    "Egypte": (26.8206, 30.8025),
    "Émirats Arabes Unis": (23.4241, 53.8478),
    "Emirats Arabes Unis": (23.4241, 53.8478),
    "Equateur": (-1.8312, -78.1834),
    "Équateur": (-1.8312, -78.1834),
    "Espagne": (40.4637, -3.7492),
    "Etats-Unis": (37.0902, -95.7129),
    "États-Unis": (37.0902, -95.7129),
    "USA": (37.0902, -95.7129),
    "Finlande": (61.9241, 25.7482),
    "Géorgie": (42.3154, 43.3569),
    "Grèce": (39.0742, 21.8243),
    "Guatemala": (15.7835, -90.2308),
    "Guyane": (3.9339, -53.1258),
    "Ile de la Réunion": (-21.1151, 55.5364),
    "Inde": (20.5937, 78.9629),
    "Indonésie": (-0.7893, 113.9213),
    "Irlande": (53.1424, -7.6921),
    "Islande": (64.9631, -19.0208),
    "Italie": (41.8719, 12.5674),
    "Japon": (36.2048, 138.2529),
    "Jordanie": (30.5852, 36.2384),
    "Kenya": (-0.0236, 37.9062),
    "Kosovo": (42.6026, 20.903),
    "Laos": (19.8563, 102.4955),
    "Madagascar": (-18.7669, 46.8691),
    "Madère": (32.7607, -16.9595),
    "MADÈRE": (32.7607, -16.9595),
    "Malaisie": (4.2105, 101.9758),
    "Malte": (35.9375, 14.3754),
    "Maroc": (31.7917, -7.0926),
    "Mexique": (23.6345, -102.5528),
    "Mongolie": (46.8625, 104.1917),
    "Myanmar": (21.9162, 95.956),
    "Nicaragua": (12.8654, -85.2072),
    "Norvège": (60.472, 8.4689),
    "Oman": (21.4735, 55.9754),
    "Ouzbékistan": (41.3775, 64.5853),
    "Panama": (8.538, -80.7821),
    "Philippines": (12.8797, 121.774),
    "Polynésie Française": (-17.6797, -149.4068),
    "Polynésie française": (-17.6797, -149.4068),
    "Portugal": (39.3999, -8.2245),
    "Pouilles": (41.0, 16.5),
    "Qatar": (25.3548, 51.1839),
    "Roumanie": (45.9432, 24.9668),
    "Royaume-Uni": (55.3781, -3.436),
    "Sardaigne": (40.1209, 9.0129),
    "Serbie": (44.0165, 21.0059),
    "Sicile": (37.6, 14.0154),
    "Sri Lanka": (7.8731, 80.7718),
    "Suisse": (46.8182, 8.2275),
    "Tahiti": (-17.6509, -149.426),
    "Tanzanie": (-6.369, 34.8888),
    "Thaïlande": (15.87, 100.9925),
    "Tunisie": (33.8869, 9.5375),
    "Turquie": (38.9637, 35.2433),
    "Vietnam": (14.0583, 108.2772),
    "Zanzibar": (-6.1659, 39.1989),
    # Régions / zones
    "Asie": (34.0479, 100.6197),
    "Asie du Sud-Est": (10.0, 106.0),
    "Afrique": (8.7832, 34.5085),
    "Amérique latine": (-8.7832, -55.4915),
    "Europe de l'Est": (50.0, 25.0),
    "Océanie": (-22.7359, 140.0188),
    "Océan Indien": (-12.0, 55.0),
    "Sous-Continent Indien": (20.0, 78.0),
}

# Mapping des noms de pictogrammes vers des labels lisibles et des catégories
PICTO_CATEGORIES = {
    # Clientèle
    "amoureux": {"label": "En couple", "category": "clientele"},
    "famille": {"label": "En famille", "category": "clientele"},
    "groupes": {"label": "Groupes", "category": "clientele"},
    "incentive": {"label": "Incentive", "category": "clientele"},
    "individuel": {"label": "En solo", "category": "clientele"},
    "gay-friendly": {"label": "Gay friendly", "category": "clientele"},
    # Prestations
    "acceuil": {"label": "Accueil", "category": "prestations"},
    "adaptabilite": {"label": "Adaptabilité", "category": "prestations"},
    "assistance": {"label": "Assistance", "category": "prestations"},
    "autotour": {"label": "Autotour", "category": "prestations"},
    "circuit": {"label": "Circuit", "category": "prestations"},
    "city": {"label": "City-break", "category": "prestations"},
    "conference": {"label": "Conférences", "category": "prestations"},
    "congres": {"label": "Congrès", "category": "prestations"},
    "eco_responsable": {"label": "Éco-responsable", "category": "prestations"},
    "hotel": {"label": "Hébergement", "category": "prestations"},
    "luxe": {"label": "Luxe", "category": "prestations"},
    "meeting": {"label": "Meeting", "category": "prestations"},
    "mice": {"label": "MICE", "category": "prestations"},
    "nature": {"label": "Nature", "category": "prestations"},
    "sur_mesure": {"label": "Sur-mesure", "category": "prestations"},
    "team_building": {"label": "Team-building", "category": "prestations"},
    "transferts": {"label": "Transferts", "category": "prestations"},
    "visite_guidee": {"label": "Visite guidée", "category": "prestations"},
    "vtc": {"label": "VTC", "category": "prestations"},
    # Activités
    "attractions": {"label": "Attractions", "category": "activites"},
    "aventure": {"label": "Aventure", "category": "activites"},
    "carnaval": {"label": "Carnaval", "category": "activites"},
    "culture": {"label": "Culture", "category": "activites"},
    "culture_patrimoine": {"label": "Culture et patrimoine", "category": "activites"},
    "decouverte": {"label": "Découverte", "category": "activites"},
    "excursions": {"label": "Excursions", "category": "activites"},
    "feu_d_artifice": {"label": "Feu d'artifice", "category": "activites"},
    "golf": {"label": "Golf", "category": "activites"},
    "histoire": {"label": "Histoire / Châteaux", "category": "activites"},
    "illuminations": {"label": "Illuminations", "category": "activites"},
    "jardin": {"label": "Jardin", "category": "activites"},
    "montagne": {"label": "Lacs et montagne", "category": "activites"},
    "noel": {"label": "Marchés de Noël", "category": "activites"},
    "nouvel_an": {"label": "Nouvel an", "category": "activites"},
    "photo": {"label": "Photographie", "category": "activites"},
    "plongee": {"label": "Plongée", "category": "activites"},
    "rando": {"label": "Randonnée", "category": "activites"},
    "resto": {"label": "Gastronomie", "category": "activites"},
    "snorkeling": {"label": "Snorkeling", "category": "activites"},
    "sport": {"label": "Sport", "category": "activites"},
    "trail": {"label": "Trail", "category": "activites"},
    "trekking": {"label": "Trekking", "category": "activites"},
    "velo": {"label": "Vélo", "category": "activites"},
    "vendanges": {"label": "Vendanges", "category": "activites"},
    "voyage": {"label": "Voyage", "category": "activites"},
}

# Mapping des destinations vers leur continent/zone
CONTINENT_MAP = {
    "Açores": "Europe",
    "Afrique du Sud": "Afrique",
    "Albanie": "Europe",
    "Algérie": "Afrique",
    "Allemagne": "Europe",
    "Arabie Saoudite": "Moyen-Orient",
    "Argentine": "Amériques",
    "Autriche": "Europe",
    "Belize": "Amériques",
    "Brésil": "Amériques",
    "Bulgarie": "Europe",
    "Cambodge": "Asie",
    "Canada": "Amériques",
    "Cap-Vert": "Afrique",
    "Cap Vert": "Afrique",
    "Chine": "Asie",
    "Chypre": "Europe",
    "Colombie": "Amériques",
    "Corée du Nord": "Asie",
    "Corée du Sud": "Asie",
    "Costa Rica": "Amériques",
    "Croatie": "Europe",
    "Cuba": "Amériques",
    "Danemark": "Europe",
    "Ecosse": "Europe",
    "Égypte": "Afrique",
    "Egypte": "Afrique",
    "Émirats Arabes Unis": "Moyen-Orient",
    "Emirats Arabes Unis": "Moyen-Orient",
    "Equateur": "Amériques",
    "Équateur": "Amériques",
    "Espagne": "Europe",
    "Etats-Unis": "Amériques",
    "États-Unis": "Amériques",
    "USA": "Amériques",
    "Finlande": "Europe",
    "Géorgie": "Europe",
    "Grèce": "Europe",
    "Guatemala": "Amériques",
    "Guyane": "Amériques",
    "Ile de la Réunion": "Océan Indien",
    "Inde": "Asie",
    "Indonésie": "Asie",
    "Irlande": "Europe",
    "Islande": "Europe",
    "Italie": "Europe",
    "Japon": "Asie",
    "Jordanie": "Moyen-Orient",
    "Kenya": "Afrique",
    "Kosovo": "Europe",
    "Laos": "Asie",
    "Madagascar": "Afrique",
    "Madère": "Europe",
    "MADÈRE": "Europe",
    "Malaisie": "Asie",
    "Malte": "Europe",
    "Maroc": "Afrique",
    "Mexique": "Amériques",
    "Mongolie": "Asie",
    "Myanmar": "Asie",
    "Nicaragua": "Amériques",
    "Norvège": "Europe",
    "Oman": "Moyen-Orient",
    "Ouzbékistan": "Asie",
    "Panama": "Amériques",
    "Philippines": "Asie",
    "Polynésie Française": "Océanie",
    "Polynésie française": "Océanie",
    "Portugal": "Europe",
    "Pouilles": "Europe",
    "Qatar": "Moyen-Orient",
    "Roumanie": "Europe",
    "Royaume-Uni": "Europe",
    "Sardaigne": "Europe",
    "Serbie": "Europe",
    "Sicile": "Europe",
    "Sri Lanka": "Asie",
    "Suisse": "Europe",
    "Tahiti": "Océanie",
    "Tanzanie": "Afrique",
    "Thaïlande": "Asie",
    "Tunisie": "Afrique",
    "Turquie": "Europe",
    "Vietnam": "Asie",
    "Zanzibar": "Afrique",
}


# =============================================================================
# FONCTIONS
# =============================================================================

def fetch_page(url, retries=3):
    """Télécharge une page HTML avec gestion des erreurs et retries."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.read().decode(charset, errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"  [WARN] Tentative {attempt + 1}/{retries} échouée pour {url}: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    print(f"  [ERROR] Impossible de charger {url}")
    return None


def extract_dmc_links(html):
    """
    Extrait les liens vers les fiches DMC depuis la page annuaire.
    Filtre les articles d'actualité qui ne sont pas des fiches DMC.
    """
    # Trouver tous les blocs article (div class="art-XXXXX ...")
    blocks = re.finditer(
        r'<div\s+class="art-(\d+)\s+cel1[^"]*"[^>]*>(.*?)(?=<div\s+class="art-\d+\s+cel1|$)',
        html,
        re.DOTALL,
    )

    dmc_links = []
    seen_urls = set()

    for match in blocks:
        art_id = match.group(1)
        content = match.group(2)

        # Extraire le premier lien _aXXXXX.html dans ce bloc
        link_match = re.search(r'href="(/[^"]*_a(\d+)\.html)"', content)
        if not link_match:
            continue

        url_path = link_match.group(1)

        # Éviter les doublons
        if url_path in seen_urls:
            continue
        seen_urls.add(url_path)

        full_url = BASE_URL + url_path
        dmc_links.append(full_url)

    return dmc_links


def extract_dmc_data(html, url):
    """Extrait les données structurées d'une fiche DMC."""
    data = {"url": url}

    # Titre (og:title)
    title_match = re.search(r'og:title"\s*content="([^"]*)"', html)
    if title_match:
        title = title_match.group(1).strip()
        # Nettoyer le préfixe "DMC Pays" si présent, sinon garder tel quel
        data["title"] = title
    else:
        data["title"] = ""

    # Description (og:description)
    desc_match = re.search(r'og:description"\s*content="([^"]*)"', html)
    data["description"] = desc_match.group(1).strip() if desc_match else ""

    # Image principale (og:image)
    img_match = re.search(r'og:image"\s*content="([^"]*)"', html)
    data["image"] = img_match.group(1).strip() if img_match else ""

    # Destinations
    dest_match = re.search(r"DESTINATIONS\s*:\s*(.*?)Date de cr", html, re.DOTALL)
    destinations = []
    if dest_match:
        dest_text = re.sub(r"<[^>]+>", " ", dest_match.group(1))
        dest_text = dest_text.replace("&gt;", ">").replace("&amp;", "&")
        # Extraire chaque destination après ">"
        dests_raw = re.findall(r">\s*([A-ZÀ-Ü][^>]*?)(?=\s*>|\s*$)", dest_text)
        for d in dests_raw:
            d = d.strip().rstrip(".")
            if d:
                destinations.append(d)

    data["destinations"] = destinations

    # Coordonnées GPS (basées sur les destinations)
    coords_list = []
    for dest in destinations:
        dest_clean = dest.strip()
        if dest_clean in COUNTRY_COORDS:
            lat, lng = COUNTRY_COORDS[dest_clean]
            coords_list.append({"destination": dest_clean, "lat": lat, "lng": lng})
        else:
            # Essayer une correspondance partielle
            found = False
            for key, (lat, lng) in COUNTRY_COORDS.items():
                if key.lower() in dest_clean.lower() or dest_clean.lower() in key.lower():
                    coords_list.append({"destination": dest_clean, "lat": lat, "lng": lng})
                    found = True
                    break
            if not found:
                print(f"  [WARN] Destination inconnue (pas de coordonnées GPS): '{dest_clean}'")
                coords_list.append({"destination": dest_clean, "lat": None, "lng": None})

    data["coordinates"] = coords_list

    # Continents / zones
    continents = set()
    for dest in destinations:
        dest_clean = dest.strip()
        if dest_clean in CONTINENT_MAP:
            continents.add(CONTINENT_MAP[dest_clean])
        else:
            for key, continent in CONTINENT_MAP.items():
                if key.lower() in dest_clean.lower() or dest_clean.lower() in key.lower():
                    continents.add(continent)
                    break
    data["continents"] = sorted(list(continents))

    # Date de création
    date_match = re.search(
        r"Date de cr[ée]ation\s*:?\s*</b>\s*(?:<br\s*/?>)?\s*\n?\s*(.+?)(?:\n|\s*<br)",
        html,
    )
    if date_match:
        date_text = re.sub(r"<[^>]+>", "", date_match.group(1)).strip()
        data["date_creation"] = date_text
    else:
        data["date_creation"] = ""

    # Pictogrammes / Tags
    pictos_raw = re.findall(r"docs/FicheDMC/picto_([^\"\.]+)", html)
    # Dédoublonner tout en gardant l'ordre
    seen = set()
    pictos = []
    for p in pictos_raw:
        if p not in seen:
            seen.add(p)
            pictos.append(p)

    # Organiser par catégorie
    tags = {"clientele": [], "prestations": [], "activites": []}
    for picto_id in pictos:
        if picto_id in PICTO_CATEGORIES:
            info = PICTO_CATEGORIES[picto_id]
            cat = info["category"]
            tags[cat].append(
                {
                    "id": picto_id,
                    "label": info["label"],
                }
            )
        else:
            # Picto inconnu, on l'ajoute quand même dans activités
            tags["activites"].append(
                {
                    "id": picto_id,
                    "label": picto_id.replace("_", " ").title(),
                }
            )

    data["tags"] = tags

    return data


def is_dmc_fiche(html):
    """
    Vérifie qu'une page est bien une fiche DMC et non un article d'actualité.
    Une fiche DMC contient la section DESTINATIONS et des pictogrammes.
    """
    has_destinations = bool(re.search(r"DESTINATIONS\s*:", html))
    has_pictos = bool(re.search(r"docs/FicheDMC/picto_", html))
    return has_destinations and has_pictos


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("SCRAPING DMC - DestiMaG / TourMaG")
    print(f"Démarré le {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    # Étape 1 : Charger la page annuaire
    print("\n[1/3] Chargement de la page annuaire...")
    annuaire_html = fetch_page(ANNUAIRE_URL)
    if not annuaire_html:
        print("ERREUR: Impossible de charger la page annuaire. Abandon.")
        sys.exit(1)

    # Étape 2 : Extraire les liens des fiches DMC
    print("[2/3] Extraction des liens vers les fiches DMC...")
    all_links = extract_dmc_links(annuaire_html)
    print(f"  → {len(all_links)} liens trouvés dans l'annuaire")

    # Étape 3 : Scraper chaque fiche
    print(f"[3/3] Scraping de chaque fiche DMC (délai de {REQUEST_DELAY}s entre chaque)...")
    dmc_list = []
    skipped = 0

    for i, link in enumerate(all_links, 1):
        print(f"  [{i}/{len(all_links)}] {link}")
        time.sleep(REQUEST_DELAY)

        html = fetch_page(link)
        if not html:
            skipped += 1
            continue

        # Vérifier que c'est bien une fiche DMC
        if not is_dmc_fiche(html):
            print(f"    → Pas une fiche DMC (article d'actu ?), ignoré.")
            skipped += 1
            continue

        dmc_data = extract_dmc_data(html, link)
        dmc_list.append(dmc_data)
        print(f"    → OK: {dmc_data['title']} ({', '.join(dmc_data['destinations'])})")

    # Générer le JSON
    output = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": ANNUAIRE_URL,
            "total_dmc": len(dmc_list),
            "total_links_found": len(all_links),
            "skipped": skipped,
        },
        "dmc": dmc_list,
    }

    # Écrire le fichier
    import os
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"TERMINÉ !")
    print(f"  → {len(dmc_list)} fiches DMC extraites")
    print(f"  → {skipped} liens ignorés (articles d'actu ou erreurs)")
    print(f"  → Fichier généré : {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
