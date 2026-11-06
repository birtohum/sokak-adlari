# Sokaklarımız kimin adını taşıyor?

**Site:** https://birtohum.github.io/sokak-adlari/

OpenStreetMap'teki Türkiye sokaklarını saydım: kaçının adı yok, kaçı bir kişinin adını taşıyor, o kişilerin kaçı kadın.

**Sonuç (OSM 4 Kasım 2026):** 231.889 tekil sokak. %40'ının (92.785) adı yok, yalnız numarası var. Adı açıkça bir kişiyi anan 26.181 sokağın 1.002'si kadın, 24.712'si erkek: **kadın oranı %3,9**. En çok sokağa adı verilen kişi Atatürk (1.114), en çok sokağa adı verilen kadın Zübeyde Hanım (124).

## Yöntem

1. `araclar/osm_cek.py`: Geofabrik Türkiye dosyasından adlandırılmış yollar (410 bin parça).
2. `araclar/temizle.py`: tür sözcükleri ve numaralar atılır; aynı öz ad + yaklaşık 3 km'lik hücre tek sokak sayılır. Şehirlerarası yol, kavşak, köprü, site, kümeevleri kapsam dışı.
3. `araclar/siniflandir.py`: 42.071 farklı ad dil modeline (Meta Muse Spark) sorulur: kişi / kişi değil / belirsiz, cinsiyet, tür. Maliyet 0,62 $.
4. `araclar/analiz.py`: sayım, il ataması, elle düzeltme listesi (`ELLE`).

## Ne kadar güvenilir?

- **Elle denetim:** rastgele 150 “kişi” kararından 2'si hatalı, 100 “kadın” kararından 2'si hatalı ya da şüpheli, 100 “kişi değil” kararında kaçak görülmedi. Denetimi tek kişi yaptı, örnek küçük (`veri/denetim_ornek.csv`).
- **En büyük belirsizlik:** “Gül, Çiğdem, Yasemin, Murat, Barış” gibi tek sözcüklü 40.528 sokak hem ad hem sözcük olabildiği için sayılmadı. Hepsi kişi sayılsaydı oran %26 olurdu. Çoğu çiçek ve doğa adı olduğundan gerçek değer düşük uca yakın olmalı, ama bu ölçülmedi.
- OSM kapsamı illere göre değişir; il sıralaması eğilim gösterir. Resmî adres verisi açık olmadığı için kullanılamadı.

Veri: © OpenStreetMap katkıcıları, ODbL. Türetilen veri (`site/veri/`, `veri/ozler.json`, `veri/sinif.jsonl`) de ODbL. Kod: MIT.
