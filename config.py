import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8080))
    DEBUG = os.getenv('FLASK_ENV') != 'production'
    
    POPULAR_STOCKS = {
        'US': {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corp.',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com',
            'NVDA': 'NVIDIA Corp.',
            'META': 'Meta Platforms',
            'TSLA': 'Tesla Inc.',
            'NFLX': 'Netflix Inc.'
        },
        'India': {
            'RELIANCE.NS': 'Reliance Industries',
            'TCS.NS': 'Tata Consultancy',
            'INFY.NS': 'Infosys Ltd'
        }
    }
    
    INDICES = {
        '^GSPC': 'S&P 500',
        '^DJI': 'Dow Jones',
        '^IXIC': 'NASDAQ'
    }