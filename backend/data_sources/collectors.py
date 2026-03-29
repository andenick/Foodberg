"""
Foodberg Data Collectors
Independent data fetching from APIs - not dependent on Robin

Each collector fetches from original source APIs and stores in Foodberg's database.
"""

import httpx
import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from .api_keys import get_fred_key, get_bls_key, get_alpha_vantage_key


class AlphaVantageCollector:
    """
    Collect commodity prices from Alpha Vantage API
    https://www.alphavantage.co/documentation/

    Free tier: 25 requests/day - use for daily commodity futures
    Provides: WHEAT, CORN, SUGAR, COFFEE, COTTON, SOYBEANS, and more
    """

    BASE_URL = "https://www.alphavantage.co/query"

    # Commodity functions available
    COMMODITIES = {
        "WHEAT": "Global Wheat Prices",
        "CORN": "Global Corn Prices",
        "SUGAR": "Global Sugar Prices",
        "COFFEE": "Global Coffee Prices",
        "COTTON": "Global Cotton Prices",
        "NATURAL_GAS": "Natural Gas (energy/fertilizer cost driver)",
        "BRENT": "Brent Crude Oil (transport cost driver)",
        "WTI": "WTI Crude Oil (transport cost driver)",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_alpha_vantage_key()
        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key not configured. "
                "Get free key at: https://www.alphavantage.co/support/#api-key"
            )

    def fetch_commodity(self, commodity: str, interval: str = "monthly") -> List[Dict]:
        """
        Fetch commodity price data

        Args:
            commodity: One of WHEAT, CORN, SUGAR, COFFEE, COTTON, etc.
            interval: 'daily', 'weekly', or 'monthly'
        """
        params = {
            "function": commodity,
            "interval": interval,
            "apikey": self.api_key,
        }

        response = httpx.get(self.BASE_URL, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        # Check for API errors
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
        if "Note" in data:
            raise ValueError(f"API rate limit: {data['Note']}")

        # Parse data based on response structure
        observations = []
        data_key = f"data"  # Alpha Vantage uses "data" for commodities

        for item in data.get("data", []):
            try:
                observations.append(
                    {
                        "commodity": commodity,
                        "date": item.get("date"),
                        "value": float(item.get("value", 0)),
                    }
                )
            except (ValueError, TypeError):
                continue

        return observations

    def fetch_all_commodities(self, interval: str = "monthly") -> Dict[str, List[Dict]]:
        """Fetch all food-related commodities"""
        results = {}

        for commodity, name in self.COMMODITIES.items():
            print(f"  Fetching {commodity}: {name}...")
            try:
                data = self.fetch_commodity(commodity, interval)
                results[commodity] = {
                    "name": name,
                    "data": data,
                    "count": len(data),
                }
                print(f"    ✓ {len(data)} observations")
            except Exception as e:
                print(f"    ✗ Error: {e}")
                results[commodity] = {"name": name, "error": str(e)}

        return results

    def fetch_economic_indicators(self) -> Dict[str, List[Dict]]:
        """Fetch economic indicators that affect food prices"""
        indicators = {
            "CPI": "Consumer Price Index",
            "INFLATION": "Inflation Rate",
            "REAL_GDP": "Real GDP",
        }

        results = {}
        for indicator, name in indicators.items():
            print(f"  Fetching {indicator}: {name}...")
            try:
                params = {
                    "function": indicator,
                    "apikey": self.api_key,
                }
                response = httpx.get(self.BASE_URL, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                observations = []
                for item in data.get("data", []):
                    try:
                        observations.append(
                            {
                                "indicator": indicator,
                                "date": item.get("date"),
                                "value": float(item.get("value", 0)),
                            }
                        )
                    except (ValueError, TypeError):
                        continue

                results[indicator] = {
                    "name": name,
                    "data": observations,
                    "count": len(observations),
                }
                print(f"    ✓ {len(observations)} observations")
            except Exception as e:
                print(f"    ✗ Error: {e}")
                results[indicator] = {"name": name, "error": str(e)}

        return results


class WorldBankCollector:
    """
    Collect global agricultural indicators from World Bank API
    https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

    No API key required - 16,000+ indicators available
    """

    BASE_URL = "https://api.worldbank.org/v2"

    # Agriculture and food-related indicators
    INDICATORS = {
        # Food & Agriculture
        "AG.PRD.FOOD.XD": "Food Production Index",
        "AG.PRD.CROP.XD": "Crop Production Index",
        "AG.PRD.LVSK.XD": "Livestock Production Index",
        "AG.LND.AGRI.K2": "Agricultural Land (sq km)",
        "AG.LND.AGRI.ZS": "Agricultural Land (% of land)",
        "AG.LND.ARBL.ZS": "Arable Land (% of land)",
        "AG.CON.FERT.ZS": "Fertilizer Consumption (kg/ha)",
        # Food Prices & Security
        "FP.CPI.TOTL": "Consumer Price Index (food)",
        "SN.ITK.DEFC.ZS": "Prevalence of Undernourishment (%)",
        # Trade
        "TX.VAL.FOOD.ZS.UN": "Food Exports (% of merchandise)",
        "TM.VAL.FOOD.ZS.UN": "Food Imports (% of merchandise)",
    }

    # Major agricultural countries
    COUNTRIES = [
        "USA",
        "CHN",
        "IND",
        "BRA",
        "RUS",
        "ARG",
        "AUS",
        "CAN",
        "FRA",
        "DEU",
        "IDN",
        "THA",
        "VNM",
        "MEX",
        "NGA",
        "WLD",
    ]

    def __init__(self):
        # No API key needed for World Bank
        pass

    def fetch_indicator(
        self,
        indicator: str,
        countries: List[str] = None,
        start_year: int = None,
        end_year: int = None,
    ) -> List[Dict]:
        """
        Fetch World Bank indicator data

        Args:
            indicator: World Bank indicator code (e.g., "AG.PRD.FOOD.XD")
            countries: List of ISO3 country codes (default: major ag countries)
            start_year: Start year (default: 2000)
            end_year: End year (default: current year)
        """
        if countries is None:
            countries = self.COUNTRIES
        if start_year is None:
            start_year = 2000
        if end_year is None:
            end_year = datetime.now().year

        # World Bank API uses semicolon-separated country codes
        country_str = ";".join(countries)

        url = f"{self.BASE_URL}/country/{country_str}/indicator/{indicator}"
        params = {
            "format": "json",
            "date": f"{start_year}:{end_year}",
            "per_page": 1000,
        }

        response = httpx.get(url, params=params, timeout=60.0)
        response.raise_for_status()
        data = response.json()

        # World Bank returns [metadata, data] structure
        if not isinstance(data, list) or len(data) < 2:
            return []

        observations = []
        for item in data[1] or []:
            if item.get("value") is not None:
                observations.append(
                    {
                        "indicator": indicator,
                        "country": item.get("country", {}).get("id"),
                        "country_name": item.get("country", {}).get("value"),
                        "date": item.get("date"),
                        "value": float(item["value"]),
                    }
                )

        return observations

    def fetch_all_indicators(self) -> Dict[str, Dict]:
        """Fetch all agricultural indicators"""
        results = {}

        for indicator, name in self.INDICATORS.items():
            print(f"  Fetching {indicator}: {name}...")
            try:
                data = self.fetch_indicator(indicator)
                results[indicator] = {
                    "name": name,
                    "data": data,
                    "count": len(data),
                    "countries": len(set(d["country"] for d in data)) if data else 0,
                }
                print(
                    f"    ✓ {len(data)} observations from {results[indicator]['countries']} countries"
                )
            except Exception as e:
                print(f"    ✗ Error: {e}")
                results[indicator] = {"name": name, "error": str(e)}

        return results

    def fetch_global_food_prices(self) -> Dict[str, List[Dict]]:
        """Fetch global food price indices"""
        # World Bank Global Food Prices database indicators
        price_indicators = {
            "PNUTS_USD": "Peanuts Price ($/mt)",
            "PWHEATUS_USD": "Wheat Price US ($/mt)",
            "PMAIZMT_USD": "Maize Price ($/mt)",
            "PRICENPQ_USD": "Rice Price ($/mt)",
            "PSOYB_USD": "Soybeans Price ($/mt)",
            "PBEEF_USD": "Beef Price ($/kg)",
            "PPOULT_USD": "Poultry Price ($/kg)",
            "PSUGAISA_USD": "Sugar Price ($/kg)",
        }

        results = {}
        for indicator, name in price_indicators.items():
            print(f"  Fetching {indicator}: {name}...")
            try:
                # World Bank commodity prices use different endpoint
                url = f"{self.BASE_URL}/country/WLD/indicator/{indicator}"
                params = {"format": "json", "per_page": 500}
                response = httpx.get(url, params=params, timeout=30.0)

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 1 and data[1]:
                        observations = []
                        for item in data[1]:
                            if item.get("value") is not None:
                                observations.append(
                                    {
                                        "commodity": indicator,
                                        "date": item.get("date"),
                                        "value": float(item["value"]),
                                    }
                                )
                        results[indicator] = {
                            "name": name,
                            "data": observations,
                            "count": len(observations),
                        }
                        print(f"    ✓ {len(observations)} observations")
                    else:
                        results[indicator] = {"name": name, "data": [], "count": 0}
                        print(f"    ○ No data available")
                else:
                    results[indicator] = {
                        "name": name,
                        "error": f"HTTP {response.status_code}",
                    }
                    print(f"    ✗ HTTP {response.status_code}")
            except Exception as e:
                print(f"    ✗ Error: {e}")
                results[indicator] = {"name": name, "error": str(e)}

        return results


class FREDCollector:
    """
    Collect economic data directly from FRED API
    https://fred.stlouisfed.org/docs/api/
    """

    BASE_URL = "https://api.stlouisfed.org/fred"

    # Food-related FRED series
    FOOD_SERIES = {
        # Consumer Price Index - Food
        "CPIUFDSL": "CPI - Food",
        "CUSR0000SAF11": "CPI - Food at Home",
        "CUSR0000SEFV": "CPI - Food Away from Home",
        "CUSR0000SAF111": "CPI - Cereals and Bakery",
        "CUSR0000SAF112": "CPI - Meats, Poultry, Fish, Eggs",
        "CUSR0000SEFJ": "CPI - Dairy",
        "CUSR0000SAF113": "CPI - Fruits and Vegetables",
        # Producer Price Index - Food
        "WPU01": "PPI - Farm Products",
        "WPU02": "PPI - Processed Foods",
        # General Economic Indicators
        "CPIAUCSL": "CPI - All Items",
        "UNRATE": "Unemployment Rate",
        "FEDFUNDS": "Federal Funds Rate",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_fred_key()
        if not self.api_key:
            raise ValueError(
                "FRED API key not configured. Set FRED_API_KEY environment variable."
            )

    def fetch_series(
        self, series_id: str, start_date: str = None, end_date: str = None
    ) -> List[Dict]:
        """Fetch a single FRED series"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=3650)).strftime(
                "%Y-%m-%d"
            )  # 10 years
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        url = f"{self.BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date,
        }

        response = httpx.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        observations = []
        for obs in data.get("observations", []):
            if obs["value"] != ".":
                observations.append(
                    {
                        "series_id": series_id,
                        "date": obs["date"],
                        "value": float(obs["value"]),
                    }
                )

        return observations

    def fetch_all_food_series(self, start_date: str = None) -> Dict[str, List[Dict]]:
        """Fetch all food-related FRED series"""
        results = {}

        for series_id, name in self.FOOD_SERIES.items():
            print(f"  Fetching {series_id}: {name}...")
            try:
                data = self.fetch_series(series_id, start_date)
                results[series_id] = {"name": name, "data": data, "count": len(data)}
                print(f"    ✓ {len(data)} observations")
            except Exception as e:
                print(f"    ✗ Error: {e}")
                results[series_id] = {"name": name, "error": str(e)}

        return results


class BLSCollector:
    """
    Collect data directly from BLS API
    https://www.bls.gov/developers/
    """

    BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

    # Food CPI series
    FOOD_SERIES = {
        "CUUR0000SAF": "CPI - Food and Beverages",
        "CUUR0000SAF11": "CPI - Food at Home",
        "CUUR0000SEFV": "CPI - Food Away from Home",
        "CUUR0000SAF111": "CPI - Cereals and Bakery",
        "CUUR0000SAF112": "CPI - Meats, Poultry, Fish, Eggs",
        "CUUR0000SEFJ": "CPI - Dairy",
        "CUUR0000SAF113": "CPI - Fruits and Vegetables",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_bls_key()
        # BLS works without key but with limits

    def fetch_series(
        self, series_ids: List[str], start_year: int = None, end_year: int = None
    ) -> List[Dict]:
        """Fetch BLS series data"""
        if not start_year:
            start_year = datetime.now().year - 10
        if not end_year:
            end_year = datetime.now().year

        # BLS API limits
        year_limit = 20 if self.api_key else 10
        if end_year - start_year > year_limit:
            start_year = end_year - year_limit

        payload = {
            "seriesid": series_ids[:25],  # Max 25 per request
            "startyear": str(start_year),
            "endyear": str(end_year),
        }

        if self.api_key:
            payload["registrationkey"] = self.api_key

        headers = {"Content-type": "application/json"}
        response = httpx.post(
            self.BASE_URL, json=payload, headers=headers, timeout=30.0
        )
        response.raise_for_status()
        result = response.json()

        if result.get("status") != "REQUEST_SUCCEEDED":
            raise ValueError(f"BLS API error: {result.get('message', 'Unknown error')}")

        observations = []
        for series in result.get("Results", {}).get("series", []):
            series_id = series["seriesID"]
            for obs in series.get("data", []):
                # Convert period (M01-M12) to date
                period = obs["period"]
                if period.startswith("M"):
                    month = int(period[1:])
                    date = f"{obs['year']}-{month:02d}-01"
                    observations.append(
                        {
                            "series_id": series_id,
                            "date": date,
                            "value": float(obs["value"]),
                            "period_name": obs.get("periodName", ""),
                        }
                    )

        return observations

    def fetch_all_food_series(self, start_year: int = None) -> Dict[str, List[Dict]]:
        """Fetch all food CPI series"""
        series_ids = list(self.FOOD_SERIES.keys())

        print(f"  Fetching {len(series_ids)} BLS series...")
        try:
            all_data = self.fetch_series(series_ids, start_year)

            # Group by series
            results = {}
            for series_id, name in self.FOOD_SERIES.items():
                series_data = [d for d in all_data if d["series_id"] == series_id]
                results[series_id] = {
                    "name": name,
                    "data": series_data,
                    "count": len(series_data),
                }
                print(f"    ✓ {series_id}: {len(series_data)} observations")

            return results
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return {"error": str(e)}


class FAOCollector:
    """
    Collect FAO Food Price Index data
    Downloads directly from FAO's public CSV
    """

    CSV_URL = "https://www.fao.org/media/docs/worldfoodsituationlibraries/default-document-library/food_price_indices_data_csv_dec.csv"

    def fetch_food_price_index(self) -> Dict[str, List[Dict]]:
        """Download and parse FAO Food Price Index CSV"""
        print(f"  Downloading FAO Food Price Index...")

        response = httpx.get(self.CSV_URL, timeout=60.0, follow_redirects=True)
        response.raise_for_status()

        csv_content = response.text
        results = self._parse_fao_csv(csv_content)

        total = sum(len(v) for v in results.values())
        print(f"    ✓ {total} observations across {len(results)} categories")

        return results

    def _parse_fao_csv(self, csv_content: str) -> Dict[str, List[Dict]]:
        """Parse FAO CSV into structured data"""
        categories = {
            "food": [],
            "meat": [],
            "dairy": [],
            "cereals": [],
            "oils": [],
            "sugar": [],
        }

        lines = csv_content.strip().split("\n")

        # Find header row
        header_idx = None
        for i, line in enumerate(lines):
            if "Date" in line and "Food Price Index" in line:
                header_idx = i
                break

        if header_idx is None:
            raise ValueError("Could not find header row in FAO CSV")

        # Parse data rows
        col_map = {
            1: "food",  # Food Price Index
            2: "meat",  # Meat
            3: "dairy",  # Dairy
            4: "cereals",  # Cereals
            5: "oils",  # Oils
            6: "sugar",  # Sugar
        }

        for line in lines[header_idx + 1 :]:
            if not line.strip():
                continue

            values = line.split(",")
            date_val = values[0].strip() if values else ""

            # Check for valid date (YYYY-MM format)
            if not date_val or not (date_val[0].isdigit() and "-" in date_val):
                continue

            for col_idx, category in col_map.items():
                if col_idx < len(values):
                    try:
                        val = values[col_idx].strip()
                        if val:
                            categories[category].append(
                                {
                                    "date": date_val,
                                    "value": float(val),
                                    "category": category,
                                }
                            )
                    except (ValueError, IndexError):
                        pass

        return categories


def collect_all_data(
    output_dir: Path = None, include_alpha_vantage: bool = False
) -> Dict:
    """
    Collect data from all sources
    Returns summary of what was collected

    Args:
        output_dir: Directory to save collected data
        include_alpha_vantage: Whether to include Alpha Vantage (uses API quota)
    """
    import json

    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "collected"

    output_dir.mkdir(parents=True, exist_ok=True)

    results = {"timestamp": datetime.now().isoformat(), "sources": {}}

    # FRED
    print("\n[1/5] Collecting FRED data...")
    try:
        fred = FREDCollector()
        fred_data = fred.fetch_all_food_series()

        # Save to file
        with open(output_dir / "fred_data.json", "w") as f:
            json.dump(fred_data, f, indent=2)

        total = sum(
            d.get("count", 0) for d in fred_data.values() if isinstance(d, dict)
        )
        results["sources"]["fred"] = {
            "status": "success",
            "series": len(fred_data),
            "observations": total,
            "file": "fred_data.json",
        }
    except Exception as e:
        print(f"  ✗ FRED collection failed: {e}")
        results["sources"]["fred"] = {"status": "error", "error": str(e)}

    # BLS
    print("\n[2/5] Collecting BLS data...")
    try:
        bls = BLSCollector()
        bls_data = bls.fetch_all_food_series()

        with open(output_dir / "bls_data.json", "w") as f:
            json.dump(bls_data, f, indent=2)

        if "error" not in bls_data:
            total = sum(
                d.get("count", 0) for d in bls_data.values() if isinstance(d, dict)
            )
            results["sources"]["bls"] = {
                "status": "success",
                "series": len(bls_data),
                "observations": total,
                "file": "bls_data.json",
            }
        else:
            results["sources"]["bls"] = {"status": "error", "error": bls_data["error"]}
    except Exception as e:
        print(f"  ✗ BLS collection failed: {e}")
        results["sources"]["bls"] = {"status": "error", "error": str(e)}

    # FAO
    print("\n[3/5] Collecting FAO data...")
    try:
        fao = FAOCollector()
        fao_data = fao.fetch_food_price_index()

        with open(output_dir / "fao_data.json", "w") as f:
            json.dump(fao_data, f, indent=2)

        total = sum(len(v) for v in fao_data.values())
        results["sources"]["fao"] = {
            "status": "success",
            "categories": len(fao_data),
            "observations": total,
            "file": "fao_data.json",
        }
    except Exception as e:
        print(f"  ✗ FAO collection failed: {e}")
        results["sources"]["fao"] = {"status": "error", "error": str(e)}

    # World Bank (no API key needed)
    print("\n[4/5] Collecting World Bank data...")
    try:
        wb = WorldBankCollector()
        wb_data = wb.fetch_all_indicators()

        with open(output_dir / "worldbank_data.json", "w") as f:
            json.dump(wb_data, f, indent=2)

        total = sum(
            d.get("count", 0)
            for d in wb_data.values()
            if isinstance(d, dict) and "count" in d
        )
        results["sources"]["worldbank"] = {
            "status": "success",
            "indicators": len(wb_data),
            "observations": total,
            "file": "worldbank_data.json",
        }
    except Exception as e:
        print(f"  ✗ World Bank collection failed: {e}")
        results["sources"]["worldbank"] = {"status": "error", "error": str(e)}

    # Alpha Vantage (optional - uses daily quota)
    if include_alpha_vantage:
        print("\n[5/5] Collecting Alpha Vantage commodity data...")
        try:
            av = AlphaVantageCollector()
            av_data = av.fetch_all_commodities()

            with open(output_dir / "alphavantage_data.json", "w") as f:
                json.dump(av_data, f, indent=2)

            total = sum(
                d.get("count", 0)
                for d in av_data.values()
                if isinstance(d, dict) and "count" in d
            )
            results["sources"]["alphavantage"] = {
                "status": "success",
                "commodities": len(av_data),
                "observations": total,
                "file": "alphavantage_data.json",
            }
        except Exception as e:
            print(f"  ✗ Alpha Vantage collection failed: {e}")
            results["sources"]["alphavantage"] = {"status": "error", "error": str(e)}
    else:
        print("\n[5/5] Skipping Alpha Vantage (use --alpha-vantage flag to include)")
        results["sources"]["alphavantage"] = {
            "status": "skipped",
            "reason": "Not requested",
        }

    # Save summary
    with open(output_dir / "collection_summary.json", "w") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collect food commodity data")
    parser.add_argument(
        "--alpha-vantage",
        action="store_true",
        help="Include Alpha Vantage data (uses API quota)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("FOODBERG DATA COLLECTION")
    print("=" * 60)

    results = collect_all_data(include_alpha_vantage=args.alpha_vantage)

    print("\n" + "=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)

    for source, info in results["sources"].items():
        status = info.get("status", "unknown")
        if status == "success":
            obs = info.get("observations", 0)
            print(f"  ✓ {source.upper()}: {obs:,} observations")
        elif status == "skipped":
            print(f"  ○ {source.upper()}: {info.get('reason', 'skipped')}")
        else:
            print(f"  ✗ {source.upper()}: {info.get('error', 'failed')}")
