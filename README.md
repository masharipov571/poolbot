# PoolBot - Professional Telegram Quiz Bot & Web Admin Panel

PoolBot — bu Telegram foydalanuvchilari uchun avtomatik tarzda DOCX, PDF, va TXT test fayllaridan quizlar (Telegram Poll Quiz Mode) yaratuvchi, foydalanuvchilar o'yin statistikasini yozib boruvchi va butunlay yopiq (Stealth) premium SaaS Admin Dashboard orqali boshqariladigan zamonaviy tizim.

---

## ✨ Loyiha Tarkibi va Imkoniyatlari

### 🤖 Telegram Bot (Aiogram 3)
- **User Ro'yxatga olish:** Botga start bosgan foydalanuvchilar ma'lumotlar bazasida xavfsiz saqlanadi.
- **Avtomatik Parser:** DOCX, PDF, va TXT fayllarini yuklang. Tizim maxsus quiz sintaksisi bo'yicha savollarni avtomatik tarzda ajratadi va bazaga yozadi.
- **Parametrlar:** Savollar sonini tanlash (5, 10, 20 yoki barchasi) hamda har bir savol uchun taymer belgilash (15s, 30s, 60s yoki cheksiz).
- **Aktiv Poll Quiz Mode:** Savollar shaxsiylashtirilmagan (non-anonymous) Telegram poll shaklida keladi. Bu orqali foydalanuvchi javoblari real-time rejimida kuzatib boriladi.
- **Cheating Protection:** Savollar va variantlar tartibi har bir foydalanuvchi uchun alohida chalkashtiriladi (shuffle).
- **Natijalar Oynasi:** O'yin yakunida sarflangan vaqt, to'g'ri/noto'g'ri javob foizlari va rag'batlantiruvchi premium score card ko'rsatiladi.

### 🌐 Maxfiy Web Admin Dashboard (React + FastAPI)
- **Stealth Kirish (SSO):** Dashboard oddiy foydalanuvchilar uchun butunlay ko'rinmas (404 Not Found) va hech qanday login/parol formasiga ega emas. Admin botda `/admin` buyrug'ini yozganda bot unga 5 daqiqa amal qiluvchi, bir martalik kirish havolasini yaratib beradi.
- **Real-Time Analitika:** DAU/WAU/MAU ko'rsatkichlari, testlar soni, foydalanuvchilarning kunlik o'sish grafigi (Area chart), eng faol o'yinchilar va eng ko'p topshirilgan testlar.
- **User va Quizzes Boshqaruvi:** Foydalanuvchilarni qidirish, bloklash hamda testlarni savollari bilan birga ko'rish va o'chirish.
- **Keng qamrovli Broadcast (Xabar yuborish):** Matnli, rasmli, videoli yoki faylli xabarlarni barcha foydalanuvchilarga yuborish. Rejalashtirilgan (Scheduled) yuborish, inline tugmalar qo'shish, FloodWait (429) xavfsizlik cheklovlariga qarshi avtomatik kutish hamda real-time progress bar va yuborishni bekor qilish (Cancel) imkoniyati.

---

## 📁 Loyiha Tuzilishi

```text
poolbot/
├── backend/
│   ├── app/
│   │   ├── routers/            # API Routerlar (auth, analytics, users, quizzes, broadcast)
│   │   ├── config.py           # Loyiha sozlamalari (Pydantic BaseSettings)
│   │   ├── database.py         # SQLAlchemy async DB ulanishi (SQLite/PostgreSQL)
│   │   ├── models.py           # Ma'lumotlar bazasi ORM modellari
│   │   ├── schemas.py          # Pydantic validatsiya sxemalari
│   │   ├── parser.py           # DOCX/PDF/TXT parser moduli
│   │   ├── auth.py             # JWT va Kirish tokenlari xavfsizlik boshqaruvi
│   │   ├── bot.py              # Aiogram 3 Telegram Bot logic
│   │   └── main.py             # FastAPI entrypoint va bot poller startup
│   ├── requirements.txt        # Python paketlari ro'yxati
│   └── Dockerfile              # Backend Docker sozlamasi
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # To'liq SaaS Dashboard UI va logic
│   │   ├── main.jsx            # React root mount
│   │   └── index.css           # Premium Tailwind va Neon stilizatsiyalari
│   ├── tailwind.config.js      # Neon violet/pink ranglar sozlamasi
│   ├── vite.config.js          # Vite va /api proxy sozlamasi
│   ├── index.html              # HTML shell
│   └── package.json            # Node dependency va skriptlar
├── docker-compose.yml          # Production Docker Compose fayli
├── nginx.conf                  # SSL va API proxy uchun Nginx sozlamasi
└── README.md                   # Ushbu qo'llanma
```

