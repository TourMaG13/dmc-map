#!/usr/bin/env python3
import json, re, os, xml.etree.ElementTree as ET
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import requests

RSS = "https://www.tourmag.com/xml/syndication.rss?t={tag}"
MAX = 3
HDR = {"User-Agent": "Mozilla/5.0"}
IMG_RE = re.compile(r"<img[^>]+src=.([^ >]+)")

def init_fb():
    sa = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    cred = credentials.Certificate(json.loads(sa)) if sa else credentials.Certificate("service-account.json")
    firebase_admin.initialize_app(cred)
    return firestore.client()

def fetch(tag):
    url = RSS.format(tag=tag)
    try:
        r = requests.get(url, headers=HDR, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        print(f"  ERR: {e}")
        return []
    out = []
    for it in root.findall(".//item")[:MAX]:
        t = it.findtext("title","").strip()
        lk = it.findtext("link","").strip()
        pd = it.findtext("pubDate","").strip()
        ds = it.findtext("description","").strip()
        img = ""
        enc = it.find("enclosure")
        if enc is not None: img = enc.get("url","")
        if not img:
            m = IMG_RE.search(ds)
            if m: img = m.group(1)
        ex = re.sub(r"<[^>]+>","",ds).strip()[:200]
        dt_s = ""
        if pd:
            try:
                dt_s = datetime.strptime(pd[:25].strip(),"%a, %d %b %Y %H:%M:%S").strftime("%d/%m/%Y")
            except ValueError: pass
        if t and lk: out.append({"title":t,"url":lk,"image":img,"date":dt_s,"excerpt":ex})
    return out

def main():
    print(f"RSS Fetcher - {datetime.now().isoformat()}")
    db = init_fb()
    ls = []
    for doc in db.collection("dmc").stream():
        d = doc.to_dict()
        tag = d.get("tag_tourmag","").strip()
        if tag: ls.append({"id":doc.id,"title":d.get("title",""),"tag":tag})
    print(f"Found {len(ls)} DMCs")
    up = 0
   for x in ls:
    print(f"[{x['title']}] {x['tag']}")
    arts = fetch(x["tag"])
    if arts:
        print(f"  -> {len(arts)} articles")
        db.collection("dmc").document(x["id"]).update({
            "latest_news": arts,
            "news_updated_at": firestore.SERVER_TIMESTAMP
        })
        up += 1
    else:
        print("  -> 0")
    print(f"Done {up}/{len(ls)}")

if __name__=="__main__": main()
