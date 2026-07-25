# =============================================================================
# Foodberg — one retail price series, from the public API, in Python
#
# Foodberg's API needs no key, no registration and no rate limit. Every endpoint
# below is the same one the website itself calls to draw its own charts.
#
# Run:   python foodberg_prices.py
# Needs: pip install requests pandas matplotlib
# =============================================================================

import io

import matplotlib.pyplot as plt
import pandas as pd
import requests

# --- WHERE TO POINT AT THE DATA ---------------------------------------------
# ITEM is a commodity slug. The full list of slugs, with the sources and the
# real coverage span each one has, is at:
#   https://foodberg.org/api/prices/coverage      (the "commodities" object)
#
# SOURCE is one of:
#   retail     BLS Average Price — monthly, US retail, in kitchen units
#   pinksheet  World Bank Pink Sheet — monthly, global spot
#   nass       USDA NASS price received — annual, US farm gate
#
# Change these two lines; nothing below needs to change.
ITEM = "tomatoes-field-grown"
SOURCE = "retail"

resp = requests.get(
    f"https://foodberg.org/api/prices/source/{ITEM}",
    params={"source": SOURCE},
    timeout=30,
)
resp.raise_for_status()
payload = resp.json()

# The payload carries has_history, label, unit, data_points, date_range and
# "data" — date / year / price. Nothing is interpolated or extrapolated: a
# month with no published price simply has no row.
assert payload["has_history"], payload.get("note", "no series for this item/source")

prices = pd.DataFrame(payload["data"])
prices["date"] = pd.to_datetime(prices["date"])

print(payload["label"])
print(payload["data_points"], "observations,",
      payload["date_range"]["start"], "->", payload["date_range"]["end"])
print("latest:", prices["price"].iloc[-1], payload["unit"])
# BLS US retail average — Tomatoes, field grown
# 552 observations, 1980-01-01 -> 2026-06-01
# latest: 2.154 $ per lb

ax = prices.plot(x="date", y="price", legend=False, figsize=(9, 4))
ax.set_title(payload["label"])
ax.set_xlabel("")
ax.set_ylabel(payload["unit"])
plt.tight_layout()
plt.show()

# --- OR TAKE THE WHOLE TABLE ------------------------------------------------
# Every dataset listed on /data is also one flat file. No pagination, no key.
# retail_prices columns: food_item, price, unit, store_type, location, state,
#                        country, date, source, brand, quality_grade, imported_at
#
# Fetched through requests rather than pd.read_csv(url) directly. pandas reads a
# URL with urllib, and Cloudflare — which fronts foodberg.org — refuses
# urllib's default "Python-urllib/3.x" User-Agent with HTTP 403. requests,
# libcurl and R are all served normally (checked 2026-07-25), so this is a
# bot-fingerprint quirk of one client, not a restriction on the data.
bulk = requests.get(
    "https://foodberg.org/api/download/retail_prices.csv",
    timeout=120,
)
bulk.raise_for_status()
retail = pd.read_csv(io.StringIO(bulk.text))
print(len(retail), "rows,", retail["food_item"].nunique(), "items")
