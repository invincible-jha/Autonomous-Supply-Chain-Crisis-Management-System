"""
OpenWeatherMap API integration for weather event monitoring.
"""
import os
import logging
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeatherAPIIntegration:
    """
    Integration with OpenWeatherMap API for weather event monitoring.

    Monitors weather conditions and alerts for supply chain impacts:
    - Severe weather warnings
    - Natural disasters
    - Extreme temperatures
    - Precipitation and flooding
    - Wind and storms
    """

    # OpenWeatherMap API endpoints
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"

    # Severity thresholds
    SEVERE_WEATHER_CODES = {
        # Thunderstorm group (2xx)
        200: ('low', 'Thunderstorm with light rain'),
        201: ('medium', 'Thunderstorm with rain'),
        202: ('high', 'Thunderstorm with heavy rain'),
        210: ('medium', 'Light thunderstorm'),
        211: ('high', 'Thunderstorm'),
        212: ('critical', 'Heavy thunderstorm'),
        221: ('medium', 'Ragged thunderstorm'),
        230: ('medium', 'Thunderstorm with light drizzle'),
        231: ('medium', 'Thunderstorm with drizzle'),
        232: ('high', 'Thunderstorm with heavy drizzle'),

        # Drizzle group (3xx) - Low severity for supply chain
        # Snow group (6xx)
        600: ('low', 'Light snow'),
        601: ('medium', 'Snow'),
        602: ('high', 'Heavy snow'),
        611: ('medium', 'Sleet'),
        612: ('high', 'Light shower sleet'),
        613: ('high', 'Shower sleet'),
        615: ('medium', 'Light rain and snow'),
        616: ('medium', 'Rain and snow'),
        620: ('medium', 'Light shower snow'),
        621: ('high', 'Shower snow'),
        622: ('critical', 'Heavy shower snow'),

        # Atmosphere group (7xx)
        701: ('low', 'Mist'),
        711: ('medium', 'Smoke'),
        721: ('low', 'Haze'),
        731: ('medium', 'Sand/dust whirls'),
        741: ('medium', 'Fog'),
        751: ('medium', 'Sand'),
        761: ('medium', 'Dust'),
        762: ('critical', 'Volcanic ash'),
        771: ('high', 'Squalls'),
        781: ('critical', 'Tornado'),

        # Extreme weather (9xx - hypothetical, mapped from descriptions)
        900: ('critical', 'Tornado'),
        901: ('critical', 'Tropical storm'),
        902: ('critical', 'Hurricane'),
        903: ('medium', 'Cold'),
        904: ('medium', 'Hot'),
        905: ('high', 'Windy'),
        906: ('critical', 'Hail'),
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenWeatherMap API client.

        Args:
            api_key: OpenWeatherMap API key (or set OPENWEATHERMAP_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENWEATHERMAP_API_KEY')

        if not self.api_key:
            logger.warning("OpenWeatherMap API key not provided. Set OPENWEATHERMAP_API_KEY environment variable.")
        else:
            logger.info("OpenWeatherMap API client initialized successfully")

    def is_available(self) -> bool:
        """Check if Weather API is available and configured."""
        return self.api_key is not None

    def fetch_weather_for_location(self,
                                   latitude: float,
                                   longitude: float,
                                   location_name: str = "Unknown") -> Optional[Dict[str, Any]]:
        """
        Fetch current weather and alerts for a specific location.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            location_name: Human-readable location name

        Returns:
            Weather event dictionary or None
        """
        if not self.is_available():
            logger.warning("Weather API not available")
            return None

        try:
            # Fetch current weather
            url = f"{self.BASE_URL}/weather"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse weather data
            event = self._parse_weather_data(data, location_name)

            if event:
                logger.info(f"Fetched weather for {location_name}: {event.get('title')}")

            return event

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather for {location_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in weather fetch: {e}")
            return None

    def fetch_weather_for_locations(self,
                                    locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fetch weather for multiple locations.

        Args:
            locations: List of location dicts with 'latitude', 'longitude', 'name'

        Returns:
            List of weather event dictionaries
        """
        if not self.is_available():
            return []

        events = []
        for location in locations:
            lat = location.get('latitude')
            lon = location.get('longitude')
            name = location.get('name', 'Unknown')

            if lat is not None and lon is not None:
                event = self.fetch_weather_for_location(lat, lon, name)
                if event:
                    events.append(event)

        logger.info(f"Fetched weather for {len(events)} locations")
        return events

    def fetch_severe_weather_alerts(self,
                                    latitude: float,
                                    longitude: float,
                                    location_name: str = "Unknown") -> List[Dict[str, Any]]:
        """
        Fetch severe weather alerts for a location.

        Note: Requires OpenWeatherMap One Call API (subscription).
        Falls back to current weather if not available.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            location_name: Human-readable location name

        Returns:
            List of alert dictionaries
        """
        if not self.is_available():
            return []

        try:
            # Try One Call API for alerts (requires subscription)
            url = self.ONECALL_URL
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'exclude': 'minutely,hourly,daily',
                'units': 'metric'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                alerts = data.get('alerts', [])

                parsed_alerts = []
                for alert in alerts:
                    parsed_alert = self._parse_alert(alert, location_name, latitude, longitude)
                    if parsed_alert:
                        parsed_alerts.append(parsed_alert)

                return parsed_alerts
            else:
                # Fall back to current weather check
                logger.debug(f"One Call API not available, using current weather for {location_name}")
                event = self.fetch_weather_for_location(latitude, longitude, location_name)
                return [event] if event and event.get('severity_score', 0) > 50 else []

        except Exception as e:
            logger.error(f"Error fetching weather alerts for {location_name}: {e}")
            return []

    def _parse_weather_data(self, data: Dict, location_name: str) -> Optional[Dict[str, Any]]:
        """
        Parse OpenWeatherMap response into standardized event format.

        Args:
            data: OpenWeatherMap API response
            location_name: Location name

        Returns:
            Parsed event dictionary or None
        """
        try:
            weather = data.get('weather', [{}])[0]
            weather_code = weather.get('id', 0)
            weather_main = weather.get('main', 'Unknown')
            weather_description = weather.get('description', '')

            main = data.get('main', {})
            wind = data.get('wind', {})

            # Calculate severity
            severity_info = self.SEVERE_WEATHER_CODES.get(weather_code, ('low', weather_description))
            severity_level, severity_description = severity_info

            # Map severity to score
            severity_map = {'low': 20, 'medium': 50, 'high': 75, 'critical': 95}
            severity_score = severity_map.get(severity_level, 20)

            # Adjust severity based on additional factors
            temp = main.get('temp', 20)
            wind_speed = wind.get('speed', 0)

            # Extreme temperatures
            if temp < -10 or temp > 45:
                severity_score = min(100, severity_score + 20)
                severity_description += f" (Extreme temp: {temp}°C)"

            # High winds
            if wind_speed > 20:  # > 72 km/h
                severity_score = min(100, severity_score + 15)
                severity_description += f" (High winds: {wind_speed} m/s)"

            # Only create event if severity is meaningful
            if severity_score < 30:
                return None

            coords = data.get('coord', {})
            event = {
                'event_id': f"weather_{location_name}_{datetime.now().strftime('%Y%m%d%H')}",
                'source': 'openweathermap',
                'event_type': 'weather',
                'title': f"{severity_level.title()} Weather: {weather_main} in {location_name}",
                'description': f"{severity_description}. Temperature: {temp}°C, Wind: {wind_speed} m/s",
                'url': f"https://openweathermap.org/city/{data.get('id')}",
                'published_at': datetime.utcfromtimestamp(data.get('dt', datetime.now().timestamp())),
                'location_country': data.get('sys', {}).get('country'),
                'location_city': location_name,
                'latitude': coords.get('lat'),
                'longitude': coords.get('lon'),
                'severity_score': severity_score,
                'confidence_score': 0.9,  # Weather data is high confidence
                'raw_data': data,
                'processed': False
            }

            return event

        except Exception as e:
            logger.error(f"Error parsing weather data: {e}")
            return None

    def _parse_alert(self,
                    alert: Dict,
                    location_name: str,
                    latitude: float,
                    longitude: float) -> Optional[Dict[str, Any]]:
        """
        Parse weather alert into standardized event format.

        Args:
            alert: Weather alert from One Call API
            location_name: Location name
            latitude: Latitude
            longitude: Longitude

        Returns:
            Parsed event dictionary
        """
        try:
            event_name = alert.get('event', 'Weather Alert')
            description = alert.get('description', '')
            start_time = datetime.utcfromtimestamp(alert.get('start', datetime.now().timestamp()))

            # Determine severity from alert event name
            severity_score = self._calculate_alert_severity(event_name, description)

            event = {
                'event_id': f"weather_alert_{location_name}_{start_time.strftime('%Y%m%d%H%M')}",
                'source': 'openweathermap_alert',
                'event_type': 'weather',
                'title': f"Weather Alert: {event_name} - {location_name}",
                'description': description,
                'url': None,
                'published_at': start_time,
                'location_city': location_name,
                'latitude': latitude,
                'longitude': longitude,
                'severity_score': severity_score,
                'confidence_score': 0.95,  # Official alerts are very high confidence
                'raw_data': alert,
                'processed': False
            }

            return event

        except Exception as e:
            logger.error(f"Error parsing weather alert: {e}")
            return None

    def _calculate_alert_severity(self, event_name: str, description: str) -> float:
        """
        Calculate severity score for weather alert.

        Args:
            event_name: Alert event name
            description: Alert description

        Returns:
            Severity score (0-100)
        """
        text = f"{event_name} {description}".lower()

        critical_keywords = ['hurricane', 'tornado', 'typhoon', 'cyclone', 'tsunami', 'earthquake']
        high_keywords = ['severe', 'extreme', 'warning', 'dangerous', 'flooding', 'storm']
        medium_keywords = ['alert', 'watch', 'advisory', 'wind', 'rain', 'snow']

        if any(keyword in text for keyword in critical_keywords):
            return 95
        elif any(keyword in text for keyword in high_keywords):
            return 75
        elif any(keyword in text for keyword in medium_keywords):
            return 50
        else:
            return 30

    def get_api_usage(self) -> Dict[str, Any]:
        """
        Get API usage information.

        Returns:
            Dictionary with usage information
        """
        return {
            'available': self.is_available(),
            'note': 'Free tier: 1000 calls/day. Check dashboard at https://home.openweathermap.org/api_keys'
        }
