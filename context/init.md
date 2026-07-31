# Blueprint: Free Indian Stock Market Data Agent (NSE/BSE)

---

## 1. System Requirements & Dependencies

Ensure your project environment has the following core python packages initialized:

```bash
pip install yfinance pandas pandas-ta beautifulsoup4 requests lxml
```

---

## 2. Core Python Core Implementation Code

```python
import requests
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from bs4 import BeautifulSoup

class IndianMarketDataEngine:
    """
    Unified engine to extract fundamentals, financial statements,
    technical indicators, and peer comparisons for Indian Stocks.
    """
    
    def __init__(self, symbol: str):
        """
        Args:
            symbol (str): Clean stock ticker without suffix (e.g., 'RELIANCE', 'TCS', 'INFY')
        """
        self.raw_symbol = symbol.upper().strip()
        self.nse_ticker = f"{self.raw_symbol}.NS"
        self.bse_ticker = f"{self.raw_symbol}.BO"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def fetch_fundamentals_and_statements(self):
        """
        Category: Fundamentals & Financial Statements
        Extracts valuation ratios and multi-year corporate financial sheets.
        """
        ticker = yf.Ticker(self.nse_ticker)
        info = ticker.info
        
        # 1. Summary Fundamentals
        ratios = {
            "Ticker": self.nse_ticker,
            "Current Price": info.get("currentPrice"),
            "Trailing PE": info.get("trailingPE"),
            "Forward PE": info.get("forwardPE"),
            "Price to Book (PB)": info.get("priceToBook"),
            "Dividend Yield": info.get("dividendYield"),
            "Market Cap": info.get("marketCap"),
            "ROE": info.get("returnOnEquity"),
            "Debt to Equity": info.get("debtToEquity")
        }
        
        # 2. Financial Statements (Pandas DataFrames)
        income_statement = ticker.financials      # Profit & Loss Account
        balance_sheet = ticker.balance_sheet    # Balance Sheet Matrix
        cash_flow = ticker.cashflow             # Cash Flow Data Rows
        
        return ratios, income_statement, balance_sheet, cash_flow

    def compute_technical_indicators(self, period: str = "1y", interval: str = "1d"):
        """
        Category: Technical Analysis
        Downloads raw OHLCV pricing and maps mathematical equations locally.
        """
        # Fetch historical structural windows
        df = yf.download(self.nse_ticker, period=period, interval=interval, progress=False)
        if df.empty:
            raise ValueError(f"No historical valuation returns for symbol: {self.nse_ticker}")
            
        # Clean yfinance MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
        # Append Exponential Moving Averages (EMA)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['EMA_50'] = ta.ema(df['Close'], length=50)
        df['EMA_200'] = ta.ema(df['Close'], length=200)
        
        # Append Relative Strength Index (RSI)
        df['RSI_14'] = ta.rsi(df['Close'], length=14)
        
        # Append MACD (Moving Average Convergence Divergence)
        macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        
        return df

    def extract_peer_analysis(self):
        """
        Category: Peer Comparison Analysis
        Scrapes domestic comparative sector metrics from Screener India.
        """
        url = f"https://screener.in{self.raw_symbol}/"
        response = requests.get(url, headers=self.headers, timeout=15)
        
        if response.status_code != 200:
            return f"Failed web connection interface check. Status: {response.status_code}"
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Locate the specific DOM section object for sector peers
        peer_section = soup.find('section', {'id': 'peers'})
        if not peer_section:
            return "No domestic peer presentation elements present in DOM."
            
        table_element = peer_section.find('table', {'class': 'data-table'})
        if not table_element:
            return "Nested data-table structural matrix missing inside peer window."
            
        # Convert HTML raw tree directly to Pandas dataframe lists
        dfs = pd.read_html(str(table_element))
        clean_df = dfs[0]
        
        # Strip indexing artifacts for processing
        if 'S.No.' in clean_df.columns:
            clean_df = clean_df.drop(columns=['S.No.'])
            
        return clean_df

# ==========================================
# Execution Verification Check Routine
# ==========================================
if __name__ == "__main__":
    print("[1/4] Booting Engine pipeline for: RELIANCE...")
    engine = IndianMarketDataEngine("RELIANCE")
    
    # 1. Fundamentals Verification
    print("\n--- Extracting Valuation Ratios ---")
    ratios, income, balance, cash = engine.fetch_fundamentals_and_statements()
    print(f"PE Ratio: {ratios['Trailing PE']} | PB Ratio: {ratios['Price to Book (PB)']}")
    
    # 2. Technicals Verification
    print("\n--- Calculating Local Technical Indicators ---")
    tech_df = engine.compute_technical_indicators()
    print(tech_df[['Close', 'EMA_20', 'RSI_14']].tail(5))
    
    # 3. Peers Verification
    print("\n--- Fetching Domestic Industry Peer Group Matrix ---")
    peer_matrix = engine.extract_peer_analysis()
    if isinstance(peer_matrix, pd.DataFrame):
        print(peer_matrix.head(5))
    else:
        print(peer_matrix)
```

---

## 3. Implementation Guardrails for Your AI Agent
Instruct Claude or Cursor to adhere strictly to these engineering parameters:
1. **Handling Empty Values:** Free data sets contain `NaN` values for specific metrics during quarter-transition windows. Ensure calculations use `.fillna(method='ffill')` or handle dictionary keys gracefully using `.get()`.
2. **Scraping Blockages:** If Screener introduces custom proxy firewalls, instruct your agent to shift headers toward rotating User-Agents or add an inline delay (`time.sleep(2)`) between iterative stock lists.
3. **Dataframe Formatting:** When printing or saving output dataframes, explicitly drop MultiIndex layers that `yfinance` creates dynamically depending on the version package installed.
