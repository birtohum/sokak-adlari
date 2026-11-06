"""veri/ozler.json'daki her farklı sokak adını sınıflandırır: veri/sinif.jsonl (kaldığı yerden devam eder).
Model: muse-spark-1.3-contributor (sokak adları zaten açık OSM verisi). Harcama tavanı: 4 $.
    python araclar/siniflandir.py [--deneme]
"""
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "veri" / "sinif.jsonl"
URL, MODEL = "https://api.meta.ai/v1/chat/completions", "muse-spark-1.3-contributor"
GIR, CIK, TAVAN = 0.10 / 1e6, 0.20 / 1e6, 4.0
PARTI = 50

ISTEM = """Türkiye'deki sokak adları veriyorum (Sokak/Cadde sözcükleri atılmış). Her biri için bir kişiyi anıp anmadığını belirle.

k (kişi mi):
 1 = açıkça belirli bir insanı anıyor: ad+soyad ("Hasan Yurt"), unvanlı kişi ("Şehit Kadir Akgün", "Emin Ali Paşa", "İmam Ömer", "Zübeyde Hanım"), ya da tek adla bilinen tarihî kişi ("Atatürk", "İnönü", "Fatih", "Barbaros", "Mevlana", "Alparslan", "Yunus Emre").
 0 = kişi değil: yer, bitki, kavram, kurum, soyut sözcük ("Cumhuriyet", "Lale", "Okul", "Çınar", "Karacadağ", "Hürriyet").
 2 = belirsiz: tek başına bir ad ya da soyadına benzeyen sözcük, kişi olması da olmaması da mümkün ("Belma", "Peker", "Demirtaş", "Yıldız", "Barış", "Güneş").
c (cinsiyet, yalnız k=1 ve k=2 için): "e" erkek, "k" kadın, "?" adın kendisinden anlaşılmıyor ya da her iki cinse de konuyor. Gül, Yıldız gibi çiçek/doğa adlarında k=2 ise kadın adı olarak yaz. Bilmediğin bir adda "?" yaz, tahmin etme.
t (tür, yalnız k=1 için): "sehit" (Şehit unvanı olan ya da şehit olduğu açık), "asker" (paşa, general, kurtuluş savaşı komutanı, padişah dışı), "padisah" (hükümdar, sultan, han), "siyaset" (Atatürk dahil devlet adamları, siyasetçi), "din" (din büyüğü, sahabe, veli, imam), "edebiyat" (şair, yazar, düşünür), "sanat" (ressam, müzisyen, mimar, oyuncu), "bilim" (bilim insanı, doktor, öğretmen, hekim olarak bilinen), "yerel" (tanınmadığı anlaşılan yerel kişi, muhtar, hayırsever), "diger".
a (yalnız tanınmış tarihî/ünlü kişiyse): adının tam ve standart yazılışı ("Fatih" -> "Fatih Sultan Mehmet", "İnönü" -> "İsmet İnönü"). Tanınmış değilse boş bırak; ünlü olmayan birini ünlü biriyle eşleştirme.

Yalnızca JSON döndür: {"s":[{"n":"ad","k":1,"c":"e","t":"yerel","a":""}, ...]} her ad için bir satır, verilen sırayla, "n" alanı verilen adın aynısı.

ADLAR:
"""


def anahtar():
    for s in open(Path.home() / ".pflow-anahtarlar.env", encoding="utf-8"):
        if s.startswith("META_MODEL_API_KEY="):
            return s.split("=", 1)[1].strip().strip('"')
    raise SystemExit("anahtar yok")


KEY = anahtar()
_kilit = threading.Lock()
harcanan = [0.0]


def sor(adlar):
    govde = {"model": MODEL, "max_tokens": 16000, "reasoning_effort": "low", "response_format": {"type": "json_object"},
             "messages": [{"role": "user", "content": ISTEM + json.dumps(adlar, ensure_ascii=False)}]}
    r = urllib.request.Request(URL, data=json.dumps(govde).encode(), headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    for i in range(6):
        try:
            j = json.load(urllib.request.urlopen(r, timeout=240))
            break
        except urllib.error.HTTPError as h:
            if h.code in (429, 500, 502, 503) and i < 5:
                time.sleep(10 * (i + 1)); continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if i == 5:
                raise
            time.sleep(10 * (i + 1))
    u = j.get("usage", {})
    with _kilit:
        harcanan[0] += u.get("prompt_tokens", 0) * GIR + u.get("completion_tokens", 0) * CIK
    m = j["choices"][0]["message"].get("content")
    if not m:
        raise RuntimeError(f"boş cevap: {j['choices'][0].get('finish_reason')} {u}")
    m = re.sub(r"^```(json)?|```$", "", m.strip(), flags=re.M)
    return json.loads(m[m.find("{"): m.rfind("}") + 1])["s"]


def is_(parti):
    if harcanan[0] >= TAVAN:
        return 0
    try:
        s = sor(parti)
    except Exception as h:  # noqa: BLE001
        print("hata:", repr(h)[:120], flush=True)
        return 0
    istenen = set(parti)
    tamam = [x for x in s if x.get("n") in istenen and x.get("k") in (0, 1, 2)]
    with _kilit, open(CIKTI, "a", encoding="utf-8") as f:
        for x in tamam:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    return len(tamam)


def main():
    ozler = [x[0] for x in json.loads((KOK / "veri" / "ozler.json").read_text(encoding="utf-8"))]
    if "--deneme" in sys.argv:
        import random
        random.seed(11)
        o = ozler[:15] + random.sample(ozler, 35)
        for x in sor(o):
            print(x)
        print("harcama", round(harcanan[0], 5))
        return
    bitti = set()
    if CIKTI.exists():
        bitti = {json.loads(s)["n"] for s in open(CIKTI, encoding="utf-8") if s.strip()}
    kalan = [o for o in ozler if o not in bitti]
    print("kalan", len(kalan), flush=True)
    partiler = [kalan[i:i + PARTI] for i in range(0, len(kalan), PARTI)]
    t, top = time.time(), 0
    with ThreadPoolExecutor(12) as ex:
        for i, n in enumerate(ex.map(is_, partiler), 1):
            top += n
            if i % 20 == 0:
                print(f"{i}/{len(partiler)} parti, {top} ad, {harcanan[0]:.3f} $, {time.time() - t:.0f} sn", flush=True)
    print("bitti", top, round(harcanan[0], 3))


if __name__ == "__main__":
    main()
