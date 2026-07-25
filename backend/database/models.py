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


class WasdePsd(Base):
    """WASDE PSD (Production, Supply and Distribution) — global supply/demand

    The largest table in Foodberg (1.98M rows). USDA Foreign Agricultural Service
    PSD Online data: production, supply, distribution for all major agricultural
    commodities by country, marketing year.
    """
    __tablename__ = 'wasde_psd'

    id = Column(Integer, primary_key=True, autoincrement=True)
    commodity = Column(String(100), nullable=False, index=True)
    commodity_code = Column(String(20))
    country = Column(String(100), nullable=False, index=True)
    country_code = Column(String(10))
    market_year = Column(Integer, nullable=False, index=True)
    calendar_year = Column(Integer)
    attribute = Column(String(200), nullable=False, index=True)
    attribute_id = Column(String(20))
    unit = Column(String(50))
    value = Column(Float)
    is_aggregate = Column(Integer, default=0)
    n_countries = Column(Integer)
    vintage_month = Column(String(10))
    source = Column(String(50), default='USDA PSD')
    source_url = Column(Text)

    __table_args__ = (
        Index('ix_psd_commodity_year', 'commodity', 'market_year'),
        Index('ix_psd_country_commodity', 'country', 'commodity'),
        Index('ix_psd_attribute', 'attribute'),
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


class AmsWholesalePrice(Base):
    """USDA AMS Market News — daily terminal-market wholesale prices.

    One row per published price line item. The publisher quotes a price for a
    specific PACKAGE of a specific VARIETY from a specific ORIGIN, so the row
    is deliberately NOT collapsed to a single price per commodity: the package
    and the origin are the analytical content.

    Provenance travels with every row (source, slug_name/slug_id as the
    publisher series id, retrieval_url, retrieved_at, unit, geography). Fields
    the publisher does not emit are stored NULL — never defaulted, never
    inferred.

    Populated by Technical/scripts/ingest_ams.py via
    data_sources/usda_client.py (MARS API v3.1, addressed by numeric slug_id).
    """
    __tablename__ = 'ams_wholesale_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Report identity / geography
    report_date = Column(String(10), nullable=False)  # ISO YYYY-MM-DD
    published_date = Column(String(30))
    slug_id = Column(String(10), nullable=False)
    slug_name = Column(String(20), nullable=False)
    report_title = Column(Text)
    market = Column(String(120))
    city = Column(String(80))
    state = Column(String(10))
    geography = Column(String(120))

    # What was sold
    category = Column(String(80))
    commodity = Column(String(120), nullable=False)
    variety = Column(String(160))
    package = Column(String(160))
    grade = Column(String(120))
    item_size = Column(String(120))
    organic = Column(String(10))
    origin = Column(String(120))
    origin_detail = Column(String(160))
    repack = Column(String(40))
    storage = Column(String(80))
    quality = Column(String(120))
    condition = Column(String(120))
    appearance = Column(String(120))
    crop = Column(String(120))
    district = Column(String(120))
    environment = Column(String(120))
    transportation_mode = Column(String(80))
    unit_of_sale = Column(String(120))

    # Prices (USD for the quoted package)
    low_price = Column(Float)
    high_price = Column(Float)
    mostly_low_price = Column(Float)
    mostly_high_price = Column(Float)
    market_tone_comments = Column(Text)

    # Provenance
    unit = Column(String(180))
    source = Column(String(60), default='USDA AMS Market News')
    retrieval_url = Column(Text)
    retrieved_at = Column(String(40))
    # SHA-1 of the full price line item; see __table_args__.
    row_hash = Column(String(40), nullable=False)

    __table_args__ = (
        # IDEMPOTENCE KEY.
        #
        # The obvious natural key — (report_date, slug_id, commodity, variety,
        # package, grade, item_size, organic, origin) — is NOT unique in the
        # publisher's own data and cannot be used as the UNIQUE constraint. On
        # New York vegetables for 2026-07-23 alone it collapses 377 published
        # line items into 338: AMS legitimately prints several price lines for
        # one lot description that differ only on appearance ('Fine
        # Appearance' vs none), condition ('Holdovers'), quality, or on the
        # price itself (Peppers, Finger Hot / 4 kg cartons / Netherlands
        # prints at 30.00, 34.00 and 35.00-36.00 on the same day). Enforcing
        # uniqueness on those nine columns would silently discard ~10% of real
        # observations.
        #
        # So the UNIQUE constraint is row_hash — a digest of the full price
        # line item (identity fields AND the four prices). Byte-identical
        # repeats collapse, every genuinely distinct line survives, and
        # re-running any window is still a no-op. The nine-column natural key
        # is kept below as a NON-unique lookup path.
        Index('ux_ams_row_hash', 'row_hash', unique=True),
        Index(
            'ix_ams_natural_key',
            'report_date', 'slug_id', 'commodity', 'variety', 'package',
            'grade', 'item_size', 'organic', 'origin',
        ),
        Index('ix_ams_commodity_date', 'commodity', 'report_date'),
        Index('ix_ams_market_date', 'market', 'report_date'),
        Index('ix_ams_city_date', 'city', 'report_date'),
        Index('ix_ams_report_date', 'report_date'),
    )

    def __repr__(self):
        return (
            f"<AmsWholesalePrice({self.report_date} {self.slug_name} "
            f"{self.commodity} {self.package} {self.low_price}-{self.high_price})>"
        )
