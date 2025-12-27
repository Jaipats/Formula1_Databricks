"""
OpenF1 API Client
Handles API requests with rate limiting, error handling, and retry logic
"""

import requests
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenF1Client:
    """Client for interacting with OpenF1 API"""
    
    def __init__(self, base_url: str, rate_limit_delay: float = 1.0, 
                 timeout: int = 30, retry_attempts: int = 3):
        """
        Initialize API client
        
        Args:
            base_url: Base URL for the API
            rate_limit_delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.last_request_time = 0
        
    def _rate_limit_wait(self):
        """Wait if necessary to respect rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Make API request with retry logic
        
        Args:
            endpoint: API endpoint (e.g., 'sessions', 'drivers')
            params: Query parameters
            
        Returns:
            List of records from API
        """
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                self._rate_limit_wait()
                
                logger.info(f"Fetching {endpoint} with params: {params}")
                response = requests.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully fetched {len(data)} records from {endpoint}")
                return data
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {endpoint}")
                if attempt == self.retry_attempts - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.HTTPError as e:
                # Handle 422 errors (data not available) gracefully
                if e.response.status_code == 422:
                    logger.info(f"Data not available for {endpoint} with params {params} (422 error)")
                    return []  # Return empty list instead of raising
                logger.error(f"HTTP error on attempt {attempt + 1} for {endpoint}: {str(e)}")
                if attempt == self.retry_attempts - 1:
                    raise
                time.sleep(2 ** attempt)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error on attempt {attempt + 1} for {endpoint}: {str(e)}")
                if attempt == self.retry_attempts - 1:
                    raise
                time.sleep(2 ** attempt)
        
        return []
    
    def get_meetings(self, year: int) -> List[Dict]:
        """
        Get all meetings (race weekends) for a year
        
        Args:
            year: Year to fetch
            
        Returns:
            List of meeting records
        """
        return self._make_request('meetings', {'year': year})
    
    def get_sessions(self, year: int = None, meeting_key: int = None) -> List[Dict]:
        """
        Get sessions
        
        Args:
            year: Year to fetch
            meeting_key: Specific meeting key
            
        Returns:
            List of session records
        """
        params = {}
        if year:
            params['year'] = year
        if meeting_key:
            params['meeting_key'] = meeting_key
            
        return self._make_request('sessions', params)
    
    def get_drivers(self, session_key: int) -> List[Dict]:
        """Get drivers for a specific session"""
        return self._make_request('drivers', {'session_key': session_key})
    
    def get_laps(self, session_key: int, driver_number: int = None) -> List[Dict]:
        """Get lap data for a session"""
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        return self._make_request('laps', params)
    
    def get_car_data(self, session_key: int, driver_number: int) -> List[Dict]:
        """Get car telemetry data for a specific driver in a session"""
        params = {
            'session_key': session_key,
            'driver_number': driver_number
        }
        return self._make_request('car_data', params)
    
    def get_position(self, session_key: int, driver_number: int = None) -> List[Dict]:
        """Get position data"""
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        return self._make_request('position', params)
    
    def get_pit_stops(self, session_key: int) -> List[Dict]:
        """Get pit stop data"""
        return self._make_request('pit', {'session_key': session_key})
    
    def get_stints(self, session_key: int) -> List[Dict]:
        """Get stint data (tyre strategies)"""
        return self._make_request('stints', {'session_key': session_key})
    
    def get_weather(self, session_key: int) -> List[Dict]:
        """Get weather data"""
        return self._make_request('weather', {'session_key': session_key})
    
    def get_race_control(self, session_key: int) -> List[Dict]:
        """Get race control messages"""
        return self._make_request('race_control', {'session_key': session_key})
    
    def get_team_radio(self, session_key: int) -> List[Dict]:
        """Get team radio communications"""
        return self._make_request('team_radio', {'session_key': session_key})
    
    def get_intervals(self, session_key: int) -> List[Dict]:
        """Get interval data between cars"""
        return self._make_request('intervals', {'session_key': session_key})
    
    def get_location(self, session_key: int, driver_number: int) -> List[Dict]:
        """Get location data for a specific driver"""
        params = {
            'session_key': session_key,
            'driver_number': driver_number
        }
        return self._make_request('location', params)
    
    def get_overtakes(self, session_key: int) -> List[Dict]:
        """Get overtake data (beta)"""
        return self._make_request('overtakes', {'session_key': session_key})
    
    def get_session_result(self, session_key: int) -> List[Dict]:
        """Get session results (beta)"""
        return self._make_request('session_result', {'session_key': session_key})
    
    def get_starting_grid(self, session_key: int) -> List[Dict]:
        """Get starting grid positions (beta)"""
        return self._make_request('starting_grid', {'session_key': session_key})

