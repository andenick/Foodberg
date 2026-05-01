"""
API Key Management for Foodberg
Loads keys from environment variables or config file
"""

import os
import json
from pathlib import Path
from typing import Optional


def load_api_keys() -> dict:
    """
    Load API keys from environment variables first, then fall back to config file.

    Priority:
    1. Environment variables (for production/deployment)
    2. Local config file (for development)
    3. Robin's ADMIN folder (fallback reference - not recommended for production)
    """
    keys = {
        "fred": os.getenv("FRED_API_KEY"),
        "bls": os.getenv("BLS_API_KEY"),
        "usda_nass": os.getenv("USDA_NASS_API_KEY") or os.getenv("USDA_API_KEY"),
        "usda_ams": os.getenv("USDA_AMS_API_KEY"),
        "bea": os.getenv("BEA_API_KEY"),
        "alpha_vantage": os.getenv("ALPHA_VANTAGE_API_KEY"),
    }

    # Check if any keys are missing
    missing = [k for k, v in keys.items() if not v]

    if missing:
        # Try local config file
        config_path = Path(__file__).parent.parent / "config" / "api_keys.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                for key in missing:
                    if key in config and not keys[key]:
                        keys[key] = config[key]
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")

    return keys


def get_fred_key() -> Optional[str]:
    """Get FRED API key"""
    return load_api_keys().get("fred")


def get_bls_key() -> Optional[str]:
    """Get BLS API key"""
    return load_api_keys().get("bls")


def get_usda_nass_key() -> Optional[str]:
    """Get USDA NASS Quick Stats API key"""
    return load_api_keys().get("usda_nass")


def get_usda_ams_key() -> Optional[str]:
    """Get USDA AMS Market News API key"""
    return load_api_keys().get("usda_ams")


def get_bea_key() -> Optional[str]:
    """Get BEA API key"""
    return load_api_keys().get("bea")


def get_alpha_vantage_key() -> Optional[str]:
    """Get Alpha Vantage API key (for commodity futures)"""
    return load_api_keys().get("alpha_vantage")
