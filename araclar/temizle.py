"""yollar.csv -> veri/sokaklar.json (tekil sokaklar) + veri/ozler.json (sınıflandırılacak farklı adlar)

Tekil sokak: aynı öz ad + aynı ~3 km'lik ızgara hücresi (OSM bir sokağı birçok parçaya böler).
Öz ad: tür sözcükleri (Sokak, Caddesi...), sıra numaraları ve sonundaki numaralar atılmış ad.
Kapsam dışı: şehirlerarası yollar ("A - B Yolu"), kavşak, köprü, site, kümeevleri.
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
HARITA = Path.home() / "Desktop" / "portfolyo" / "veri" / "kart-harita.json"
IL = ("Adana Adıyaman Afyonkarahisar Ağrı Amasya Ankara Antalya Artvin Aydın Balıkesir Bilecik Bingöl Bitlis Bolu Burdur Bursa Çanakkale Çankırı Çorum Denizli "
      "Diyarbakır Edirne Elazığ Erzincan Erzurum Eskişehir Gaziantep Giresun Gümüşhane Hakkari Hatay Isparta Mersin İstanbul İzmir Kars Kastamonu Kayseri Kırklareli Kırşehir "
      "Kocaeli Konya Kütahya Malatya Manisa Kahramanmaraş Mardin Muğla Muş Nevşehir Niğde Ordu Rize Sakarya Samsun Siirt Sinop Sivas Tekirdağ Tokat Trabzon Tunceli Şanlıurfa "
      "Uşak Van Yozgat Zonguldak Aksaray Bayburt Karaman Kırıkkale Batman Şırnak Bartın Ardahan Iğdır Yalova Karabük Kilis Osmaniye Düzce").split()

TUR = r"(?:sokağı|sokagi|sokak|sok\.?|sk\.?|caddesi|cadde|cad\.?|cd\.?|bulvarı|bulvar|blv\.?|çıkmazı|çıkmaz|meydanı|yolu|yol|geçidi|geçit|aralığı|aralık)"
SONDAN = re.compile(rf"(?:\s+{TUR})+\s*$", re.I)
KAPSAM_DISI = re.compile(r"kümeevler|küme evler|kavşağı|köprüsü|tüneli|sitesi|evleri?$|çevreyolu|karayolu|otoyol|yanyol|içyol|otoban|viyadük|\bblok\b", re.I)


def kucuk(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def oz(ad):
    """Dönüş: (tür, öz). tür: 'numara' | 'disi' | 'ad'"""
    a = re.sub(r"\s+", " ", ad).strip()
    if KAPSAM_DISI.search(a) or re.search(r"\s[-–]\s?\S|\S-\S.*yolu$", a, re.I) and re.search(r"yolu?$", a, re.I):
        return "disi", None
    if re.search(r"yolu?$", a, re.I):  # "Salkımlı yolu" köy yolları: kişi adı değil, kapsam dışı
        return "disi", None
    a = SONDAN.sub("", a).strip()
    # numaralar: "554", "1545. Çıkmaz", "244/2", "Haliliye 49", "4. Çetin", "Sanayi 18"
    a2 = re.sub(r"\b\d+(?:[./]\d*)*\.?(?:\s*nolu|\s*no\.?)?", " ", a, flags=re.I)
    a2 = re.sub(r"\s+", " ", a2).strip(" .-/")
    if not a2 or not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]{2}", a2):
        return "numara", None
    return "ad", a2


def main():
    h = json.loads(HARITA.read_text(encoding="utf-8"))
    print("harita anahtarları:", list(h)[:6])
    gorulen, say = {}, Counter()
    for r in csv.DictReader(open(KOK / "veri" / "yollar.csv", encoding="utf-8")):
        t, o = oz(r["ad"])
        lat, lon = float(r["lat"]), float(r["lon"])
        hucre = (round(lat / 0.03), round(lon / 0.03))
        k = (kucuk(o) if o else "#" + kucuk(r["ad"]), hucre, t)
        if k not in gorulen:
            gorulen[k] = (o, t, lat, lon, r["ad"])
            say[t] += 1
    print(say)
    (KOK / "veri" / "sokaklar_ham.json").write_text(json.dumps(list(gorulen.values()), ensure_ascii=False), encoding="utf-8")
    ozler = Counter(v[0] for v in gorulen.values() if v[1] == "ad")
    (KOK / "veri" / "ozler.json").write_text(json.dumps(ozler.most_common(), ensure_ascii=False), encoding="utf-8")
    print("farklı öz ad:", len(ozler), ozler.most_common(30))


if __name__ == "__main__":
    main()
