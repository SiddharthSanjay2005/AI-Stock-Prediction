import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class DataManager:
    def get_stock_data(self, symbol, period='1y'):
        """Fetch stock data from Yahoo Finance"""
        try:
            print(f"Fetching {symbol} data...")
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data is None or data.empty:
                print(f"No data for {symbol}")
                return None
            
            print(f"Got {len(data)} rows for {symbol}")
            return data
            
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def get_realtime_quote(self, symbol):
        """Get current stock quote"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get latest price
            hist = ticker.history(period='1d')
            if hist.empty:
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            prev_close = info.get('previousClose', current_price)
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'price': round(current_price, 2),
                'change': round(((current_price - prev_close) / prev_close) * 100, 2),
                'open': round(float(hist['Open'].iloc[-1]), 2),
                'high': round(float(hist['High'].iloc[-1]), 2),
                'low': round(float(hist['Low'].iloc[-1]), 2),
                'volume': int(hist['Volume'].iloc[-1]),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE'),
                'sector': info.get('sector', 'N/A'),
                'exchange': info.get('exchange', 'N/A')
            }
        except Exception as e:
            print(f"Quote error: {e}")
            return None
    
    def get_market_indices(self):
        """Get major market indices"""
        indices_data = {}
        indices = {'^GSPC': 'S&P 500', '^DJI': 'Dow Jones', '^IXIC': 'NASDAQ'}
        
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='2d')
                if not hist.empty and len(hist) >= 2:
                    current = float(hist['Close'].iloc[-1])
                    previous = float(hist['Close'].iloc[-2])
                    change = ((current - previous) / previous) * 100
                    indices_data[name] = {
                        'price': round(current, 2),
                        'change': round(change, 2),
                        'change_str': f"{change:+.2f}%"
                    }
            except:
                continue
        
        return indices_data