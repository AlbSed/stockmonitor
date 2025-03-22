# Stock Market Monitor

A real-time stock market monitoring application that tracks stock prices, provides price alerts, and displays historical data through an interactive web interface.

## Features

- Real-time stock price monitoring
- Interactive price charts using Plotly
- Price change alerts and notifications
- Daily summary statistics
- Support for multiple data sources (Yahoo Finance, Alpha Vantage)
- Persistent data storage using DuckDB
- Modern web interface built with Streamlit

## Prerequisites

- Docker and Docker Compose
- Python 3.9 or higher (for local development)
- Alpha Vantage API key (optional, for additional data source)

## Configuration

Create a `.env` file in the project root with your configuration:

```env
# Required: Alpha Vantage API key for additional data source
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Optional: Configure stock symbols (defaults to AAPL, GOOGL, MSFT, AMZN)
STOCK_SYMBOLS=AAPL,GOOGL,MSFT,AMZN
```

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd stocks_watcher
```

2. Build and start the application:
```bash
docker compose up --build
```

3. Access the web interface at `http://localhost:8501`

### Local Development

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Project Structure

```
stocks_watcher/
├── app.py                 # Streamlit web interface
├── stock_monitor.py       # Stock monitoring service
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile            # Docker configuration
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables and configuration
├── data/               # Data storage directory
├── logs/               # Log files directory
├── clients/            # Data source clients
│   ├── __init__.py
│   ├── base_client.py  # Base client interface
│   ├── alpha_vantage.py # Alpha Vantage API client
│   └── yahoo_finance.py # Yahoo Finance client
└── utils/
    ├── __init__.py
    ├── config.py      # Configuration management
    ├── data_storage.py # Database operations
    └── logger.py      # Logging setup
```

## Usage

1. **View Current Market Status**
   - Select a stock symbol from the sidebar
   - View current price and daily changes
   - See interactive price charts

2. **Monitor Price Alerts**
   - Track significant price changes
   - View daily summary statistics
   - Monitor price trends

3. **Update Stock Data**
   - Click the "Update Stock Data" button in the sidebar
   - View real-time price updates
   - Track changes from previous data

## Data Sources

The application supports multiple data sources:
- Yahoo Finance (default)
- Alpha Vantage (optional, requires API key)

## Development

### Adding New Features

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:
```bash
git add .
git commit -m "Add your feature"
```

3. Push changes and create a pull request:
```bash
git push origin feature/your-feature-name
```

### Running Tests

```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the web interface
- [Yahoo Finance](https://finance.yahoo.com/) for stock data
- [Alpha Vantage](https://www.alphavantage.co/) for additional data source
- [DuckDB](https://duckdb.org/) for data storage
- [Plotly](https://plotly.com/) for interactive charts 