from alpha_vantage.timeseries import TimeSeries
from typing import Dict, Optional
from .base_client import StockDataClient

class AlphaVantageClient(StockDataClient):
    """Client for fetching stock data from Alpha Vantage"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.ts = TimeSeries(key=api_key, output_format='pandas')
        self.logger.info("Initialized Alpha Vantage client")
    
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        try:
            self.logger.info(f"Fetching data for {symbol} from Alpha Vantage")
            data, meta_data = self.ts.get_quote_endpoint(symbol)
            if not data.empty:
                result = {
                    'price': float(data['05. price'].iloc[0]),
                    'prev_close': float(data['08. previous close'].iloc[0]),
                    'company_name': meta_data.get('2. Symbol', 'N/A')
                }
                self.logger.info(f"Successfully fetched data for {symbol}")
                return result
            self.logger.warning(f"No data returned for {symbol}")
        except Exception as e:
            self.logger.error(f"Error fetching Alpha Vantage data for {symbol}: {str(e)}")
        return None
    
    def get_source_name(self) -> str:
        return "Alpha Vantage" 