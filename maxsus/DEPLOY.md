# w1.myteacher.uz — deploy buyruqlari

SSH access bor kompyuterda ketma-ket bajariladi. Tartib muhim.

Server: `root@46.8.195.59` · DNS: `w1.myteacher.uz` → `46.8.195.59` (tekshirilgan 2026-09-03)

**Tegilmaydi:** boshqa nginx site fayllari, `mycrm-api` / `lms-api` va boshqa pm2 jarayonlari,
mavjud `/var/www/*` papkalar. Qayta ishga tushiriladigan yagona jarayon — `aiteacher-api`.
nginx `restart` emas, `reload` qilinadi (ochiq ulanishlar uzilmaydi) va faqat `nginx -t` o'tgach.

---

## 0. Ko'rik — hech narsani o'zgartirmaydi

```bash
ssh root@46.8.195.59 'pm2 list; echo "--- NGINX SAYTLAR ---"; ls /etc/nginx/sites-enabled/; echo "--- WWW ---"; ls -la /var/www/; echo "--- W1 BOR? ---"; ls -d /var/www/w1 2>/dev/null || echo yoq'
```

### Eng muhimi: Click kalitining nomi

Qiymatni ko'rsatmaydi, faqat o'zgaruvchi nomini:

```bash
ssh root@46.8.195.59 'grep -oE "^[A-Z_]*CLICK[A-Z_]*" /var/www/aiteacher/aiteacher-api/.env'
```

Javobda **`CLICK_SECRET_KEY`** bo'lishi shart — kod aynan shu nomni o'qiydi.

Boshqacha nomlangan bo'lsa (`CLICK_SECRET`, `CLICK_KEY` va h.k.) **to'xtang va xabar bering.**
Imzo tekshiruvi ishlamasa backend to'lovni umuman qabul qilmaydi — bu ataylab shunday, chunki
tekshiruvsiz "success" qabul qilinsa har kim checkout ochib, to'lamasdan callback yuborib
bepul obuna olardi.

---

## 1. Backend

```bash
ssh root@46.8.195.59 'source ~/.nvm/nvm.sh && cd /var/www/aiteacher/aiteacher-api && git pull && npm run build && pm2 restart aiteacher-api && pm2 list | grep aiteacher'
```

Tekshirish:

```bash
curl -s https://ai.myteacher.uz/api/campaigns/maxsus/session
```

`{"message":"Kampaniya topilmadi",...}` kelishi **to'g'ri** — modul ishlayapti, kampaniya hali
yaratilmagan. `404 Cannot GET` kelsa modul yuklanmagan (build o'tmagan yoki `git pull` eski
commitda qolgan).

---

## 2. nginx — yangi, alohida server bloki

```bash
ssh root@46.8.195.59 'mkdir -p /var/www/w1 && cat > /etc/nginx/sites-available/w1.myteacher.uz <<'"'"'EOF'"'"'
server {
    listen 80;
    listen [::]:80;
    server_name w1.myteacher.uz;
    root /var/www/w1;
    index index.html;
    try_files $uri $uri/ =404;
    add_header X-Robots-Tag "noindex, nofollow" always;
    location = /index.html { add_header Cache-Control "no-cache, must-revalidate"; add_header X-Robots-Tag "noindex, nofollow" always; }
    location ~* \.(mp4|webm)$ { expires 30d; add_header Cache-Control "public"; add_header Accept-Ranges bytes; add_header X-Robots-Tag "noindex, nofollow" always; }
    location ~* \.(jpg|jpeg|webp|png|svg)$ { expires 30d; add_header Cache-Control "public"; add_header X-Robots-Tag "noindex, nofollow" always; }
    access_log /var/log/nginx/w1.access.log;
    error_log  /var/log/nginx/w1.error.log;
}
EOF
echo "fayl yozildi"'
```

Yoqish — `nginx -t` o'tmasa reload bo'lmaydi:

```bash
ssh root@46.8.195.59 'ln -sf /etc/nginx/sites-available/w1.myteacher.uz /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx && echo RELOAD_OK'
```

`try_files ... =404` — asosiy saytdan muhim farqi. `myteacher.uz` da catch-all har qanday
yo'lga HTML qaytaradi, shuning uchun yetishmayotgan video jimgina buziladi. Bu yerda darhol
404 beradi va xato ko'rinadi.

---

## 3. SSL

certbot faqat `w1` blokini o'zgartiradi va 443 qismini o'zi yozadi:

```bash
ssh root@46.8.195.59 'certbot --nginx -d w1.myteacher.uz --non-interactive --agree-tos -m alfastarsx@gmail.com --redirect'
```

---

## 4. Sahifa fayllari

Server repodan o'zi olib kelsa eng qulay:

