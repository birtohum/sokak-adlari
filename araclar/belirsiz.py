"""Belirsiz (k=2) tek sözcüklü adları ayırır: veri/belirsiz.jsonl
 s=1: adın dışında yaygın bir sözcük anlamı da var (Gül, Çiğdem, Barış, Zafer, Doğan, Aydın, Kartal)
 s=0: Türkçede neredeyse yalnızca kişi adı (Elif, Merve, Burak, Emre, Hakan)
 s=2: yer adı ya da soyadı gibi (Demirtaş, Peker)
Sokak adı olarak "s=0" sözcükler büyük olasılıkla bir kişiyi ya da kişi adını anar; orta tahmin için kullanılır.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import siniflandir as S

CIKTI = S.KOK / "veri" / "belirsiz.jsonl"
ISTEM = """Türkiye'de sokak adı olan tek sözcükler veriyorum. Her biri için:
s=1: kişi adı olmanın yanında günlük dilde yaygın bir sözcük ya da yer anlamı var; bir sokağa bu anlamla da verilebilir (Gül, Çiğdem, Yasemin, Bahar, Barış, Zafer, Doğan, Aydın, Kartal, Ada, Nur, Sultan, Hayat, Fırat, Ege).
s=0: Türkçede neredeyse yalnızca kişi adı olarak kullanılır, başka yaygın anlamı yok (Elif, Merve, Zeynep, Burcu, Burak, Emre, Hakan, Serdar, Oğuzhan).
s=2: soyadı ya da yer adı gibi duruyor, ad değil (Demirtaş, Peker, Gündoğdu, Karadağ).
Yalnızca JSON döndür: {"s":[{"n":"ad","s":0}, ...]} verilen sırayla.

ADLAR:
"""
S.ISTEM = ISTEM


def is_(parti):
    try:
        y = S.sor(parti)
    except Exception as h:  # noqa: BLE001
        print("hata", repr(h)[:100], flush=True)
        return 0
    ok = [x for x in y if x.get("n") in set(parti) and x.get("s") in (0, 1, 2)]
    with S._kilit, open(CIKTI, "a", encoding="utf-8") as f:
        for x in ok:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    return len(ok)


def main():
    adlar = [json.loads(s) for s in open(S.CIKTI, encoding="utf-8") if s.strip()]
    hedef = [x["n"] for x in adlar if x["k"] == 2 and x.get("c") in ("e", "k")]
    bitti = {json.loads(s)["n"] for s in open(CIKTI, encoding="utf-8")} if CIKTI.exists() else set()
    kalan = [a for a in hedef if a not in bitti]
    print("hedef", len(hedef), "kalan", len(kalan), flush=True)
    with ThreadPoolExecutor(12) as ex:
        print("bitti", sum(ex.map(is_, [kalan[i:i + 50] for i in range(0, len(kalan), 50)])), round(S.harcanan[0], 3))


if __name__ == "__main__":
    main()
