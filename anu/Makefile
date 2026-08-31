# Foodberg replication pipeline — run from the anu/ directory.
PY  ?= python
SCR = scripts

.PHONY: all quick nass faostat fetch process validate clean

# Full pipeline: every keyless source + FAOSTAT bulk + processor + validator.
all: fetch process validate

# Everything except the two FAOSTAT bulk zips (~400 MB) and the key-gated
# NASS family. The validator tolerates the missing faostat_ families.
quick:
	$(PY) $(SCR)/L01_fetch_pinksheet.py
	$(PY) $(SCR)/L03_fetch_fao_fpi.py
	$(PY) $(SCR)/L04_fetch_fred.py
	$(PY) $(SCR)/L05_fetch_blsgov.py
	$(PY) $(SCR)/L06_fetch_blsgap.py
	$(PY) $(SCR)/P01_harmonise_pinksheet.py
	$(PY) $(SCR)/P03_harmonise_fpi.py
	$(PY) $(SCR)/P04_harmonise_indicators.py
	$(PY) $(SCR)/P05_harmonise_retail.py
	$(PY) $(SCR)/P06_construct_composites.py
	$(PY) $(SCR)/V01_validate.py --allow-missing faostat_

faostat:
	$(PY) $(SCR)/L02_fetch_faostat.py
	$(PY) $(SCR)/P02_harmonise_faostat.py

nass:
	$(PY) $(SCR)/L07_fetch_nass_wasde.py
	$(PY) $(SCR)/P07_harmonise_nass.py
	$(PY) $(SCR)/V01_validate.py

fetch:
	$(PY) $(SCR)/L01_fetch_pinksheet.py
	$(PY) $(SCR)/L02_fetch_faostat.py
	$(PY) $(SCR)/L03_fetch_fao_fpi.py
	$(PY) $(SCR)/L04_fetch_fred.py
	$(PY) $(SCR)/L05_fetch_blsgov.py
	$(PY) $(SCR)/L06_fetch_blsgap.py

process:
	$(PY) $(SCR)/P01_harmonise_pinksheet.py
	$(PY) $(SCR)/P02_harmonise_faostat.py
	$(PY) $(SCR)/P03_harmonise_fpi.py
	$(PY) $(SCR)/P04_harmonise_indicators.py
	$(PY) $(SCR)/P05_harmonise_retail.py
	$(PY) $(SCR)/P06_construct_composites.py

validate:
	$(PY) $(SCR)/V01_validate.py

clean:
	rm -rf data
