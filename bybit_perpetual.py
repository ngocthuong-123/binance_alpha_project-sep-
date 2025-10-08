import json
import csv
import re
from datetime import datetime
from telethon import TelegramClient
import asyncio

class BybitPerpetualScraper:
    def __init__(self, config_path="config/telegram_contracts_scraper.json"):
        self.config = self.load_config(config_path)
        self.client = None
        self.messages_data = []
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def init_client(self):
        """Initialize Telegram client"""
        tg_config = self.config['telegram']
        self.client = TelegramClient(
            'bybit_session',
            int(tg_config['api_id']),
            tg_config['api_hash']
        )
        await self.client.start()
    
    def extract_trading_pair(self, message_text):
        """Extract trading pair from message - SIMPLE VERSION"""
        # Tìm pattern XXXUSDT trong message
        match = re.search(r'(\w+USDT)', message_text)
        if match:
            return match.group(1)
        return "UNKNOWN"
    
    async def scrape_channel(self, channel_entity):
        """Scrape messages from a single channel"""
        print(f"🔍 Đang quét channel: {channel_entity}")
        
        filters = self.config['filters']
        start_date = datetime.strptime(filters['date_range']['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(filters['date_range']['end_date'], '%Y-%m-%d')
        
        async for message in self.client.iter_messages(channel_entity):
            # Check date range
            if message.date.replace(tzinfo=None) < start_date:
                break
            if message.date.replace(tzinfo=None) > end_date:
                continue
            
            if message.text and "Perpetual Contract" in message.text:
                trading_pair = self.extract_trading_pair(message.text)
                
                if trading_pair != "UNKNOWN":
                    self.messages_data.append({
                        'ngay': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'cap_giao_dich': trading_pair
                    })
                    print(f"✅ Found: {trading_pair} - {message.date}")
    
    async def run_scraper(self):
        """Main scraping function"""
        await self.init_client()
        
        for channel in self.config['telegram']['channels']:
            try:
                entity = await self.client.get_entity(channel)
                await self.scrape_channel(entity)
            except Exception as e:
                print(f"❌ Error scraping {channel}: {e}")
        
        await self.export_to_csv()
        await self.client.disconnect()
    
    async def export_to_csv(self):
        """Export data to CSV file"""
        if not self.messages_data:
            print("📊 Không có bản ghi nào để xuất")
            return
            
        filename = self.config['output']['filename']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['stt', 'ngay', 'cap_giao_dich']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, message in enumerate(self.messages_data, 1):
                writer.writerow({
                    'stt': i,
                    'ngay': message['ngay'],
                    'cap_giao_dich': message['cap_giao_dich']
                })
        
        print(f"📊 Đã xuất {len(self.messages_data)} bản ghi ra file {filename}")

# Main execution
async def main():
    scraper = BybitPerpetualScraper()
    await scraper.run_scraper()

if __name__ == "__main__":
    asyncio.run(main())