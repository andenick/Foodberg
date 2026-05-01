"""
Live Data Collector for Foodberg
Fetches fresh data from live APIs that aren't available via Robin's offline stores.

Usage:
    cd backend
    python -m database.collect_live [--skip-alpha-vantage] [--skip-ams]

Sources:
    1. FRED food-specific series (12 series, 10+ years)
    2. BLS extended CPI history (7 series, 20 years with registered key)
    3. FAO Food Price Index CSV (real data, replaces mock)
    4. World Bank Pink Sheet commodity prices (20 commodities)
    5. Alpha Vantage commodity futures (8 commodities, 25 req/day limit)
    6. USDA AMS Market News terminal prices (12 markets)
"""

import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.manager import DatabaseManager
from database.models import EconomicIndicator, GlobalPrice, MarketPrice


def collect_fred_food_series(db_manager: DatabaseManager) -> Dict:
    """Fetch 12 food-specific FRED series via live API"""
    from data_sources.collectors import FREDCollector

    stats = {"imported": 0, "skipped": 0, "errors": 0, "series": {}}

    print(f"\n{'='*70}")
    print("FRED FOOD-SPECIFIC SERIES (Live API)")
    print(f"{'='*70}\n")

    try:
        collector = FREDCollector()
    except ValueError as e:
        print(f"  FRED API key not configured: {e}")
        stats["errors"] = 1
        return stats

    results = collector.fetch_all_food_series(start_date="2006-01-01")

    session = db_manager.get_session()
    try:
        for series_id, series_info in results.items():
            if "error" in series_info:
                print(f"  {series_id}: ERROR - {series_info['error']}")
                stats["errors"] += 1
                continue

            data = series_info.get("data", [])
            name = series_info.get("name", series_id)
            inserted = 0

            category_map = {
                "CPIUFDSL": "Food CPI",
                "CUSR0000SAF11": "Food CPI",
                "CUSR0000SEFV": "Food CPI",
                "CUSR0000SAF111": "Food CPI",
                "CUSR0000SAF112": "Food CPI",
                "CUSR0000SEFJ": "Food CPI",
                "CUSR0000SAF113": "Food CPI",
                "WPU01": "PPI",
                "WPU02": "PPI",
                "CPIAUCSL": "Inflation",
                "UNRATE": "Employment",
                "FEDFUNDS": "Interest Rates",
            }

            for obs in data:
                try:
                    date_obj = datetime.strptime(obs["date"], "%Y-%m-%d")
                    existing = (
                        session.query(EconomicIndicator)
                        .filter(
                            EconomicIndicator.series_id == series_id,
                            EconomicIndicator.date == date_obj,
                            EconomicIndicator.source == "FRED",
                        )
                        .first()
                    )
                    if existing:
                        stats["skipped"] += 1
                        continue

                    record = EconomicIndicator(
                        date=date_obj,
                        series_id=series_id,
                        indicator_name=name,
                        value=float(obs["value"]),
                        category=category_map.get(series_id, "Other"),
                        frequency="Monthly",
                        source="FRED",
                    )
                    session.add(record)
                    inserted += 1
                except Exception as e:
                    stats["errors"] += 1

            session.commit()
            stats["imported"] += inserted
            stats["series"][series_id] = inserted
            print(f"  {series_id} ({name}): {inserted} new, {len(data) - inserted} skipped")

    finally:
        session.close()

    print(f"\n  Total: {stats['imported']} imported, {stats['skipped']} skipped")
    return stats


def collect_bls_extended(db_manager: DatabaseManager) -> Dict:
    """Fetch BLS CPI food series with 20-year history (registered key)"""
    from data_sources.collectors import BLSCollector

    stats = {"imported": 0, "skipped": 0, "errors": 0, "series": {}}

    print(f"\n{'='*70}")
    print("BLS EXTENDED CPI HISTORY (Live API, 20-year)")
    print(f"{'='*70}\n")

    try:
        collector = BLSCollector()
    except Exception as e:
        print(f"  BLS collector init failed: {e}")
        stats["errors"] = 1
        return stats

    start_year = 2006
    results = collector.fetch_all_food_series(start_year=start_year)

    if "error" in results:
        print(f"  BLS API error: {results['error']}")
        stats["errors"] = 1
        return stats

    session = db_manager.get_session()
    try:
        for series_id, series_info in results.items():
            if isinstance(series_info, str):
                continue
            if "error" in series_info:
                stats["errors"] += 1
                continue

            data = series_info.get("data", [])
            name = series_info.get("name", series_id)
            inserted = 0

            for obs in data:
                try:
                    date_obj = datetime.strptime(obs["date"], "%Y-%m-%d")
                    existing = (
                        session.query(EconomicIndicator)
                        .filter(
                            EconomicIndicator.series_id == series_id,
                            EconomicIndicator.date == date_obj,
                        )
                        .first()
                    )
                    if existing:
                        stats["skipped"] += 1
                        continue

                    record = EconomicIndicator(
                        date=date_obj,
                        series_id=series_id,
                        indicator_name=name,
                        value=float(obs["value"]),
                        category="Food CPI",
                        frequency="Monthly",
                        source="BLS",
                    )
                    session.add(record)
                    inserted += 1
                except Exception as e:
                    stats["errors"] += 1

            session.commit()
            stats["imported"] += inserted
            stats["series"][series_id] = inserted
            print(f"  {series_id} ({name}): {inserted} new")

    finally:
        session.close()

    print(f"\n  Total: {stats['imported']} imported, {stats['skipped']} skipped")
    return stats


