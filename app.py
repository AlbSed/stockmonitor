import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from utils.data_storage import StockDataStorage
from utils.config import load_config
from utils.logger import setup_logger
from stock_monitor import main as run_stock_monitor

# Setup logging
logger = setup_logger('StreamlitApp')

# Initialize data storage
@st.cache_resource
def get_data_storage():
    return StockDataStorage()

# Load configuration
@st.cache_data
def load_stock_config():
    return load_config()

def create_price_chart(df, symbol):
    """Create a candlestick chart for a stock"""
    fig = go.Figure(data=[go.Candlestick(
        x=df['date'],
        open=df['opening_price'],
        high=df['high_price'],
        low=df['low_price'],
        close=df['closing_price']
    )])
    
    fig.update_layout(
        title=f'{symbol} Price History',
        yaxis_title='Price ($)',
        xaxis_title='Date',
        template='plotly_dark'
    )
    
    return fig

def trigger_stock_update():
    """Trigger a stock data update"""
    try:
        run_stock_monitor(one_time=True)
        st.success("Stock data updated successfully!")
    except Exception as e:
        st.error(f"Error updating stock data: {str(e)}")
        logger.error(f"Failed to trigger stock update: {str(e)}")

def main():
    st.set_page_config(
        page_title="Stock Market Monitor",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 Stock Market Monitor")
    
    # Initialize data storage
    data_storage = get_data_storage()
    
    # Load configuration
    config = load_stock_config()
    symbols = config.get('symbols', [])
    
    # Sidebar
    st.sidebar.title("Settings")
    
    # Add update trigger button
    if st.sidebar.button("🔄 Update Stock Data"):
        trigger_stock_update()
        st.rerun()
    
    # Show last update time
    latest_data = data_storage.get_latest_data()
    if latest_data is not None and not latest_data.empty:
        try:
            last_update = pd.to_datetime(latest_data['timestamp'].iloc[0])
            st.sidebar.write(f"Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        except (KeyError, IndexError) as e:
            logger.warning(f"Could not get last update time: {str(e)}")
            st.sidebar.write("Last Update: Not available")
    
    selected_symbol = st.sidebar.selectbox(
        "Select Stock Symbol",
        symbols,
        index=0
    )
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Current Market Status")
        
        # Get latest data
        if latest_data is not None:
            # Filter for selected symbol
            symbol_data = latest_data[latest_data['Symbol'] == selected_symbol]
            if not symbol_data.empty:
                # Display current price and changes
                current_price = float(symbol_data['Current Price'].iloc[0].replace('$', ''))
                daily_change = float(symbol_data['Daily Change'].iloc[0].replace('%', ''))
                
                st.metric(
                    label=f"{selected_symbol} Current Price",
                    value=f"${current_price:.2f}",
                    delta=f"{daily_change:.2f}%"
                )
                
                # Get historical data for chart
                historical_data = data_storage.get_daily_summary(
                    date=datetime.now() - timedelta(days=30)
                )
                if historical_data is not None:
                    symbol_history = historical_data[historical_data['Symbol'] == selected_symbol]
                    if not symbol_history.empty:
                        st.plotly_chart(
                            create_price_chart(symbol_history, selected_symbol),
                            use_container_width=True
                        )
    
    with col2:
        st.subheader("Price Alerts")
        
        # Get comparison data
        if latest_data is not None:
            comparison_data = data_storage.compare_with_previous(latest_data)
            if comparison_data is not None:
                alerts = data_storage.analyze_price_changes(comparison_data)
                if alerts:
                    # Display significant changes
                    if alerts['significant_changes']:
                        st.write("Significant Price Changes:")
                        for change in alerts['significant_changes']:
                            if change['symbol'] == selected_symbol:
                                direction = "↑" if change['direction'] == 'increase' else "↓"
                                st.write(
                                    f"{direction} {change['symbol']}: "
                                    f"${change['previous_price']:.2f} → "
                                    f"${change['current_price']:.2f} "
                                    f"({change['change_pct']:.2f}%)"
                                )
    
    # Daily Summary
    st.subheader("Daily Summary")
    daily_summary = data_storage.get_daily_summary()
    if daily_summary is not None:
        symbol_summary = daily_summary[daily_summary['Symbol'] == selected_symbol]
        if not symbol_summary.empty:
            col3, col4, col5 = st.columns(3)
            
            with col3:
                st.metric(
                    "Opening Price",
                    symbol_summary['Opening Price'].iloc[0]
                )
            with col4:
                st.metric(
                    "Closing Price",
                    symbol_summary['Closing Price'].iloc[0]
                )
            with col5:
                st.metric(
                    "Average Price",
                    symbol_summary['Average Price'].iloc[0]
                )
    
    # Data Sources
    st.sidebar.subheader("Data Sources")
    if latest_data is not None:
        symbol_data = latest_data[latest_data['Symbol'] == selected_symbol]
        if not symbol_data.empty:
            st.sidebar.write(f"Sources: {symbol_data['Sources'].iloc[0]}")

if __name__ == "__main__":
    main() 