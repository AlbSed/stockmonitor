import os
from dotenv import load_dotenv
from utils.logger import setup_logger

logger = setup_logger('Config')

def load_config():
    """
    Load configuration from .env file and config.yaml
    
    Returns:
        dict: Configuration dictionary containing symbols and API keys
    """
    try:
        load_dotenv()
        
        # Load stock symbols from environment variable
        symbols_str = os.getenv('STOCK_SYMBOLS', '')
        if not symbols_str:
            logger.error("No stock symbols found in .env file. Please configure STOCK_SYMBOLS.")
            return {'symbols': [], 'alpha_vantage_key': None}
        
        symbols = [symbol.strip() for symbol in symbols_str.split(',')]
        if not symbols:
            logger.error("No valid stock symbols found in STOCK_SYMBOLS configuration.")
            return {'symbols': [], 'alpha_vantage_key': None}
            
        logger.info(f"Loaded {len(symbols)} stock symbols from config")

        # Load Alpha Vantage API key
        alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', '')
        if not alpha_vantage_key or alpha_vantage_key == 'your_api_key_here':
            logger.warning("Alpha Vantage API key not configured. Only using Yahoo Finance data.")
            alpha_vantage_key = None
        else:
            logger.info("Alpha Vantage API key loaded successfully")
        
        return {
            'symbols': symbols,
            'alpha_vantage_key': alpha_vantage_key
        }
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        return {'symbols': [], 'alpha_vantage_key': None} 