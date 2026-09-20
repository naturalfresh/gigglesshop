# Giggles Premium — Telegram Mini App

Bu paket `@GigglesShopBot` uchun premium Telegram do‘kon skeleti: katalog, M/L/XL variantlari, savat, qidiruv, brend filtri, narx bo‘yicha saralash, buyurtma formasi va admin chatga buyurtma yuborish.

## Zipdan olingan mahsulotlar

5 ta mahsulot va M/L/XL rasmlar/narxlar `webapp/products.json` ichida. Rasmlar `webapp/assets/` ichida alohida saqlangan.

## 1) O‘rnatish

Python 3.11+ tavsiya etiladi.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
# .venv\\Scripts\\activate
pip install -r requirements.txt
```

## 2) Environment

`.env.example` ni `.env` qilib, qiymatlarni to‘ldiring. Shell orqali eksport qilish yoki hosting panelining Environment Variables bo‘limidan kiritish mumkin.

```text
BOT_TOKEN=BotFather bergan token
WEBAPP_URL=https://sizning-domeningiz.uz
ADMIN_CHAT_ID=              # /id buyrug‘i bilan bilib olasiz
PORT=8080
```

## 3) Ishga tushirish

```bash
python bot.py
```

Web server `PORT` portida ishlaydi. Telegram Mini App HTTPS URL bilan ochilishi kerak.

## 4) Telegram’da ulash

1. `@BotFather` → `@GigglesShopBot`.
2. Main Mini App / Web App sifatida `WEBAPP_URL` manzilini qo‘ying.
3. Botga o‘zingiz `/id` yuboring va chiqqan ID ni `ADMIN_CHAT_ID` ga yozing.
4. Botni qayta ishga tushiring.
5. Bot ichidagi `🛍 Giggles do‘konini ochish` tugmasi orqali test qiling.
6. Main Mini App sozlangach, Telegram direct link orqali `?startapp=...` ishlatish mumkin.

## Buyurtma xavfsizligi

Frontend `/api/order` ga Telegram `initData` yuboradi. Backend HMAC orqali Telegram imzosini tekshiradi va faqat tekshirilgan foydalanuvchidan kelgan buyurtmani qabul qiladi.

## Keyin qo‘shiladigan premium modullar

- Buyurtma statuslari
- Promokodlar
- Yangi mahsulot / qoldiq boshqaruvi
- Click/Payme/Uzum Bank kabi to‘lov integratsiyasi
- Admin panel
- Push xabarnomalar
- Yetkazib berish zonalari va xarita
