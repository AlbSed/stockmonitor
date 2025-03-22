import pandas as pd
from datetime import datetime
import time
from clients import YahooFinanceClient, AlphaVantageClient
from utils.logger import setup_logger
from utils.data_storage import StockDataStorage
import sys
import argparse
from utils.config import load_config
import yfinance as yf

# Set up logger
logger = setup_logger('StockMonitor')

def validate_symbol(symbol: str, api_key: str = None) -> bool:
    """Validate a stock symbol using Yahoo Finance"""
    try:
        logger.info(f"Validating symbol: {symbol}")
        stock = yf.Ticker(symbol)
        info = stock.info
        if info and 'regularMarketPrice' in info:
            logger.info(f"Symbol {symbol} validated through Yahoo Finance")
            return True
        return False
    except Exception as e:
        logger.error(f"Error validating symbol {symbol}: {str(e)}")
        return False

def get_stock_data(symbol: str, api_key: str = None) -> pd.DataFrame:
    """Get stock data from Yahoo Finance"""
    try:
        logger.info(f"Fetching data for {symbol} from Yahoo Finance")
        stock = yf.Ticker(symbol)
        info = stock.info
        
        if not info or 'regularMarketPrice' not in info:
            logger.error(f"No data available for {symbol}")
            return None
            
        data = pd.DataFrame([{
            'Symbol': symbol,
            'Company': info.get('longName', 'Unknown'),
            'Current Price': f"${info['regularMarketPrice']:.2f}",
            'Previous Close': f"${info['previousClose']:.2f}",
            'Daily Change': f"{info['regularMarketChangePercent']:.2f}%",
            'Sources': 'Yahoo Finance'
        }])
        
        logger.info(f"Successfully fetched data for {symbol}")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

def calculate_average_price(data_sources):
    """
    Calculate average price from multiple data sources
    
    Args:
        data_sources: List of dictionaries containing stock data from different sources
    """
    try:
        prices = []
        prev_closes = []
        
        for data in data_sources:
            if data and data['price']:
                prices.append(data['price'])
            if data and data['prev_close']:
                prev_closes.append(data['prev_close'])
        
        if not prices:
            logger.warning("No valid prices found in any data source")
            return None, None
            
        if not prev_closes:
            logger.warning("No valid previous close prices found in any data source")
            return None, None
        
        avg_price = sum(prices) / len(prices)
        avg_prev_close = sum(prev_closes) / len(prev_closes)
        
        logger.debug(f"Calculated average price: {avg_price}, previous close: {avg_prev_close}")
        return avg_price, avg_prev_close
    except Exception as e:
        logger.error(f"Error calculating average price: {str(e)}")
        return None, None

def calculate_daily_change(current_price, prev_close):
    """
    Calculate daily price change percentage
    
    Args:
        current_price: Current stock price
        prev_close: Previous closing price
    """
    try:
        if not current_price or not prev_close or prev_close == 0:
            logger.warning("Cannot calculate daily change: invalid price data")
            return None
            
        daily_change = ((current_price - prev_close) / prev_close) * 100
        logger.debug(f"Calculated daily change: {daily_change}%")
        return daily_change
    except Exception as e:
        logger.error(f"Error calculating daily change: {str(e)}")
        return None

