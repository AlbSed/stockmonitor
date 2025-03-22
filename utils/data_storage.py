import pandas as pd
import os
from datetime import datetime
import duckdb
from utils.logger import setup_logger

logger = setup_logger('DataStorage')

class StockDataStorage:
    def __init__(self, base_dir='data', price_change_threshold=5.0):
        """
        Initialize the data storage with DuckDB database
        
        Args:
            base_dir (str): Base directory for storing database files
            price_change_threshold (float): Percentage threshold for significant price changes
        """
        self.base_dir = base_dir
        self.price_change_threshold = price_change_threshold
        self._ensure_directory_exists()
        self.db_path = os.path.join(base_dir, 'stock_data.db')
        self._initialize_database()
        
    def _ensure_directory_exists(self):
        """Ensure the data directory exists"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            logger.info(f"Created data directory: {self.base_dir}")
            
    def _initialize_database(self):
        """Initialize DuckDB database and create necessary tables"""
        try:
            self.conn = duckdb.connect(self.db_path)
            
            # Create tables if they don't exist
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_snapshots (
                    timestamp TIMESTAMP,
                    symbol VARCHAR,
                    company VARCHAR,
                    current_price DECIMAL(10,2),
                    previous_close DECIMAL(10,2),
                    daily_change DECIMAL(5,2),
                    sources VARCHAR,
                    PRIMARY KEY (timestamp, symbol)
                )
            """)
            
            # Create daily summary view
            self.conn.execute("""
                CREATE OR REPLACE VIEW daily_summary AS
                WITH ranked_data AS (
                    SELECT 
                        CAST(timestamp AS DATE) as date,
                        symbol,
                        company,
                        current_price,
                        daily_change,
                        sources,
                        ROW_NUMBER() OVER (PARTITION BY CAST(timestamp AS DATE), symbol ORDER BY timestamp) as rn_asc,
                        ROW_NUMBER() OVER (PARTITION BY CAST(timestamp AS DATE), symbol ORDER BY timestamp DESC) as rn_desc
                    FROM stock_snapshots
                )
                SELECT 
                    date,
                    symbol,
                    company,
                    MAX(CASE WHEN rn_asc = 1 THEN current_price END) as opening_price,
                    MAX(CASE WHEN rn_desc = 1 THEN current_price END) as closing_price,
                    MAX(current_price) as high_price,
                    MIN(current_price) as low_price,
                    AVG(current_price) as average_price,
                    MAX(CASE WHEN rn_asc = 1 THEN daily_change END) as opening_change,
                    MAX(CASE WHEN rn_desc = 1 THEN daily_change END) as closing_change,
                    sources
                FROM ranked_data
                GROUP BY date, symbol, company, sources
            """)
            
            logger.info("Initialized DuckDB database and created tables")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
            
    def save_stock_data(self, df: pd.DataFrame, timestamp: datetime = None):
        """
        Save stock data to DuckDB database
        
        Args:
            df (pd.DataFrame): DataFrame containing stock data
            timestamp (datetime, optional): Timestamp for the data. Defaults to current time.
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
                
            # Prepare data for insertion
            df['timestamp'] = timestamp
            df['current_price'] = df['Current Price'].str.replace('$', '').astype(float)
            df['previous_close'] = df['Previous Close'].str.replace('$', '').astype(float)
            df['daily_change'] = df['Daily Change'].str.replace('%', '').astype(float)
            
            # Insert data into database
            self.conn.execute("""
                INSERT INTO stock_snapshots 
                (timestamp, symbol, company, current_price, previous_close, daily_change, sources)
                SELECT 
                    timestamp,
                    "Symbol",
                    "Company",
                    current_price,
                    previous_close,
                    daily_change,
                    "Sources"
                FROM df
            """)
            
            logger.info(f"Saved stock data for timestamp {timestamp}")
            
        except Exception as e:
            logger.error(f"Error saving stock data: {str(e)}")
            
    def get_latest_data(self):
        """
        Get the most recent stock data from the database
        
        Returns:
            pd.DataFrame: DataFrame containing the latest stock data
        """
        try:
            query = """
                WITH latest_timestamp AS (
                    SELECT MAX(timestamp) as max_ts
                    FROM stock_snapshots
                )
                SELECT 
                    timestamp,
                    symbol as "Symbol",
                    company as "Company",
                    CONCAT('$', current_price) as "Current Price",
                    CONCAT('$', previous_close) as "Previous Close",
                    CONCAT(daily_change, '%') as "Daily Change",
                    sources as "Sources"
                FROM stock_snapshots
                WHERE timestamp = (SELECT max_ts FROM latest_timestamp)
            """
            
            df = self.conn.execute(query).df()
            logger.info("Retrieved latest data from database")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving latest data: {str(e)}")
            return None
            
    def get_daily_summary(self, date: datetime = None):
        """
        Get the daily summary for a specific date
        
        Args:
            date (datetime, optional): Date to get summary for. Defaults to current date.
            
        Returns:
            pd.DataFrame: DataFrame containing the daily summary
        """
        try:
            if date is None:
                date = datetime.now()
                
            query = """
                SELECT 
                    symbol as "Symbol",
                    company as "Company",
                    CONCAT('$', opening_price) as "Opening Price",
                    CONCAT('$', closing_price) as "Closing Price",
                    CONCAT('$', high_price) as "High Price",
                    CONCAT('$', low_price) as "Low Price",
                    CONCAT('$', average_price) as "Average Price",
                    CONCAT(opening_change, '%') as "Opening Change",
                    CONCAT(closing_change, '%') as "Closing Change",
                    sources as "Sources"
                FROM daily_summary
                WHERE date = ?
            """
            
            df = self.conn.execute(query, [date.date()]).df()
            logger.info(f"Retrieved daily summary for {date.date()}")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving daily summary: {str(e)}")
            return None
            
    def compare_with_previous(self, current_df: pd.DataFrame):
        """
        Compare current data with the most recent saved data
        
        Args:
            current_df (pd.DataFrame): Current stock data to compare
            
        Returns:
            pd.DataFrame: DataFrame with comparison results
        """
        try:
            # Get the previous data
            previous_df = self.get_latest_data()
            if previous_df is None:
                logger.info("No previous data found for comparison")
                return None
                
            # Create a copy of current data for comparison
            comparison_df = current_df.copy()
            
            # Add comparison columns
            comparison_df['Previous Price'] = None
            comparison_df['Price Change'] = None
            comparison_df['Previous Daily Change'] = None
            comparison_df['Change in Daily Change'] = None
            
            # Helper function to safely convert price strings to float
            def safe_price_convert(price_str):
                if isinstance(price_str, float):
                    return price_str
                if isinstance(price_str, str):
                    return float(price_str.replace('$', '').replace(',', ''))
                return None
                
            # Helper function to safely convert percentage strings to float
            def safe_percent_convert(percent_str):
                if isinstance(percent_str, float):
                    return percent_str
                if isinstance(percent_str, str):
                    return float(percent_str.replace('%', '').replace(',', ''))
                return None
            
            # Compare each symbol
            for idx, row in comparison_df.iterrows():
                symbol = row['Symbol']
                prev_row = previous_df[previous_df['Symbol'] == symbol]
                
                if not prev_row.empty:
                    try:
                        # Get previous values and convert safely
                        prev_price = safe_price_convert(prev_row['Current Price'].iloc[0])
                        prev_daily_change = safe_percent_convert(prev_row['Daily Change'].iloc[0])
                        
                        # Get current values and convert safely
                        current_price = safe_price_convert(row['Current Price'])
                        current_daily_change = safe_percent_convert(row['Daily Change'])
                        
                        if all(v is not None for v in [prev_price, current_price, prev_daily_change, current_daily_change]):
                            # Calculate changes
                            price_change = current_price - prev_price
                            daily_change_diff = current_daily_change - prev_daily_change
                            
                            # Update comparison columns
                            comparison_df.at[idx, 'Previous Price'] = f"${prev_price:.2f}"
                            comparison_df.at[idx, 'Price Change'] = f"${price_change:.2f}"
                            comparison_df.at[idx, 'Previous Daily Change'] = f"{prev_daily_change:.2f}%"
                            comparison_df.at[idx, 'Change in Daily Change'] = f"{daily_change_diff:.2f}%"
                        else:
                            logger.warning(f"Could not convert values for {symbol}, skipping comparison")
                            
                    except Exception as e:
                        logger.error(f"Error processing comparison for {symbol}: {str(e)}")
                        continue
                    
            logger.info("Successfully compared current data with previous data")
            return comparison_df
            
        except Exception as e:
            logger.error(f"Error comparing data: {str(e)}")
            return None
            
    def analyze_price_changes(self, comparison_df: pd.DataFrame):
        """
        Analyze price changes and generate alerts for significant movements
        
        Args:
            comparison_df (pd.DataFrame): DataFrame with comparison data
            
        Returns:
            dict: Dictionary containing alerts and analysis results
        """
        try:
            alerts = {
                'significant_changes': [],
                'daily_change_alerts': [],
                'summary': {
                    'total_symbols': len(comparison_df),
                    'significant_changes': 0,
                    'positive_changes': 0,
                    'negative_changes': 0
                }
            }
            
            for _, row in comparison_df.iterrows():
                symbol = row['Symbol']
                
                # Skip if no previous data
                if pd.isna(row['Previous Price']) or pd.isna(row['Current Price']):
                    continue
                    
                # Convert price strings to float
                current_price = float(row['Current Price'].replace('$', ''))
                previous_price = float(row['Previous Price'].replace('$', ''))
                
                # Calculate price change percentage
                price_change_pct = ((current_price - previous_price) / previous_price) * 100
                
                # Check for significant price changes
                if abs(price_change_pct) >= self.price_change_threshold:
                    alerts['significant_changes'].append({
                        'symbol': symbol,
                        'company': row['Company'],
                        'current_price': current_price,
                        'previous_price': previous_price,
                        'change_pct': price_change_pct,
                        'direction': 'increase' if price_change_pct > 0 else 'decrease'
                    })
                    alerts['summary']['significant_changes'] += 1
                    if price_change_pct > 0:
                        alerts['summary']['positive_changes'] += 1
                    else:
                        alerts['summary']['negative_changes'] += 1
                
                # Check for significant daily change changes
                if pd.notna(row['Change in Daily Change']):
                    daily_change_diff = float(row['Change in Daily Change'].replace('%', ''))
                    if abs(daily_change_diff) >= self.price_change_threshold:
                        alerts['daily_change_alerts'].append({
                            'symbol': symbol,
                            'company': row['Company'],
                            'current_daily_change': float(row['Daily Change'].replace('%', '')),
                            'previous_daily_change': float(row['Previous Daily Change'].replace('%', '')),
                            'change_diff': daily_change_diff
                        })
            
            logger.info(f"Analyzed price changes for {alerts['summary']['total_symbols']} symbols")
            return alerts
            
        except Exception as e:
            logger.error(f"Error analyzing price changes: {str(e)}")
            return None
            
    def generate_report(self, comparison_df: pd.DataFrame):
        """
        Generate a detailed report of price changes and alerts
        
        Args:
            comparison_df (pd.DataFrame): DataFrame with comparison data
            
        Returns:
            str: Formatted report text
        """
        try:
            alerts = self.analyze_price_changes(comparison_df)
            if not alerts:
                return "No significant changes detected."
                
            report = []
            report.append("\nPrice Movement Analysis Report")
            report.append("=" * 50)
            
            # Add summary
            report.append("\nSummary:")
            report.append(f"Total Symbols Analyzed: {alerts['summary']['total_symbols']}")
            report.append(f"Significant Changes Detected: {alerts['summary']['significant_changes']}")
            report.append(f"Positive Changes: {alerts['summary']['positive_changes']}")
            report.append(f"Negative Changes: {alerts['summary']['negative_changes']}")
            
            # Add significant price changes
            if alerts['significant_changes']:
                report.append("\nSignificant Price Changes:")
                report.append("-" * 50)
                for change in alerts['significant_changes']:
                    direction = "↑" if change['direction'] == 'increase' else "↓"
                    report.append(
                        f"{direction} {change['symbol']} ({change['company']}): "
                        f"${change['previous_price']:.2f} → ${change['current_price']:.2f} "
                        f"({change['change_pct']:.2f}%)"
                    )
            
            # Add daily change alerts
            if alerts['daily_change_alerts']:
                report.append("\nSignificant Daily Change Changes:")
                report.append("-" * 50)
                for alert in alerts['daily_change_alerts']:
                    direction = "↑" if alert['change_diff'] > 0 else "↓"
                    report.append(
                        f"{direction} {alert['symbol']} ({alert['company']}): "
                        f"Daily Change: {alert['previous_daily_change']:.2f}% → "
                        f"{alert['current_daily_change']:.2f}% "
                        f"(Change: {alert['change_diff']:.2f}%)"
                    )
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return "Error generating report."
            
    def __del__(self):
        """Close the database connection when the object is destroyed"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
                logger.info("Closed database connection")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}") 