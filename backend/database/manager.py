"""
Database Manager for Foodberg Price Database
Handles connections, sessions, and queries for the integrated food prices database
"""

from sqlalchemy import create_engine, func, and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

from .models import (
    Base,
    WASDEData,
    MarketPrice,
    EconomicIndicator,
    GlobalPrice,
    RetailPrice,
    DataSourceSync,
    CompositeIndex,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Central database manager for Foodberg price database

    Provides:
    - Connection management
    - Session handling
    - Query builders for price searches
    - Data validation and sanitization
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file. Defaults to backend/data/foodberg.db
        """
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / 'data' / 'foodberg.db')

        # Create database directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create engine with connection pooling
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},  # Allow multiple threads
            poolclass=StaticPool,
            echo=False  # Set to True for SQL query debugging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self.db_path = db_path
        logger.info(f"Database manager initialized: {db_path}")

    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")

    def get_session(self) -> Session:
        """
        Get a new database session

        Returns:
            SQLAlchemy Session object
        """
        return self.SessionLocal()

    # ==================== WASDE QUERIES ====================

    def get_wasde_prices(
        self,
        commodity: Optional[str] = None,
        location: Optional[str] = None,
        year: Optional[int] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query WASDE price data (PRICE RECEIVED category)

        Args:
            commodity: Commodity name (e.g., 'WHEAT', 'CORN')
            location: Location (state name or 'US TOTAL')
            year: Specific year
            start_year: Start of year range
            end_year: End of year range
            limit: Maximum records to return

        Returns:
            List of price records as dictionaries
        """
        session = self.get_session()
        try:
            query = session.query(WASDEData).filter(
                WASDEData.statistic_category.like('%PRICE%')
            )

            if commodity:
                query = query.filter(WASDEData.commodity == commodity.upper())
            if location:
                query = query.filter(WASDEData.location == location.upper())
            if year:
                query = query.filter(WASDEData.year == year)
            if start_year:
                query = query.filter(WASDEData.year >= start_year)
            if end_year:
                query = query.filter(WASDEData.year <= end_year)

            query = query.order_by(desc(WASDEData.year)).limit(limit)
            results = query.all()

            return [self._wasde_to_dict(record) for record in results]
        finally:
            session.close()

    def get_wasde_commodities(self) -> List[str]:
        """Get list of all commodities in WASDE data"""
        session = self.get_session()
        try:
            results = session.query(WASDEData.commodity).distinct().all()
            return sorted([r[0] for r in results])
        finally:
            session.close()

    def get_wasde_statistics(self, commodity: str) -> Dict[str, Any]:
        """Get summary statistics for a commodity's price data"""
        session = self.get_session()
        try:
            query = session.query(WASDEData).filter(
                and_(
                    WASDEData.commodity == commodity.upper(),
                    WASDEData.statistic_category.like('%PRICE%'),
                    WASDEData.numeric_value.isnot(None)
                )
            )

            records = query.all()
            if not records:
                return {}

            prices = [r.numeric_value for r in records if r.numeric_value]

            return {
                'commodity': commodity,
                'count': len(prices),
                'min_price': min(prices) if prices else None,
                'max_price': max(prices) if prices else None,
                'avg_price': sum(prices) / len(prices) if prices else None,
                'latest_year': max(r.year for r in records)
            }
        finally:
            session.close()

    # ==================== MARKET PRICE QUERIES ====================

    def get_market_prices(
        self,
        commodity: Optional[str] = None,
        market_location: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query USDA terminal market prices

        Args:
            commodity: Commodity name
            market_location: Terminal market (e.g., 'new_york', 'los_angeles')
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum records to return

        Returns:
            List of market price records
        """
        session = self.get_session()
        try:
            query = session.query(MarketPrice)

            if commodity:
                query = query.filter(MarketPrice.commodity.like(f'%{commodity}%'))
            if market_location:
                query = query.filter(MarketPrice.market_location.like(f'%{market_location}%'))
            if start_date:
                query = query.filter(MarketPrice.report_date >= start_date)
            if end_date:
                query = query.filter(MarketPrice.report_date <= end_date)

            query = query.order_by(desc(MarketPrice.report_date)).limit(limit)
            results = query.all()

            return [self._market_price_to_dict(record) for record in results]
        finally:
            session.close()

    # ==================== ECONOMIC INDICATOR QUERIES ====================

    def get_economic_indicators(
        self,
        indicator_name: Optional[str] = None,
        series_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query FRED economic indicators

        Args:
            indicator_name: Indicator name (e.g., 'Food CPI')
            series_id: FRED series ID (e.g., 'CPIUFDSL')
            category: Category (CPI, PPI, Inflation)
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum records to return

        Returns:
            List of economic indicator records
        """
        session = self.get_session()
        try:
            query = session.query(EconomicIndicator)

            if indicator_name:
                query = query.filter(EconomicIndicator.indicator_name.like(f'%{indicator_name}%'))
            if series_id:
                query = query.filter(EconomicIndicator.series_id == series_id)
            if category:
                query = query.filter(EconomicIndicator.category == category)
            if start_date:
                query = query.filter(EconomicIndicator.date >= start_date)
            if end_date:
                query = query.filter(EconomicIndicator.date <= end_date)

            query = query.order_by(desc(EconomicIndicator.date)).limit(limit)
            results = query.all()

            return [self._indicator_to_dict(record) for record in results]
        finally:
            session.close()

    # ==================== UNIFIED PRICE SEARCH ====================

    def search_prices(
        self,
        commodity: str,
        sources: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        location: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Unified price search across all data sources

        Args:
            commodity: Commodity to search for
            sources: List of sources to query ('wasde', 'market', 'global', 'retail')
            start_date: Start of date range
            end_date: End of date range
            location: Geographic location filter
            limit: Maximum records per source

        Returns:
            Dictionary with results from each data source
        """
        if sources is None:
            sources = ['wasde', 'market', 'global', 'retail']

        results = {}

        if 'wasde' in sources:
            # Convert datetime to year for WASDE
            start_year = start_date.year if start_date else None
            end_year = end_date.year if end_date else None
            results['wasde'] = self.get_wasde_prices(
                commodity=commodity,
                location=location,
                start_year=start_year,
                end_year=end_year,
                limit=limit
            )

        if 'market' in sources:
            results['market'] = self.get_market_prices(
                commodity=commodity,
                market_location=location,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )

        if 'global' in sources:
            results['global'] = self.get_global_prices(
                commodity=commodity,
                region=location,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )

        if 'retail' in sources:
            results['retail'] = self.get_retail_prices(
                food_item=commodity,
                location=location,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )

        return results

    def get_global_prices(
        self,
        commodity: Optional[str] = None,
        region: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Query global commodity prices from FAO/World Bank"""
        session = self.get_session()
        try:
            query = session.query(GlobalPrice)

            if commodity:
                query = query.filter(GlobalPrice.commodity.like(f'%{commodity}%'))
            if region:
                query = query.filter(GlobalPrice.region.like(f'%{region}%'))
            if start_date:
                query = query.filter(GlobalPrice.date >= start_date)
            if end_date:
                query = query.filter(GlobalPrice.date <= end_date)

            query = query.order_by(desc(GlobalPrice.date)).limit(limit)
            results = query.all()

            return [self._global_price_to_dict(record) for record in results]
        finally:
            session.close()

    def get_commodity_price_history(
        self,
        commodity: str,
        limit: int = 5000,
    ) -> List[Dict[str, Any]]:
        """
        Return the real monthly price-history series for a commodity from
        global_prices (Alpha Vantage spot-price series, 1992-present).

        These are genuine historical monthly prices. WASDE is NOT used here
        because the local WASDE table holds a single marketing-year only and
        cannot yield a time series. Returns an empty list when no real series
        exists for the commodity (caller must NOT fabricate one).
        """
        # Map a user-facing commodity name to the Alpha Vantage series label
        # stored in global_prices.commodity. Only these have real monthly history.
        alias = {
            'wheat': 'WHEAT',
            'corn': 'CORN',
            'maize': 'CORN',
            'coffee': 'COFFEE',
            'sugar': 'SUGAR',
            'cotton': 'COTTON',
        }
        key = (commodity or '').strip().lower()
        series = alias.get(key)
        if not series:
            return []

        session = self.get_session()
        try:
            records = (
                session.query(GlobalPrice)
                .filter(
                    GlobalPrice.commodity == series,
                    GlobalPrice.source == 'Alpha Vantage',
                )
                .order_by(asc(GlobalPrice.date))
                .limit(limit)
                .all()
            )
            out = []
            for r in records:
                if r.price is None or r.date is None:
                    continue
                out.append({
                    'date': r.date.isoformat(),
                    'year': r.date.year,
                    'price': r.price,
                    'unit': r.unit,
                    'currency': r.currency,
                    'source': r.source,
                    'series': series,
                })
            return out
        finally:
            session.close()

    def get_retail_prices(
        self,
        food_item: Optional[str] = None,
        location: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Query retail food prices from API Ninja and other sources"""
        session = self.get_session()
        try:
            query = session.query(RetailPrice)

            if food_item:
                query = query.filter(RetailPrice.food_item.like(f'%{food_item}%'))
            if location:
                query = query.filter(or_(
                    RetailPrice.location.like(f'%{location}%'),
                    RetailPrice.state.like(f'%{location}%')
                ))
            if start_date:
                query = query.filter(RetailPrice.date >= start_date)
            if end_date:
                query = query.filter(RetailPrice.date <= end_date)

            query = query.order_by(desc(RetailPrice.date)).limit(limit)
            results = query.all()

            return [self._retail_price_to_dict(record) for record in results]
        finally:
            session.close()

    # ==================== DATA SOURCE SYNC TRACKING ====================

    def update_sync_status(
        self,
        source_name: str,
        status: str,
        records_synced: int = 0,
        error_message: Optional[str] = None
    ):
        """Update sync status for a data source"""
        session = self.get_session()
        try:
            sync_record = session.query(DataSourceSync).filter_by(
                source_name=source_name
            ).first()

            if sync_record is None:
                sync_record = DataSourceSync(source_name=source_name)
                session.add(sync_record)

            sync_record.last_sync_time = datetime.utcnow()
            sync_record.last_sync_status = status
            sync_record.records_synced = records_synced
            sync_record.error_message = error_message

            session.commit()
        finally:
            session.close()

    def get_sync_status(self, source_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sync status for data sources"""
        session = self.get_session()
        try:
            query = session.query(DataSourceSync)

            if source_name:
                query = query.filter_by(source_name=source_name)

            results = query.all()
            return [
                {
                    'source': r.source_name,
                    'last_sync': r.last_sync_time.isoformat() if r.last_sync_time else None,
                    'status': r.last_sync_status,
                    'records': r.records_synced,
                    'error': r.error_message
                }
                for r in results
            ]
        finally:
            session.close()

    # ==================== HELPER METHODS ====================

    def _wasde_to_dict(self, record: WASDEData) -> Dict[str, Any]:
        """Convert WASDE record to dictionary"""
        return {
            'id': record.id,
            'commodity': record.commodity,
            'statistic_category': record.statistic_category,
            'value': record.value,
            'numeric_value': record.numeric_value,
            'unit': record.unit,
            'location': record.location,
            'state_code': record.state_code,
            'year': record.year,
            'short_desc': record.short_desc,
            'source': 'WASDE',
            'imported_at': record.imported_at.isoformat() if record.imported_at else None
        }

    def _market_price_to_dict(self, record: MarketPrice) -> Dict[str, Any]:
        """Convert market price record to dictionary"""
        return {
            'id': record.id,
            'commodity': record.commodity,
            'variety': record.variety,
            'market_location': record.market_location,
            'low_price': record.low_price,
            'high_price': record.high_price,
            'avg_price': record.avg_price,
            'unit': record.unit,
            'origin': record.origin,
            'report_date': record.report_date.isoformat() if record.report_date else None,
            'source': record.source,
            'imported_at': record.imported_at.isoformat() if record.imported_at else None
        }

    def _indicator_to_dict(self, record: EconomicIndicator) -> Dict[str, Any]:
        """Convert economic indicator record to dictionary"""
        return {
            'id': record.id,
            'indicator_name': record.indicator_name,
            'series_id': record.series_id,
            'value': record.value,
            'date': record.date.isoformat() if record.date else None,
            'category': record.category,
            'source': record.source,
            'imported_at': record.imported_at.isoformat() if record.imported_at else None
        }

    def _global_price_to_dict(self, record: GlobalPrice) -> Dict[str, Any]:
        """Convert global price record to dictionary"""
        return {
            'id': record.id,
            'commodity': record.commodity,
            'price': record.price,
            'currency': record.currency,
            'unit': record.unit,
            'region': record.region,
            'country': record.country,
            'date': record.date.isoformat() if record.date else None,
            'source': record.source,
            'imported_at': record.imported_at.isoformat() if record.imported_at else None
        }

    def _retail_price_to_dict(self, record: RetailPrice) -> Dict[str, Any]:
        """Convert retail price record to dictionary"""
        return {
            'id': record.id,
            'food_item': record.food_item,
            'price': record.price,
            'unit': record.unit,
            'store_type': record.store_type,
            'location': record.location,
            'state': record.state,
            'date': record.date.isoformat() if record.date else None,
            'source': record.source,
            'brand': record.brand,
            'quality_grade': record.quality_grade,
            'imported_at': record.imported_at.isoformat() if record.imported_at else None
        }

    def get_database_stats(self) -> Dict[str, int]:
        """Get record counts for all tables"""
        session = self.get_session()
        try:
            stats = {
                'wasde_data': session.query(func.count(WASDEData.id)).scalar(),
                'market_prices': session.query(func.count(MarketPrice.id)).scalar(),
                'economic_indicators': session.query(func.count(EconomicIndicator.id)).scalar(),
                'global_prices': session.query(func.count(GlobalPrice.id)).scalar(),
                'retail_prices': session.query(func.count(RetailPrice.id)).scalar(),
                'composite_indices': session.query(func.count(CompositeIndex.id)).scalar(),
            }
            stats['total'] = sum(stats.values())
            return stats
        finally:
            session.close()

    # ==================== COMPOSITE INDEX QUERIES ====================

    def get_composite_indices(self) -> List[Dict[str, Any]]:
        """Get latest composite index values for all categories"""
        session = self.get_session()
        try:
            from sqlalchemy import distinct
            categories = session.query(distinct(CompositeIndex.category)).all()
            results = []
            for (category,) in categories:
                latest = (
                    session.query(CompositeIndex)
                    .filter(CompositeIndex.category == category)
                    .order_by(desc(CompositeIndex.date))
                    .first()
                )
                if latest:
                    results.append(self._composite_to_dict(latest))
            return results
        finally:
            session.close()

    def get_composite_index_history(self, category: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get historical values for a composite index category"""
        session = self.get_session()
        try:
            records = (
                session.query(CompositeIndex)
                .filter(CompositeIndex.category == category)
                .order_by(asc(CompositeIndex.date))
                .limit(limit)
                .all()
            )
            return [self._composite_to_dict(r) for r in records]
        finally:
            session.close()

    def _composite_to_dict(self, record: CompositeIndex) -> Dict[str, Any]:
        """Convert composite index record to dictionary"""
        import json as _json
        components = None
        if record.components_json:
            try:
                components = _json.loads(record.components_json)
            except:
                components = record.components_json
        return {
            'id': record.id,
            'date': record.date.isoformat() if record.date else None,
            'category': record.category,
            'index_value': record.index_value,
            'components': components,
            'base_period': record.base_period,
            'computed_at': record.computed_at.isoformat() if record.computed_at else None,
        }