def collect_fao_real_csv(db_manager: DatabaseManager) -> Dict:
    """Download real FAO Food Price Index CSV and import"""
    from data_sources.collectors import FAOCollector

    stats = {"imported": 0, "skipped": 0, "errors": 0, "categories": {}}

    print(f"\n{'='*70}")
    print("FAO FOOD PRICE INDEX (Real CSV Download)")
    print(f"{'='*70}\n")

    try:
        collector = FAOCollector()
        fao_data = collector.fetch_food_price_index()
    except Exception as e:
        print(f"  FAO CSV download failed: {e}")
        stats["errors"] = 1
        return stats

    session = db_manager.get_session()
    try:
        for category, records in fao_data.items():
            commodity_name = f"FAO Food Price Index - {category.title()}"
            inserted = 0

            for obs in records:
                try:
                    date_obj = datetime.strptime(obs["date"], "%Y-%m")
                    existing = (
                        session.query(GlobalPrice)
                        .filter(
                            GlobalPrice.commodity == commodity_name,
                            GlobalPrice.date == date_obj,
                            GlobalPrice.source == "FAO",
                        )
                        .first()
                    )
                    if existing:
                        # Update value if different (real data replacing Robin snapshot)
                        if abs(existing.price - float(obs["value"])) > 0.01:
                            existing.price = float(obs["value"])
                            inserted += 1
                        else:
                            stats["skipped"] += 1
                        continue

                    record = GlobalPrice(
                        date=date_obj,
                        commodity=commodity_name,
                        price=float(obs["value"]),
                        currency="index",
                        unit="2014-2016=100",
                        region="Global",
                        source="FAO",
                        indicator_code=f"fao_food_{category}",
                    )
                    session.add(record)
                    inserted += 1
                except Exception as e:
                    stats["errors"] += 1

            session.commit()
            stats["imported"] += inserted
            stats["categories"][category] = inserted
            print(f"  {category}: {inserted} new/updated, {len(records)} total")

    finally:
        session.close()

    print(f"\n  Total: {stats['imported']} imported, {stats['skipped']} skipped")
    return stats


def collect_worldbank_pink_sheet(db_manager: DatabaseManager) -> Dict:
    """Fetch World Bank Pink Sheet commodity prices via API"""
    from data_sources.collectors import WorldBankCollector

    stats = {"imported": 0, "skipped": 0, "errors": 0, "commodities": {}}

    print(f"\n{'='*70}")
    print("WORLD BANK PINK SHEET COMMODITIES (Live API)")
    print(f"{'='*70}\n")

    collector = WorldBankCollector()

    commodity_indicators = {
        "AG.PRD.FOOD.XD": "Food Production Index",
        "AG.PRD.CROP.XD": "Crop Production Index",
        "AG.PRD.LVSK.XD": "Livestock Production Index",
        "AG.LND.CREL.HA": "Land Under Cereal Production",
        "AG.PRD.CREL.MT": "Cereal Production (metric tons)",
        "AG.YLD.CREL.KG": "Cereal Yield (kg/hectare)",
        "NV.AGR.TOTL.ZS": "Agriculture Value Added (% GDP)",
        "TM.VAL.FOOD.ZS.UN": "Food Imports (% merchandise)",
        "TX.VAL.FOOD.ZS.UN": "Food Exports (% merchandise)",
        "FP.CPI.TOTL": "Consumer Price Index",
        "SN.ITK.DEFC.ZS": "Prevalence of Undernourishment (%)",
    }

    countries = ["USA", "CHN", "IND", "BRA", "ARG", "AUS", "CAN", "WLD"]

    session = db_manager.get_session()
    try:
        for indicator_code, indicator_name in commodity_indicators.items():
            print(f"  Fetching {indicator_code}: {indicator_name}...")
            try:
                data = collector.fetch_indicator(
                    indicator_code, countries=countries, start_year=1990
                )

                inserted = 0
                for obs in data:
                    try:
                        year = int(obs["date"])
                        date_obj = datetime(year, 7, 1)
                        country_code = obs.get("country", "WLD")
                        country_name = obs.get("country_name", "World")

                        existing = (
                            session.query(GlobalPrice)
                            .filter(
                                GlobalPrice.commodity == indicator_name,
                                GlobalPrice.date == date_obj,
                                GlobalPrice.country == country_code,
                                GlobalPrice.source == "World Bank",
                            )
                            .first()
                        )
                        if existing:
                            stats["skipped"] += 1
                            continue

                        record = GlobalPrice(
                            date=date_obj,
                            commodity=indicator_name,
                            price=float(obs["value"]),
                            currency="Index" if "Index" in indicator_name else "USD",
                            unit="index" if "Index" in indicator_name else "various",
                            region=country_name,
                            country=country_code,
                            source="World Bank",
                            indicator_code=indicator_code,
                        )
                        session.add(record)
                        inserted += 1
                    except Exception:
                        stats["errors"] += 1

                session.commit()
                stats["imported"] += inserted
                stats["commodities"][indicator_code] = inserted
                print(f"    {inserted} new records from {len(data)} observations")

            except Exception as e:
                print(f"    ERROR: {e}")
                stats["errors"] += 1
                time.sleep(1)

    finally:
        session.close()

    print(f"\n  Total: {stats['imported']} imported, {stats['skipped']} skipped")
    return stats


