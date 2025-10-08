import json
import csv
import re
from datetime import datetime
from telethon import TelegramClient
import asyncio

class BinanceAlphaScraper:
    def __init__(self, config_path="config/telegram_alpha_scraper.json"):
        self.config = self.load_config(config_path)
        self.client = None
        self.messages_data = []
        
    def load_config(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def init_client(self):
        tg_config = self.config['telegram']
        
        print("🔐 TELEGRAM LOGIN")
        print("Đang kết nối...")
        
        self.client = TelegramClient(
            'alpha_session',
            int(tg_config['api_id']),
            tg_config['api_hash']
        )
        
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            print("❌ Chưa đăng nhập. Chạy qr_login.py trước!")
            return False
        
        print("✅ Đã đăng nhập!")
        return True
    
    def extract_token_info(self, message_text):
        # Tìm token có $ prefix
        token_match = re.search(r'\$([A-Z0-9]{1,10})\b', message_text)
        token = token_match.group(1).upper() if token_match else None
        message_lower = message_text.lower()
        if "added" in message_lower:
            loai_thong_bao = "addition"
        elif "listed" in message_lower:
            loai_thong_bao = "listing"
        else:
            loai_thong_bao = "binance_alpha"
        return token, loai_thong_bao
    async def scrape_channel(self, channel_entity):
        print(f"🔍 Đang quét channel: {channel_entity}")
        
        filters = self.config['filters']
        start_date = datetime.strptime(filters['date_range']['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(filters['date_range']['end_date'], '%Y-%m-%d')
        
        print(f"   📅 Date range: {start_date} đến {end_date}")
        
        try:
            entity = await self.client.get_entity(channel_entity)
            print(f"   ✅ Đã tìm thấy: {getattr(entity, 'title', 'Unknown')}")
            
            count = 0
            
            async for message in self.client.iter_messages(entity, limit=1000):
                # Kiểm tra ngày tháng - chỉ lấy tháng 9/2025
                message_date = message.date.replace(tzinfo=None)
                if message_date < start_date or message_date > end_date:
                    continue
                    
                if message.text:
                    raw_text = message.text
                    
                    # CHỈ kiểm tra "Binance alpha" (có cả Binance và alpha)
                    if "binance" in raw_text.lower() and "alpha" in raw_text.lower():
                        print(f"   🎯 TÌM THẤY BINANCE ALPHA: {message_date} - {raw_text[:80]}...")
                        
                        token, loai_thong_bao = self.extract_token_info(raw_text)
                        
                        if token:
                            self.messages_data.append({
                                'ngay': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                                'loai_thong_bao': loai_thong_bao,
                                'token': token,
                                'message': raw_text[:100]
                            })
                            print(f"   ✅ Đã thêm: {token} - {message.date}")
                            count += 1
            
            print(f"   📊 Tổng tin có token: {count}")
            
        except Exception as e:
            print(f"❌ Lỗi khi quét {channel_entity}: {e}")
    
    async def run_scraper(self):
        """Main scraping function"""
        if not await self.init_client():
            return
        
        print("🚀 Bắt đầu quét channels...")
        
        for channel in self.config['telegram']['channels']:
            try:
                await self.scrape_channel(channel)
            except Exception as e:
                print(f"❌ Lỗi với channel {channel}: {e}")
        
        await self.export_to_csv()
        await self.client.disconnect()
        print("🎉 Hoàn thành!")
    
    async def export_to_csv(self):
        """Export data to CSV file"""
        output_config = self.config['output']
        filename = output_config['filename']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=output_config['columns'])
            writer.writeheader()
            
            for i, message in enumerate(self.messages_data, 1):
                writer.writerow({
                    'stt': i,
                    'ngay': message['ngay'],
                    'loai_thong_bao': message['loai_thong_bao'],
                    'token': message['token']
                })
        
        print(f"📊 Đã xuất {len(self.messages_data)} bản ghi ra file {filename}")

async def main():
    scraper = BinanceAlphaScraper()
    await scraper.run_scraper()

if __name__ == "__main__":
    asyncio.run(main())