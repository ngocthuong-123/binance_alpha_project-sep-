import asyncio
from telethon import TelegramClient
import json
import qrcode

async def main():
    with open('config/telegram_alpha_scraper.json', 'r') as f:
        config = json.load(f)
    
    tg_config = config['telegram']
    
    client = TelegramClient('alpha_session', int(tg_config['api_id']), tg_config['api_hash'])
    
    print("🔐 ĐĂNG NHẬP BẰNG QR CODE")
    print("1. Mở Telegram app trên điện thoại")
    print("2. Vào Settings → Devices → Link Desktop Device")
    print("3. Quét mã QR bên dưới:")
    print()
    
    await client.connect()
    qr_login = await client.qr_login()
    
    # Hiển thị QR code
    qr = qrcode.QRCode()
    qr.add_data(qr_login.url)
    qr.make()
    qr.print_ascii(tty=True)
    
    print("\nĐang chờ quét mã...")
    try:
        await qr_login.wait(timeout=60)
        print("✅ Đăng nhập thành công!")
        
        # Lưu session
        await client.disconnect()
        
        # Chạy scraper
        from binance_alpha_scraper import BinanceAlphaScraper
        scraper = BinanceAlphaScraper()
        await scraper.run_scraper()
        
    except asyncio.TimeoutError:
        print("❌ QR code hết hạn. Chạy lại để tạo mã mới.")

if __name__ == '__main__':
    asyncio.run(main())