def collect_alpha_vantage(db_manager: DatabaseManager) -> Dict:
    """Fetch Alpha Vantage commodity futures (rate limited: 25/day)"""
    from data_sources.collectors import AlphaVantageCollector

    stats = {"imported": 0, "skipped": 0, "errors": 0, "commodities": {}}

    print(f"\n{'='*70}")
    print("ALPHA VANTAGE COMMODITY FUTURES (Live API, 25 req/day limit)")
    print(f"{'='*70}\n")

    try:
        collector = AlphaVantageCollector()
    except ValueError as e:
        print(f"  Alpha Vantage API key not configured: {e}")
        stats["errors"] = 1
        return stats

    food_commodities = ["WHEAT", "CORN", "SUGAR", "COFFEE", "COTTON"]

    session = db_manager.get_session()
    try:
        for commodity in food_commodities:
            print(f"  Fetching {commodity}...")
            try:
                data = collector.fetch_commodity(commodity, interval="monthly")
                inserted = 0

                for obs in data:
                    try:
                        date_obj = datetime.strptime(obs["date"], "%Y-%m-%d")
                        value = obs.get("value", 0)
                        if value == 0 or value == ".":
                            continue

                        existing = (
                            session.query(GlobalPrice)
                            .filter(
                                GlobalPrice.commodity == f"Alpha Vantage - {commodity}",
                                GlobalPrice.date == date_obj,
                                GlobalPrice.source == "Alpha Vantage",
                            )
                            .first()
                        )
                        if existing:
                            stats["skipped"] += 1
                            continue

                        record = GlobalPrice(
                            date=date_obj,
                            commodity=f"Alpha Vantage - {commodity}",
                            price=float(value),
                            currency="USD",
                            unit="USD per unit",
                            region="Global",
                            source="Alpha Vantage",
                            indicator_code=commodity,
                        )
                        session.add(record)
                        inserted += 1
                    except Exception:
                        stats["errors"] += 1

                session.commit()
                stats["imported"] += inserted
                stats["commodities"][commodity] = inserted
                print(f"    {inserted} new records from {len(data)} observations")

                time.sleep(12)

            except Exception as e:
                print(f"    ERROR: {e}")
                stats["errors"] += 1
                time.sleep(12)

    finally:
        session.close()

    print(f"\n  Total: {stats['imported']} imported, {stats['skipped']} skipped")
    return stats


