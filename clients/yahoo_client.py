import yfinance as yf
from typing import Dict, Optional
from .base_client import StockDataClient

class YahooFinanceClient(StockDataClient):
    """Client for fetching stock data from Yahoo Finance"""
    
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        try:
            self.logger.info(f"Fetching data for {symbol} from Yahoo Finance")
            stock = yf.Ticker(symbol)
            info = stock.info
            data = {
                'price': info.get('currentPrice', None),
                'prev_close': info.get('previousClose', None),
                'company_name': info.get('longName', 'N/A')
            }
            self.logger.info(f"Successfully fetched data for {symbol}")
            return data
        except Exception as e:
            self.logger.error(f"Error fetching Yahoo Finance data for {symbol}: {str(e)}")
            return None
    
    def get_source_name(self) -> str:
        return "Yahoo Finance" 