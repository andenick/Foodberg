# =============================================================================
# Foodberg — one retail price series, from the public API, in R
#
# Foodberg's API needs no key, no registration and no rate limit. Every endpoint
# below is the same one the website itself calls to draw its own charts.
#
# Run:   Rscript foodberg_prices.R
# Needs: install.packages("jsonlite")
# =============================================================================

library(jsonlite)

# --- WHERE TO POINT AT THE DATA ---------------------------------------------
# `item` is a commodity slug. The full list of slugs, with the sources and the
# real coverage span each one has, is at:
#   https://foodberg.org/api/prices/coverage      (the `commodities` object)
#
# `source` is one of:
#   retail     BLS Average Price — monthly, US retail, in kitchen units
#   pinksheet  World Bank Pink Sheet — monthly, global spot
#   nass       USDA NASS price received — annual, US farm gate
#
# Change these two lines; nothing below needs to change.
item   <- "tomatoes-field-grown"
source <- "retail"

url  <- paste0("https://foodberg.org/api/prices/source/", item, "?source=", source)
resp <- fromJSON(url)

# The payload carries has_history, label, unit, data_points, date_range and
# `data` — a data frame of date / year / price. Nothing is interpolated or
# extrapolated: a month with no published price simply has no row.
stopifnot(isTRUE(resp$has_history))

prices <- resp$data
prices$date <- as.Date(prices$date)

cat(resp$label, "\n")
cat(resp$data_points, "observations,",
    resp$date_range$start, "->", resp$date_range$end, "\n")
cat("latest:", tail(prices$price, 1), resp$unit, "\n")
# BLS US retail average — Tomatoes, field grown
# 552 observations, 1980-01-01 -> 2026-06-01
# latest: 2.154 $ per lb

plot(prices$date, prices$price, type = "l",
     main = resp$label, xlab = "", ylab = resp$unit)

# --- OR TAKE THE WHOLE TABLE ------------------------------------------------
# Every dataset listed on /data is also one flat file. No pagination, no key.
# retail_prices columns: food_item, price, unit, store_type, location, state,
#                        country, date, source, brand, quality_grade, imported_at
retail <- read.csv("https://foodberg.org/api/download/retail_prices.csv",
                   stringsAsFactors = FALSE)
cat(nrow(retail), "rows,", length(unique(retail$food_item)), "items\n")