def collect_usda_ams(db_manager: DatabaseManager) -> Dict:
    """Fetch USDA AMS Market News terminal prices"""
    stats = {"imported": 0, "skipped": 0, "errors": 0, "markets": {}}

    print(f"\n{'='*70}")
    print("USDA AMS MARKET NEWS TERMINAL PRICES (Live API)")
    print(f"{'='*70}\n")

    try:
        from data_sources.usda_client import USDAMarketNewsClient
        client = USDAMarketNewsClient()
    except Exception as e:
        print(f"  USDA AMS client init failed: {e}")
        stats["errors"] = 1
        return stats

    markets = list(client.terminal_markets.keys())

    session = db_manager.get_session()
    try:
        for market in markets:
            print(f"  Fetching {market}...")
            try:
                data = client.get_terminal_market_prices(market)

                if not data or not data.get("commodities"):
                    print(f"    No data available")
                    continue

                report_date_str = data.get("reportDate")
                if report_date_str:
                    try:
                        report_date = datetime.fromisoformat(report_date_str)
                    except ValueError:
                        report_date = datetime.now()
                else:
                    report_date = datetime.now()

                inserted = 0
                for commodity, varieties in data["commodities"].items():
                    for variety_data in varieties:
                        record = MarketPrice(
                            commodity=commodity.upper(),
                            variety=variety_data.get("variety", "standard"),
                            market_location=market,
                            low_price=variety_data.get("lowPrice"),
                            high_price=variety_data.get("highPrice"),
                            avg_price=variety_data.get("avgPrice"),
                            unit=variety_data.get("unit", "each"),
                            origin=variety_data.get("origin", "Unknown"),
                            report_date=report_date,
                            source="USDA Market News",
                        )
                        session.add(record)
                        inserted += 1

                session.commit()
                stats["imported"] += inserted
                stats["markets"][market] = inserted
                print(f"    {inserted} price records")

            except Exception as e:
                print(f"    ERROR: {e}")
                stats["errors"] += 1
                session.rollback()

    finally:
        session.close()

    print(f"\n  Total: {stats['imported']} imported, {stats['errors']} errors")
    return stats


def run_all_live_collection(
    skip_alpha_vantage: bool = False,
    skip_ams: bool = False,
):
    """Run all live data collection"""
    print("=" * 70)
    print("FOODBERG LIVE DATA COLLECTION")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    db_manager = DatabaseManager()
    db_manager.create_tables()

    all_stats = {}

    # 1. FRED food series
    print("\n[1/6] FRED Food-Specific Series...")
    all_stats["FRED Live"] = collect_fred_food_series(db_manager)

    # 2. BLS extended history
    print("\n[2/6] BLS Extended CPI History...")
    all_stats["BLS Live"] = collect_bls_extended(db_manager)

    # 3. FAO real CSV
    print("\n[3/6] FAO Real Food Price Index CSV...")
    all_stats["FAO Live"] = collect_fao_real_csv(db_manager)

    # 4. World Bank Pink Sheet
    print("\n[4/6] World Bank Pink Sheet Commodities...")
    all_stats["WB Live"] = collect_worldbank_pink_sheet(db_manager)

    # 5. Alpha Vantage
    if skip_alpha_vantage:
        print("\n[5/6] Alpha Vantage: SKIPPED (--skip-alpha-vantage)")
        all_stats["Alpha Vantage"] = {"status": "skipped"}
    else:
        print("\n[5/6] Alpha Vantage Commodity Futures...")
        all_stats["Alpha Vantage"] = collect_alpha_vantage(db_manager)

    # 6. USDA AMS
    if skip_ams:
        print("\n[6/6] USDA AMS: SKIPPED (--skip-ams)")
        all_stats["USDA AMS"] = {"status": "skipped"}
    else:
        print("\n[6/6] USDA AMS Market News Terminal Prices...")
        all_stats["USDA AMS"] = collect_usda_ams(db_manager)

    # Summary
    print("\n" + "=" * 70)
    print("LIVE COLLECTION SUMMARY")
    print("=" * 70)
    total_imported = 0
    for source, stats in all_stats.items():
        if "status" in stats and stats["status"] == "skipped":
            print(f"  {source}: SKIPPED")
        else:
            imported = stats.get("imported", 0)
            errors = stats.get("errors", 0)
            total_imported += imported
            status = "OK" if errors == 0 else f"PARTIAL ({errors} errors)"
            print(f"  {source}: {imported} imported [{status}]")

    print(f"\n  TOTAL NEW RECORDS: {total_imported}")

    # Database stats
    print("\nDatabase table counts:")
    try:
        db_stats = db_manager.get_database_stats()
        for table, count in db_stats.items():
            print(f"  {table}: {count:,}")
    except Exception as e:
        print(f"  Could not get stats: {e}")

    print(f"\nCompleted: {datetime.now().isoformat()}")
    print("=" * 70)

    return all_stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Foodberg Live Data Collection")
    parser.add_argument(
        "--skip-alpha-vantage",
        action="store_true",
        help="Skip Alpha Vantage (preserves daily API quota)",
    )
    parser.add_argument(
        "--skip-ams",
        action="store_true",
        help="Skip USDA AMS Market News (if API is down)",
    )
    args = parser.parse_args()

    run_all_live_collection(
        skip_alpha_vantage=args.skip_alpha_vantage,
        skip_ams=args.skip_ams,
    )
