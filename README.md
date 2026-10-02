# 🎯 Maqsadlarim — Telegram bot

Shaxsiy maqsadlar nazoratchi bot. Bot: `@MaqsadNazoratchi_bot`

Uzoq muddatli maqsadlaringizni unutmaslik, ularni kichik vazifalarga bo'lish, har kuni
reja tuzish, kechqurun natijalarni tekshirish (check-in) va progressni tahlil qilish
uchun mo'ljallangan.

---

## 1. Imkoniyatlar

- `/start` — botni tanishtirish va "🚀 Boshlash" tugmasi
- **Asosiy menyu**: 🎯 Maqsadlarim, ➕ Yangi maqsad, 📅 Bugungi reja, 📝 Bugungi Check-in,
  📊 Natijalarim, 🔥 Streak, ⚙️ Sozlamalar
- **Yangi maqsad qo'shish**: nomi → nega muhim → muddat → kutilgan natija
- **Bosqichlarga bo'lish**: har bir maqsadni ketma-ket bosqichlarga bo'lish, har bosqichga
  kunlik vazifalar biriktirish
- **Kunlik reja**: har bir vazifani ✅ Bajarildi / 🟡 Qisman / ❌ Bajarilmadi deb belgilash
- **Bajarilmagan vazifa sababi**: ⏰ Vaqt yetmadi / 😴 Charchadim / 📱 Chalg'idim /
  ❓ Vazifa juda katta edi / 🔄 Boshqa sabab — va "juda katta" bo'lsa, uni kichik
  vazifalarga avtomatik bo'lib berish taklifi
- **Kechki Check-in**: bajarilgan/bajarilmagan vazifalar avtomatik hisoblanadi, so'ng
  erkin izoh va ertangi kun uchun reja so'raladi
- **Streak**: ketma-ket faol kunlar hisoblanadi (🔥 masalan: 7 kunlik streak)
- **Haftalik/oylik hisobot**: bajarilgan/bajarilmagan vazifalar, foiz, streak, har bir
  maqsad progressi (0% → 10% → 25% → 50% → 75% → 100%)
- **Eslatmalar**: ertalabki reja va kechki check-in vaqtini o'zi sozlaydi (⚙️ Sozlamalar)
- **Faolsizlik nazorati**: 3 kun kirmasa eslatma, 7 kun kirmasa "Recovery rejimi" xabari

---

## 2. Loyiha tuzilmasi

```
maqsad_bot/
├── bot.py                 # Botni ishga tushirish nuqtasi
├── config.py                # .env dan sozlamalarni o'qish
├── database.py               # SQLite bilan ishlash (aiosqlite, to'liq async)
├── keyboards.py              # Barcha inline klaviaturalar
├── utils.py                  # Sana, progress-bar va boshqa yordamchi funksiyalar
├── requirements.txt
├── .env.example
├── README.md
└── handlers/
    ├── __init__.py
    ├── start.py               # /start, asosiy menyu
    ├── goals.py                # Yangi maqsad, bosqichlar, maqsadlar ro'yxati
    ├── daily_plan.py            # Bugungi reja, vazifa statusi, sabab, bo'lish
    ├── checkin.py               # Kechki check-in
    ├── stats.py                 # Streak va haftalik/oylik hisobot
    ├── settings.py              # Eslatma vaqtlarini sozlash
    └── jobs.py                  # JobQueue: eslatmalar, faolsizlik nazorati
```

Ma'lumotlar bazasi jadvallari: `users`, `goals`, `stages`, `tasks`, `checkins`, `streaks`
(barchasi `database.py` ichida `SCHEMA` sifatida tavsiflangan va bot birinchi marta
ishga tushganda avtomatik yaratiladi).

---

## 3. O'rnatish va ishga tushirish

### 3.1. Talablar

