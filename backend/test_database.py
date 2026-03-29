"""Quick database verification script"""
from database.manager import DatabaseManager

db = DatabaseManager()

print("Database Verification:")
print("="*60)

# Get overall stats
stats = db.get_database_stats()
print("\nRecord Counts:")
for key, value in stats.items():
    print(f"  {key:25s}: {value:8,}")

# Get commodities
commodities = db.get_wasde_commodities()
print(f"\nCommodities Imported: {len(commodities)}")
print(f"  {', '.join(commodities[:10])}")

# Get wheat stats
wheat_stats = db.get_wasde_statistics('WHEAT')
print("\nWheat Price Statistics:")
for key, value in wheat_stats.items():
    print(f"  {key}: {value}")

# Get sample price data
prices = db.get_wasde_prices(commodity='WHEAT', limit=5)
print(f"\nSample Wheat Prices ({len(prices)} records):")
for i, price in enumerate(prices[:3], 1):
    print(f"  {i}. {price['short_desc'][:60]}")
    print(f"     Value: {price['value']} {price['unit']}")
    print(f"     Location: {price['location']}, Year: {price['year']}")

print("\n" + "="*60)
print("[OK] Database verification complete!")
