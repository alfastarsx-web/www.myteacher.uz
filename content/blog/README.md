# Blogga maqola qo'shish

## 1. Yangi fayl yarating

`content/blog/` ichida `.md` fayl yarating. **Fayl nomi = URL manzili**, shuning uchun uni diqqat bilan tanlang:

```
content/blog/ielts-listening-maslahatlar.md
        ->  https://myteacher.uz/blog/ielts-listening-maslahatlar.html
```

Fayl nomi qoidalari: faqat kichik lotin harflari, raqamlar va defis. Bo'sh joy, apostrof, o'zbekcha maxsus belgilar ishlatmang.

## 2. Frontmatter to'ldiring

Har bir fayl `---` bloki bilan boshlanadi:

```markdown
---
title: IELTS Listening uchun 7 ta amaliy maslahat
description: Listening bo'limida ball yo'qotmaslik uchun eng ko'p ishlaydigan texnikalar va tayyorgarlik usullari.
date: 2026-09-01
keywords: IELTS Listening, listening maslahatlar, IELTS tayyorgarlik
---
```

| Maydon | Majburiymi | Izoh |
|---|---|---|
| `title` | ha | Sahifa sarlavhasi va Google'da ko'rinadigan matn. 60 belgigacha ideal |
| `description` | ha | Google natijalaridagi tavsif. 150–160 belgi optimal |
| `date` | ha | `YYYY-MM-DD` formatida. Ro'yxatda saralash shu bo'yicha |
| `keywords` | yo'q | Vergul bilan ajratilgan |
| `slug` | yo'q | URL'ni fayl nomidan boshqacha qilmoqchi bo'lsangiz |

## 3. Maqolani yozing

Frontmatterdan keyin oddiy Markdown:

```markdown
Kirish paragrafi.

## Asosiy sarlavha

Matn. **Qalin** va *kursiv* ishlaydi.

### Kichik sarlavha

- ro'yxat elementi
- yana biri

1. raqamlangan
2. ro'yxat

> Iqtibos yoki muhim eslatma

| Ustun | Ustun |
|---|---|
| qiymat | qiymat |

[Havola matni](https://myteacher.uz/)
```

**Diqqat:** `# ` (bitta panjara) ishlatmang — sahifa sarlavhasi `title` maydonidan avtomatik qo'yiladi. Maqola ichida `##` dan boshlang.

## 4. Generatorni ishga tushiring

Repo ildizidan:

```
python3 tools/build_blog.py
```

Bu quyidagilarni yangilaydi:

- `blog/<slug>.html` — maqola sahifasi
- `blog/index.html` — blog ro'yxati
- `sitemap.xml` — barcha URL'lar bilan

## 5. Commit qiling

`content/` va `blog/` papkalarini, hamda `sitemap.xml` ni birga commit qiling. Generatsiya qilingan HTML'ni **qo'lda tahrirlamang** — keyingi build uni qayta yozadi. O'zgartirish kerak bo'lsa `.md` faylni yoki `tools/build_blog.py` shablonini tahrirlang.

---

## SEO bo'yicha eslatmalar

- **Bitta maqola = bitta aniq savol.** "Ingliz tili haqida hammasi" emas, "IELTS 6.5 uchun qancha vaqt kerak" — odamlar aynan shunday qidiradi.
- **Sarlavhaga savolni yozing.** Google savol shaklidagi so'rovlarni aynan shunday sarlavhalar bilan moslashtiradi.
- **Kamida 800 so'z.** Qisqa maqolalar raqobatda yutqazadi.
- **Ichki havola qo'ying.** Yangi maqoladan eski maqolaga havola bering — bu indekslashga yordam beradi.
- **AI bilan quyilgan matn qo'ymang.** Google "helpful content" tizimi bunday saytlarni butunlay tushiradi. Mentorlar tajribasidan real misollar, aniq raqamlar yozing.
