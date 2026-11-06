"""sokaklar_ham.json + sinif.jsonl -> site/veri/ozet.json, site/veri/noktalar.bin, veri/denetim_ornek.csv

Sayım birimi tekil sokak (aynı öz ad + ~3 km hücre). "Kişi" = modelin k=1 dediği adlar; k=2 (tek başına ad ya da
soyadına benzeyen, belirsiz) oranlara katılmaz, ayrı raporlanır. Kadın oranı = kadın / (kadın + erkek); cinsiyeti
adından anlaşılmayanlar paydaya girmez.
"""
import csv
import json
import random
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "araclar"))
from temizle import HARITA, IL  # noqa: E402

SITE = KOK / "site" / "veri"
# 0 = kişi değil, 2 = belirsiz (tek başına sözcük)
ELLE = {"Gazi": 2, "Yıldırım": 2, "Beyazıt": 2, "Timur": 2, "Atilla": 2, "Başöğretmen": 2, "Pembe Gül": 0, "Pembe Ay": 0, "Su Akar": 0, "Şehrazat": 0,
        "Konuralp Fırın": 0, "Soğanağa Camii": 0, "Çiçek Sever": 2, "Atam": 2}


def noktada(lat, lon, halka):
    ic = False
    j = len(halka) - 1
    for i in range(len(halka)):
        xi, yi = halka[i]; xj, yj = halka[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            ic = not ic
        j = i
    return ic


def il_bulucu():
    h = json.loads(HARITA.read_text(encoding="utf-8"))
    iller = []
    for plaka, halka in h["sinir"]:
        xs = [p[0] for p in halka]; ys = [p[1] for p in halka]
        iller.append((plaka, halka, min(xs), max(xs), min(ys), max(ys), sum(xs) / len(xs), sum(ys) / len(ys)))
    onbellek = {}

    def bul(lat, lon):
        k = (round(lat, 2), round(lon, 2))
        if k in onbellek:
            return onbellek[k]
        sonuc = None
        for p, ha, x0, x1, y0, y1, _, _ in iller:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and noktada(lat, lon, ha):
                sonuc = p
                break
        if sonuc is None:  # kıyı: sadeleştirilmiş sınırın dışında kalan nokta, en yakın halka köşesinin ili
            en, sonuc = 1e9, None
            for p, ha, x0, x1, y0, y1, _, _ in iller:
                if x0 - .3 <= lon <= x1 + .3 and y0 - .3 <= lat <= y1 + .3:
                    for x, y in ha[::3]:
                        d = (x - lon) ** 2 + (y - lat) ** 2
                        if d < en:
                            en, sonuc = d, p
        onbellek[k] = sonuc
        return sonuc
    return bul, h["sinir"]


def main():
    sinif = {}
    for s in open(KOK / "veri" / "sinif.jsonl", encoding="utf-8"):
        if s.strip():
            x = json.loads(s)
            sinif[x["n"]] = x
    # Elle düzeltmeler: üst listeleri ve denetim örneğini okurken bulunan model hataları
    for ad, k in ELLE.items():
        if ad in sinif:
            sinif[ad] = {"n": ad, "k": k, "c": sinif[ad].get("c", "?") if k == 2 else "", "t": "", "a": ""}
    ham = json.loads((KOK / "veri" / "sokaklar_ham.json").read_text(encoding="utf-8"))
    bul, sinir = il_bulucu()
    say = Counter()
    il = defaultdict(lambda: Counter())
    kisi_say, kadin_say, tur_say = Counter(), Counter(), Counter()
    il_kadin, il_kisi = defaultdict(Counter), defaultdict(Counter)
    noktalar = []
    eksik = 0
    ad_cins = {}
    for o, t, lat, lon, ham_ad in ham:
        if t == "disi":
            say["disi"] += 1
            continue
        p = bul(lat, lon)
        if p is None:  # Türkiye dışı
            say["disi"] += 1
            continue
        say["sokak"] += 1
        il[p]["sokak"] += 1
        if t == "numara":
            say["numara"] += 1; il[p]["numara"] += 1
            continue
        c = sinif.get(o)
        if not c:
            eksik += 1
            continue
        if c["k"] == 0:
            say["kavram"] += 1
        elif c["k"] == 2:
            say["belirsiz"] += 1
            if c.get("c") == "k":
                say["belirsiz_kadin"] += 1
            elif c.get("c") == "e":
                say["belirsiz_erkek"] += 1
        else:
            cins = c.get("c", "?")
            ad = (c.get("a") or o).strip()
            say["kisi"] += 1; il[p]["kisi"] += 1
            tur_say[c.get("t", "diger")] += 1
            kisi_say[ad] += 1
            ad_cins[ad] = (cins, c.get("t", "diger"))
            il_kisi[p][ad] += 1
            if cins == "k":
                say["kadin"] += 1; il[p]["kadin"] += 1; kadin_say[ad] += 1; il_kadin[p][ad] += 1
            elif cins == "e":
                say["erkek"] += 1; il[p]["erkek"] += 1
            else:
                say["bilinmez"] += 1
            if cins in "ek":
                noktalar.append((lat, lon, cins == "k"))
    say["eksik"] = eksik
    plaka_ad = {i + 1: a for i, a in enumerate(IL)}
    iller = []
    for p in sorted(il):
        c = il[p]
        iller.append({"p": p, "ad": plaka_ad.get(int(p), str(p)), **{k: c[k] for k in ("sokak", "numara", "kisi", "kadin", "erkek")},
                      "kadinlar": il_kadin[p].most_common(8), "kisiler": il_kisi[p].most_common(8)})
    ozet = {"say": dict(say), "turler": tur_say.most_common(),
            "kisiler": [[a, n, *ad_cins[a]] for a, n in kisi_say.most_common(60)],
            "kadinlar": [[a, n, ad_cins[a][1]] for a, n in kadin_say.most_common(60)],
            "iller": iller, "osm_tarih": "2026-11-04"}
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "ozet.json").write_text(json.dumps(ozet, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (SITE / "sinir.json").write_text(json.dumps([[p, [[round(x, 3), round(y, 3)] for x, y in r]] for p, r in sinir], separators=(",", ":")), encoding="utf-8")
    # nokta dosyası: enlem/boylam uint16 (Türkiye kutusuna ölçekli), üst bit kadın
    random.seed(1); random.shuffle(noktalar)
    B0, B1, L0, L1 = 35.5, 42.3, 25.5, 45.0
    with open(SITE / "noktalar.bin", "wb") as f:
        for lat, lon, k in noktalar:
            y = int((lat - B0) / (B1 - B0) * 32767); x = int((lon - L0) / (L1 - L0) * 65535)
            f.write(struct.pack("<HH", x, max(0, min(32767, y)) | (0x8000 if k else 0)))
    print({k: say[k] for k in sorted(say)})
    print("kadın oranı", round(say["kadin"] / (say["kadin"] + say["erkek"]) * 100, 2), "%", "nokta", len(noktalar))
    print("en çok:", kisi_say.most_common(15)); print("kadın:", kadin_say.most_common(25)); print(tur_say.most_common())
    # elle denetim örneği
    random.seed(42)
    k1 = [x for x in sinif.values() if x["k"] == 1]
    with open(KOK / "veri" / "denetim_ornek.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["ad", "k", "c", "t", "a"])
        for x in random.sample(k1, 150) + random.sample([x for x in k1 if x.get("c") == "k"], 100) + random.sample([x for x in sinif.values() if x["k"] == 0], 100):
            w.writerow([x["n"], x["k"], x.get("c", ""), x.get("t", ""), x.get("a", "")])


if __name__ == "__main__":
    main()