- Python **3.10** yoki undan yuqori versiya
- Telegram bot tokeni ([@BotFather](https://t.me/BotFather) orqali olinadi)

### 3.2. Loyihani tayyorlash

```bash
# 1) Loyiha papkasiga kiring
cd maqsad_bot

# 2) (tavsiya) virtual muhit yarating
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3) kerakli kutubxonalarni o'rnating
pip install -r requirements.txt
```

### 3.3. Bot tokenini sozlash

`.env.example` faylidan nusxa ko'chiring va o'z tokeningizni kiriting:

```bash
cp .env.example .env
```

`.env` faylini oching va quyidagini o'zgartiring:

```
BOT_TOKEN=SIZNING_TOKEN_BU_YERGA
```

> ⚠️ Tokenni hech qachon kodning o'ziga yozmang va `.env` faylini ochiq
> repozitoriyga (GitHub va h.k.) yuklamang.

### 3.4. Botni ishga tushirish

```bash
python bot.py
```

Konsolda quyidagiga o'xshash yozuv chiqsa, bot ishga tushgan bo'ladi:

```
... - handlers.jobs - INFO - Ma'lumotlar bazasi tayyor va fon vazifalar (job) rejalashtirildi.
... - __main__ - INFO - Bot ishga tushmoqda...
```

Endi Telegram'da botingizga (`@MaqsadNazoratchi_bot`) o'ting va `/start` buyrug'ini
yuboring.

---

## 4. Foydalanish bo'yicha qisqa qo'llanma

1. `/start` → "🚀 Boshlash" tugmasini bosing.
2. **➕ Yangi maqsad** orqali maqsad qo'shing (nomi, sababi, muddati, natijasi).
3. Bot bosqichlarga bo'lishni taklif qiladi — xohlasangiz bosqichlarni ketma-ket kiriting.
4. **🎯 Maqsadlarim** bo'limidan har bir maqsadga/bosqichga bugungi vazifa qo'shing.
5. **📅 Bugungi reja** orqali kun davomida vazifalar holatini belgilab boring.
6. Kechqurun **📝 Bugungi Check-in** orqali kunni yakunlang — bot avtomatik hisoblab,
   sizdan qisqacha izoh va ertangi reja so'raydi.
7. **🔥 Streak** va **📊 Natijalarim** orqali progressingizni kuzating.
8. **⚙️ Sozlamalar** orqali ertalabki/kechki eslatma vaqtlarini o'zingizga moslang.

---

## 5. Texnik tafsilotlar

- **Til/freymvork**: Python 3, [`python-telegram-bot`](https://python-telegram-bot.org/)
  (v22+, to'liq async, `ApplicationBuilder`, `ConversationHandler`, `JobQueue`)
- **Ma'lumotlar bazasi**: SQLite, `aiosqlite` orqali async tarzda
- **Klaviaturalar**: faqat `InlineKeyboardButton` / `InlineKeyboardMarkup`
- **Eslatmalar**: `JobQueue.run_daily` — har bir foydalanuvchi uchun alohida, o'zi
  belgilagan vaqtda (vaqt mintaqasi `.env` dagi `TIMEZONE` bo'yicha, standart
  `Asia/Tashkent`)
- **Faolsizlik nazorati**: har kuni bir marta (`.env` dagi `INACTIVITY_CHECK_HOUR/MINUTE`
  bo'yicha) barcha foydalanuvchilar tekshiriladi

### Muhim muhit o'zgaruvchilari (`.env`)

| O'zgaruvchi              | Tavsif                                         | Standart qiymat  |
|---------------------------|------------------------------------------------|-------------------|
| `BOT_TOKEN`                | @BotFather'dan olingan token (majburiy)         | —                 |
| `TIMEZONE`                 | Eslatmalar uchun vaqt mintaqasi                 | `Asia/Tashkent`   |
| `DB_PATH`                  | SQLite fayli yo'li                              | `maqsadlarim.db`  |
| `INACTIVITY_CHECK_HOUR`    | Faolsizlik tekshiruvi soati                     | `12`              |
| `INACTIVITY_CHECK_MINUTE`  | Faolsizlik tekshiruvi daqiqasi                  | `0`               |

---

## 6. Muammolarni bartaraf etish

- **`BOT_TOKEN topilmadi` xatosi** — `.env` fayl mavjudligini va unda `BOT_TOKEN=...`
  qatori to'g'ri yozilganini tekshiring.
- **Eslatmalar kelmayapti** — `python-telegram-bot[job-queue]` to'g'ri o'rnatilganini
  tekshiring (`pip show apscheduler`), chunki `JobQueue` shu kutubxonaga bog'liq.
- **`ModuleNotFoundError`** — virtual muhitni faollashtirib
  (`source venv/bin/activate`), `pip install -r requirements.txt` ni qayta bajaring.
- **Bazani "tozalash"** — botni to'xtatib, `maqsadlarim.db` faylini o'chiring va botni
  qayta ishga tushiring (yangi baza avtomatik yaratiladi). Bu barcha foydalanuvchi
  ma'lumotlarini o'chirib tashlaydi.

---

## 7. Kengaytirish g'oyalari

- Guruh/jamoa maqsadlari (bir nechta foydalanuvchi bitta maqsadni kuzatishi)
- Haftalik hisobotni avtomatik yuborish (masalan, har yakshanba kechqurun)
- Grafik/diagramma ko'rinishidagi progress hisobotlari
- Ovozli xabar orqali check-in qilish imkoniyati
