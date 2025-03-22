from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging
from utils.logger import setup_logger

class StockDataClient(ABC):
    """Base class for stock data clients"""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
    
    @abstractmethod
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """
        Get stock data for a given symbol
        
        Args:
            symbol: Stock symbol to fetch data for
            
        Returns:
            Dictionary containing stock data or None if error occurs
            Expected format:
            {
                'price': float,
                'prev_close': float,
                'company_name': str
            }
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Get the name of the data source
        
        Returns:
            String name of the data source
        """
        pass 