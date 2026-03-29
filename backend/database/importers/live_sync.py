"""
Live Data Sync for External Data Sources
Pulls data from USDA Market News, FRED, FAO, World Bank, API Ninja
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from ..models import MarketPrice, EconomicIndicator, GlobalPrice, RetailPrice
from ..manager import DatabaseManager

logger = logging.getLogger(__name__)


class LiveDataSync:
    """
    Sync live data from external sources into database

    Supports:
    - USDA Market News (terminal markets)
    - FRED (economic indicators)
    - FAO (global prices) - placeholder
    - World Bank (global prices) - placeholder
    - API Ninja (retail prices) - placeholder
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize live data sync

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        logger.info("Live Data Sync initialized")

    async def sync_all_sources(self) -> Dict[str, Dict]:
        """
        Sync all data sources

        Returns:
            Dictionary with sync results for each source
        """
        results = {}

        try:
            results['usda_market'] = await self.sync_usda_market_news()
        except Exception as e:
            logger.error(f"Error syncing USDA Market News: {e}")
            results['usda_market'] = {'status': 'ERROR', 'error': str(e)}

        try:
            results['fred'] = await self.sync_fred_indicators()
        except Exception as e:
            logger.error(f"Error syncing FRED: {e}")
            results['fred'] = {'status': 'ERROR', 'error': str(e)}

        # Placeholders for future implementation
        results['fao'] = {'status': 'NOT_IMPLEMENTED'}
        results['world_bank'] = {'status': 'NOT_IMPLEMENTED'}
        results['api_ninja'] = {'status': 'NOT_IMPLEMENTED'}

        return results

    async def sync_usda_market_news(self) -> Dict:
        """
        Sync USDA Market News terminal market prices

        Returns:
            Sync statistics
        """
        try:
            from ...data_sources.usda_client import USDAMarketNewsClient

            client = USDAMarketNewsClient()
            terminal_markets = [
                'atlanta', 'boston', 'chicago', 'columbia', 'dallas', 'detroit',
                'los_angeles', 'miami', 'new_york', 'philadelphia',
                'san_francisco', 'seattle'
            ]

            total_records = 0
            errors = 0

            session = self.db_manager.get_session()
            try:
                for market in terminal_markets:
                    try:
                        # Get prices for this market
                        data = client.get_terminal_market_prices(market)

                        if not data or not data.get('commodities'):
                            continue

                        report_date_str = data.get('reportDate')
                        if not report_date_str:
                            report_date = datetime.now()
                        else:
                            try:
                                report_date = datetime.fromisoformat(report_date_str)
                            except:
                                report_date = datetime.now()

                        # Insert records
                        for commodity, varieties in data['commodities'].items():
                            for variety_data in varieties:
                                market_price = MarketPrice(
                                    commodity=commodity.upper(),
                                    variety=variety_data.get('variety', 'standard'),
                                    market_location=market,
                                    low_price=variety_data.get('lowPrice'),
                                    high_price=variety_data.get('highPrice'),
                                    avg_price=variety_data.get('avgPrice'),
                                    unit=variety_data.get('unit', 'each'),
                                    origin=variety_data.get('origin', 'Unknown'),
                                    report_date=report_date,
                                    source='USDA Market News'
                                )
                                session.add(market_price)
                                total_records += 1

                        session.commit()

                    except Exception as e:
                        logger.error(f"Error syncing {market}: {e}")
                        errors += 1
                        session.rollback()

            finally:
                session.close()

            # Update sync status
            self.db_manager.update_sync_status(
                source_name='USDA Market News',
                status='SUCCESS' if errors == 0 else 'PARTIAL',
                records_synced=total_records
            )

            return {
                'status': 'SUCCESS' if errors == 0 else 'PARTIAL',
                'records_synced': total_records,
                'markets_synced': len(terminal_markets) - errors,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"Fatal error in USDA Market News sync: {e}")
            self.db_manager.update_sync_status(
                source_name='USDA Market News',
                status='FAILED',
                error_message=str(e)
            )
            return {'status': 'FAILED', 'error': str(e)}

    async def sync_fred_indicators(self) -> Dict:
        """
        Sync FRED economic indicators

        Returns:
            Sync statistics
        """
        try:
            from ...data_sources.fred_client import FREDClient

            client = FREDClient()

            # Define indicators to sync
            indicators = {
                'food_cpi': ('CPIUFDSL', 'Food CPI', 'CPI'),
                'food_home_cpi': ('CUSR0000SAF11', 'Food at Home CPI', 'CPI'),
                'food_away_cpi': ('CUSR0000SEFV', 'Food Away from Home CPI', 'CPI'),
                'ppi_farm': ('WPU01', 'Farm Products PPI', 'PPI'),
                'ppi_food': ('WPU02', 'Processed Foods PPI', 'PPI'),
                'inflation': ('FPCPITOTLZGUSA', 'Inflation Rate', 'Inflation'),
            }

            total_records = 0
            errors = 0

            session = self.db_manager.get_session()
            try:
                for key, (series_id, name, category) in indicators.items():
                    try:
                        # Get last 24 months of data
                        data = await client.get_series_data(series_id, limit=24)

                        for observation in data:
                            if observation['value'] is None:
                                continue

                            # Check if record already exists
                            existing = session.query(EconomicIndicator).filter_by(
                                series_id=series_id,
                                date=datetime.fromisoformat(observation['date'])
                            ).first()

                            if not existing:
                                indicator = EconomicIndicator(
                                    indicator_name=name,
                                    series_id=series_id,
                                    value=observation['value'],
                                    date=datetime.fromisoformat(observation['date']),
                                    category=category,
                                    frequency='Monthly',
                                    source='FRED'
                                )
                                session.add(indicator)
                                total_records += 1

                        session.commit()

                    except Exception as e:
                        logger.error(f"Error syncing {name}: {e}")
                        errors += 1
                        session.rollback()

            finally:
                session.close()

            # Update sync status
            self.db_manager.update_sync_status(
                source_name='FRED',
                status='SUCCESS' if errors == 0 else 'PARTIAL',
                records_synced=total_records
            )

            return {
                'status': 'SUCCESS' if errors == 0 else 'PARTIAL',
                'records_synced': total_records,
                'indicators_synced': len(indicators) - errors,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"Fatal error in FRED sync: {e}")
            self.db_manager.update_sync_status(
                source_name='FRED',
                status='FAILED',
                error_message=str(e)
            )
            return {'status': 'FAILED', 'error': str(e)}

    async def sync_fao_prices(self) -> Dict:
        """
        Sync FAO global commodity prices

        TODO: Implement FAO data sync
        """
        return {'status': 'NOT_IMPLEMENTED'}

    async def sync_world_bank_prices(self) -> Dict:
        """
        Sync World Bank commodity prices

        TODO: Implement World Bank data sync
        """
        return {'status': 'NOT_IMPLEMENTED'}

    async def sync_retail_prices(self) -> Dict:
        """
        Sync retail food prices from API Ninja

        TODO: Implement API Ninja data sync
        """
        return {'status': 'NOT_IMPLEMENTED'}


# Command-line interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Sync live data sources')
    parser.add_argument('--db-path', help='Path to SQLite database file')
    parser.add_argument('--source', choices=['usda', 'fred', 'all'], default='all',
                       help='Data source to sync')

    args = parser.parse_args()

    # Initialize database manager
    db_manager = DatabaseManager(db_path=args.db_path)

    # Initialize sync
    sync = LiveDataSync(db_manager)

    # Run sync
    async def run_sync():
        if args.source == 'all':
            results = await sync.sync_all_sources()
        elif args.source == 'usda':
            results = {'usda': await sync.sync_usda_market_news()}
        elif args.source == 'fred':
            results = {'fred': await sync.sync_fred_indicators()}

        print(f"\nSync Results:")
        for source, result in results.items():
            print(f"  {source}: {result.get('status')} - {result.get('records_synced', 0)} records")

    asyncio.run(run_sync())
    print("\n✓ Sync complete!")
