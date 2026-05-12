#!/usr/bin/env python3
"""
FRED (Federal Reserve Economic Data) API Client
Fetches food-related economic indicators
"""

import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

from database.manager import DatabaseManager
from database.models import EconomicIndicator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FREDClient:
    """
    Client for fetching economic indicators from FRED API
    """

    # Food-related FRED series to collect
    FOOD_SERIES = {
        'CPIUFDSL': {
            'name': 'Consumer Price Index - Food',
            'category': 'CPI',
            'frequency': 'Monthly'
        },
        'CPIUFDNS': {
            'name': 'Consumer Price Index - Food and Beverages',
            'category': 'CPI',
            'frequency': 'Monthly'
        },
        'CUSR0000SAF11': {
            'name': 'CPI - Food at Home',
            'category': 'CPI',
            'frequency': 'Monthly'
        },
        'CUSR0000SEFV': {
            'name': 'CPI - Food Away from Home',
            'category': 'CPI',
            'frequency': 'Monthly'
        },
        'WPU01': {
            'name': 'Producer Price Index - Farm Products',
            'category': 'PPI',
            'frequency': 'Monthly'
        },
        'PPIFID': {
            'name': 'PPI - Finished Goods: Food',
            'category': 'PPI',
            'frequency': 'Monthly'
        },
        'WPU0211': {
            'name': 'PPI - Grains',
            'category': 'PPI',
            'frequency': 'Monthly'
        },
        'WPU0212': {
            'name': 'PPI - Livestock and Poultry',
            'category': 'PPI',
            'frequency': 'Monthly'
        },
        'PPIACO': {
            'name': 'PPI - All Commodities',
            'category': 'PPI',
            'frequency': 'Monthly'
        },
        'CPIAUCSL': {
            'name': 'Consumer Price Index - All Items',
            'category': 'CPI',
            'frequency': 'Monthly'
        }
    }

    def __init__(self, api_key=None):
        """Initialize FRED client with API key"""
        if api_key:
            self.api_key = api_key
        else:
            # Try to load from Robin's api_keys.json
            api_keys_path = Path(os.environ.get("API_KEYS_PATH", "backend/config/api_keys.json"))
            if api_keys_path.exists():
                with open(api_keys_path, 'r') as f:
                    keys = json.load(f)
                    self.api_key = keys.get('fred_api_key')
            else:
                raise ValueError("No API key provided and Robin's api_keys.json not found")

        self.base_url = "https://api.stlouisfed.org/fred"
        self.db_manager = DatabaseManager()

    def fetch_series_observations(self, series_id, start_date=None, end_date=None):
        """
        Fetch observations for a specific FRED series

        Args:
            series_id: FRED series ID (e.g., 'CPIUFDSL')
            start_date: Start date (YYYY-MM-DD format), default to 10 years ago
            end_date: End date (YYYY-MM-DD format), default to today

        Returns:
            List of observations with date and value
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d')  # 10 years
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        url = f"{self.base_url}/series/observations"
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'observations' in data:
                return data['observations']
            else:
                logger.error(f"No observations found for {series_id}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {series_id}: {e}")
            return []

    def import_series(self, series_id, series_info, batch_size=1000):
        """
        Import a single FRED series into the database

        Args:
            series_id: FRED series ID
            series_info: Dictionary with series metadata (name, category, frequency)
            batch_size: Number of records per batch

        Returns:
            Number of records imported
        """
        print(f"\nImporting {series_id}: {series_info['name']}...")

        # Fetch observations
        observations = self.fetch_series_observations(series_id)

        if not observations:
            print(f"  [WARN] No data returned for {series_id}")
            return 0

        # Filter out null values (FRED uses '.' for missing data)
        valid_obs = [obs for obs in observations if obs['value'] != '.']

        print(f"  Total observations: {len(observations)} ({len(valid_obs)} valid)")

        # Process in batches
        session = self.db_manager.get_session()
        batch = []
        imported = 0

        try:
            for idx, obs in enumerate(valid_obs):
                # Parse date and value
                obs_date = datetime.strptime(obs['date'], '%Y-%m-%d')
                value = float(obs['value'])

                # Create EconomicIndicator object
                indicator = EconomicIndicator(
                    indicator_name=series_info['name'],
                    series_id=series_id,
                    value=value,
                    date=obs_date,
                    category=series_info['category'],
                    frequency=series_info['frequency'],
                    source='FRED',
                    imported_at=datetime.now()
                )

                batch.append(indicator)

                # Insert batch when full
                if len(batch) >= batch_size:
                    session.bulk_save_objects(batch)
                    session.commit()
                    imported += len(batch)

                    progress = (idx + 1) / len(valid_obs) * 100
                    print(f"  Progress: {progress:.1f}% ({imported:,}/{len(valid_obs):,})", end='\r')

                    batch = []

            # Insert remaining records
            if batch:
                session.bulk_save_objects(batch)
                session.commit()
                imported += len(batch)

            print(f"\n  [OK] Imported {imported:,} observations for {series_id}")

            # Update sync status
            self.db_manager.update_sync_status(
                source_name=f'FRED-{series_id}',
                status='SUCCESS',
                records_synced=imported
            )

            return imported

        except Exception as e:
            session.rollback()
            print(f"\n  [ERROR] Failed to import {series_id}: {e}")
            logger.exception(e)

            # Update sync status
            self.db_manager.update_sync_status(
                source_name=f'FRED-{series_id}',
                status='FAILED',
                error_message=str(e)
            )

            return 0
        finally:
            session.close()

    def import_all_series(self):
        """Import all predefined food-related FRED series"""
        print("\n" + "="*80)
        print("FRED ECONOMIC INDICATORS IMPORT")
        print("Source: Federal Reserve Economic Data (FRED)")
        print("="*80)

        print(f"\nFound {len(self.FOOD_SERIES)} economic indicator series to import")
        print("Time range: Last 10 years\n")

        # Import each series
        start_time = time.time()
        total_imported = 0
        successful = 0
        failed = []

        for idx, (series_id, series_info) in enumerate(self.FOOD_SERIES.items(), 1):
            print(f"\n[{idx}/{len(self.FOOD_SERIES)}] ", end='')

            # Rate limiting (FRED allows 120 requests/minute)
            if idx > 1:
                time.sleep(0.5)  # 2 requests/second = well under limit

            count = self.import_series(series_id, series_info)
            total_imported += count

            if count > 0:
                successful += 1
            else:
                failed.append(series_id)

        # Summary
        duration = time.time() - start_time

        print("\n" + "="*80)
        print("IMPORT COMPLETE")
        print("="*80)
        print(f"Series processed:   {len(self.FOOD_SERIES)}")
        print(f"Successful imports: {successful}")
        print(f"Failed imports:     {len(failed)}")
        print(f"Total observations: {total_imported:,}")
        print(f"Duration:           {duration:.1f} seconds ({duration/60:.1f} minutes)")
        if total_imported > 0:
            print(f"Records/second:     {total_imported/duration:,.0f}")

        if failed:
            print(f"\nFailed series: {', '.join(failed)}")

        print("="*80)


def main():
    """Run FRED data import"""
    client = FREDClient()
    client.import_all_series()


if __name__ == '__main__':
    main()