```bash
ssh root@46.8.195.59 'cd /tmp && rm -rf w1src && git clone --depth 1 git@github.com:alfastarsx-web/www.myteacher.uz.git w1src && cp w1src/maxsus/index.html w1src/maxsus/video-poster.jpg w1src/maxsus/robots.txt /var/www/w1/ && rm -rf w1src && ls -la /var/www/w1/'
```

`Permission denied` bersa — serverda bu repoga deploy kaliti yo'q. U holda uchta faylni
repodan qo'lda yuboring:

```bash
scp index.html video-poster.jpg robots.txt root@46.8.195.59:/var/www/w1/
```

---

## 5. Video — git bermaydi

`promo.mp4` (23 MB) `.gitignore` da: har qayta kodlashda repo tarixiga yangi 23 MB blob
qo'shilib borardi. Fayl **faqat Sardorning Mac'ida**:

```
/Users/sardorxudoyberdiyev/Documents/www.myteacher.uz/maxsus/promo.mp4
```

Access bor kompyuterga o'tkazib, so'ng:

```bash
scp promo.mp4 root@46.8.195.59:/var/www/w1/
```

Tekshirish — `video/mp4` qaytishi shart:

```bash
curl -sI https://w1.myteacher.uz/promo.mp4 | head -3
```

`text/html` kelsa fayl yo'q. Sahifa buzilmaydi (poster + "Video hozircha yuklanmadi" chiqadi,
`video_error` eventi yoziladi), lekin konversiya nolga tushadi.

---

## 6. Kampaniya yaratish

Admin token:

```bash
curl -s -X POST https://ai.myteacher.uz/api/auth/sign-in -H 'Content-Type: application/json' -d '{"phoneNumber":"<admin raqami>","password":"<parol>"}'
```

Plan ID'lari:

```bash
curl -s https://ai.myteacher.uz/api/plans -H "Authorization: Bearer <token>"
```

Kampaniya. `landingUrl` **majburiy** — busiz SMS havolasi `w1.myteacher.uz/maxsus?ref=` bo'lib
404 beradi:

```bash
curl -s -X POST https://ai.myteacher.uz/api/campaigns -H "Authorization: Bearer <token>" -H 'Content-Type: application/json' -d '{"slug":"maxsus","name":"Mentor-kurs reaktivatsiya (SMS)","landingUrl":"https://w1.myteacher.uz","deadlineAt":"2026-09-07T23:59:59+05:00","offers":[{"key":"mentor","planId":"<mentor plan id>","months":1,"price":399000},{"key":"mentorsiz","planId":"<mentorsiz plan id>","months":1,"price":199000}]}'
```

`price` qiymatlari sahifadagi kartalar bilan **bir xil** bo'lishi shart. Summani server
hisoblaydi — farq qilsa odam 399 000 ko'rib boshqa summa to'laydi.

---

## 7. Yakuniy tekshiruv

```bash
curl -s https://w1.myteacher.uz/ | grep -o "<title>.*</title>"; curl -s https://w1.myteacher.uz/robots.txt; curl -s https://ai.myteacher.uz/api/campaigns/maxsus/session
```

Kutiladi:

- sarlavha `MyTeacher — sizga yuborilgan maxsus taklif`
- robots'da `Disallow: /`
- session'da `state: "offer"`, narxlar `399000` va `199000`, `paymentTypes` bo'sh emas

So'ng to'liq tekshiruv ro'yxatidan o'ting — ayniqsa pul yo'lini real to'lov bilan.

---

## Lidlar va SMS

```bash
curl -s -X POST https://ai.myteacher.uz/api/campaigns/<id>/leads/import -H "Authorization: Bearer <token>" -H 'Content-Type: application/json' -d '{"leads":[{"phoneNumber":"+998901234567","name":"Dilnoza R.","smsVariant":"D"}]}'
```

Bir so'rovda 5000 tagacha. Takror raqamlar o'tkazib yuboriladi — qayta yuborsangiz odam
ikkinchi SMS olmaydi.

CSV (SMS provayderiga):

```bash
curl -s "https://ai.myteacher.uz/api/campaigns/<id>/leads/export" -H "Authorization: Bearer <token>" -o leads.csv
```

---

## Bir narsa noto'g'ri ketsa

SMS ketib bo'lgandan keyin nosozlik chiqsa — sahifani o'chirmang. Kampaniyani standart holatga
o'tkazing: chegirma bloklari va countdown yo'qoladi, odamlar buzilgan sahifa ko'rmaydi.
To'lagan odamlarning obunasi baribir ochiladi.

```bash
curl -s -X PATCH https://ai.myteacher.uz/api/campaigns/<id> -H "Authorization: Bearer <token>" -H 'Content-Type: application/json' -d '{"isActive": false}'
```
