"""Türkiye OSM dosyasından adlandırılmış yolları çıkarır: veri/yollar.csv
Sütunlar: ad, tur (highway), lat, lon, uzunluk_yaklasik_m yok; yalnız tek bir temsilî nokta.
Aynı ad birçok parçaya bölünmüş olur; sayım sonradan il + ad üzerinden tekilleştirilir.
"""
import csv
import sys
from pathlib import Path

import osmium

KOK = Path(__file__).resolve().parent.parent
PBF = next((KOK / "veri" / "ham").glob("*.osm.pbf"))
YOL = {"residential", "primary", "secondary", "tertiary", "unclassified", "living_street", "pedestrian", "trunk",
       "primary_link", "secondary_link", "tertiary_link", "service"}


class Y(osmium.SimpleHandler):
    def __init__(self, w):
        super().__init__()
        self.w, self.n = w, 0

    def way(self, y):
        if y.tags.get("highway") not in YOL:
            return
        ad = y.tags.get("name")
        if not ad:
            return
        try:
            d = y.nodes[len(y.nodes) // 2]
            self.w.writerow([ad, y.tags["highway"], round(d.location.lat, 5), round(d.location.lon, 5),
                             y.tags.get("name:etymology:wikidata", "")])
            self.n += 1
        except (osmium.InvalidLocationError, IndexError):
            pass


with open(KOK / "veri" / "yollar.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ad", "tur", "lat", "lon", "etimoloji"])
    h = Y(w)
    h.apply_file(str(PBF), locations=True, idx="flex_mem")
print("yol parçası:", h.n)
