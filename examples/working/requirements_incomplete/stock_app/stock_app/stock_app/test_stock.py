import pytest
from stock_app import stock

def test_get_stock_info_valid():
    info = stock.get_stock_info('AAPL')
    assert 'shortName' in info
    assert 'regularMarketPrice' in info or 'currentPrice' in info

def test_format_stock_info():
    formatted = stock.format_stock_info('AAPL')
    assert "Stock" in formatted
    assert "Price" in formatted

def test_format_stock_info_invalid_ticker():
    # Using a likely invalid ticker
    formatted = stock.format_stock_info('INVALID_TICKER')
    assert "N/A" in formatted or "Invalid" in formatted
