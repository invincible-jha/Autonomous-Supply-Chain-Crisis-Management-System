"""
NewsAPI integration for geopolitical event monitoring.
"""
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException

logger = logging.getLogger(__name__)


class NewsAPIIntegration:
    """
    Integration with NewsAPI for geopolitical event monitoring.

    Monitors news sources for supply chain relevant events like:
    - Trade sanctions and tariffs
    - Border closures and restrictions
    - Political unrest and conflicts
    - Regulatory changes
    - Major policy announcements
    """

    # Keywords to search for supply chain disruptions
    GEOPOLITICAL_KEYWORDS = [
        'sanctions', 'tariff', 'trade war', 'border closure', 'embargo',
        'political unrest', 'military conflict', 'coup', 'protests',
        'strike', 'labor dispute', 'port closure', 'transportation ban',
        'export ban', 'import restriction', 'supply chain', 'shortage'
    ]

    # High-risk regions to monitor
    HIGH_RISK_REGIONS = {
        'Eastern Europe': ['Ukraine', 'Russia', 'Belarus', 'Moldova'],
        'Middle East': ['Iran', 'Iraq', 'Syria', 'Yemen', 'Israel', 'Palestine'],
        'East Asia': ['China', 'Taiwan', 'North Korea', 'South Korea'],
        'South Asia': ['Pakistan', 'Afghanistan', 'Myanmar']
    }

    # Supply chain related categories
    RELEVANT_CATEGORIES = ['business', 'technology']

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NewsAPI client.

        Args:
            api_key: NewsAPI key (or set NEWSAPI_KEY environment variable)
        """
        self.api_key = api_key or os.getenv('NEWSAPI_KEY')

        if not self.api_key:
            logger.warning("NewsAPI key not provided. Set NEWSAPI_KEY environment variable.")
            self.client = None
        else:
            try:
                self.client = NewsApiClient(api_key=self.api_key)
                logger.info("NewsAPI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize NewsAPI client: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Check if NewsAPI is available and configured."""
        return self.client is not None

    def fetch_geopolitical_events(self,
                                  hours_back: int = 24,
                                  max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch geopolitical events from NewsAPI.

        Args:
            hours_back: Number of hours to look back
            max_results: Maximum number of results to return

        Returns:
            List of event dictionaries
        """
        if not self.is_available():
            logger.warning("NewsAPI not available, returning empty results")
            return []

        events = []
        from_date = datetime.now() - timedelta(hours=hours_back)
        to_date = datetime.now()

        try:
            # Search for each keyword
            for keyword in self.GEOPOLITICAL_KEYWORDS[:5]:  # Limit to avoid rate limits
                try:
                    response = self.client.get_everything(
                        q=keyword,
                        from_param=from_date.isoformat(),
                        to=to_date.isoformat(),
                        language='en',
                        sort_by='publishedAt',
                        page_size=min(20, max_results)
                    )

                    if response['status'] == 'ok':
                        articles = response.get('articles', [])
                        for article in articles:
                            event = self._parse_article(article, keyword)
                            if event:
                                events.append(event)

                        logger.info(f"Fetched {len(articles)} articles for keyword '{keyword}'")
                    else:
                        logger.warning(f"NewsAPI returned status: {response.get('status')}")

                except NewsAPIException as e:
                    logger.error(f"NewsAPI error for keyword '{keyword}': {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error fetching news for '{keyword}': {e}")
                    continue

            # Deduplicate by URL
            events = self._deduplicate_events(events)
            logger.info(f"Fetched {len(events)} unique geopolitical events")

            return events[:max_results]

        except Exception as e:
            logger.error(f"Error fetching geopolitical events: {e}")
            return []

    def fetch_by_region(self,
                       region_countries: List[str],
                       hours_back: int = 24,
                       max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch events for specific countries/regions.

        Args:
            region_countries: List of country names to search
            hours_back: Number of hours to look back
            max_results: Maximum number of results

        Returns:
            List of event dictionaries
        """
        if not self.is_available():
            return []

        events = []
        from_date = datetime.now() - timedelta(hours=hours_back)
        to_date = datetime.now()

        for country in region_countries[:3]:  # Limit to avoid rate limits
            try:
                # Search for supply chain + country
                query = f'"{country}" AND (supply chain OR shortage OR disruption OR sanctions)'

                response = self.client.get_everything(
                    q=query,
                    from_param=from_date.isoformat(),
                    to=to_date.isoformat(),
                    language='en',
                    sort_by='publishedAt',
                    page_size=20
                )

                if response['status'] == 'ok':
                    articles = response.get('articles', [])
                    for article in articles:
                        event = self._parse_article(article, f"regional:{country}")
                        if event:
                            event['location_country'] = country
                            events.append(event)

            except Exception as e:
                logger.error(f"Error fetching news for {country}: {e}")
                continue

        events = self._deduplicate_events(events)
        return events[:max_results]

    def _parse_article(self, article: Dict, keyword: str) -> Optional[Dict[str, Any]]:
        """
        Parse NewsAPI article into standardized event format.

        Args:
            article: NewsAPI article dictionary
            keyword: Keyword that matched this article

        Returns:
            Parsed event dictionary or None if parsing fails
        """
        try:
            # Extract publication date
            published_at_str = article.get('publishedAt', '')
            published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))

            # Calculate severity score based on title/description
            title = article.get('title', '')
            description = article.get('description', '')
            severity = self._calculate_severity(title, description)

            # Calculate confidence score
            confidence = self._calculate_confidence(article, keyword)

            # Extract location if possible
            location = self._extract_location(title, description)

            event = {
                'event_id': f"news_{hash(article.get('url', ''))}",
                'source': 'newsapi',
                'event_type': 'geopolitical',
                'title': title[:500] if title else 'Untitled',
                'description': description[:1000] if description else '',
                'url': article.get('url'),
                'published_at': published_at,
                'location_country': location.get('country'),
                'location_region': location.get('region'),
                'location_city': location.get('city'),
                'severity_score': severity,
                'confidence_score': confidence,
                'raw_data': article,
                'processed': False
            }

            return event

        except Exception as e:
            logger.error(f"Error parsing article: {e}")
            return None

    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """Deduplicate events by URL."""
        seen_urls = set()
        unique_events = []

        for event in events:
            url = event.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_events.append(event)

        return unique_events

    def _calculate_severity(self, title: str, description: str) -> float:
        """
        Calculate severity score (0-100) based on content.

        High severity keywords: war, crisis, emergency, critical, shutdown
        Medium severity keywords: disruption, delay, shortage, strike
        Low severity keywords: concern, warning, potential, risk
        """
        text = f"{title} {description}".lower()

        high_severity_keywords = [
            'war', 'crisis', 'emergency', 'critical', 'shutdown', 'collapse',
            'catastrophe', 'disaster', 'devastation', 'closure', 'blockade'
        ]
        medium_severity_keywords = [
            'disruption', 'delay', 'shortage', 'strike', 'protest', 'conflict',
            'suspension', 'restriction', 'ban', 'sanction', 'embargo'
        ]
        low_severity_keywords = [
            'concern', 'warning', 'potential', 'risk', 'threat', 'worry',
            'issue', 'problem', 'challenge', 'uncertainty'
        ]

        high_count = sum(1 for keyword in high_severity_keywords if keyword in text)
        medium_count = sum(1 for keyword in medium_severity_keywords if keyword in text)
        low_count = sum(1 for keyword in low_severity_keywords if keyword in text)

        # Calculate weighted score
        score = (high_count * 80) + (medium_count * 50) + (low_count * 20)

        # Normalize to 0-100
        return min(100, score)

    def _calculate_confidence(self, article: Dict, keyword: str) -> float:
        """
        Calculate confidence score (0-1) based on article quality.

        Factors:
        - Source reputation
        - Article completeness
        - Keyword relevance
        """
        score = 0.5  # Base score

        # Check source quality (simplified)
        source = article.get('source', {}).get('name', '').lower()
        reputable_sources = [
            'reuters', 'bloomberg', 'financial times', 'wall street journal',
            'bbc', 'cnn', 'associated press', 'the guardian'
        ]
        if any(rep in source for rep in reputable_sources):
            score += 0.2

        # Check completeness
        if article.get('title') and article.get('description'):
            score += 0.1
        if article.get('content'):
            score += 0.1

        # Check keyword relevance
        title = article.get('title', '').lower()
        if keyword.lower() in title:
            score += 0.1

        return min(1.0, score)

    def _extract_location(self, title: str, description: str) -> Dict[str, Optional[str]]:
        """
        Extract location information from text.

        Uses simple keyword matching for now.
        In production, use NLP/NER for better extraction.
        """
        text = f"{title} {description}".lower()

        location = {
            'country': None,
            'region': None,
            'city': None
        }

        # Check for country mentions
        for region, countries in self.HIGH_RISK_REGIONS.items():
            for country in countries:
                if country.lower() in text:
                    location['country'] = country
                    location['region'] = region
                    break
            if location['country']:
                break

        # Check for other major countries
        major_countries = [
            'United States', 'China', 'Japan', 'Germany', 'United Kingdom',
            'France', 'India', 'Brazil', 'Canada', 'Australia', 'Mexico'
        ]
        if not location['country']:
            for country in major_countries:
                if country.lower() in text:
                    location['country'] = country
                    break

        return location

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status from NewsAPI.

        Returns:
            Dictionary with rate limit information
        """
        if not self.is_available():
            return {'available': False}

        # NewsAPI doesn't provide direct rate limit info
        # This is a placeholder for monitoring
        return {
            'available': True,
            'note': 'Check NewsAPI dashboard for usage: https://newsapi.org/account'
        }
