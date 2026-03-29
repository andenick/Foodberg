"""
SQLAlchemy ORM Models for Foodberg Price Database
Defines tables for 6 integrated data sources
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class WASDEData(Base):
    """WASDE (World Agricultural Supply and Demand Estimates) data from USDA NASS"""
    __tablename__ = 'wasde_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    commodity = Column(String(100), nullable=False, index=True)
    statistic_category = Column(String(200), nullable=False, index=True)
    value = Column(String(100))  # String because can contain commas, ranges, etc.
    numeric_value = Column(Float)  # Parsed numeric value when applicable
    unit = Column(String(50))
    location = Column(String(100), index=True)  # State name or "US TOTAL"
    state_code = Column(String(2))  # Two-letter state code
    agg_level = Column(String(50))  # NATIONAL, STATE, COUNTY, etc.
    year = Column(Integer, index=True)
    reference_period = Column(String(100))  # YEAR, MONTH, etc.
    short_desc = Column(Text)  # Human-readable description
    source_desc = Column(String(100))  # SURVEY, CENSUS, etc.
    sector = Column(String(50))  # CROPS, ANIMALS, etc.
    group_desc = Column(String(100))  # Field classification
    class_desc = Column(String(100))  # ALL CLASSES, WINTER, SPRING, etc.
    freq_desc = Column(String(50))  # ANNUAL, MONTHLY, WEEKLY
    load_time = Column(DateTime)  # When USDA loaded this record
    imported_at = Column(DateTime, default=datetime.utcnow)

    # Additional metadata from NASS
    prodn_practice = Column(String(100))
    util_practice = Column(String(100))
    domain_desc = Column(String(200))
    domaincat_desc = Column(String(200))

    __table_args__ = (
        Index('ix_wasde_commodity_year', 'commodity', 'year'),
        Index('ix_wasde_commodity_location', 'commodity', 'location'),
        Index('ix_wasde_statistic_category', 'statistic_category'),
    )


class MarketPrice(Base):
    """USDA Market News - Terminal market prices for fresh produce"""
    __tablename__ = 'market_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    commodity = Column(String(100), nullable=False, index=True)
    variety = Column(String(100))  # Variety of the commodity
    market_location = Column(String(100), nullable=False, index=True)  # Terminal market name
    low_price = Column(Float)
    high_price = Column(Float)
    avg_price = Column(Float, index=True)
    unit = Column(String(50))  # each, lb, kg, case, etc.
    origin = Column(String(100))  # Where the commodity was grown
    report_date = Column(DateTime, nullable=False, index=True)
    source = Column(String(50), default='USDA Market News')
    imported_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_market_commodity_date', 'commodity', 'report_date'),
        Index('ix_market_location_date', 'market_location', 'report_date'),
    )


class EconomicIndicator(Base):
    """FRED (Federal Reserve Economic Data) - Economic indicators affecting food prices"""
    __tablename__ = 'economic_indicators'

    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_name = Column(String(200), nullable=False, index=True)  # Food CPI, PPI Farm, etc.
    series_id = Column(String(100), nullable=False, index=True)  # FRED series ID
    value = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    category = Column(String(100))  # CPI, PPI, Inflation, etc.
    frequency = Column(String(50))  # Monthly, Quarterly, Annual
    source = Column(String(50), default='FRED')
    imported_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_indicator_series_date', 'series_id', 'date'),
        Index('ix_indicator_category_date', 'category', 'date'),
    )


class GlobalPrice(Base):
    """FAO and World Bank - Global commodity prices"""
    __tablename__ = 'global_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    commodity = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    unit = Column(String(50))
    region = Column(String(100), index=True)  # Global, Europe, Asia, etc.
    country = Column(String(100))
    date = Column(DateTime, nullable=False, index=True)
    source = Column(String(50), nullable=False)  # FAO or World Bank
    indicator_code = Column(String(100))  # Original indicator code from source
    imported_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_global_commodity_date', 'commodity', 'date'),
        Index('ix_global_region_date', 'region', 'date'),
    )


class RetailPrice(Base):
    """API Ninja and other retail price sources - Consumer-facing food prices"""
    __tablename__ = 'retail_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    food_item = Column(String(200), nullable=False, index=True)
    price = Column(Float, nullable=False)
    unit = Column(String(50))  # lb, kg, each, gallon, etc.
    store_type = Column(String(100))  # Grocery, Wholesale, Restaurant Supply, etc.
    location = Column(String(100), index=True)  # City or region
    state = Column(String(2))
    country = Column(String(50), default='USA')
    date = Column(DateTime, nullable=False, index=True)
    source = Column(String(50), default='API Ninja')
    brand = Column(String(100))  # Brand name if applicable
    quality_grade = Column(String(50))  # Organic, Conventional, Premium, etc.
    imported_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_retail_food_date', 'food_item', 'date'),
        Index('ix_retail_location_date', 'location', 'date'),
    )


# Utility table for tracking data source sync status
class DataSourceSync(Base):
    """Track last successful sync for each data source"""
    __tablename__ = 'data_source_sync'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(100), nullable=False, unique=True, index=True)
    last_sync_time = Column(DateTime, nullable=False)
    last_sync_status = Column(String(20))  # SUCCESS, FAILED, PARTIAL
    records_synced = Column(Integer, default=0)
    error_message = Column(Text)
    next_sync_time = Column(DateTime)
    sync_frequency = Column(String(50))  # daily, weekly, monthly

    def __repr__(self):
        return f"<DataSourceSync(source={self.source_name}, last_sync={self.last_sync_time}, status={self.last_sync_status})>"


class CompositeIndex(Base):
    """Computed composite food price indices by food group"""
    __tablename__ = 'composite_indices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # cereals, meat, dairy, oils, sugar, produce, overall
    index_value = Column(Float, nullable=False)
    components_json = Column(Text)  # JSON with individual component values
    base_period = Column(String(50), default='2014-2016')
    computed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_composite_date_category', 'date', 'category'),
    )
