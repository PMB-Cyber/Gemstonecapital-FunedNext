import yfinance as yf
from textblob import TextBlob
from fundednext_trading_system.monitoring.logger import logger

class NewsSentiment:
    def get_sentiment(self, symbol):
        """
        Fetches news for a given symbol and returns an aggregate sentiment score.
        """
        try:
            # Append '=X' for forex pairs
            if len(symbol) == 6 and symbol.isalpha():
                symbol += "=X"
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if not news:
                return 0.0

            sentiment_scores = []
            for article in news:
                title = article.get('title', '')
                analysis = TextBlob(title)
                sentiment_scores.append(analysis.sentiment.polarity)

            if not sentiment_scores:
                return 0.0

            return sum(sentiment_scores) / len(sentiment_scores)

        except Exception as e:
            logger.error(f"Error fetching or analyzing news for {symbol}: {e}")
            return 0.0
