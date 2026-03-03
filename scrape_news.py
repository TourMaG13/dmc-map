#!/usr/bin/env python3
import json, re, os, xml.etree.ElementTree as ET
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import requests

RSS_URL = "https://www.tourmag.com/xml/syndication.rss?t={tag}"
MAX_ARTICLES = 3
HEADERS = {"User-Agent": "Mozilla/5.0"}

def init_firebase():
    sa = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    cred = credentials.Certificate(json.loads(sa)) if sa else credentials.Certificate("service-account.json")
    firebase_admin.initialize_app(cred)
    return firestore.client()

def fetch_rss(tag):
    url = RSS_URL.format(tag=tag)
    print(f"  RSS: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        print(f"  ERROR: {e}")
        return []
    articles = []
    for item in root.findall(".//item")[:MAX_ARTICLES]:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()
        desc = item.findtext("description", "").strip()
        image = ""
        enc = item.find("enclosure")
        if enc is not None: image = enc.get("url", "")
        if not image:
            m = re.search(r'<img[^>]+src=["']([^"']+)', desc)
            if m: image = m.group(1)
        excerpt = re.sub(r'<[^>]+>', '', desc).strip()[:200]
        date_str = ""
        if pub_date:
            try:
                dt = datetime.strptime(pub_date[:25].strip(), "%a, %d %b %Y %H:%M:%S")
                date_str = dt.strftime("%d/%m/%Y")
            except ValueError: pass
        if title and link:
            articles.append({"title": title, "url": link, "image": image, "date": date_str, "excerpt": excerpt})
    return articles

def main():
    print(f"TourMag RSS - {datetime.now().isoformat()}")
    db = init_firebase()
    dmc_list = []
    for doc in db.collection("dmc").stream():
        data = doc.to_dict()
        tag = data.get("tag_tourmag", "").strip()
        if tag: dmc_list.append({"id": doc.id, "title": data.get("title", ""), "tag": tag})
    print(f"Found {len(dmc_list)} DMCs with tag_tourmag")
    updated = 0
    for dmc in dmc_list:
        print(f"[{dmc['title']}] tag={dmc['tag']}")
        articles = fetch_rss(dmc["tag"])
        if articles:
            print(f"  -> {len(articles)} articles")
            db.collection("dmc").document(dmc["id"]).update({"latest_news": articles, "news_updated_at": firestore.SERVER_TIMESTAMP})
            updated += 1
        else: print("  -> No articles")
    print(f"Done. {updated}/{len(dmc_list)} updated.")

if __name__ == "__main__": main()