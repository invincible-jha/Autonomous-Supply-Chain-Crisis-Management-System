"""
External data source integrations.
"""
from .news_api import NewsAPIIntegration
from .weather_api import WeatherAPIIntegration

__all__ = ['NewsAPIIntegration', 'WeatherAPIIntegration']