---

## 📑 Test Savollari Formati

Yuklanayotgan test fayli (DOCX, PDF yoki TXT) ichidagi savollar quyidagi shaklda yozilishi shart:

```text
+++
Kvant mexanikasidagi Shryodinger tenglamasi qaysi yili yaratilgan?
===
#1925-yilda
===
1915-yilda
===
1930-yilda
===
1905-yilda
+++

+++
Quyidagilardan qaysi biri dasturlash tili hisoblanadi?
===
HTML
===
#Python
===
CSS
===
JSON
+++
```

**Qoidalar:**
1. Har bir savol bloki `+++` bilan boshlanib, `+++` bilan tugashi kerak.
2. Variantlar `===` belgisi yordamida ajratiladi.
3. Faqatgina bitta to'g'ri javob variantining boshiga `#` belgisi qo'yiladi.

---

## 🚀 Ishga Tushirish Qo'llanmasi

### 1. Mahalliy ishga tushirish (Local Run)

#### Backend sozlash:
1. `backend` papkasiga o'ting:
   ```bash
   cd backend
   ```
2. Virtual muhit yarating va faollashtiring:
   ```bash
   python -m venv venv
   # Windowsda:
   venv\Scripts\activate
   # Linux/MacOSda:
   source venv/bin/activate
   ```
3. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
4. `.env` faylini yarating va quyidagi parametrlarni kiriting:
   ```env
   BOT_TOKEN=Sening_Telegram_Bot_Tokening
   ADMIN_TELEGRAM_ID=Sening_Telegram_User_ID
   DATABASE_URL=sqlite+aiosqlite:///./poolbot.db
   JWT_SECRET=maxfiy_jwt_kaliti
   ```
5. Serverni ishga tushiring:
   ```bash
   uvicorn app.main:app --reload
   ```
   *Ushbu buyruq FastAPI (port 8000) va Telegram Bot polling jarayonini bir vaqtda parallel ishga tushiradi!*

#### Frontend sozlash:
1. `frontend` papkasiga o'ting:
   ```bash
   cd ../frontend
   ```
2. Kerakli paketlarni o'rnating:
   ```bash
   npm install
   ```
3. Ishlab chiqish serverini yoqing:
   ```bash
   npm run dev
   ```
4. Brauzerda `http://localhost:5173` manzilini oching (404 Stealth xabari chiqadi).
5. Botga o'tib, `/admin` buyrug'ini yozing va kirish tugmasini bosib dashboardga kiring!

---

## 🐳 Docker yordamida ishga tushirish (Production)

Loyiha PostgreSQL, Redis, FastAPI backend va Nginx reverse proxy bilan Docker Compose orqali to'liq avtomatlashtirilgan.

1. Barcha loyiha sozlamalarini `docker-compose.yml` ichida konfiguratsiya qiling (Bot token va Admin ID).
2. Quyidagi buyruqni bosing:
   ```bash
   docker-compose up --build -d
   ```
3. Nginx 80 (HTTP) va 443 (HTTPS) portlarida static dashboard fayllarini taqdim etadi hamda `/api` so'rovlarini avtomatik ravishda backend containeriga yo'naltiradi.

Loyiha butunlay tayyor va production-ready holatda!
