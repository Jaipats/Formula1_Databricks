"""
Data Fetcher Module
Orchestrates fetching data from OpenF1 API for all enabled endpoints
Supports parallel processing for faster data ingestion
"""

import logging
from typing import List, Dict, Any, Callable
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)


class F1DataFetcher:
    """Orchestrates data fetching from OpenF1 API"""

    def __init__(self, api_client, config, volume_writer=None):
        """
        Initialize data fetcher

        Args:
            api_client: OpenF1Client instance
            config: PipelineConfig instance
            volume_writer: Optional VolumeDataWriter for incremental storage
        """
        self.api_client = api_client
        self.config = config
        self.volume_writer = volume_writer
        self.use_volume_staging = volume_writer is not None

    def fetch_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch all enabled endpoint data for the configured year
        Supports parallel processing for faster ingestion

        Returns:
            Dictionary mapping endpoint names to DataFrames
        """
        year = self.config.target_year
        logger.info(f"Starting data fetch for year {year}")

        # Check if parallel processing is enabled
        parallel_config = self.config.config.get('api', {})
        parallel_enabled = parallel_config.get('parallel_endpoints', False)
        max_workers = parallel_config.get('max_workers', 3)

        all_data = {}

        # Step 1: Fetch meetings and sessions (always sequential - these are prerequisites)
        logger.info("Fetching meetings...")
        meetings = self.api_client.get_meetings(year)

        if not meetings:
            logger.warning(f"No meetings found for year {year}")
            return all_data

        all_data['meetings'] = pd.DataFrame(meetings)
        logger.info(f"Found {len(meetings)} meetings")

        # Step 2: Fetch sessions for all meetings
        logger.info("Fetching sessions...")
        all_sessions = []
        for meeting in meetings:
            meeting_key = meeting['meeting_key']
            sessions = self.api_client.get_sessions(meeting_key=meeting_key)
            all_sessions.extend(sessions)

        if not all_sessions:
            logger.warning("No sessions found")
            return all_data

        all_data['sessions'] = pd.DataFrame(all_sessions)
        session_keys = [s['session_key'] for s in all_sessions]
        logger.info(f"Found {len(all_sessions)} sessions")

        # Step 3: Fetch session-level data for each session
        endpoints = self.config.enabled_endpoints

        if parallel_enabled:
            logger.info(
                f"Parallel processing enabled with {max_workers} workers")
            all_data.update(self._fetch_session_data_parallel(
                session_keys, endpoints, max_workers))
        else:
            logger.info("Sequential processing (parallel disabled)")
            all_data.update(self._fetch_session_data_sequential(
                session_keys, endpoints))

        return all_data

    def _fetch_session_data_sequential(self, session_keys: List[int],
                                       endpoints: Dict[str, bool]) -> Dict[str, pd.DataFrame]:
        """
        Fetch session data sequentially (original method)

        Args:
            session_keys: List of session keys to fetch
            endpoints: Dictionary of enabled endpoints

        Returns:
            Dictionary mapping endpoint names to DataFrames
        """
        result = {}

        if endpoints.get('drivers'):
            result['drivers'] = self._fetch_drivers(session_keys)

        if endpoints.get('laps'):
            result['laps'] = self._fetch_laps(session_keys)

        if endpoints.get('pit'):
            result['pit'] = self._fetch_pit_stops(session_keys)

        if endpoints.get('stints'):
            result['stints'] = self._fetch_stints(session_keys)

        if endpoints.get('weather'):
            result['weather'] = self._fetch_weather(session_keys)

        if endpoints.get('race_control'):
            result['race_control'] = self._fetch_race_control(session_keys)

        if endpoints.get('team_radio'):
            result['team_radio'] = self._fetch_team_radio(session_keys)

        if endpoints.get('intervals'):
            result['intervals'] = self._fetch_intervals(session_keys)

        if endpoints.get('overtakes'):
            result['overtakes'] = self._fetch_overtakes(session_keys)

        if endpoints.get('session_result'):
            result['session_result'] = self._fetch_session_results(
                session_keys)

        if endpoints.get('starting_grid'):
            result['starting_grid'] = self._fetch_starting_grid(session_keys)

        # Step 4: Fetch driver-specific data (car_data, position, location)
        # These require driver numbers per session
        if endpoints.get('car_data') or endpoints.get('position') or endpoints.get('location'):
            result.update(self._fetch_driver_specific_data(
                session_keys, endpoints))

        return result

    def _fetch_session_data_parallel(self, session_keys: List[int],
                                     endpoints: Dict[str, bool],
                                     max_workers: int = 3) -> Dict[str, pd.DataFrame]:
        """
        Fetch session data in parallel for faster processing

        Args:
            session_keys: List of session keys to fetch
            endpoints: Dictionary of enabled endpoints
            max_workers: Maximum number of parallel threads

        Returns:
            Dictionary mapping endpoint names to DataFrames
        """
        result = {}

        # Define fetch tasks for each endpoint
        fetch_tasks = []

        if endpoints.get('drivers'):
            fetch_tasks.append(
                ('drivers', lambda: self._fetch_drivers(session_keys)))

        if endpoints.get('laps'):
            fetch_tasks.append(
                ('laps', lambda: self._fetch_laps(session_keys)))

        if endpoints.get('pit'):
            fetch_tasks.append(
                ('pit', lambda: self._fetch_pit_stops(session_keys)))

        if endpoints.get('stints'):
            fetch_tasks.append(
                ('stints', lambda: self._fetch_stints(session_keys)))

        if endpoints.get('weather'):
            fetch_tasks.append(
                ('weather', lambda: self._fetch_weather(session_keys)))

        if endpoints.get('race_control'):
            fetch_tasks.append(
                ('race_control', lambda: self._fetch_race_control(session_keys)))

        if endpoints.get('team_radio'):
            fetch_tasks.append(
                ('team_radio', lambda: self._fetch_team_radio(session_keys)))

        if endpoints.get('intervals'):
            fetch_tasks.append(
                ('intervals', lambda: self._fetch_intervals(session_keys)))

        if endpoints.get('overtakes'):
            fetch_tasks.append(
                ('overtakes', lambda: self._fetch_overtakes(session_keys)))

        if endpoints.get('session_result'):
            fetch_tasks.append(
                ('session_result', lambda: self._fetch_session_results(session_keys)))

        if endpoints.get('starting_grid'):
            fetch_tasks.append(
                ('starting_grid', lambda: self._fetch_starting_grid(session_keys)))

        # Execute fetch tasks in parallel
        logger.info(
            f"Starting parallel fetch for {len(fetch_tasks)} endpoints...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_endpoint = {
                executor.submit(fetch_func): endpoint_name
                for endpoint_name, fetch_func in fetch_tasks
            }

            # Process completed tasks as they finish
            for future in as_completed(future_to_endpoint):
                endpoint_name = future_to_endpoint[future]
                try:
                    data = future.result()
                    result[endpoint_name] = data
                    logger.info(
                        f"✓ Completed parallel fetch for {endpoint_name}")
                except Exception as e:
                    logger.error(
                        f"✗ Error in parallel fetch for {endpoint_name}: {str(e)}")
                    # Empty DataFrame on error
                    result[endpoint_name] = pd.DataFrame()

        # Fetch driver-specific data (car_data, position, location) after main endpoints
        # These are more complex and benefit from being done separately
        if endpoints.get('car_data') or endpoints.get('position') or endpoints.get('location'):
            logger.info("Fetching driver-specific data...")
            result.update(self._fetch_driver_specific_data(
                session_keys, endpoints))

        logger.info(
            f"✓ Parallel fetch complete for all {len(fetch_tasks)} endpoints")
        return result

    def _fetch_drivers(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch drivers for all sessions"""
        logger.info(f"Fetching drivers for {len(session_keys)} sessions...")
        all_drivers = []

        for session_key in session_keys:
            try:
                drivers = self.api_client.get_drivers(session_key)
                all_drivers.extend(drivers)
            except Exception as e:
                logger.error(
                    f"Error fetching drivers for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_drivers)} driver records")
        return pd.DataFrame(all_drivers) if all_drivers else pd.DataFrame()

    def _fetch_laps(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch laps for all sessions"""
        logger.info(f"Fetching laps for {len(session_keys)} sessions...")
        all_laps = []

        for session_key in session_keys:
            try:
                laps = self.api_client.get_laps(session_key)
                all_laps.extend(laps)
            except Exception as e:
                logger.error(
                    f"Error fetching laps for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_laps)} lap records")
        return pd.DataFrame(all_laps) if all_laps else pd.DataFrame()

    def _fetch_pit_stops(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch pit stops for all sessions"""
        logger.info(f"Fetching pit stops for {len(session_keys)} sessions...")
        all_pits = []

        for session_key in session_keys:
            try:
                pits = self.api_client.get_pit_stops(session_key)
                all_pits.extend(pits)
            except Exception as e:
                logger.error(
                    f"Error fetching pit stops for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_pits)} pit stop records")
        return pd.DataFrame(all_pits) if all_pits else pd.DataFrame()

    def _fetch_stints(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch stints for all sessions"""
        logger.info(f"Fetching stints for {len(session_keys)} sessions...")
        all_stints = []

        for session_key in session_keys:
            try:
                stints = self.api_client.get_stints(session_key)
                all_stints.extend(stints)
            except Exception as e:
                logger.error(
                    f"Error fetching stints for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_stints)} stint records")
        return pd.DataFrame(all_stints) if all_stints else pd.DataFrame()

    def _fetch_weather(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch weather for all sessions"""
        logger.info(f"Fetching weather for {len(session_keys)} sessions...")
        all_weather = []

        for session_key in session_keys:
            try:
                weather = self.api_client.get_weather(session_key)
                all_weather.extend(weather)
            except Exception as e:
                logger.error(
                    f"Error fetching weather for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_weather)} weather records")
        return pd.DataFrame(all_weather) if all_weather else pd.DataFrame()

    def _fetch_race_control(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch race control messages for all sessions"""
        logger.info(
            f"Fetching race control for {len(session_keys)} sessions...")
        all_rc = []

        for session_key in session_keys:
            try:
                rc = self.api_client.get_race_control(session_key)
                all_rc.extend(rc)
            except Exception as e:
                logger.error(
                    f"Error fetching race control for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_rc)} race control records")
        return pd.DataFrame(all_rc) if all_rc else pd.DataFrame()

    def _fetch_team_radio(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch team radio for all sessions"""
        logger.info(f"Fetching team radio for {len(session_keys)} sessions...")
        all_radio = []

        for session_key in session_keys:
            try:
                radio = self.api_client.get_team_radio(session_key)
                all_radio.extend(radio)
            except Exception as e:
                logger.error(
                    f"Error fetching team radio for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_radio)} team radio records")
        return pd.DataFrame(all_radio) if all_radio else pd.DataFrame()

    def _fetch_intervals(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch intervals for all sessions"""
        logger.info(f"Fetching intervals for {len(session_keys)} sessions...")
        all_intervals = []

        for session_key in session_keys:
            try:
                intervals = self.api_client.get_intervals(session_key)
                all_intervals.extend(intervals)
            except Exception as e:
                logger.error(
                    f"Error fetching intervals for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_intervals)} interval records")
        return pd.DataFrame(all_intervals) if all_intervals else pd.DataFrame()

    def _fetch_overtakes(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch overtakes for all sessions"""
        logger.info(f"Fetching overtakes for {len(session_keys)} sessions...")
        all_overtakes = []

        for session_key in session_keys:
            try:
                overtakes = self.api_client.get_overtakes(session_key)
                all_overtakes.extend(overtakes)
            except Exception as e:
                logger.error(
                    f"Error fetching overtakes for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_overtakes)} overtake records")
        return pd.DataFrame(all_overtakes) if all_overtakes else pd.DataFrame()

    def _fetch_session_results(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch session results for all sessions"""
        logger.info(
            f"Fetching session results for {len(session_keys)} sessions...")
        all_results = []

        for session_key in session_keys:
            try:
                results = self.api_client.get_session_result(session_key)
                all_results.extend(results)
            except Exception as e:
                logger.error(
                    f"Error fetching session results for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_results)} session result records")
        return pd.DataFrame(all_results) if all_results else pd.DataFrame()

    def _fetch_starting_grid(self, session_keys: List[int]) -> pd.DataFrame:
        """Fetch starting grid for all sessions"""
        logger.info(
            f"Fetching starting grid for {len(session_keys)} sessions...")
        all_grids = []

        for session_key in session_keys:
            try:
                grids = self.api_client.get_starting_grid(session_key)
                all_grids.extend(grids)
            except Exception as e:
                logger.error(
                    f"Error fetching starting grid for session {session_key}: {str(e)}")

        logger.info(f"Fetched {len(all_grids)} starting grid records")
        return pd.DataFrame(all_grids) if all_grids else pd.DataFrame()

    def _fetch_driver_specific_data(self, session_keys: List[int],
                                    endpoints: Dict[str, bool]) -> Dict[str, pd.DataFrame]:
        """
        Fetch driver-specific data (car_data, position, location)
        These endpoints require both session_key and driver_number

        Note: Some data may not be available for all sessions (e.g., car_data for future/recent races)
        """
        result = {}

        # First, get all driver numbers per session
        logger.info("Getting driver numbers for each session...")
        session_drivers = {}

        for session_key in session_keys:
            try:
                drivers = self.api_client.get_drivers(session_key)
                driver_numbers = [d['driver_number'] for d in drivers]
                session_drivers[session_key] = driver_numbers
            except Exception as e:
                logger.warning(
                    f"Error fetching drivers for session {session_key}: {str(e)}")

        # Fetch car_data with optional filtering and incremental writing
        if endpoints.get('car_data'):
            logger.info(
                "Fetching car data (may be unavailable for some sessions)...")
            all_car_data = []
            successful_fetches = 0
            skipped_fetches = 0

            # Get filtering options from config
            car_data_config = self.config.config.get(
                'data', {}).get('car_data_filters', {})
            speed_filter = car_data_config.get('speed_gte', None)
            sample_drivers = car_data_config.get('sample_drivers', False)

            if speed_filter:
                logger.info(
                    f"Applying speed filter: speed >= {speed_filter} km/h")

            for session_key, driver_numbers in session_drivers.items():
                # Optionally sample drivers (for testing/reducing data volume)
                if sample_drivers:
                    driver_numbers = driver_numbers[:5]
                    logger.info(
                        f"Sampling first {len(driver_numbers)} drivers for session {session_key}")

                for driver_number in driver_numbers:
                    try:
                        # Fetch with optional speed filter
                        car_data = self.api_client.get_car_data(
                            session_key, driver_number, speed_gte=speed_filter)

                        if car_data:
                            # Write incrementally to volume if enabled
                            if self.use_volume_staging:
                                batch_id = f"session_{session_key}_driver_{driver_number}"
                                self.volume_writer.write_data_batch(
                                    'car_data', car_data, batch_id)
                            else:
                                all_car_data.extend(car_data)

                            successful_fetches += 1
                            logger.info(
                                f"✓ Fetched {len(car_data)} car_data records for session {session_key}, driver {driver_number}")
                        else:
                            skipped_fetches += 1
                    except Exception as e:
                        logger.warning(
                            f"Skipping car data for session {session_key}, driver {driver_number}: {str(e)}")
                        skipped_fetches += 1

            logger.info(
                f"Car data summary: {successful_fetches} successful, {skipped_fetches} skipped")

            if not self.use_volume_staging:
                logger.info(
                    f"Total car data records in memory: {len(all_car_data)}")
                result['car_data'] = pd.DataFrame(
                    all_car_data) if all_car_data else pd.DataFrame()
            else:
                logger.info("Car data written incrementally to volume")
                # Empty - data is in volume
                result['car_data'] = pd.DataFrame()

        # Fetch position
        if endpoints.get('position'):
            logger.info("Fetching position data...")
            all_positions = []
            successful_fetches = 0
            skipped_fetches = 0

            for session_key, driver_numbers in session_drivers.items():
                for driver_number in driver_numbers:
                    try:
                        positions = self.api_client.get_position(
                            session_key, driver_number)
                        if positions:
                            all_positions.extend(positions)
                            successful_fetches += 1
                        else:
                            skipped_fetches += 1
                    except Exception as e:
                        logger.warning(
                            f"Skipping position for session {session_key}, driver {driver_number}: {str(e)}")
                        skipped_fetches += 1

            logger.info(
                f"Fetched {len(all_positions)} position records ({successful_fetches} successful, {skipped_fetches} skipped)")
            result['position'] = pd.DataFrame(
                all_positions) if all_positions else pd.DataFrame()

        # Fetch location (usually disabled due to size)
        if endpoints.get('location'):
            logger.info("Fetching location data...")
            all_locations = []
            successful_fetches = 0
            skipped_fetches = 0

            for session_key, driver_numbers in session_drivers.items():
                for driver_number in driver_numbers:
                    try:
                        locations = self.api_client.get_location(
                            session_key, driver_number)
                        if locations:
                            all_locations.extend(locations)
                            successful_fetches += 1
                        else:
                            skipped_fetches += 1
                    except Exception as e:
                        logger.warning(
                            f"Skipping location for session {session_key}, driver {driver_number}: {str(e)}")
                        skipped_fetches += 1

            logger.info(
                f"Fetched {len(all_locations)} location records ({successful_fetches} successful, {skipped_fetches} skipped)")
            result['location'] = pd.DataFrame(
                all_locations) if all_locations else pd.DataFrame()

        return result
