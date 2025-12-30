import unittest
from unittest.mock import patch, MagicMock
from fundednext_trading_system.trading_core.news_sentiment import NewsSentiment
from textblob import TextBlob

class TestNewsSentiment(unittest.TestCase):

    @patch('yfinance.Ticker')
    def test_get_sentiment_success(self, mock_ticker):
        # Mock the yfinance Ticker object
        instance = mock_ticker.return_value
        instance.news = [
            {'title': 'good'},
            {'title': 'bad'},
        ]

        # Initialize the news sentiment class and get sentiment
        sentiment = NewsSentiment()
        score = sentiment.get_sentiment('AAPL')

        # Calculate expected score to be more robust
        expected_score = (TextBlob('good').sentiment.polarity + TextBlob('bad').sentiment.polarity) / 2
        self.assertAlmostEqual(score, expected_score)

    @patch('yfinance.Ticker')
    def test_get_sentiment_no_news(self, mock_ticker):
        # Mock the yfinance Ticker object with no news
        instance = mock_ticker.return_value
        instance.news = []

        # Initialize the news sentiment class and get sentiment
        sentiment = NewsSentiment()
        score = sentiment.get_sentiment('AAPL')

        # Assertions
        self.assertEqual(score, 0.0)

    @patch('yfinance.Ticker')
    def test_get_sentiment_api_error(self, mock_ticker):
        # Mock the yfinance Ticker to raise an exception
        mock_ticker.side_effect = Exception("API Error")

        # Initialize the news sentiment class and get sentiment
        sentiment = NewsSentiment()
        score = sentiment.get_sentiment('AAPL')

        # Assertions
        self.assertEqual(score, 0.0)

if __name__ == '__main__':
    unittest.main()
