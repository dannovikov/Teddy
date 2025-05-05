import yfinance as yf

def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info
    except Exception:
        return {}

def format_stock_info(ticker):
    info = get_stock_info(ticker)
    name = info.get('shortName', 'N/A')
    current_price = info.get('currentPrice', 'N/A')
    currency = info.get('currency', 'N/A')
    formatted_text = f"Stock: {name} (Ticker: {ticker})\nPrice: {current_price} {currency}"
    return formatted_text
