#!/usr/bin/env python3
"""Verify WASDE data import"""

from database.manager import DatabaseManager
from database.models import WASDEData

db = DatabaseManager()
session = db.get_session()

# Get total records
total = session.query(WASDEData).count()
print(f'Total records: {total:,}')

# Get unique commodities
commodities = session.query(WASDEData.commodity).distinct().all()
print(f'Unique commodities: {len(commodities)}')

# Show count per commodity
print('\nRecords per commodity:')
for c in sorted([x[0] for x in commodities]):
    count = session.query(WASDEData).filter(WASDEData.commodity == c).count()
    print(f'  {c}: {count:,}')

session.close()
