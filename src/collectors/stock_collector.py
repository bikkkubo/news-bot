import yfinance as yf
import logging
from typing import Dict, Any
from src.config import MARKET_NAMES

logger = logging.getLogger(__name__)

class StockDataCollector:
    def __init__(self):
        # Mapping of internal keys to Yahoo Finance tickers
        self.tickers = {
            "DOW": "^DJI",
            "NASDAQ": "^IXIC",
            "SP500": "^GSPC",
            "NIKKEI": "^N225"
        }

    def fetch_stock_prices(self) -> Dict[str, Any]:
        """
        Fetch stock data for the defined tickers.
        Returns a dictionary with market names as keys and data as values.
        """
        stock_data = {}
        
        for key, ticker_symbol in self.tickers.items():
            market_name = MARKET_NAMES.get(key, key)
            try:
                ticker = yf.Ticker(ticker_symbol)
                # Get the latest history (1 day)
                hist = ticker.history(period="2d")
                
                if len(hist) >= 1:
                    # Use the most recent close
                    current_close = hist['Close'].iloc[-1]
                    
                    # Calculate change if we have previous day data
                    if len(hist) >= 2:
                        prev_close = hist['Close'].iloc[-2]
                        change = current_close - prev_close
                        change_pct = (change / prev_close) * 100
                    else:
                        # Fallback if only 1 day data is available (e.g. new listing or API limit)
                        # Try to get previous close from info
                        info = ticker.info
                        prev_close = info.get('previousClose', current_close)
                        change = current_close - prev_close
                        change_pct = (change / prev_close) * 100

                    stock_data[market_name] = {
                        "close": round(current_close, 2),
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2),
                        "symbol": ticker_symbol
                    }
                    logger.info(f"Fetched data for {market_name}: {stock_data[market_name]}")
                else:
                    logger.warning(f"No history data found for {market_name} ({ticker_symbol})")
                    
            except Exception as e:
                logger.error(f"Error fetching data for {market_name} ({ticker_symbol}): {e}")
                # Continue to next ticker even if one fails
                continue
                
        return stock_data

if __name__ == "__main__":
    # Simple test
    collector = StockDataCollector()
    print(collector.fetch_stock_prices())
