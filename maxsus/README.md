# `/maxsus` — reaktivatsiya landing page

SMS kampaniyasi uchun izolyatsiyalangan conversion sahifasi (TZ: 2026-08-31).
Bitta o'zi yetarli HTML fayl — build step, framework, tashqi JS kutubxona yo'q.
Logotip faylga inline qilingan, shuning uchun sahifa **bitta HTTP so'rov** bilan ochiladi.

```
maxsus/
  index.html        ← sahifaning o'zi (CSS + JS ichida)
  video-poster.svg  ← VAQTINCHALIK poster; haqiqiy videoning 1-kadri bilan almashtiriladi
  README.md         ← shu fayl
```

---

## 1. Sozlamalar — `index.html` ichidagi `CONFIG`

Skript boshidagi `CONFIG` obyektida hammasi bir joyda:

| Kalit | Hozirgi qiymat | Nima qilish kerak |
|---|---|---|
| `checkoutUrl` | `https://myteacher.uz/checkout` | **⚠️ PLACEHOLDER.** Haqiqiy veb-checkout tayyor bo'lgach almashtiriladi. |
| `fallbackDeadlineIso` | `2026-09-07T23:59:59+05:00` | Kampaniyaning haqiqiy tugash vaqti. Backend ulanmaguncha countdown shunga qarab ishlaydi. |
| `sessionEndpoint` | `''` (o'chiq) | Backend tayyor bo'lgach to'ldiriladi — countdown server vaqtiga bog'lanadi. |
| `trackEndpoint` | `''` (o'chiq) | Analitika endpointi. Bo'sh bo'lsa event'lar faqat `window.dataLayer` ga tushadi (GTM/Meta Pixel o'qiy oladi). |
| `requireToken` | `false` | `true` qilinsa — `?ref=` token'siz kirganda chegirma ko'rsatilmaydi, standart narx chiqadi. |

CTA bosilganda ochiladigan manzil: `checkoutUrl?plan=mentor|mentorsiz&ref=<token>`.

---

## 2. Backend kontrakti (hali qurilmagan)

### `GET {sessionEndpoint}?ref=<token>`

```json
{
  "deadlineIso":   "2026-09-07T23:59:59+05:00",
  "serverTimeIso": "2026-09-03T14:20:05+05:00",
  "state":         "offer"
}
```

- `deadlineIso` — kampaniya tugash vaqti. **Cookie/localStorage ishlatilmaydi** (TZ 5): sahifa
  yangilansa ham, boshqa qurilmadan ochilsa ham countdown reset bo'lmaydi.
- `serverTimeIso` — brauzer soati noto'g'ri qo'yilgan bo'lsa ham to'g'ri sanashi uchun.
  Sahifa `serverTime − Date.now()` farqini hisoblab, shu tuzatma bilan sanaydi.
- `state` — `"offer"` yoki `"standard"`. `"standard"` kelsa chegirma bloklari darhol yashiriladi.

So'rov muvaffaqiyatsiz bo'lsa sahifa `fallbackDeadlineIso` bilan davom etadi — **hech qachon
oq ekran yoki buzilgan holat chiqmaydi.**

CORS: sahifa `myteacher.uz` da, API boshqa domenda (masalan `ai.myteacher.uz`) bo'lsa,
backendda `Access-Control-Allow-Origin: https://myteacher.uz` kerak.

### `POST {trackEndpoint}` — analitika (TZ 6)

`navigator.sendBeacon` orqali JSON yuboriladi:

```json
{ "event": "cta_click", "ref": "<token>", "page": "maxsus",
  "ts": "2026-09-03T14:20:05.123Z", "plan": "mentor", "position": "plans", "state": "offer" }
```

Yuboriladigan event'lar:

| Event | Qo'shimcha maydonlar | TZ 6-bo'limdagi talab |
|---|---|---|
| `page_view` | `hasToken`, `referrer` | Sahifaga kirish (token bilan) |
| `video_play`, `video_unmute`, `video_pause` | `at` (soniya) | — |
| `video_progress` | `percent`: 10/25/50/75/95 | Video necha % ko'rilgani |
| `video_complete` | — | Oxirigacha ko'rilgani |
| `video_error` | `src` | Video yuklanmagani (soft-launch nazorati) |
| `cta_click` | `plan`, `position`, `state` | **MENTOR va MENTORSIZ alohida** |
| `checkout_start` | `plan`, `state` | Checkout boshlangani |
| `payment_success` | `plan` | To'lov yakunlangani — pastga qarang |
| `scroll_depth` | `percent`: 25/50/75/100 | Qayerda tashlab ketishayotgani |
| `faq_open` | `index` | — |
| `offer_expired` | — | Muddat tugab standart holatga o'tgani |
| `sticky_cta_shown` | — | — |

Har bir event `ref` token bilan yuboriladi — SMS hook varianti (D/E/F) → landing view →
tarif tanlash → to'lov zanjiri bitta token orqali kuzatiladi.

**`payment_success`** — to'lovdan keyin foydalanuvchi `/maxsus?ref=<token>&paid=1&plan=mentor`
ga qaytarilsa qayd etiladi. Ishonchli hisob backend webhook'ida (Payme/Click) bo'lishi kerak;
sahifadagi bu event faqat qo'shimcha signal.

---

## 3. nginx — MUHIM

Hozir `myteacher.uz` da nginx **har qanday yo'lga** root `index.html` ni qaytaradi.
Ya'ni hech narsa qilinmasa `myteacher.uz/maxsus` **asosiy saytni** ko'rsatadi.

Server blokiga catch-all `location /` dan **oldin** qo'shiladi:

```nginx
location = /maxsus  { return 301 /maxsus/; }

location /maxsus/ {
    alias /var/www/<sayt-root>/maxsus/;
    index index.html;
    try_files $uri $uri/ /maxsus/index.html;

    # Qidiruv tizimlariga chiqmasin (TZ 3, 9.1.1) — meta tegga qo'shimcha himoya
    add_header X-Robots-Tag "noindex, nofollow" always;

    # Video/poster keshlansin, HTML keshlanmasin (deadline holati eskirmasligi uchun)
    location ~* \.(mp4|webm|vtt|svg|jpg|webp)$ { expires 30d; add_header Cache-Control "public"; }
    location ~* \.html$ { add_header Cache-Control "no-cache"; }
}
```

`robots.txt` ga ham qo'shish tavsiya etiladi:

```
Disallow: /maxsus
```

---

## 4. Deploy

> ### ⚠️ `promo.mp4` git'da YO'Q
> Video (23 MB) `.gitignore` da. Ya'ni `git pull` bilan deploy qilinganda **video kelmaydi** —
> uni serverga bir marta alohida yuklash kerak:
> ```bash
> scp maxsus/promo.mp4 root@46.8.195.59:/var/www/<sayt-root>/maxsus/
> ```
> Unutilsa sahifa buzilmaydi — poster ko'rinadi va "Video hozircha yuklanmadi" yozuvi chiqadi,
> `video_error` eventi qayd etiladi. Lekin konversiya nolga tushadi, shuning uchun deploydan
> keyin ALBATTA tekshiring.

**Bu repoda GitHub Actions yo'q — main'ga merge qilish jonli saytni yangilamaydi.**
Deploy qo'lda: `maxsus/` papkasini **butunlay** (index.html + video-poster + video fayllar)
serverdagi sayt root'iga ko'chiring. Yetishmayotgan fayl 404 bermaydi — nginx HTML qaytaradi
va rasm/video jimgina buziladi, shuning uchun deploydan keyin har bir faylni tekshiring:

```bash
curl -sI https://myteacher.uz/maxsus/promo.mp4 | head -3   # Content-Type: video/mp4 bo'lishi shart
```

---

## 5. Video

**Manba (master):** `IMG_9676.MOV` — 1080x1920, HEVC, 30 fps, 11 Mbps, **134.6 s**, 182 MB.
CapCut outro'siz eksport (2026-09-03). Undan oldingi, oxirida 2 soniyalik CapCut logotipi bo'lgan
versiya almashtirildi — qayta kodlashda albatta shu fayldan foydalaning.
`.gitignore` orqali git'dan chetlatilgan. **Saytga hech qachon shu fayl qo'yilmaydi.**

HEVC + `.MOV` brauzerlarda ishonchli emas (Android Chrome'da qurilmaga bog'liq, Firefox'da
deyarli yo'q), shuning uchun H.264 MP4 ga o'girish majburiy — optimizatsiya emas.

Ishlatilgan buyruqlar:

```bash
ffmpeg -y -i IMG_9676.MOV -vf "scale=720:1280:flags=lanczos" -c:v libx264 -profile:v high -level 4.0 -crf 25 -maxrate 1500k -bufsize 3000k -preset slow -pix_fmt yuv420p -g 60 -c:a aac -b:a 96k -ac 1 -ar 44100 -movflags +faststart promo.mp4
```

```bash
ffmpeg -y -ss 4 -i IMG_9676.MOV -frames:v 1 -vf "scale=720:1280:flags=lanczos" -q:v 8 video-poster.jpg
```

- `-movflags +faststart` — moov atomi fayl boshiga ko'chadi, ya'ni video **to'liq yuklanishini
  kutmasdan** boshlanadi. Bu TZ 5-bo'limdagi 2-3 soniya talabi uchun hal qiluvchi.
- `-g 60` — har 2 soniyada keyframe, tez seek qilish uchun.
- `-ac 1` — bitta so'zlovchi uchun mono yetarli, bitrate tejaydi.
- Poster 4-soniyadan olingan: gapiruvchi kameraga qarab turgan, subtitrda ochilish jumlasi
  ko'rinadigan kadr.

**VP9 `.webm` qo'shilmadi.** ~20% kichikroq bo'lardi, lekin kodlash juda uzoq va MP4 hamma
joyda ishlaydi. Keyinchalik qo'shilsa, `<source>` MP4 dan **oldin** qo'yiladi.

**Subtitr** videoga kuydirilgan, shuning uchun `<track>` fayl kerak emas — olib tashlandi.

### Videoni qayerdan berish

| Bosqich | Yechim | Taxminiy trafik |
|---|---|---|
| Soft-launch (500-1000) | O'z serveringiz — bir marta `scp` | ~13 GB |
| 1-kohort (10 000) | CDN tavsiya etiladi | ~66 GB |
| To'liq (50 000) | **CDN majburiy** (Bunny.net) | ~330 GB |

Asosiy xavf umumiy trafik emas, **bir vaqtdagi zarba**: SMS bir zumda ketadi va 500 kishi
bir paytda ochsa ~600 Mbps kerak bo'ladi. VPS porti buni ko'tarmasa video hammaga uziladi.
Serverning port tezligi tekshirilsin.

CDN'ga o'tganda `index.html` da faqat bitta qator o'zgaradi:
`<source src="promo.mp4">` → `<source src="https://<zona>.b-cdn.net/promo.mp4">`

**Video git'ga qo'shilmasin** — har deployda repo tarixiga yozilib, repo shishib ketadi.

---

## 5b. Marketingdan kutilayotgan qolgan kontent

`index.html` ichida `<!-- MARKETING: ... -->` izohlari va `[kvadrat qavs]` ichidagi
placeholder matnlar qo'yilgan. To'ldirilishi kerak:

- [x] ~~Video fayl~~ — tayyor
- [x] ~~Poster~~ — tayyor
- [ ] **Tarif matnlari** — nom, narx, xizmatlar ro'yxati (TZ 8.1). Hozirgilar taxminiy.
- [x] ~~2-3 ta REAL testimonial~~ — `sharhlar.html` dan olindi (manba: "MyTeacher | FEEDBACKS"
      Telegram kanali). Tanlanganlar: **Gulmira R.** (A2 -> B1, nazoratchi ustoz Azizbek),
      **Nigina A.** (mentor Shoxista, speaking), **Nigora N.** (CEFR B2).
      Matnlar qisqartirilgan, so'zlar o'zgartirilmagan; tushirilgan joylar `[...]` bilan belgilangan.
      **Yulduzli reyting qo'yilmagan** — asosiy saytda ham ataylab olib tashlangan (commit `ee6d4f0`:
      453 ta real xabardan atigi 2 tasida reyting bor, 4.9/5 da asos yo'q). Landing'da ham qaytarilmasin.
      ⚠️ **Nigora N.** kuchli natija (CEFR B2) beradi, lekin mentor mahsulotini bevosita tilga olmaydi.
      TZ 8.1 qat'iy "MENTOR mahsulotidan" desa, uni **Zulfiya** (15-iyul 2025, "mentorlarni kuzatdim
      — juda zo'r") bilan almashtirish mumkin.
- [ ] **"Nega bu narx?"** — bitta qisqa jumla (TZ 8.3)
- [ ] **FAQ javoblari** — sahifadagilar `[QORALAMA]` deb belgilangan, tasdiqlanishi kerak (TZ 8.3)

⚠️ **Xabar mosligi:** video "bu navbatdagi 50% chegirma degan reklama emas" deb boshlanadi,
sahifa esa chizilgan narx + countdown bilan ochiladi — ya'ni aynan chegirma reklamasiga
o'xshaydi. "Nega bu narx?" bloki shu ziddiyatni yopishi kerak; matni videodagi sabab bilan
bir xil bo'lsin.

## 6. Ishga tushirishdan oldingi tekshiruv ro'yxati

- [ ] `?ref=<token>` bilan ochilganda countdown to'g'ri sanaydi
- [ ] Sahifani yangilaganda countdown reset bo'lmaydi (backend ulangach)
- [ ] Boshqa qurilmadan ochilganda ham bir xil vaqt ko'rsatadi
- [ ] Muddat tugagach: countdown va chegirma yo'qoladi, standart narx chiqadi *(tekshirilgan ✓)*
- [ ] Video mobil brauzerda ovozsiz avtoplay bo'ladi, bosilganda ovoz yoqiladi
- [ ] MENTOR va MENTORSIZ tugmalari alohida-alohida qayd etiladi
- [ ] CTA to'g'ridan-to'g'ri veb-checkout'ni ochadi (ilova do'koniga emas)
- [ ] To'lovdan keyin telefon raqami bazaga tushadi (backend)
- [ ] Sahifada asosiy saytga olib ketadigan birorta havola yo'q *(tekshirilgan ✓ — logotip ham bosilmaydi)*
- [ ] `noindex` ishlayapti: `curl -I https://myteacher.uz/maxsus/ | grep -i robots`
- [ ] Real telefon raqami bilan to'liq funnel: SMS → landing → checkout → to'lov → ilova
