"""Wikidata'dan (CC0) Türkiye/Osmanlı vatandaşı insanları sayfa sayfa çeker: veri/kisiler.json
  [{ad, q, cins, meslek, dogum, olum, site}]
Tanınmış adlarla sokak eşleştirmek ve ilk addan cinsiyet tablosu çıkarmak için kullanılır.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
VERI = Path(__file__).resolve().parent.parent / "veri"
UA = {"User-Agent": "sokak-adlari/0.1 (github.com/birtohum/sokak-adlari)", "Accept": "application/sparql-results+json"}
SAYFA = 15000


def sorgu(q):
    u = "https://query.wikidata.org/sparql"
    veri = urllib.parse.urlencode({"query": q}).encode()
    for i in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, data=veri, headers=UA), timeout=90))["results"]["bindings"]
        except Exception as h:  # noqa: BLE001
            print("tekrar:", h, flush=True)
            time.sleep(15 * (i + 1))
    raise RuntimeError("Wikidata sorgusu başarısız")


# Önce yalnız kimlik + Türkçe ad + cinsiyet + site sayısı; ayrıntılar yalnız eşleşenler için sonra alınır
KISI = """SELECT ?k ?ad ?cins ?site WHERE {
  { SELECT ?k WHERE { ?k wdt:P27 wd:%s } ORDER BY ?k LIMIT %d OFFSET %d }
  ?k wdt:P31 wd:Q5; rdfs:label ?ad. FILTER(LANG(?ad) = "tr")
  ?k wikibase:sitelinks ?site.
  OPTIONAL { ?k wdt:P21 ?cins }
}"""
DETAY = """SELECT ?k (SAMPLE(?mAd) AS ?meslek) (MIN(?d) AS ?dogum) (MIN(?o) AS ?olum) WHERE {
  VALUES ?k { %s }
  OPTIONAL { ?k wdt:P106 ?m. ?m rdfs:label ?mAd. FILTER(LANG(?mAd) = "tr") }
  OPTIONAL { ?k wdt:P569 ?d } OPTIONAL { ?k wdt:P570 ?o }
} GROUP BY ?k"""


def kisiler():
    gorulen = {}
    for ulke in ("Q43", "Q12560"):  # Türkiye, Osmanlı İmparatorluğu
        ofset = 0
        while True:
            b = sorgu(KISI % (ulke, SAYFA, ofset))
            for x in b:
                q = x["k"]["value"].rsplit("/", 1)[1]
                c = x.get("cins", {}).get("value", "").rsplit("/", 1)[-1]
                gorulen[q] = {"ad": x["ad"]["value"], "q": q, "cins": {"Q6581097": "e", "Q6581072": "k"}.get(c, "?"), "site": int(x["site"]["value"])}
            print(ulke, ofset, len(b), "toplam", len(gorulen), flush=True)
            # alt sorgu insan olmayanları da sayar: boş sayfa gelene kadar ilerle
            if not b and ofset > 0:
                break
            ofset += SAYFA
            if ofset > 400000:
                break
            time.sleep(1)
    return list(gorulen.values())


def main():
    k = kisiler()
    (VERI / "kisiler.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
    print("kişi:", len(k), {c: sum(x["cins"] == c for x in k) for c in "ek?"})


if __name__ == "__main__":
    main()
