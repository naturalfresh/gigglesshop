import asyncio
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Message, MenuButtonWebApp

BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
WEBAPP_URL = (os.getenv('WEBAPP_URL') or os.getenv('RENDER_EXTERNAL_URL') or '').strip().rstrip('/')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '').strip()
PORT = int(os.getenv('PORT', '8080'))
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / 'webapp'
ORDERS_FILE = BASE_DIR / 'orders.jsonl'
CATALOG_FILE = WEB_DIR / 'products.json'

if not BOT_TOKEN:
    raise SystemExit('BOT_TOKEN is required')
if not WEBAPP_URL:
    raise SystemExit('WEBAPP_URL is required, e.g. https://your-domain.com')

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


def verify_init_data(init_data: str) -> dict:
    if not init_data:
        raise ValueError('Telegram initData missing')
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received = pairs.pop('hash', None)
    if not received:
        raise ValueError('Telegram hash missing')
    data_check_string = '\n'.join(f'{k}={pairs[k]}' for k in sorted(pairs))
    secret = hmac.new(b'WebAppData', BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise ValueError('Invalid Telegram initData')
    try:
        pairs['user'] = json.loads(pairs.get('user', '{}'))
    except json.JSONDecodeError:
        pairs['user'] = {}
    return pairs


def money(n: int) -> str:
    return f'{n:,}'.replace(',', ' ') + ' so\'m'


def save_order(order: dict):
    with ORDERS_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(order, ensure_ascii=False) + '\n')


def format_admin(order: dict) -> str:
    customer = order['customer']
    user = order.get('telegram_user') or {}
    lines = [
        '🛍 <b>YANGI GIGGLES BUYURTMA</b>',
        f"🆔 <code>{order['id']}</code>",
        f"👤 {customer['name']}",
        f"📞 {customer['phone']}",
        f"📍 {customer['address']}",
    ]
    if user:
        u = ('@' + user['username']) if user.get('username') else str(user.get('id', ''))
        lines.append(f'💬 Telegram: {u}')
    if customer.get('note'):
        lines.append(f"📝 {customer['note']}")
    lines.append('')
    for i, item in enumerate(order['items'], 1):
        lines.append(f"{i}. {item['name']} · {item['size']} · {money(item['price'])}")
    lines.append('')
    lines.append(f"💰 <b>Jami: {money(order['total'])}</b>")
    return '\n'.join(lines)


@dp.message(CommandStart())
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🛍 Giggles do‘konini ochish', web_app=WebAppInfo(url=WEBAPP_URL))]])
    await message.answer(
        '✨ <b>Giggles Premium</b>\n\nKattalar uchun mahsulotlar katalogi. O‘lcham va narxni tanlang, savatni to‘ldiring va buyurtmani Telegram ichida yuboring.',
        reply_markup=kb,
    )


@dp.message(Command('id'))
async def chat_id(message: Message):
    await message.answer(f'<b>Sizning Telegram chat ID:</b> <code>{message.chat.id}</code>')


async def health(_: web.Request):
    return web.json_response({'ok': True, 'service': 'Giggles Premium'})


async def order_api(request: web.Request):
    try:
        payload = await request.json()
        init_data = payload.get('telegram', {}).get('init_data', '')
        verified = verify_init_data(init_data)
        if not verified.get('user'):
            raise ValueError('Telegram user missing')
        items = payload.get('items') or []
        customer = payload.get('customer') or {}
        if not items or not customer.get('name') or not customer.get('phone') or not customer.get('address'):
            raise ValueError('Required fields missing')
        catalog = {p['id']: p for p in json.loads(CATALOG_FILE.read_text(encoding='utf-8'))}
        clean_items = []
        for raw in items[:50]:
            product_id = str(raw.get('product_id', ''))
            size = str(raw.get('size', '')).upper()
            p = catalog.get(product_id)
            if not p or size not in p['prices']:
                raise ValueError('Invalid product or size')
            clean_items.append({
                'product_id': product_id,
                'name': p['name'],
                'size': size,
                'price': int(p['prices'][size]),
            })
        total = sum(x['price'] for x in clean_items)
        order = {
            'id': secrets.token_hex(4).upper(),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'telegram_user': verified['user'],
            'customer': {
                'name': str(customer['name'])[:120],
                'phone': str(customer['phone'])[:40],
                'address': str(customer['address'])[:300],
                'note': str(customer.get('note', ''))[:500],
            },
            'items': clean_items,
            'total': total,
        }
        save_order(order)
        if ADMIN_CHAT_ID:
            await bot.send_message(int(ADMIN_CHAT_ID), format_admin(order))
        return web.json_response({'ok': True, 'order_id': order['id']})
    except Exception as e:
        return web.json_response({'ok': False, 'error': str(e)}, status=400)


async def static_app(request: web.Request):
    path = request.match_info.get('path', '')
    file = (WEB_DIR / path).resolve() if path else (WEB_DIR / 'index.html').resolve()
    if WEB_DIR.resolve() not in file.parents and file != WEB_DIR.resolve():
        raise web.HTTPForbidden()
    if not file.exists() or not file.is_file():
        file = WEB_DIR / 'index.html'
    return web.FileResponse(file)


async def web_server():
    app = web.Application()
    app.router.add_get('/health', health)
    app.router.add_post('/api/order', order_api)
    app.router.add_get('/', static_app)
    app.router.add_get('/{path:.*}', static_app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    return runner


async def main():
    await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text='🛍 Giggles', web_app=WebAppInfo(url=WEBAPP_URL)))
    runner = await web_server()
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