def get_stock_status(symbols, alpha_vantage_key):
    """
    Get current status of specified stock symbols from multiple sources
    """
    results = []
    
    try:
        # Initialize clients
        yahoo_client = YahooFinanceClient()
        alpha_vantage_client = AlphaVantageClient(alpha_vantage_key) if alpha_vantage_key else None
        
        if not yahoo_client:
            logger.error("Failed to initialize Yahoo Finance client")
            return pd.DataFrame()
            
        for symbol in symbols:
            try:
                logger.info(f"Processing stock: {symbol}")
                # Get data from all available sources
                data_sources = []
                source_names = []
                
                # Get Yahoo Finance data
                yahoo_data = yahoo_client.get_stock_data(symbol)
                if yahoo_data:
                    data_sources.append(yahoo_data)
                    source_names.append(yahoo_client.get_source_name())
                
                # Get Alpha Vantage data if available
                if alpha_vantage_client:
                    alpha_vantage_data = alpha_vantage_client.get_stock_data(symbol)
                    if alpha_vantage_data:
                        data_sources.append(alpha_vantage_data)
                        source_names.append(alpha_vantage_client.get_source_name())
                
                if not data_sources:
                    logger.warning(f"No data sources available for {symbol}")
                    results.append({
                        'Symbol': symbol,
                        'Company': 'N/A',
                        'Current Price': 'N/A',
                        'Previous Close': 'N/A',
                        'Daily Change': 'N/A',
                        'Sources': 'N/A'
                    })
                    continue
                
                # Calculate average prices
                avg_price, avg_prev_close = calculate_average_price(data_sources)
                
                # Calculate daily change
                daily_change = calculate_daily_change(avg_price, avg_prev_close)
                
                # Get company name (prefer Yahoo Finance name if available)
                company_name = next(
                    (data['company_name'] for data in data_sources if data['company_name'] != 'N/A'),
                    'N/A'
                )
                
                results.append({
                    'Symbol': symbol,
                    'Company': company_name,
                    'Current Price': f"${avg_price:.2f}" if avg_price else 'N/A',
                    'Previous Close': f"${avg_prev_close:.2f}" if avg_prev_close else 'N/A',
                    'Daily Change': f"{daily_change:.2f}%" if daily_change is not None else 'N/A',
                    'Sources': ' + '.join(source_names) if source_names else 'N/A'
                })
                
                logger.info(f"Successfully processed {symbol}")
                
                # Add delay to respect API rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                results.append({
                    'Symbol': symbol,
                    'Company': 'Error',
                    'Current Price': 'N/A',
                    'Previous Close': 'N/A',
                    'Daily Change': f"Error: {str(e)}",
                    'Sources': 'Error'
                })
        
        if not results:
            logger.error("No results were generated for any symbols")
            return pd.DataFrame()
            
        return pd.DataFrame(results)
        
    except Exception as e:
        logger.error(f"Critical error in get_stock_status: {str(e)}")
        return pd.DataFrame()

def main(one_time: bool = False):
    """Main function to run the stock monitor"""
    try:
        logger.info("Starting Stock Monitor")
        
        # Load configuration
        config = load_config()
        symbols = config.get('symbols', [])
        api_key = config.get('alpha_vantage_api_key')
        
        if not symbols:
            logger.error("No stock symbols configured")
            return
            
        logger.info(f"Loaded {len(symbols)} stock symbols from config")
        
        if not api_key:
            logger.warning("Alpha Vantage API key not configured. Only using Yahoo Finance data.")
        
        # Validate symbols
        valid_symbols = []
        for symbol in symbols:
            if validate_symbol(symbol, api_key):
                valid_symbols.append(symbol)
                
        logger.info(f"Found {len(valid_symbols)} valid symbols out of {len(symbols)}")
        
        if not valid_symbols:
            logger.error("No valid symbols found")
            return
            
        logger.info(f"Monitoring {len(valid_symbols)} valid stocks: {', '.join(valid_symbols)}")
        
        # Initialize data storage
        data_storage = StockDataStorage()
        
        while True:
            try:
                # Get latest data for comparison
                previous_data = data_storage.get_latest_data()
                
                # Process each stock
                for symbol in valid_symbols:
                    logger.info(f"Processing stock: {symbol}")
                    stock_data = get_stock_data(symbol, api_key)
                    
                    if stock_data is not None:
                        logger.info(f"Successfully processed {symbol}")
                    else:
                        logger.error(f"Failed to process {symbol}")
                
                # Save current data
                current_data = data_storage.get_latest_data()
                if current_data is not None:
                    data_storage.save_stock_data(current_data)
                    
                    # Compare with previous data
                    if previous_data is not None:
                        comparison_data = data_storage.compare_with_previous(current_data)
                        if comparison_data is not None:
                            # Generate and print report
                            report = data_storage.generate_report(comparison_data)
                            print("\n" + report)
                
                if one_time:
                    logger.info("One-time run completed, exiting")
                    break
                    
                # Wait before next update
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                if one_time:
                    break
                time.sleep(60)  # Wait 1 minute before retrying
                
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Stock Market Monitor')
    parser.add_argument('--one-time', action='store_true', help='Run once and exit')
    args = parser.parse_args()
    
    main(one_time=args.one_time)