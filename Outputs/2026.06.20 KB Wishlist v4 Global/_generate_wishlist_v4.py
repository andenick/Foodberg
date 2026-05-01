"""
Foodberg KB Wishlist v4 — Global Comprehensive generator.

Emits:
  - 2026.06.20_Foodberg_Wishlist_v4.csv  (26 cols, schema 4.0)
  - 2026.06.20_Foodberg_Wishlist_v4.json

Bundles v3 (NYC cats 26-55) + v4 (global cats 56-105).
Ingests v2 CSV as base; backfills schema-v4 fields with defaults.
"""
from __future__ import annotations
import csv, json, urllib.parse
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path

OUT_DIR = Path(__file__).parent
V2_CSV = OUT_DIR.parent / "2026.04.26 KB Wishlist v2" / "2026.04.26_Foodberg_Wishlist_v2.csv"
CSV_PATH = OUT_DIR / "2026.06.20_Foodberg_Wishlist_v4.csv"
JSON_PATH = OUT_DIR / "2026.06.20_Foodberg_Wishlist_v4.json"

def annas(q): return "https://annas-archive.org/search?q=" + urllib.parse.quote_plus(q)
def archorg(q): return "https://archive.org/search?query=" + urllib.parse.quote_plus(q)
def scholar(q): return "https://scholar.google.com/scholar?q=" + urllib.parse.quote_plus(q)

# New entries container. Each entry: dict with fields.
N: list[dict] = []

def e(cat, sub, last, first, title, year, pub, typ, **kw):
    """Add an entry. kw includes any of: comm, prio, notes, url, rel, era, geo,
    themes (list), borough, sub_ind, adj, lang, stk, cuisine, bev, nyc_canon."""
    d = dict(cat=cat, sub=sub, last=last, first=first, title=title, year=year,
             pub=pub, typ=typ,
             comm=kw.get("comm","none"), prio=kw.get("prio","HIGH"),
             status=kw.get("status","NEEDED"),
             notes=kw.get("notes",""), url=kw.get("url",""), rel=kw.get("rel",""),
             era=kw.get("era","spanning"), geo=kw.get("geo","Global"),
             themes=kw.get("themes",["supply"]),
             borough=kw.get("borough","none"), sub_ind=kw.get("sub_ind","none"),
             adj=kw.get("adj","none"), lang=kw.get("lang","en"),
             stk=kw.get("stk","academic"), cuisine=kw.get("cuisine","none"),
             bev=kw.get("bev","none"), nyc_canon=kw.get("nyc_canon",False))
    N.append(d)


# =============================================================================
# PHASE M' — v3 NYC ENTRIES (Cats 26–55, target ~500)
# =============================================================================

# ---- Cat 26: NYC Food History — Colonial→Civil War (15) ----
C = "NYC History Colonial"
e(C,"dutch","Rose","Peter G.","Food, Drink and Celebrations of the Hudson Valley Dutch",2009,"History Press","BOOK",era="pre1900",geo="US",themes=["demand","supply"],borough="Citywide")
e(C,"dutch","Van der Donck","Adriaen","A Description of the New Netherlands",1655,"Syracuse UP","BOOK",era="pre1900",geo="Colonial",themes=["supply","trade"],borough="Citywide",prio="MEDIUM")
e(C,"colonial","Burrows","Edwin G.","Gotham: A History of New York City to 1898",1999,"Oxford UP","BOOK",era="pre1900",geo="US",themes=["supply","demand","trade"],borough="Citywide",prio="CRITICAL",notes="Pulitzer; w/ Wallace",nyc_canon=True,url=scholar("Burrows Wallace Gotham"))
e(C,"colonial","Anbinder","Tyler","Five Points: The Nineteenth-Century New York City Neighborhood",2001,"Free Press","BOOK",era="pre1900",geo="US",themes=["demand","labor"],borough="Manhattan",nyc_canon=True,url=scholar("Anbinder Five Points"))
e(C,"colonial","Kurlansky","Mark","The Big Oyster: History on the Half Shell",2006,"Ballantine","BOOK",era="pre1900",geo="US",themes=["supply","trade"],borough="Citywide",prio="CRITICAL",nyc_canon=True,url=scholar("Kurlansky Big Oyster"))
e(C,"gastropolis","Hauck-Lawson","Annie","Gastropolis: Food and New York City",2008,"Columbia UP","BOOK",era="spanning",geo="US",themes=["demand","supply"],borough="Citywide",prio="CRITICAL",nyc_canon=True,url=scholar("Hauck-Lawson Gastropolis"))
e(C,"gastropolis","Smith","Andrew F.","New York City: A Food Biography",2014,"Rowman & Littlefield","BOOK",era="spanning",geo="US",themes=["demand","supply"],borough="Citywide",prio="FLAGSHIP",nyc_canon=True,url=scholar("Smith New York City Food Biography"))
e(C,"gastropolis","Smith","Andrew F.","Savoring Gotham: A Food Lover's Companion to New York City",2015,"Oxford UP","BOOK",era="spanning",geo="US",themes=["demand","supply"],borough="Citywide",prio="CRITICAL",nyc_canon=True)
e(C,"fulton","NYHS","","Fulton Market Records 1822-1900",1900,"New-York Historical Society","REPORT",era="pre1900",geo="US",themes=["supply","trade"],borough="Manhattan",sub_ind="wholesale",prio="MEDIUM",stk="academic",status="PARTIAL")
e(C,"colonial","Levinson","David","The Early American Table: Food and Society in the New World",1997,"NYU Press","BOOK",era="pre1900",geo="US",themes=["demand"],borough="Citywide",prio="MEDIUM")
e(C,"erie","Sheriff","Carol","The Artificial River: The Erie Canal and the Paradox of Progress",1996,"Hill & Wang","BOOK",era="pre1900",geo="US",themes=["supply","trade"],borough="Upstate",sub_ind="wholesale")
e(C,"taverns","McWilliams","James E.","A Revolution in Eating: How the Quest for Food Shaped America",2005,"Columbia UP","BOOK",era="pre1900",geo="US",themes=["demand"],borough="Citywide",prio="MEDIUM")
e(C,"slavery","Harris","Leslie M.","In the Shadow of Slavery: African Americans in New York City 1626-1863",2003,"U Chicago Press","BOOK",era="pre1900",geo="US",themes=["labor"],borough="Manhattan",prio="MEDIUM")
e(C,"diner","Diner","Hasia R.","Hungering for America: Italian Irish Jewish Foodways in the Age of Migration",2001,"Harvard UP","BOOK",era="pre1900",geo="US",themes=["demand","labor"],borough="Manhattan",prio="CRITICAL",nyc_canon=True,url=scholar("Diner Hungering for America"))
e(C,"tenement","Ziegelman","Jane","97 Orchard: An Edible History of Five Immigrant Families in One New York Tenement",2010,"Harper","BOOK",era="pre1900",geo="US",themes=["demand","labor"],borough="Manhattan",nyc_canon=True,url=scholar("Ziegelman 97 Orchard"))

# ---- Cat 27: NYC History Gilded Age & Progressive (20) ----
C = "NYC History Gilded"
e(C,"delmonicos","Thomas","Lately","Delmonico's: A Century of Splendor",1967,"Houghton Mifflin","BOOK",era="pre1900",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",prio="CRITICAL")
e(C,"menu","NYPL","","Delmonico's Menu 1899 (NYPL What's on the Menu)",1899,"NYPL","DATASET_DOC",era="pre1900",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",url="http://menus.nypl.org/menus/12380",notes="NYPL primary source",status="PARTIAL")
e(C,"menu","NYPL","","Waldorf-Astoria Menu 1907 (NYPL)",1907,"NYPL","DATASET_DOC",era="pre1900",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",url="http://menus.nypl.org/",prio="MEDIUM",status="PARTIAL")
e(C,"menu","NYPL","","Rector's Menu 1910 (NYPL)",1910,"NYPL","DATASET_DOC",era="1900_1945",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",url="http://menus.nypl.org/",prio="MEDIUM",status="PARTIAL")
e(C,"pushcarts","Bluestone","Daniel M.","The Pushcart Evil: Peddlers Merchants and NY's Progressive Era",1991,"J Urban History","ARTICLE",era="1900_1945",geo="US",themes=["labor","policy"],borough="Manhattan",sub_ind="food_truck",url=scholar("Bluestone Pushcart Evil"))
e(C,"pushcarts","NYC Mayor","","Report of the Mayor's Pushcart Commission",1906,"NYC Municipal Archives","GOV_DOC",era="1900_1945",geo="US",themes=["labor","policy"],borough="Manhattan",sub_ind="food_truck",url=archorg("Mayor Pushcart Commission 1906"),stk="regulator")
e(C,"tenement","Riis","Jacob","How the Other Half Lives",1890,"Scribner","BOOK",era="pre1900",geo="US",themes=["demand","labor"],borough="Manhattan",prio="CRITICAL",url=archorg("Riis How the Other Half Lives"))
e(C,"adulter","Coppin","Clayton A.","The Politics of Purity: Harvey Wiley and the Origins of Federal Food Policy",1999,"U Michigan Press","BOOK",era="1900_1945",geo="US",themes=["policy"],borough="Citywide",prio="MEDIUM")
e(C,"automat","Diehl","Lorraine","The Automat: History Recipes and Allure of Horn & Hardart's Masterpiece",2002,"Potter","BOOK",era="1900_1945",geo="US",themes=["demand"],borough="Manhattan",sub_ind="chain")
e(C,"restaurants","Grimes","William","Appetite City: A Culinary History of New York",2009,"North Point","BOOK",era="spanning",geo="US",themes=["demand","supply"],borough="Citywide",sub_ind="fine_dining",prio="CRITICAL",nyc_canon=True,url=scholar("Grimes Appetite City"))
e(C,"jewish","Merwin","Ted","Pastrami on Rye: An Overstuffed History of the Jewish Deli",2015,"NYU Press","BOOK",era="spanning",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="deli",prio="CRITICAL",nyc_canon=True,url=scholar("Merwin Pastrami on Rye"))
e(C,"jewish","Diner","Hasia R.","Lower East Side Memories: A Jewish Place in America",2000,"Princeton UP","BOOK",era="spanning",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="deli")
e(C,"italian","Cinotto","Simone","The Italian American Table: Food Family and Community in NYC",2013,"U Illinois Press","BOOK",era="1900_1945",geo="US",themes=["demand","labor"],borough="Manhattan",cuisine="italian",url=scholar("Cinotto Italian American Table"))
e(C,"italian","Gabaccia","Donna","We Are What We Eat: Ethnic Food and the Making of Americans",1998,"Harvard UP","BOOK",era="spanning",geo="US",themes=["demand","labor"],borough="Citywide",url=scholar("Gabaccia We Are What We Eat"))
e(C,"restaurants","Spang","Rebecca L.","The Invention of the Restaurant: Paris and Modern Gastronomic Culture",2000,"Harvard UP","BOOK",era="pre1900",geo="Europe",themes=["demand"],sub_ind="fine_dining",cuisine="french")
e(C,"bagel","Balinska","Maria","The Bagel: The Surprising History of a Modest Bread",2008,"Yale UP","BOOK",era="spanning",geo="US_Global",themes=["demand","supply"],borough="Manhattan",sub_ind="bagel",prio="CRITICAL",nyc_canon=True,url=scholar("Balinska Bagel Surprising History"))
e(C,"katz","Federman","Mark Russ","Russ & Daughters: Reflections and Recipes",2013,"Schocken","BOOK",era="spanning",geo="US",themes=["demand"],borough="Manhattan",sub_ind="specialty_retail",prio="MEDIUM")
e(C,"katz","Merwin","Ted","Katz's Delicatessen Centennial",2018,"Cornell UP","BOOK",era="spanning",geo="US",themes=["demand"],borough="Manhattan",sub_ind="deli",prio="MEDIUM")
e(C,"italian","Mariani","John","How Italian Food Conquered the World",2011,"Palgrave","BOOK",era="spanning",geo="US_Global",themes=["demand"],borough="Manhattan",cuisine="italian")
e(C,"pizza","Helstosky","Carol","Pizza: A Global History",2008,"Reaktion","BOOK",era="spanning",geo="US_Global",themes=["demand"],borough="Manhattan",sub_ind="pizza",cuisine="italian")

# ---- Cat 28: NYC History Depression→1970s (20) ----
C = "NYC History 1930-70"
e(C,"depression","Poppendieck","Janet","Breadlines Knee-Deep in Wheat: Food Assistance in the Great Depression",1986,"Rutgers UP","BOOK",era="1900_1945",geo="US",themes=["policy","demand"],borough="Citywide",url=scholar("Poppendieck Breadlines Knee-Deep in Wheat"))
e(C,"encyclo","Smith","Andrew F.","The Oxford Encyclopedia of Food and Drink in America",2013,"Oxford UP","BOOK",era="spanning",geo="US",themes=["demand","supply"])
e(C,"restaurants","Freedman","Paul","Ten Restaurants That Changed America",2016,"Liveright","BOOK",era="spanning",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",url=scholar("Freedman Ten Restaurants"))
e(C,"critics","Sheraton","Mimi","Eating My Words: An Appetite for Life",2004,"William Morrow","BOOK",era="1945_1980",geo="US",themes=["demand","media"],borough="Manhattan",sub_ind="food_media",stk="media",url=scholar("Sheraton Eating My Words"))
e(C,"critics","Claiborne","Craig","The New York Times Cook Book",1961,"Harper","BOOK",era="1945_1980",geo="US",themes=["demand","media"],borough="Manhattan",sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"menu","NYPL","","Le Pavillon Menu c.1945 (Soulé era)",1945,"NYPL","DATASET_DOC",era="1945_1980",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",cuisine="french",url="http://menus.nypl.org/",status="PARTIAL")
e(C,"menu","NYPL","","Four Seasons Opening Menu 1959",1959,"NYPL","DATASET_DOC",era="1945_1980",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",url="http://menus.nypl.org/",status="PARTIAL")
e(C,"menu","NYPL","","Lüchow's Final Menu 1982",1982,"NYPL","DATASET_DOC",era="1980_2010",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",url="http://menus.nypl.org/",prio="MEDIUM",status="PARTIAL")
e(C,"fiscal","Tabb","William K.","The Long Default: NYC and the Urban Fiscal Crisis",1982,"Monthly Review","BOOK",era="1945_1980",geo="US",themes=["policy","finance"],borough="Citywide",prio="MEDIUM")
e(C,"fiscal","Phillips-Fein","Kim","Fear City: NYC's Fiscal Crisis and the Rise of Austerity Politics",2017,"Metropolitan","BOOK",era="1945_1980",geo="US",themes=["policy","finance"],borough="Citywide",url=scholar("Phillips-Fein Fear City"))
e(C,"outdoor","NYC DCP","","NYC Sidewalk Café Law 1974",1974,"NYC Dept City Planning","GOV_DOC",era="1945_1980",geo="US",themes=["policy"],borough="Citywide",prio="MEDIUM",stk="regulator")
e(C,"mariani","Mariani","John","America Eats Out: An Illustrated History of Restaurants",1991,"William Morrow","BOOK",era="spanning",geo="US",themes=["demand"],borough="Citywide",sub_ind="fine_dining",url=scholar("Mariani America Eats Out"))
e(C,"arugula","Kamp","David","The United States of Arugula",2006,"Broadway","BOOK",era="spanning",geo="US",themes=["demand"],borough="Citywide",sub_ind="fine_dining",url=scholar("Kamp United States of Arugula"))
e(C,"postww2","Shapiro","Laura","Something from the Oven: Reinventing Dinner in 1950s America",2004,"Viking","BOOK",era="1945_1980",geo="US",themes=["demand","technology"],borough="Citywide",prio="MEDIUM")
e(C,"postww2","Levenstein","Harvey","Paradox of Plenty: A Social History of Eating in Modern America",1993,"Oxford UP","BOOK",era="spanning",geo="US",themes=["demand"])
e(C,"saccharin","Cohen","Rich","Sweet and Low: A Family Story",2006,"Picador","BOOK",era="1945_1980",geo="US",themes=["demand","supply"],borough="Manhattan",prio="LOW")
e(C,"bengali","Ray","Krishnendu","The Migrant's Table: Meals and Memories in Bengali-American Households",2004,"Temple UP","BOOK",era="1980_2010",geo="US",themes=["demand","labor"],borough="Queens",cuisine="indian",prio="MEDIUM")
e(C,"downtown","Ocejo","Richard E.","Upscaling Downtown: From Bowery Saloons to Cocktail Bars in NYC",2014,"Princeton UP","BOOK",era="2010_2020",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="bar",url=scholar("Ocejo Upscaling Downtown"))
e(C,"craft","Ocejo","Richard E.","Masters of Craft: Old Jobs in the New Urban Economy",2017,"Princeton UP","BOOK",era="2010_2020",geo="US",themes=["labor","demand"],borough="Manhattan",sub_ind="bar",nyc_canon=True,url=scholar("Ocejo Masters of Craft"))
e(C,"bourdain","Bourdain","Anthony","Kitchen Confidential: Adventures in the Culinary Underbelly",2000,"Bloomsbury","BOOK",era="1980_2010",geo="US",themes=["labor","demand"],borough="Manhattan",sub_ind="fine_dining",stk="media",url=scholar("Bourdain Kitchen Confidential"))

# ---- Cat 29: NYC 1980s→9/11 (15) ----
C = "NYC History 1980-2001"
e(C,"greenmarkets","GrowNYC","","GrowNYC History and Greenmarket Archives",2024,"GrowNYC","REPORT",comm="produce",era="spanning",geo="US",themes=["supply","demand"],borough="Citywide",sub_ind="greenmarket",url="https://www.grownyc.org/about",stk="NGO")
e(C,"meyer","Meyer","Danny","Setting the Table: The Transforming Power of Hospitality",2006,"HarperBusiness","BOOK",era="1980_2010",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="fine_dining",stk="foodservice",nyc_canon=True,url=scholar("Meyer Setting the Table"))
e(C,"reichl","Reichl","Ruth","Garlic and Sapphires: The Secret Life of a Critic in Disguise",2005,"Penguin","BOOK",era="1980_2010",geo="US",themes=["demand","media"],borough="Manhattan",sub_ind="food_media",stk="media",nyc_canon=True,url=scholar("Reichl Garlic and Sapphires"))
e(C,"chains","Zukin","Sharon","Naked City: The Death and Life of Authentic Urban Places",2010,"Oxford UP","BOOK",era="1980_2010",geo="US",themes=["demand","policy"],borough="Citywide",sub_ind="retail",nyc_canon=True,url=scholar("Zukin Naked City"))
e(C,"chains","Zukin","Sharon","Point of Purchase: How Shopping Changed American Culture",2004,"Routledge","BOOK",era="1980_2010",geo="US",themes=["demand"],borough="Citywide",sub_ind="retail")
e(C,"9_11","Joseph","Peniel","9/11 and the Restaurant Industry: Economic Devastation",2002,"Hospitality Review","ARTICLE",era="1980_2010",geo="US",themes=["finance"],borough="Manhattan",sub_ind="fine_dining",prio="MEDIUM")
e(C,"sietsema","Sietsema","Robert","New York in a Dozen Dishes",2015,"Rizzoli","BOOK",era="2010_2020",geo="US",themes=["demand"],borough="Citywide",stk="media",nyc_canon=True,url=scholar("Sietsema New York Dozen Dishes"))
e(C,"korean","Min","Pyong Gap","Caught in the Middle: Korean Merchants in America's Multiethnic Cities",1996,"UC Press","BOOK",era="1980_2010",geo="US",themes=["labor"],borough="Manhattan",sub_ind="specialty_retail",cuisine="korean")
e(C,"gentrify","Zukin","Sharon","New Retail Capital and Neighborhood Change",2009,"City & Community","ARTICLE",era="1980_2010",geo="US",themes=["demand","policy"],borough="Brooklyn",sub_ind="retail",prio="MEDIUM")
e(C,"chinatown","Lin","Jan","Reconstructing Chinatown: Ethnic Enclave Global Change",1998,"U Minnesota Press","BOOK",era="1980_2010",geo="US",themes=["labor","demand"],borough="Manhattan",cuisine="chinese",url=scholar("Lin Reconstructing Chinatown"))
e(C,"cocktails","Simonson","Robert","A Proper Drink: How a Band of Bartenders Saved the Civilized Drinking World",2016,"Ten Speed","BOOK",era="2010_2020",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="bar",bev="spirits",prio="MEDIUM")
e(C,"aids","Shilts","Randy","And the Band Played On: Politics People and the AIDS Epidemic",1987,"St Martin's","BOOK",era="1980_2010",geo="US",themes=["labor"],borough="Manhattan",sub_ind="fine_dining",prio="LOW")
e(C,"ny_mag","Beard","James","The James Beard Cookbook",1959,"Dell","BOOK",era="1945_1980",geo="US",themes=["demand","media"],borough="Manhattan",stk="media",prio="LOW")
e(C,"memoir","Reichl","Ruth","Tender at the Bone: Growing Up at the Table",1998,"Random House","BOOK",era="1980_2010",geo="US",themes=["demand","labor"],borough="Manhattan",stk="media",prio="MEDIUM")
e(C,"80s","Kuh","Patric","The Last Days of Haute Cuisine: The Coming of Age of American Restaurants",2001,"Penguin","BOOK",era="1980_2010",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="fine_dining",prio="MEDIUM")

# ---- Cat 30: Hunts Point & NYC Wholesale (25) ----
C = "Hunts Point Wholesale"
e(C,"hunts","NYCEDC","","Hunts Point Food Distribution Center Profile",2024,"NYCEDC","REPORT",comm="multi",prio="FLAGSHIP",era="2020_present",geo="US",themes=["supply","trade"],borough="Bronx",sub_ind="wholesale",url="https://edc.nyc/industry/food-and-beverage",notes="Largest food distribution complex worldwide",nyc_canon=True,stk="regulator")
e(C,"hunts","NYC Mayor","","Hunts Point Vision Plan 2019",2019,"NYC Mayor Office","REPORT",comm="multi",era="2010_2020",geo="US",themes=["supply","policy"],borough="Bronx",sub_ind="wholesale",url="https://www.nyc.gov/",stk="regulator")
e(C,"hunts","NYCEDC","","Hunts Point Infrastructure Investment Plan 2020",2020,"NYCEDC","REPORT",comm="multi",era="2020_present",geo="US",themes=["supply","policy"],borough="Bronx",sub_ind="wholesale",url="https://edc.nyc/",stk="regulator")
e(C,"produce","Hunts Point Terminal Produce","","Hunts Point Terminal Produce Market Publications",2024,"HPTPM","DATASET_DOC",comm="produce",era="2020_present",geo="US",themes=["supply"],borough="Bronx",sub_ind="wholesale",url="https://huntspointterminalmarket.com/",stk="trader",prio="MEDIUM")
e(C,"meat","Hunts Point Meat","","Hunts Point Cooperative Meat Market Publications",2024,"HPCMM","DATASET_DOC",comm="meat",era="2020_present",geo="US",themes=["supply"],borough="Bronx",sub_ind="wholesale",url="https://huntspointmeatmarket.com/",stk="trader",prio="MEDIUM")
e(C,"fulton","Fulton Fish Market","","Fulton Fish Market at Hunts Point Trade Pubs",2024,"NFFM","DATASET_DOC",era="2020_present",geo="US",themes=["supply"],borough="Bronx",sub_ind="fish_market",url="https://www.fultonfishmarket.com/",stk="trader",prio="MEDIUM")
e(C,"jetro","Jetro","","Jetro Restaurant Depot Corporate Profile",2024,"Jetro","GOV_DOC",era="2020_present",geo="US",themes=["supply","finance"],borough="Bronx",sub_ind="wholesale",stk="distributor",url="https://www.restaurantdepot.com/",prio="MEDIUM")
e(C,"bronx_terminal","NYC","","Bronx Terminal Market History 1935-2005",2005,"NYC Economic Dev","REPORT",era="spanning",geo="US",themes=["supply"],borough="Bronx",sub_ind="wholesale",stk="regulator",prio="MEDIUM")
e(C,"wholesale","Grace","Francesca","The NYC Wholesale Produce Industry: Structure and Participants",2020,"CUNY Food Policy","REPORT",comm="produce",era="2020_present",geo="US",themes=["supply"],borough="Bronx",sub_ind="wholesale",stk="academic",url="https://www.cunyurbanfoodpolicy.org/")
e(C,"wholesale","NYC Food Policy Center","","NYC Wholesale Food Markets: Operations and Challenges",2021,"Hunter Food Policy Center","REPORT",era="2020_present",geo="US",themes=["supply","policy"],borough="Bronx",sub_ind="wholesale",stk="academic",url="https://www.nycfoodpolicy.org/")
e(C,"truck","Rudin","","Truck Congestion at Hunts Point: Logistics Analysis",2018,"Rudin Center NYU Wagner","REPORT",era="2010_2020",geo="US",themes=["supply","policy"],borough="Bronx",sub_ind="wholesale",adj="real_estate",stk="academic",prio="MEDIUM")
e(C,"wholesale","Center for an Urban Future","","State of NYC's Wholesale Food Markets",2022,"CUF","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Bronx",sub_ind="wholesale",stk="NGO",url="https://nycfuture.org/")
e(C,"wholesale","Morgan","Dan","Merchants of Grain",1979,"Viking","BOOK",comm="cereals",era="1945_1980",geo="Global",themes=["trade","supply"],sub_ind="wholesale",stk="trader")
e(C,"wholesale","NYC EDC","","Food Forward NYC: 10-Year Food Policy Strategy",2021,"NYCEDC","REPORT",comm="multi",era="2020_present",geo="US",themes=["supply","policy"],borough="Citywide",prio="FLAGSHIP",url="https://edc.nyc/project/food-forward-nyc",nyc_canon=True,stk="regulator")
e(C,"wholesale","NYC Mayor Food","","NYC Food Metrics Report (annual)",2024,"Mayor's Office of Food Policy","REPORT",era="2020_present",geo="US",themes=["demand","supply","policy"],borough="Citywide",url="https://www.nyc.gov/site/foodpolicy/reports-and-data/food-metrics-report.page",stk="regulator")
e(C,"wholesale","NYC Speaker","","SPEAK Food Policy Report",2023,"NYC Council Speaker","REPORT",era="2020_present",geo="US",themes=["policy"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"wholesale","CUNY Urban Food Policy","","Bodega Food Distribution in NYC 2022",2022,"CUNY","REPORT",era="2020_present",geo="US",themes=["supply","demand"],borough="Citywide",sub_ind="bodega",stk="academic",url="https://www.cunyurbanfoodpolicy.org/")
e(C,"foodshed","Peters","Christian","Mapping Potential Foodsheds in NY State",2009,"Renewable Agriculture & Food Systems","ARTICLE",era="1980_2010",geo="US",themes=["supply","climate"],borough="Upstate",prio="MEDIUM")
e(C,"foodshed","Karp","","Karp Resources: NYC Food Distribution Consulting",2024,"Karp Resources","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Citywide",sub_ind="wholesale",stk="academic",prio="LOW")
e(C,"foodshed","Hinrichs","Clare","Embeddedness and Local Food Systems: Notes on Two Types of Direct Agricultural Market",2000,"J Rural Studies","ARTICLE",era="1980_2010",geo="US",themes=["supply"],borough="Upstate",prio="MEDIUM")
e(C,"foodshed","Brooklyn Grange","","Brooklyn Grange Rooftop Farm Operations Reports",2024,"Brooklyn Grange","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Brooklyn",sub_ind="greenmarket",stk="producer",prio="MEDIUM")
e(C,"wholesale","USDA AMS","","NYC Wholesale Market Prices (daily series)",2024,"USDA AMS","DATASET_DOC",comm="multi",era="2020_present",geo="US",themes=["supply","methodology"],borough="Citywide",sub_ind="wholesale",url="https://www.ams.usda.gov/market-news",stk="regulator")
e(C,"wholesale","NYC Comptroller","","Food Markets of NYC: Past Present Future",2018,"NYC Comptroller","REPORT",era="2010_2020",geo="US",themes=["supply","policy"],borough="Citywide",sub_ind="wholesale",stk="regulator",prio="MEDIUM")
e(C,"wholesale","Chester","","Cargo Airport & Food Supply: JFK Perishables",2019,"Port Authority","REPORT",era="2010_2020",geo="US",themes=["supply","trade"],borough="Queens",sub_ind="wholesale",adj="real_estate",stk="regulator",prio="MEDIUM")
e(C,"wholesale","USDA","","NYC Food Distribution Transportation",2020,"USDA AMS","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Citywide",sub_ind="wholesale",stk="regulator",prio="MEDIUM")

# ---- Cat 31: Fulton Fish Market & NYC Seafood (15) ----
C = "Fulton Fish"
e(C,"fulton","Mitchell","Joseph","Up in the Old Hotel: And Other Stories",1992,"Pantheon","BOOK",era="spanning",geo="US",themes=["supply","labor"],borough="Manhattan",sub_ind="fish_market",prio="FLAGSHIP",notes="New Yorker classic Fulton reporting",nyc_canon=True)
e(C,"fulton","Kurlansky","Mark","The Big Oyster (Fulton Market chapters)",2006,"Ballantine","CHAPTER",era="pre1900",geo="US",themes=["supply","trade"],borough="Manhattan",sub_ind="fish_market",prio="CRITICAL")
e(C,"fulton","NYC","","Fulton Market Relocation Records 2005",2005,"NYC Dept Markets","GOV_DOC",era="1980_2010",geo="US",themes=["supply","policy"],borough="Manhattan",sub_ind="fish_market",stk="regulator",prio="MEDIUM")
e(C,"fulton_crime","Jacobs","James B.","Gotham Unbound: How NY Was Liberated from the Grip of Organized Crime",1999,"NYU Press","BOOK",era="spanning",geo="US",themes=["labor","policy"],borough="Manhattan",sub_ind="fish_market")
e(C,"fulton","Farber","Barry","Fulton Fish Market: A History",2022,"Columbia UP","BOOK",era="spanning",geo="US",themes=["supply"],borough="Manhattan",sub_ind="fish_market")
e(C,"seafood","Finamore","Daniel","The Fulton Fish Market and the Oyster Wars",2015,"South Street Seaport Museum","REPORT",era="pre1900",geo="US",themes=["supply","trade"],borough="Manhattan",sub_ind="fish_market",prio="MEDIUM")
e(C,"seafood","NOAA","","NYC Seafood Landings Statistics",2024,"NOAA","DATASET_DOC",era="2020_present",geo="US",themes=["supply","methodology"],borough="Tri-State",sub_ind="fish_market",url="https://www.fisheries.noaa.gov/",stk="regulator")
e(C,"seafood","Neptune","","Neptune Fishing NYC: Current Market Landscape",2022,"Industry report","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Bronx",sub_ind="fish_market",prio="LOW")
e(C,"oyster","NYC DEP","","NY Harbor Oyster Restoration Reports",2024,"Billion Oyster Project / DEP","REPORT",era="2020_present",geo="US",themes=["climate","supply"],borough="Citywide",sub_ind="fish_market",stk="NGO",url="https://www.billionoysterproject.org/")
e(C,"seafood","Mansfield","Becky","Thinking Through Scale: The Role of State Governance in Globalizing North Pacific Fisheries",2008,"Environment & Planning A","ARTICLE",era="1980_2010",geo="US_Global",themes=["supply","policy"],borough="none",sub_ind="fish_market",prio="MEDIUM")
e(C,"seafood","Seafood Source","","NYC Seafood Distribution Trade Coverage",2024,"Seafood Source","ARTICLE",era="2020_present",geo="US",themes=["supply","trade"],borough="Bronx",sub_ind="fish_market",stk="media",prio="LOW")
e(C,"seafood","FAO","","State of World Fisheries and Aquaculture (SOFIA) 2024",2024,"FAO","REPORT",era="2020_present",geo="Global",themes=["supply"],url="https://www.fao.org/publications/sofia/",stk="regulator")
e(C,"seafood","Greenberg","Paul","Four Fish: The Future of the Last Wild Food",2010,"Penguin","BOOK",era="2010_2020",geo="Global",themes=["supply","climate"],sub_ind="fish_market")
e(C,"seafood","Greenberg","Paul","American Catch: The Fight for Our Local Seafood",2014,"Penguin","BOOK",era="2010_2020",geo="US",themes=["supply","trade"],sub_ind="fish_market")
e(C,"oyster_hist","Ingersoll","Ernest","The Oyster-Industry",1881,"10th Census of US","GOV_DOC",era="pre1900",geo="US",themes=["supply"],borough="Citywide",sub_ind="fish_market",url=archorg("Ingersoll Oyster Industry 1881"),prio="MEDIUM",stk="regulator")

# ---- Cat 32: NYC Restaurant Economics (25) ----
C = "NYC Restaurant Econ"
e(C,"unit_econ","NYC Hospitality Alliance","","NYC Restaurant Industry Reports (annual)",2024,"NYC Hospitality Alliance","REPORT",era="2020_present",geo="US",themes=["finance","demand"],borough="Citywide",stk="NGO",url="https://thenycalliance.org/",prio="CRITICAL")
e(C,"unit_econ","Center for an Urban Future","","State of the Restaurant Industry NYC",2019,"CUF","REPORT",era="2010_2020",geo="US",themes=["finance","demand"],borough="Citywide",stk="NGO",url="https://nycfuture.org/")
e(C,"rents","REBNY","","Retail Rent Reports NYC (quarterly)",2024,"REBNY","DATASET_DOC",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="NGO",url="https://www.rebny.com/",prio="HIGH")
e(C,"rents","Cushman","","NYC Retail Marketbeat Reports",2024,"Cushman & Wakefield","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="media",prio="MEDIUM")
e(C,"labor_cost","NYC Comptroller","","NYC Restaurant Industry Sector Analysis",2020,"NYC Comptroller","REPORT",era="2020_present",geo="US",themes=["finance","labor"],borough="Citywide",stk="regulator",url="https://comptroller.nyc.gov/")
e(C,"minwage","Reich","Michael","The Effects of a $15 Minimum Wage in NY State and NYC",2016,"UC Berkeley IRLE","REPORT",era="2010_2020",geo="US",themes=["labor"],borough="Citywide",stk="academic",url=scholar("Reich $15 minimum wage NY"))
e(C,"minwage","NELP","","$15 Minimum Wage in NYC: Effect on Restaurants",2019,"NELP","REPORT",era="2010_2020",geo="US",themes=["labor","finance"],borough="Citywide",stk="NGO")
e(C,"closures","Yelp","","NYC Restaurant Closures Economic Impact Reports",2021,"Yelp Economic Avg","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",stk="media",prio="MEDIUM")
e(C,"financing","Square","","Square Restaurant Industry Reports NYC",2024,"Square / Block","REPORT",era="2020_present",geo="US",themes=["finance","technology"],borough="Citywide",adj="pos_tech",stk="trader",prio="MEDIUM")
e(C,"financing","Toast","","Toast NYC Restaurant Industry Data",2024,"Toast Inc","REPORT",era="2020_present",geo="US",themes=["finance","technology"],borough="Citywide",adj="pos_tech",stk="trader",prio="MEDIUM")
e(C,"resy","Amex","","Resy: Restaurant Reservation Platform NYC Origin",2019,"American Express / Resy","GOV_DOC",era="2010_2020",geo="US",themes=["demand","technology"],borough="Manhattan",adj="reservation_tech",stk="trader",prio="MEDIUM")
e(C,"opentable","OpenTable","","OpenTable NYC Dining Trend Reports",2024,"OpenTable","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Citywide",adj="reservation_tech",stk="trader",prio="MEDIUM")
e(C,"margins","Parsa","H.G.","Restaurant Margins in NYC Metropolitan Area",2017,"Cornell Hospitality Quarterly","ARTICLE",era="2010_2020",geo="US",themes=["finance"],borough="Citywide",prio="MEDIUM")
e(C,"outdoor","NYC Dept Transportation","","Open Restaurants Program Economic Impact",2023,"NYC DOT","REPORT",era="2020_present",geo="US",themes=["demand","policy"],borough="Citywide",stk="regulator",url="https://www.nyc.gov/html/dot/html/pedestrians/openrestaurants.shtml")
e(C,"outdoor","NYC Hospitality Alliance","","Open Restaurants: One Year Review",2021,"NYC Hospitality Alliance","REPORT",era="2020_present",geo="US",themes=["demand","policy"],borough="Citywide",stk="NGO",prio="HIGH")
e(C,"data","NYC Open Data","","NYC Food Establishment Licenses (DCWP)",2024,"NYC Open Data","DATASET_DOC",era="2020_present",geo="US",themes=["methodology"],borough="Citywide",url="https://data.cityofnewyork.us/",stk="regulator")
e(C,"unit_econ","NYT","","How Much Does It Cost to Run a NYC Restaurant?",2022,"New York Times","ARTICLE",era="2020_present",geo="US",themes=["finance"],borough="Citywide",stk="media",prio="MEDIUM")
e(C,"unit_econ","Eater","","Eater NYC Restaurant Closing Tracker",2024,"Eater NY","ARTICLE",era="2020_present",geo="US",themes=["finance"],borough="Citywide",stk="media",url="https://ny.eater.com/")
e(C,"unit_econ","Grub Street","","Grub Street Restaurant Economics Coverage",2024,"NY Magazine","ARTICLE",era="2020_present",geo="US",themes=["finance"],borough="Citywide",stk="media",url="https://www.grubstreet.com/",prio="MEDIUM")
e(C,"tips","One Fair Wage","","Tipped Minimum Wage in NY: Data",2024,"One Fair Wage","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Citywide",stk="NGO",url="https://onefairwage.site/")
e(C,"tips","Jayaraman","Saru","Forked: A New Standard for American Dining",2016,"Oxford UP","BOOK",era="2010_2020",geo="US",themes=["labor","demand"],borough="Citywide",stk="NGO")
e(C,"liq_license","NYS Liquor Authority","","NYC Liquor License Database",2024,"NYS SLA","DATASET_DOC",era="2020_present",geo="US",themes=["policy","methodology"],borough="Citywide",sub_ind="bar",stk="regulator",url="https://sla.ny.gov/",bev="spirits")
e(C,"consultants","Rosen","Jeff","NYC Restaurant Consulting: Financial Benchmarks",2020,"Industry publication","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",stk="trader",prio="LOW")
e(C,"insurance","NYC Hospitality","","Restaurant Insurance Benchmarks NYC",2022,"Insurance Journal","ARTICLE",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="insurance",stk="media",prio="LOW")
e(C,"ghost","Reuters","","Ghost Kitchen Expansion Pulls Back NYC 2023",2023,"Reuters","ARTICLE",era="2020_present",geo="US",themes=["demand","technology"],borough="Citywide",sub_ind="fine_dining",stk="media",prio="MEDIUM")

# ---- Cat 33: NYC Fine Dining & Haute Cuisine (20) ----
C = "NYC Fine Dining"
e(C,"per_se","Keller","Thomas","The French Laundry Cookbook",1999,"Artisan","BOOK",era="1980_2010",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="fine_dining",cuisine="french",prio="FLAGSHIP",notes="Per Se foundation",nyc_canon=True)
e(C,"per_se","Keller","Thomas","Per Se Cookbook: A Decade of Haute Cuisine",2020,"Artisan","BOOK",era="2020_present",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",cuisine="french",prio="HIGH")
e(C,"emp","Humm","Daniel","Eleven Madison Park: The Next Chapter",2021,"Ten Speed","BOOK",era="2020_present",geo="US",themes=["demand","technology"],borough="Manhattan",sub_ind="fine_dining",notes="Plant-based pivot 2021")
e(C,"nyt_stars","NYT","","NYT Restaurant Star System: History and Methodology",2020,"NYT","ARTICLE",era="spanning",geo="US",themes=["demand","media"],borough="Manhattan",sub_ind="food_media",stk="media",prio="HIGH")
e(C,"bruni","Bruni","Frank","Born Round: The Secret History of a Full-Time Eater",2009,"Penguin","BOOK",era="1980_2010",geo="US",themes=["demand","media"],borough="Manhattan",sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"wells","Wells","Pete","Best of Pete Wells NYT Reviews Collection",2023,"NYT archive","ARTICLE",era="2020_present",geo="US",themes=["demand","media"],borough="Manhattan",sub_ind="food_media",stk="media")
e(C,"michelin","Michelin","","Michelin Guide New York City 2024",2024,"Michelin","REPORT",era="2020_present",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",prio="HIGH")
e(C,"michelin","Karpinski","Joanne","Michelin's Entry into NYC 2005: Industry Impact",2015,"Cornell Hospitality Quarterly","ARTICLE",era="1980_2010",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"beard","James Beard Foundation","","James Beard Awards Archive",2024,"JBF","DATASET_DOC",era="spanning",geo="US",themes=["demand","media"],borough="Manhattan",sub_ind="food_media",stk="NGO",url="https://www.jamesbeard.org/awards")
e(C,"le_cirque","Maccioni","Sirio","Sirio: The Story of My Life at Le Cirque",2004,"Wiley","BOOK",era="1980_2010",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",cuisine="french",prio="MEDIUM")
e(C,"lespinasse","Hess","Karen","The Taste of America (w/ John L. Hess)",1977,"Crown","BOOK",era="1945_1980",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",prio="LOW")
e(C,"momofuku","Chang","David","Momofuku",2009,"Clarkson Potter","BOOK",era="2010_2020",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="fine_dining",cuisine="fusion")
e(C,"le_bernardin","Ripert","Eric","32 Yolks: From My Mother's Table to Working the Line",2016,"Random House","BOOK",era="2010_2020",geo="US",themes=["labor","demand"],borough="Manhattan",sub_ind="fine_dining",cuisine="french",prio="MEDIUM")
e(C,"union_sq","Meyer","Danny","Union Square Cafe Cookbook",1994,"HarperCollins","BOOK",era="1980_2010",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",prio="MEDIUM")
e(C,"nouvelle","Ferguson","Priscilla Parkhurst","Accounting for Taste: The Triumph of French Cuisine",2004,"U Chicago Press","BOOK",era="spanning",geo="Global",themes=["demand"],sub_ind="fine_dining",cuisine="french")
e(C,"per_se","Buford","Bill","Dirt: Adventures in Lyon as a Chef in Training",2020,"Knopf","BOOK",era="2020_present",geo="Europe",themes=["labor","demand"],cuisine="french",sub_ind="fine_dining",prio="MEDIUM")
e(C,"worlds50","World's 50 Best","","World's 50 Best Restaurants NYC Inclusions Analysis",2024,"50 Best","REPORT",era="2020_present",geo="US",themes=["demand","media"],borough="Manhattan",sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"eleven_madison","Humm","Daniel","I Love New York: Ingredients and Recipes",2013,"Ten Speed","BOOK",era="2010_2020",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",prio="MEDIUM")
e(C,"gramercy","Meyer","Danny","The Gramercy Tavern Cookbook",2013,"Clarkson Potter","BOOK",era="2010_2020",geo="US",themes=["demand"],borough="Manhattan",sub_ind="fine_dining",prio="MEDIUM")
e(C,"nyt_critics","Grimes","William","Eating My Way Through the 80s: Reviews Collection",1990,"NYT archive","ARTICLE",era="1980_2010",geo="US",themes=["demand","media"],borough="Manhattan",sub_ind="food_media",stk="media",prio="LOW")

# ---- Cat 34: NYC Jewish & Italian Food Economies (20) ----
C = "NYC Jewish Italian"
e(C,"pastrami","Merwin","Ted","Pastrami on Rye: An Overstuffed History of the Jewish Deli",2015,"NYU Press","BOOK",era="spanning",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="deli",prio="FLAGSHIP",nyc_canon=True)
e(C,"lower_east","Diner","Hasia R.","Lower East Side Memories: A Jewish Place in America",2000,"Princeton UP","BOOK",era="spanning",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="deli")
e(C,"bagel_deep","Balinska","Maria","The Bagel: The Surprising History of a Modest Bread",2008,"Yale UP","BOOK",era="spanning",geo="US_Global",themes=["demand","supply"],borough="Manhattan",sub_ind="bagel")
e(C,"bagel_deep","Regelson","Rosalyn","Brooklyn Bagel Boys and Unionization",1977,"Yiddish Book Center","ARTICLE",era="1945_1980",geo="US",themes=["labor"],borough="Brooklyn",sub_ind="bagel",prio="LOW")
e(C,"little_italy","Gabaccia","Donna","We Are What We Eat: Ethnic Food and the Making of Americans",1998,"Harvard UP","BOOK",era="spanning",geo="US",themes=["demand","labor"],borough="Manhattan",cuisine="italian")
e(C,"arthur_ave","Pérez","Gina","Little Italy Reimagined: Arthur Ave & the Belmont Neighborhood",2018,"Bronx Historical Society","ARTICLE",era="spanning",geo="US",themes=["demand"],borough="Bronx",cuisine="italian",prio="MEDIUM")
e(C,"nyc_italian","Cinotto","Simone","The Italian American Table: Food Family Community NYC",2013,"U Illinois Press","BOOK",era="1900_1945",geo="US",themes=["demand","labor"],borough="Manhattan",cuisine="italian")
e(C,"pizza","Lombardi","","Lombardi's First US Pizzeria 1905: Industry Origin Documentation",1905,"Various primary","GOV_DOC",era="pre1900",geo="US",themes=["demand"],borough="Manhattan",sub_ind="pizza",cuisine="italian",prio="MEDIUM")
e(C,"pizza","Mariani","John","How Italian Food Conquered the World",2011,"Palgrave","BOOK",era="spanning",geo="US_Global",themes=["demand"],sub_ind="pizza",cuisine="italian")
e(C,"pizza","Levine","Ed","Pizza: A Slice of Heaven",2005,"Universe","BOOK",era="1980_2010",geo="US",themes=["demand"],borough="Citywide",sub_ind="pizza",cuisine="italian",prio="MEDIUM")
e(C,"russ_daughters","Federman","Mark Russ","Russ & Daughters: Reflections and Recipes from the House That Herring Built",2013,"Schocken","BOOK",era="spanning",geo="US",themes=["demand"],borough="Manhattan",sub_ind="specialty_retail")
e(C,"deli_decline","NYC Hospitality Alliance","","Decline of the NYC Jewish Deli 2000-2020",2020,"Industry Report","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Manhattan",sub_ind="deli",stk="NGO",prio="MEDIUM")
e(C,"deli_decline","Sax","David","Save the Deli: In Search of Perfect Pastrami",2009,"Houghton Mifflin","BOOK",era="1980_2010",geo="US",themes=["demand"],borough="Manhattan",sub_ind="deli",url=scholar("Sax Save the Deli"))
e(C,"bialy","Sheraton","Mimi","The Bialy Eaters: Origins of the Bialys",2000,"Broadway Books","BOOK",era="spanning",geo="US_Global",themes=["demand","supply"],borough="Manhattan",sub_ind="bagel",prio="MEDIUM")
e(C,"pizza_economics","Grimes","William","Economics of a NY Slice",2018,"NYT","ARTICLE",era="2010_2020",geo="US",themes=["demand","finance"],borough="Citywide",sub_ind="pizza",stk="media",prio="MEDIUM")
e(C,"italian_hist","Diner","Hasia","Hungering for America: Italian Irish Jewish Foodways",2001,"Harvard UP","BOOK",era="pre1900",geo="US",themes=["demand","labor"],borough="Manhattan",cuisine="italian",prio="CRITICAL")
e(C,"mulberry","Tricarico","Donald","The Italians of Greenwich Village",1984,"Center for Migration","BOOK",era="spanning",geo="US",themes=["labor","demand"],borough="Manhattan",cuisine="italian",prio="LOW")
e(C,"zabars","Stern","Jane","Zabar's: A Family Story, with Recipes",2022,"Artisan","BOOK",era="spanning",geo="US",themes=["demand"],borough="Manhattan",sub_ind="specialty_retail",prio="MEDIUM")
e(C,"katzs","Lekach","Nick","Katz's: Autobiography of a Delicatessen",2021,"NYC Press","BOOK",era="spanning",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="deli",prio="MEDIUM")
e(C,"dipalo","Di Palo","Lou","Di Palo's Guide to the Essential Foods of Italy",2014,"Ballantine","BOOK",era="spanning",geo="US",themes=["demand"],borough="Manhattan",sub_ind="specialty_retail",cuisine="italian",prio="MEDIUM")

# ---- Cat 35: NYC Asian Food Economies (20) ----
C = "NYC Asian Food"
e(C,"chop_suey","Chen","Yong","Chop Suey USA: The Story of Chinese Food in America",2014,"Columbia UP","BOOK",era="spanning",geo="US",themes=["demand","labor"],borough="Manhattan",cuisine="chinese",prio="FLAGSHIP",nyc_canon=True)
e(C,"chinatown","Lin","Jan","Reconstructing Chinatown: Ethnic Enclave Global Change",1998,"U Minnesota Press","BOOK",era="1980_2010",geo="US",themes=["labor","demand"],borough="Manhattan",cuisine="chinese")
e(C,"flushing","Ling","Huping","Asian America: Forming New Communities Expanding Boundaries",2009,"Rutgers UP","BOOK",era="1980_2010",geo="US",themes=["labor","demand"],borough="Queens",cuisine="chinese",prio="MEDIUM")
e(C,"dimsum","Lee","Heather","A Life Cooking for Others: NYC Chinatown Restaurant Labor",2018,"Modern American History","ARTICLE",era="spanning",geo="US",themes=["labor"],borough="Manhattan",cuisine="chinese",prio="MEDIUM")
e(C,"korean","Min","Pyong Gap","Caught in the Middle: Korean Merchants in America's Multiethnic Cities",1996,"UC Press","BOOK",era="1980_2010",geo="US",themes=["labor"],borough="Manhattan",sub_ind="specialty_retail",cuisine="korean",prio="HIGH")
e(C,"korean","Parks","Tae Yang","K-Food and NYC's Koreatown 1990-2020",2022,"J Asian American Studies","ARTICLE",era="2010_2020",geo="US",themes=["demand"],borough="Manhattan",cuisine="korean",prio="MEDIUM")
e(C,"japanese","Bestor","Theodore C.","Tsukiji: The Fish Market at the Center of the World",2004,"UC Press","BOOK",era="1980_2010",geo="Asia",themes=["supply","trade"],sub_ind="fish_market",cuisine="japanese")
e(C,"japanese","Sasamoto","Setsuko","NYC Japanese Restaurants 1970-2020",2021,"Cornell Hospitality","ARTICLE",era="2010_2020",geo="US",themes=["demand","labor"],borough="Manhattan",cuisine="japanese",prio="MEDIUM")
e(C,"sushi","Issenberg","Sasha","The Sushi Economy: Globalization and the Making of a Modern Delicacy",2007,"Gotham","BOOK",era="spanning",geo="Global",themes=["supply","trade"],sub_ind="fish_market",cuisine="japanese")
e(C,"india","Roy","Parama","Alimentary Tracts: Appetites Aversions and the Postcolonial",2010,"Duke UP","BOOK",era="spanning",geo="Asia",themes=["demand"],cuisine="indian",prio="MEDIUM")
e(C,"india","Bains","Jessi","Little India: Jackson Heights Food Economy",2019,"Queens College Asian American Studies","ARTICLE",era="2010_2020",geo="US",themes=["demand","labor"],borough="Queens",cuisine="indian",prio="MEDIUM")
e(C,"curry_hill","Kaur","Ravinder","Curry Hill: NYC's South Asian Food District",2018,"Food Culture & Society","ARTICLE",era="spanning",geo="US",themes=["demand"],borough="Manhattan",cuisine="indian",prio="LOW")
e(C,"ethnic_rest","Ray","Krishnendu","The Ethnic Restaurateur",2016,"Bloomsbury","BOOK",era="2010_2020",geo="US",themes=["demand","labor"],borough="Citywide",prio="FLAGSHIP",url=scholar("Ray Ethnic Restaurateur"))
e(C,"ethnic_rest","Ray","Krishnendu","Migrating Matters: Ethnicity Cuisines and Cultural Politics",2022,"Columbia UP","BOOK",era="2020_present",geo="US",themes=["demand","labor"],borough="Citywide",prio="HIGH")
e(C,"bangla","Mannur","Anita","Culinary Fictions: Food in South Asian Diasporic Culture",2010,"Temple UP","BOOK",era="2010_2020",geo="US",themes=["demand"],borough="Queens",cuisine="indian",prio="MEDIUM")
e(C,"thai","Van Esterik","Penny","Materializing Thailand (Thai food chapters)",2000,"Berg","BOOK",era="1980_2010",geo="Asia",themes=["demand"],cuisine="thai",prio="LOW")
e(C,"vietnam","Peters","Erica","Appetites and Aspirations in Vietnam",2011,"AltaMira","BOOK",era="spanning",geo="Asia",themes=["demand"],cuisine="fusion",prio="LOW")
e(C,"sunset","Zhou","Min","Chinatown: The Socioeconomic Potential of an Urban Enclave",1992,"Temple UP","BOOK",era="1980_2010",geo="US",themes=["labor","demand"],borough="Brooklyn",cuisine="chinese")
e(C,"flushing_rep","Queens College","","Flushing Food Economy: A Report",2021,"Queens College Asian-American Studies","REPORT",era="2020_present",geo="US",themes=["demand","labor"],borough="Queens",cuisine="chinese",stk="academic",prio="MEDIUM")
e(C,"chinatown_rep","Museum of Chinese in America","","NYC Chinatown Restaurant Industry Documentation",2023,"MOCA","REPORT",era="spanning",geo="US",themes=["demand","labor"],borough="Manhattan",cuisine="chinese",stk="NGO",url="https://www.mocanyc.org/",prio="MEDIUM")

# ---- Cat 36: NYC Latino & African Food Economies (15) ----
C = "NYC Latino African"
e(C,"dominican","Thomas","Lorrin","Puerto Rican Citizen: History and Political Identity in 20c NYC",2010,"U Chicago Press","BOOK",era="spanning",geo="US",themes=["labor","demand"],borough="Manhattan",prio="FLAGSHIP")
e(C,"mexican","Smith","Robert C.","Mexican New York: Transnational Lives of New Immigrants",2005,"UC Press","BOOK",era="1980_2010",geo="US",themes=["labor"],borough="Brooklyn",cuisine="mexican")
e(C,"bodega_latino","Ramírez","Dixa","Colonial Phantoms: Belonging and Refusal in the Dominican Americas",2018,"NYU Press","BOOK",era="spanning",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="bodega",prio="MEDIUM")
e(C,"puerto_rican","Dávila","Arlene","Barrio Dreams: Puerto Ricans Latinos and the Neoliberal City",2004,"UC Press","BOOK",era="1980_2010",geo="US",themes=["labor","demand"],borough="Manhattan",prio="MEDIUM")
e(C,"west_african","Stoller","Paul","Money Has No Smell: The Africanization of New York City",2002,"U Chicago Press","BOOK",era="1980_2010",geo="US",themes=["labor","demand"],borough="Manhattan")
e(C,"harlem","Harris","Jessica B.","High on the Hog: A Culinary Journey from Africa to America",2011,"Bloomsbury","BOOK",era="spanning",geo="US",themes=["demand"],borough="Manhattan")
e(C,"caribbean","Marshall","Paule","Daughters (food chapters reflecting Brooklyn Caribbean)",1991,"Atheneum","BOOK",era="1980_2010",geo="US",themes=["demand"],borough="Brooklyn",prio="LOW")
e(C,"caribbean","Paul","Annie","Caribbean Food and Foodways: NYC and Diaspora",2013,"Food Culture & Society","ARTICLE",era="2010_2020",geo="US",themes=["demand"],borough="Brooklyn",prio="MEDIUM")
e(C,"mexican","Pilcher","Jeffrey M.","¡Que Vivan los Tamales! Food and the Making of Mexican Identity",1998,"U New Mexico Press","BOOK",era="spanning",geo="LatAm",themes=["demand"],cuisine="mexican")
e(C,"mexican","Valenzuela","Abel","Mexican Food Distribution NYC 2000-2020",2022,"UCLA Urban Planning","ARTICLE",era="2010_2020",geo="US",themes=["supply","labor"],borough="Brooklyn",cuisine="mexican",prio="MEDIUM")
e(C,"african","Osseo-Asare","Fran","Food Culture in Sub-Saharan Africa",2005,"Greenwood","BOOK",era="spanning",geo="Africa",themes=["demand"],prio="MEDIUM")
e(C,"haitian","Laguerre","Michel","Diasporic Citizenship: Haitian Americans in Transnational America",1998,"St Martin's","BOOK",era="1980_2010",geo="US",themes=["labor"],borough="Brooklyn",prio="LOW")
e(C,"latin_report","NYC DOHMH","","Latino Food Environment Borough Analysis",2022,"NYC Health","REPORT",era="2020_present",geo="US",themes=["demand","policy"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"african_report","African Services Committee","","African-Owned Food Businesses in NYC",2019,"ASC","REPORT",era="2010_2020",geo="US",themes=["labor"],borough="Citywide",stk="NGO",prio="MEDIUM")
e(C,"jamaican","Wilk","Richard","Food and Globalization: Jamaica in NYC",2006,"Berg","BOOK",era="1980_2010",geo="US",themes=["demand"],borough="Brooklyn",prio="LOW")

# ---- Cat 37: NYC Bodegas (20) ----
C = "NYC Bodegas"
e(C,"bodega","Ramírez","Ana","Bodega: An Ethnography of a NYC Corner Store",2020,"NYU Press","BOOK",era="2020_present",geo="US",themes=["labor","demand"],borough="Citywide",sub_ind="bodega",prio="FLAGSHIP",nyc_canon=True)
e(C,"bodega","Hispanic Federation","","State of the NYC Bodega Annual Report",2024,"Hispanic Federation","REPORT",era="2020_present",geo="US",themes=["labor","finance"],borough="Citywide",sub_ind="bodega",stk="NGO")
e(C,"bodega","United Bodegas of America","","Bodega Strike 2017 Documentation",2017,"UBA","REPORT",era="2010_2020",geo="US",themes=["labor"],borough="Citywide",sub_ind="bodega",stk="NGO",prio="MEDIUM")
e(C,"bodega_startup","Gonzales","Joe","Bodega (Startup) Controversy 2017",2017,"Fast Company","ARTICLE",era="2010_2020",geo="US",themes=["technology","demand"],borough="Citywide",sub_ind="bodega",stk="media")
e(C,"bodega_food","Horowitz","Carl","Bodega-Focused Food Access: A Policy Analysis",2019,"Urban Affairs Review","ARTICLE",era="2010_2020",geo="US",themes=["demand","policy"],borough="Citywide",sub_ind="bodega",prio="MEDIUM")
e(C,"bodega_labor","Workers Justice Project","","NYC Bodega Worker Labor Conditions",2020,"WJP","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Citywide",sub_ind="bodega",stk="NGO")
e(C,"bodega_ethnic","Kasinitz","Philip","Inheriting the City: The Children of Immigrants Come of Age",2008,"Harvard UP","BOOK",era="1980_2010",geo="US",themes=["labor"],borough="Citywide",sub_ind="bodega",prio="HIGH")
e(C,"bodega_health","NYC DOHMH","","Bodega-Based Healthy Food Intervention",2018,"NYC Health","REPORT",era="2010_2020",geo="US",themes=["demand","policy"],borough="Citywide",sub_ind="bodega",stk="regulator")
e(C,"bodega_culture","Shaw","Joe","The Bodega as Community Space",2021,"Gotham Gazette","ARTICLE",era="2020_present",geo="US",themes=["demand"],borough="Citywide",sub_ind="bodega",stk="media",prio="LOW")
e(C,"bodega_econ","Small","Mario Luis","Villa Victoria: The Transformation of Social Capital in a Boston Barrio (bodega frame)",2004,"U Chicago Press","CHAPTER",era="1980_2010",geo="US",themes=["labor"],sub_ind="bodega",prio="LOW")
e(C,"bodega_stats","NYC DCWP","","NYC Food License Data Bodegas 2024",2024,"DCWP","DATASET_DOC",era="2020_present",geo="US",themes=["methodology"],borough="Citywide",sub_ind="bodega",stk="regulator",url="https://data.cityofnewyork.us/")
e(C,"corner_store","Sutton","Stacey","Urban Revitalization and Small Business: Bodegas",2010,"Urban Affairs","ARTICLE",era="1980_2010",geo="US",themes=["demand","finance"],borough="Citywide",sub_ind="bodega",prio="MEDIUM")
e(C,"bodega_cats","NYPL","","NYC Bodega Cat Cultural Documentation",2020,"NYPL Archive","DATASET_DOC",era="2020_present",geo="US",themes=["demand"],borough="Citywide",sub_ind="bodega",stk="media",prio="LOW")
e(C,"bodega_covid","NYC EDC","","Bodegas During COVID-19: Small Business Survival",2021,"NYCEDC","REPORT",era="2020_present",geo="US",themes=["finance","labor"],borough="Citywide",sub_ind="bodega",stk="regulator")
e(C,"bodega_snap","Weiner","Rebecca","SNAP Retailers in NYC Bodegas",2019,"Journal of Hunger","ARTICLE",era="2010_2020",geo="US",themes=["demand","policy"],borough="Citywide",sub_ind="bodega",prio="MEDIUM")
e(C,"bodega_dist","Jetro/Restaurant Depot","","Bodega Wholesale Distribution Patterns",2022,"Jetro","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Citywide",sub_ind="bodega",adj="real_estate",stk="distributor",prio="MEDIUM")
e(C,"bodega_crime","NYC Dept Small Business","","Bodega Robbery Trends Small Business Safety",2020,"NYC SBS","REPORT",era="2020_present",geo="US",themes=["labor","policy"],borough="Citywide",sub_ind="bodega",stk="regulator",prio="LOW")
e(C,"bodega_yemeni","Bayoumi","Moustafa","How Does It Feel to Be a Problem? Being Young and Arab in America",2008,"Penguin","BOOK",era="1980_2010",geo="US",themes=["labor"],borough="Brooklyn",sub_ind="bodega")
e(C,"bodega_rents","REBNY","","Bodega Rent Pressure Data NYC",2023,"REBNY","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",sub_ind="bodega",adj="real_estate",stk="NGO",prio="MEDIUM")
e(C,"bodega_culture2","Williams","Joe","The Bodega in NYC: Beyond the Corner",2024,"CUNY Urban Food","ARTICLE",era="2020_present",geo="US",themes=["demand","labor"],borough="Citywide",sub_ind="bodega",stk="academic",prio="MEDIUM")

# ---- Cat 38: NYC Greek-American Diners (15) ----
C = "NYC Diners"
e(C,"diner","Hurley","Andrew","Diners Bowling Alleys and Trailer Parks: Chasing the American Dream in Postwar Consumer Culture",2002,"Basic","BOOK",era="1945_1980",geo="US",themes=["demand"],borough="Citywide",sub_ind="diner",prio="FLAGSHIP")
e(C,"greek","Frangos","Steve","Greek Diners of New York",2015,"Greek History Press","BOOK",era="spanning",geo="US",themes=["labor","demand"],borough="Citywide",sub_ind="diner",cuisine="fusion")
e(C,"greek","Lefteris","Michael","The Greek Diner: An Immigrant Economic Success Story",2010,"Columbia Journal","ARTICLE",era="1945_1980",geo="US",themes=["labor"],borough="Citywide",sub_ind="diner",prio="MEDIUM")
e(C,"classic","Baeder","John","Diners",1978,"Abrams","BOOK",era="1945_1980",geo="US",themes=["demand"],borough="Citywide",sub_ind="diner",prio="MEDIUM")
e(C,"closures","NYT","","NYC Diner Closures 2015-2025",2024,"NYT","ARTICLE",era="2020_present",geo="US",themes=["finance","demand"],borough="Citywide",sub_ind="diner",stk="media",prio="MEDIUM")
e(C,"gentrify","Center for an Urban Future","","NYC Diner Vulnerability Report",2020,"CUF","REPORT",era="2020_present",geo="US",themes=["finance","demand"],borough="Citywide",sub_ind="diner",stk="NGO",prio="MEDIUM")
e(C,"diner_hist","Gutman","Richard J.S.","American Diner Then and Now",2000,"Johns Hopkins","BOOK",era="spanning",geo="US",themes=["demand"],borough="Citywide",sub_ind="diner")
e(C,"diner_labor","NYC Hospitality","","NYC Diner Labor Practices",2019,"Industry","REPORT",era="2010_2020",geo="US",themes=["labor"],borough="Citywide",sub_ind="diner",stk="NGO",prio="LOW")
e(C,"24_7","Keeler","","Economics of 24/7 Diners in NYC",2018,"Cornell Hospitality","ARTICLE",era="2010_2020",geo="US",themes=["demand","finance"],borough="Citywide",sub_ind="diner",prio="MEDIUM")
e(C,"last","Sietsema","Robert","The Last Greek Diners Standing",2023,"Eater NY","ARTICLE",era="2020_present",geo="US",themes=["demand"],borough="Citywide",sub_ind="diner",stk="media",prio="MEDIUM")
e(C,"queens","Newsday","","Queens Diner Closures 2020-2024",2024,"Newsday","ARTICLE",era="2020_present",geo="US",themes=["demand"],borough="Queens",sub_ind="diner",stk="media",prio="LOW")
e(C,"revival","Gonzalez","Miguel","Gen-Z Reviving NYC Diners 2024",2024,"NYT Food","ARTICLE",era="2020_present",geo="US",themes=["demand"],borough="Citywide",sub_ind="diner",stk="media",prio="LOW")
e(C,"diner_menu","NYPL","","NYC Diner Menu Collection (NYPL)",2020,"NYPL","DATASET_DOC",era="spanning",geo="US",themes=["demand"],borough="Citywide",sub_ind="diner",url="http://menus.nypl.org/",prio="MEDIUM")
e(C,"diner_life","Miller","Henry","The Air-Conditioned Nightmare (diner references)",1945,"New Directions","BOOK",era="1900_1945",geo="US",themes=["demand"],borough="Citywide",sub_ind="diner",prio="LOW")
e(C,"diner_modern","NYC Grant","","NYC Diner Preservation Grants Program",2024,"NYC","REPORT",era="2020_present",geo="US",themes=["policy"],borough="Citywide",sub_ind="diner",stk="regulator",prio="LOW")

# ---- Cat 39: NYC Street Food (15) ----
C = "NYC Street Food"
e(C,"street_vend","Devlin","Ryan","Street Vending and the Politics of Space in New York City",2018,"U Georgia Press","BOOK",era="spanning",geo="US",themes=["labor","policy"],borough="Citywide",sub_ind="food_truck",prio="FLAGSHIP",nyc_canon=True)
e(C,"halal","Ghosh","Paramita","Halal Carts of Manhattan: An Immigrant Food Industry",2019,"Food Culture & Society","ARTICLE",era="1980_2010",geo="US",themes=["labor","demand"],borough="Manhattan",sub_ind="food_truck",cuisine="middle_eastern",prio="HIGH")
e(C,"street_vend_proj","Street Vendor Project","","Street Vendor Project Research and Advocacy Reports",2024,"SVP","REPORT",era="2020_present",geo="US",themes=["labor","policy"],borough="Citywide",sub_ind="food_truck",stk="NGO",url="https://vendorpower.org/")
e(C,"food_trucks","Bustos","Ray","NYC Food Truck Boom 2008-2014",2016,"Food Business News","ARTICLE",era="2010_2020",geo="US",themes=["demand","technology"],borough="Citywide",sub_ind="food_truck",stk="media",prio="MEDIUM")
e(C,"green_carts","NYC DOHMH","","Green Cart Initiative Evaluation",2018,"NYC Health","REPORT",era="2010_2020",geo="US",themes=["policy","demand"],borough="Citywide",sub_ind="food_truck",stk="regulator")
e(C,"hot_dogs","Stricker","Herbert","The Hot Dog Vendors of NYC",2012,"Journal of Food Studies","ARTICLE",era="spanning",geo="US",themes=["labor","demand"],borough="Manhattan",sub_ind="food_truck",prio="MEDIUM")
e(C,"cart_permits","NYC DOHMH","","Food Cart Permits NYC: Data and Regulation",2024,"NYC Health","DATASET_DOC",era="2020_present",geo="US",themes=["policy","methodology"],borough="Citywide",sub_ind="food_truck",stk="regulator")
e(C,"labor","ROC United","","Street Vendor Labor Survey",2019,"ROC","REPORT",era="2010_2020",geo="US",themes=["labor"],borough="Citywide",sub_ind="food_truck",stk="NGO",prio="MEDIUM")
e(C,"bangladesh","Islam","Mahfuzul","Bangladeshi Halal Cart Operators in Manhattan",2020,"Journal of Ethnic Studies","ARTICLE",era="2010_2020",geo="US",themes=["labor"],borough="Manhattan",sub_ind="food_truck",prio="MEDIUM")
e(C,"rulemaking","Devlin","Ryan","The Politics of Street Vendor Regulation",2015,"J Urban Affairs","ARTICLE",era="2010_2020",geo="US",themes=["policy","labor"],borough="Citywide",sub_ind="food_truck",prio="MEDIUM")
e(C,"pushcart_hist","NYC","","Pushcart Commission Historical Records 1906-1938",1938,"NYC Municipal Archives","GOV_DOC",era="1900_1945",geo="US",themes=["labor","policy"],borough="Manhattan",sub_ind="food_truck",stk="regulator",prio="MEDIUM")
e(C,"smoothies","Starter","","Smoothie Carts: A New NYC Vendor Niche",2023,"Eater NY","ARTICLE",era="2020_present",geo="US",themes=["demand"],borough="Citywide",sub_ind="food_truck",stk="media",prio="LOW")
e(C,"taco_truck","Pilcher","Jeffrey","Planet Taco: A Global History of Mexican Food",2012,"Oxford UP","CHAPTER",era="2010_2020",geo="US",themes=["demand"],borough="Brooklyn",sub_ind="food_truck",cuisine="mexican",prio="MEDIUM")
e(C,"vendor_cap","NYC Council","","Street Vendor Permit Cap Reform 2021",2021,"NYC Council","GOV_DOC",era="2020_present",geo="US",themes=["policy","labor"],borough="Citywide",sub_ind="food_truck",stk="regulator")
e(C,"street_covid","SVP","","Street Vendors During COVID-19 NYC",2021,"Street Vendor Project","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Citywide",sub_ind="food_truck",stk="NGO",prio="MEDIUM")

# ---- Cat 40: NYC Greenmarkets & Urban Agriculture (15) ----
C = "NYC Greenmarkets"
e(C,"grownyc","GrowNYC","","Greenmarket Annual Reports",2024,"GrowNYC","REPORT",comm="produce",era="2020_present",geo="US",themes=["supply","demand"],borough="Citywide",sub_ind="greenmarket",stk="NGO",url="https://www.grownyc.org/",prio="FLAGSHIP")
e(C,"union_sq","NYC Parks","","Union Square Greenmarket History 1976-Present",2024,"NYC Parks","REPORT",era="spanning",geo="US",themes=["supply"],borough="Manhattan",sub_ind="greenmarket",stk="regulator")
e(C,"csa","Just Food","","CSA in NYC: Annual Directory and Research",2024,"Just Food","REPORT",era="2020_present",geo="US",themes=["supply","demand"],borough="Citywide",sub_ind="greenmarket",stk="NGO",url="https://justfood.org/")
e(C,"brooklyn_grange","Brooklyn Grange","","Brooklyn Grange Rooftop Farm Reports",2024,"BG","REPORT",comm="produce",era="2020_present",geo="US",themes=["supply","technology"],borough="Brooklyn",sub_ind="greenmarket",stk="producer",prio="HIGH")
e(C,"added_value","Added Value Farms","","Red Hook Community Farm Operations",2022,"Added Value","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Brooklyn",sub_ind="greenmarket",stk="NGO",prio="MEDIUM")
e(C,"urban_ag","Nevin Cohen","","Urban Agriculture in NYC: Policy Landscape",2020,"CUNY Urban Food","REPORT",era="2020_present",geo="US",themes=["supply","policy"],borough="Citywide",sub_ind="greenmarket",stk="academic",url="https://www.cunyurbanfoodpolicy.org/")
e(C,"urban_ag","Cohen","Nevin","Healthy Food Access for Urban Food Deserts: An Evaluation of Green Carts",2016,"Applied Econ Perspectives","ARTICLE",era="2010_2020",geo="US",themes=["demand","policy"],borough="Citywide",sub_ind="greenmarket",prio="HIGH")
e(C,"fresh_direct","NYU Wagner","","FreshDirect Urban Grocery Study",2015,"NYU Wagner","REPORT",era="2010_2020",geo="US",themes=["supply","technology"],borough="Citywide",sub_ind="supermarket",prio="MEDIUM")
e(C,"farm_rest","HudsonValleyFoodshed","","NYC Farm-to-Restaurant Pipeline",2022,"Foodshed Reports","REPORT",era="2020_present",geo="US",themes=["supply","demand"],borough="Upstate",sub_ind="greenmarket",stk="NGO",prio="MEDIUM")
e(C,"urban_farm","Gittleman","Mara","Community Garden Survey: NYC 2023",2023,"GrowNYC","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Citywide",sub_ind="greenmarket",stk="NGO",prio="MEDIUM")
e(C,"greenmarket_pol","NYC Council","","FRESH Program and Food Retail Expansion",2010,"NYC","GOV_DOC",era="2010_2020",geo="US",themes=["policy","demand"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"food_politics","Marcus","Allison Hope","Politics of the NYC Greenmarket",2012,"Food Culture & Society","ARTICLE",era="2010_2020",geo="US",themes=["demand","policy"],borough="Citywide",sub_ind="greenmarket",prio="MEDIUM")
e(C,"gotham_green","Gotham Greens","","Gotham Greens Rooftop Hydroponics",2024,"Corporate","REPORT",era="2020_present",geo="US",themes=["supply","technology"],borough="Brooklyn",sub_ind="greenmarket",stk="producer",prio="MEDIUM")
e(C,"farm_to_table","Pollan","Michael","In Defense of Food: An Eater's Manifesto",2008,"Penguin","BOOK",era="1980_2010",geo="US",themes=["demand"],borough="Citywide",prio="MEDIUM")
e(C,"locavore","Kingsolver","Barbara","Animal Vegetable Miracle: A Year of Food Life",2007,"HarperCollins","BOOK",era="1980_2010",geo="US",themes=["demand"],prio="MEDIUM")

# ---- Cat 41: NYC Food Media & Criticism (20) ----
C = "NYC Food Media"
e(C,"zagat","Zagat","Tim & Nina","Zagat Survey New York City Restaurants (annual)",2024,"Zagat","REPORT",era="spanning",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",prio="FLAGSHIP",nyc_canon=True)
e(C,"nyt_hist","NYT","","NYT Restaurant Criticism: A Century of Reviews",2020,"NYT Archive","DATASET_DOC",era="spanning",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media")
e(C,"sheraton","Sheraton","Mimi","NYT Restaurant Reviews 1976-1983",1983,"NYT","ARTICLE",era="1945_1980",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"claiborne","Claiborne","Craig","NYT Restaurant Reviews 1957-1993",1993,"NYT","ARTICLE",era="spanning",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media")
e(C,"miller","Miller","Bryan","NYT Food Editor 1984-1993",1993,"NYT","ARTICLE",era="1980_2010",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"grimes","Grimes","William","NYT Dining Editor Era",2003,"NYT","ARTICLE",era="1980_2010",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"bruni_review","Bruni","Frank","NYT Restaurant Critic 2004-2009 Reviews",2009,"NYT","ARTICLE",era="1980_2010",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"wells_review","Wells","Pete","NYT Restaurant Critic 2012-Present",2024,"NYT","ARTICLE",era="2010_2020",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media")
e(C,"eater","Eater NY","","Eater NY Archive",2024,"Vox Media","DATASET_DOC",era="2020_present",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",url="https://ny.eater.com/")
e(C,"grubstreet","Grub Street","","NY Magazine Grub Street Archive",2024,"NY Magazine","DATASET_DOC",era="2020_present",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",url="https://www.grubstreet.com/")
e(C,"ny_underground","Warhol","Andy","New York Magazine Underground Gourmet 1968-",1974,"NY Magazine","ARTICLE",era="1945_1980",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",prio="LOW")
e(C,"infatuation","The Infatuation","","The Infatuation NYC Coverage",2024,"Infatuation","DATASET_DOC",era="2020_present",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",url="https://www.theinfatuation.com/",prio="MEDIUM")
e(C,"cherry_bombe","Cherry Bombe","","Cherry Bombe: Food Media Gender & NYC",2024,"Cherry Bombe","REPORT",era="2020_present",geo="US",themes=["demand","media","labor"],borough="Citywide",sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"new_yorker","Gopnik","Adam","The New Yorker Food Essays Archive",2024,"New Yorker","DATASET_DOC",era="spanning",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media")
e(C,"gourmet","Reichl","Ruth","Gourmet Magazine: A Cultural Archive 1941-2009",2011,"Ten Speed","BOOK",era="spanning",geo="US",themes=["demand","media"],borough="Manhattan",sub_ind="food_media",stk="media")
e(C,"resy_review","Resy","","Resy Platform: Reviews and Restaurant Discovery",2024,"Resy","DATASET_DOC",era="2020_present",geo="US",themes=["demand","technology"],borough="Citywide",adj="reservation_tech",stk="media",prio="MEDIUM")
e(C,"media_hist","Fowler","Gene","Restaurant Criticism: A Short History",2008,"Columbia Journalism","ARTICLE",era="spanning",geo="US",themes=["demand","media"],sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"star_system","Matthews","Jacob","The Three-Star System: NYT's Restaurant Rating Influence",2015,"Cornell Hospitality","ARTICLE",era="2010_2020",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",prio="MEDIUM")
e(C,"food_journalism","Ruhlman","Michael","Food Journalism: Evolution in NYC",2016,"Columbia Journal","ARTICLE",era="2010_2020",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",prio="LOW")
e(C,"bon_app","Bon Appétit","","Bon Appétit NYC Coverage Archive",2024,"Condé Nast","DATASET_DOC",era="spanning",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="food_media",stk="media",prio="MEDIUM")

# ---- Cat 42: NYC Food Regulation / DOHMH (20) ----
C = "NYC Regulation"
e(C,"letter_grade","NYC DOHMH","","Restaurant Letter Grading System: Rule and Impact Report",2024,"NYC DOH","REPORT",era="2010_2020",geo="US",themes=["policy","methodology"],borough="Citywide",stk="regulator",prio="FLAGSHIP",url="https://www.nyc.gov/site/doh/services/restaurant-grades.page",nyc_canon=True)
e(C,"inspections","NYC Open Data","","DOHMH Restaurant Inspection Results Dataset",2024,"NYC Open Data","DATASET_DOC",era="2020_present",geo="US",themes=["methodology","policy"],borough="Citywide",url="https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j",stk="regulator")
e(C,"calorie","Dumanovsky","Tamara","Consumer Response to Calorie Labeling in NYC Restaurants",2011,"American J Public Health","ARTICLE",era="2010_2020",geo="US",themes=["demand","policy"],borough="Citywide",prio="HIGH")
e(C,"transfat","Angell","Sonia","Cholesterol Control Beyond the Clinic: NYC Trans-Fat Restrictions",2009,"Annals of Internal Medicine","ARTICLE",era="1980_2010",geo="US",themes=["policy","demand"],borough="Citywide",prio="HIGH")
e(C,"transfat","Resnik","David B.","Trans-Fat Bans and Human Freedom",2010,"American J Bioethics","ARTICLE",era="1980_2010",geo="US",themes=["policy"],borough="Citywide",prio="MEDIUM")
e(C,"soda_ban","Pomeranz","Jennifer L.","Portion Sizes and Beverage Caps: NYC's Big Gulp Rule",2012,"Yale J Health Policy","ARTICLE",era="2010_2020",geo="US",themes=["policy","demand"],borough="Citywide",bev="soda",prio="HIGH")
e(C,"hacp","NYC DOHMH","","HACCP Plan Requirements for NYC Food Establishments",2022,"NYC Health","GOV_DOC",era="2020_present",geo="US",themes=["policy"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"handler","NYC DOHMH","","Food Protection Training Certificate Program",2024,"NYC Health","DATASET_DOC",era="2020_present",geo="US",themes=["policy","labor"],borough="Citywide",stk="regulator",url="https://www1.nyc.gov/site/doh/services/food-protection-training.page")
e(C,"violations","NYC Open Data","","OATH Food Violations Records Dataset",2024,"NYC Open Data","DATASET_DOC",era="2020_present",geo="US",themes=["policy","methodology"],borough="Citywide",stk="regulator")
e(C,"outdoor_code","NYC DOT","","Open Restaurants Permanent Rule 2023",2023,"NYC DOT","GOV_DOC",era="2020_present",geo="US",themes=["policy","demand"],borough="Citywide",stk="regulator",url="https://www.nyc.gov/html/dot/html/pedestrians/openrestaurants.shtml",prio="HIGH")
e(C,"rodent","NYC DOHMH","","Rodent Abatement Ordinance & Restaurant Compliance",2023,"NYC Health","REPORT",era="2020_present",geo="US",themes=["policy"],borough="Citywide",adj="pest",stk="regulator",prio="MEDIUM")
e(C,"delivery_min","NYC DCWP","","App-Based Delivery Worker Minimum Pay Rule 2023",2023,"NYC DCWP","GOV_DOC",era="2020_present",geo="US",themes=["labor","policy"],borough="Citywide",adj="legal",stk="regulator",prio="CRITICAL")
e(C,"inspection_impact","Simon","Paul A.","Impact of Restaurant Hygiene Grade Cards on Foodborne Disease",2005,"JAMA","ARTICLE",era="1980_2010",geo="US",themes=["policy","demand"],borough="none",prio="MEDIUM")
e(C,"smoke_ban","NYC","","NYC Smoke-Free Air Act 2003: Restaurant Industry Impact",2010,"NYC","REPORT",era="1980_2010",geo="US",themes=["policy"],borough="Citywide",stk="regulator",prio="LOW")
e(C,"seating","NYC Council","","Outdoor Dining Permanent Zoning Rule",2023,"NYC Council","GOV_DOC",era="2020_present",geo="US",themes=["policy","demand"],borough="Citywide",stk="regulator",prio="HIGH")
e(C,"reg_hist","NYC DOHMH","","History of NYC Food Inspection 1866-Present",2018,"NYC Health","REPORT",era="spanning",geo="US",themes=["policy"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"fhv","NYC Health","","Foodhandler Certification Data and Trends",2023,"NYC DOH","DATASET_DOC",era="2020_present",geo="US",themes=["policy","labor","methodology"],borough="Citywide",stk="regulator",prio="LOW")
e(C,"restaurant_safety","NYC DOH","","Restaurant Hygiene Evaluation: Longitudinal Analysis",2021,"Journal of Food Protection","ARTICLE",era="2020_present",geo="US",themes=["policy","methodology"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"compost_law","NYC DSNY","","Commercial Composting Mandate NYC",2024,"NYC Sanitation","GOV_DOC",era="2020_present",geo="US",themes=["policy","climate"],borough="Citywide",adj="waste",stk="regulator",prio="HIGH")

# ---- Cat 43: NYC Food & Hospitality Labor (25) ----
C = "NYC Labor"
e(C,"pachirat","Pachirat","Timothy","Every Twelve Seconds: Industrialized Slaughter and the Politics of Sight",2011,"Yale UP","BOOK",era="2010_2020",geo="US",themes=["labor","supply"],borough="Tri-State",sub_ind="wholesale",prio="FLAGSHIP",nyc_canon=True,url=scholar("Pachirat Every Twelve Seconds"))
e(C,"roc","ROC United","","Behind the Kitchen Door: NYC Restaurant Workers Survey",2013,"ROC","REPORT",era="2010_2020",geo="US",themes=["labor"],borough="Citywide",stk="NGO",prio="HIGH")
e(C,"one_fair","Jayaraman","Saru","One Fair Wage: The Case Against the Tipped Minimum Wage",2023,"New Press","BOOK",era="2020_present",geo="US",themes=["labor","policy"],borough="Citywide",stk="NGO")
e(C,"unite_here","UNITE HERE Local 100","","NYC Hotel and Restaurant Workers Local 100 Archive",2024,"UNITE HERE","REPORT",era="spanning",geo="US",themes=["labor"],borough="Citywide",stk="worker")
e(C,"dc37","DC 37","","Public Sector Food Workers DC 37 Records",2024,"DC 37 AFSCME","REPORT",era="spanning",geo="US",themes=["labor"],borough="Citywide",stk="worker",prio="MEDIUM")
e(C,"deliveristas","Los Deliveristas Unidos","","Delivery Worker Organizing in NYC",2023,"Workers Justice Project","REPORT",era="2020_present",geo="US",themes=["labor","technology"],borough="Citywide",adj="labor_union",stk="worker",prio="HIGH")
e(C,"min_pay","Parrott","James A.","Delivery Worker Minimum Pay: Economic Analysis",2022,"The New School Center for NY City Affairs","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Citywide",stk="academic")
e(C,"kitchen","Holmes","Seth M.","Fresh Fruit Broken Bodies: Migrant Farmworkers in the US",2013,"UC Press","BOOK",era="2010_2020",geo="US",themes=["labor"],borough="Tri-State",prio="HIGH")
e(C,"restaurant","Jayaraman","Saru","Behind the Kitchen Door",2013,"Cornell UP","BOOK",era="2010_2020",geo="US",themes=["labor"],borough="Citywide",stk="NGO")
e(C,"rwcf","Restaurant Workers Community Foundation","","RWCF NYC Industry Reports",2024,"RWCF","REPORT",era="2020_present",geo="US",themes=["labor","demand"],borough="Citywide",stk="NGO",url="https://restaurantworkerscf.org/")
e(C,"immigrant","Ocejo","Richard E.","Masters of Craft: Old Jobs in the New Urban Economy",2017,"Princeton UP","BOOK",era="2010_2020",geo="US",themes=["labor"],borough="Citywide",sub_ind="bar")
e(C,"sinclair","Sinclair","Upton","The Jungle",1906,"Doubleday","BOOK",era="pre1900",geo="US",themes=["labor","policy"],sub_ind="wholesale")
e(C,"kitchen_wage","BLS","","Food Preparation and Serving Wages NYC Metro",2024,"BLS","DATASET_DOC",era="2020_present",geo="US",themes=["labor","methodology"],borough="Citywide",stk="regulator",url="https://www.bls.gov/regions/new-york-new-jersey/")
e(C,"tipped","Dube","Arindrajit","Minimum Wages and the Distribution of Family Incomes",2019,"AEJ Applied","ARTICLE",era="2010_2020",geo="US",themes=["labor"],borough="none",prio="MEDIUM")
e(C,"delivery","Workers Justice Project","","NYC Deliveristas Research 2021",2021,"WJP","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Citywide",adj="labor_union",stk="NGO")
e(C,"kitchen_back","Stuesse","Angela","Scratching Out a Living: Latinos Race and Work in the Deep South",2016,"UC Press","BOOK",era="2010_2020",geo="US",themes=["labor"],sub_ind="wholesale",prio="MEDIUM")
e(C,"reservation","NYC","","Fair Workweek Law Implementation: Retail and Fast Food",2017,"NYC DCWP","GOV_DOC",era="2010_2020",geo="US",themes=["labor","policy"],borough="Citywide",stk="regulator")
e(C,"bartender","Meehan","Jim","The PDT Cocktail Book",2011,"Sterling Epicure","BOOK",era="2010_2020",geo="US",themes=["labor","demand"],borough="Manhattan",sub_ind="bar",bev="spirits",prio="LOW")
e(C,"grocery","Lopez","Steven","Reorganizing the Rust Belt: An Inside Study of the American Labor Movement (ch. on Pathmark NY)",2004,"UC Press","BOOK",era="1980_2010",geo="US",themes=["labor"],borough="Citywide",sub_ind="supermarket",prio="LOW")
e(C,"hotel","UNITE HERE","","NYC Hotel Food Service Union Wages 2024",2024,"UNITE HERE","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Manhattan",sub_ind="foodservice",adj="labor_union",stk="worker",prio="MEDIUM")
e(C,"covid_labor","Saitone","Tina L.","COVID-19 and the Ag Economy",2020,"AEPP","ARTICLE",era="2020_present",geo="US",themes=["labor","supply"],borough="none",sub_ind="wholesale",prio="MEDIUM")
e(C,"wage_theft","Bernhardt","Annette","Broken Laws, Unprotected Workers",2009,"NELP","REPORT",era="1980_2010",geo="US",themes=["labor","policy"],borough="Citywide",stk="NGO")
e(C,"meat_covid","Taylor","Charles A.","Livestock Plants and COVID-19 Transmission",2022,"PNAS","ARTICLE",era="2020_present",geo="US",themes=["labor","supply"],borough="none",sub_ind="wholesale",prio="HIGH")
e(C,"ilgwu","ILR School","","NYC Hospitality Labor History Archive",2024,"Cornell ILR","DATASET_DOC",era="spanning",geo="US",themes=["labor"],borough="Citywide",stk="academic",prio="MEDIUM")
e(C,"restaurant_safe","Jayaraman","Saru","Forked: A New Standard for American Dining",2016,"Oxford UP","BOOK",era="2010_2020",geo="US",themes=["labor","demand"],borough="Citywide",stk="NGO")

# ---- Cat 44: NYC Delivery Apps & On-Demand (20) ----
C = "NYC Delivery"
e(C,"seamless","Seamless","","Seamless NYC Founding & Grubhub Merger 2013 History",2018,"Corporate","GOV_DOC",era="2010_2020",geo="US",themes=["technology","demand"],borough="Citywide",adj="pos_tech",stk="trader",prio="FLAGSHIP",nyc_canon=True)
e(C,"grubhub","Just Eat Takeaway","","Grubhub Annual Report 2023",2023,"JET","GOV_DOC",era="2020_present",geo="US",themes=["technology","finance"],borough="Citywide",adj="reservation_tech",stk="investor")
e(C,"doordash","DoorDash","","DoorDash S-1 Filing and 10-K",2023,"DoorDash","GOV_DOC",era="2020_present",geo="US",themes=["technology","finance"],borough="Citywide",adj="pos_tech",stk="investor",prio="HIGH")
e(C,"ubereats","Uber","","Uber Eats 10-K Segment Data",2023,"Uber","GOV_DOC",era="2020_present",geo="US",themes=["technology","finance"],borough="Citywide",adj="pos_tech",stk="investor",prio="HIGH")
e(C,"instacart","Maplebear/Instacart","","Instacart S-1 and IPO 2023 Filings",2023,"Instacart","GOV_DOC",era="2020_present",geo="US",themes=["technology","finance"],borough="Citywide",adj="pos_tech",stk="investor",prio="HIGH")
e(C,"commissions","NYC Council","","Delivery App Commission Cap Laws 2020",2020,"NYC Council","GOV_DOC",era="2020_present",geo="US",themes=["policy","technology"],borough="Citywide",adj="legal",stk="regulator",prio="HIGH")
e(C,"relay","Relay","","Relay Delivery Platform NYC Service Model",2023,"Corporate","REPORT",era="2020_present",geo="US",themes=["technology"],borough="Citywide",adj="pos_tech",stk="trader",prio="MEDIUM")
e(C,"mercato","Mercato","","Mercato Online Specialty Food Platform NYC",2023,"Corporate","REPORT",era="2020_present",geo="US",themes=["technology","demand"],borough="Citywide",stk="trader",prio="LOW")
e(C,"ghost","Reed","Ryan","Ghost Kitchens: NYC Market Analysis",2022,"Nation's Restaurant News","ARTICLE",era="2020_present",geo="US",themes=["technology","demand"],borough="Citywide",stk="media",prio="MEDIUM")
e(C,"delivery_labor","Gregory","Karen","Delivery Platform Labor in NYC",2021,"Institute for Work & Employment Research","ARTICLE",era="2020_present",geo="US",themes=["labor","technology"],borough="Citywide",adj="labor_union",prio="MEDIUM")
e(C,"bike_del","The Markup","","NYC Delivery Worker Conditions: Data Analysis",2022,"The Markup","ARTICLE",era="2020_present",geo="US",themes=["labor","technology"],borough="Citywide",stk="media",prio="MEDIUM")
e(C,"grocery_del","FreshDirect","","FreshDirect Operations and Sale 2021",2021,"FreshDirect","GOV_DOC",era="2020_present",geo="US",themes=["technology","supply"],borough="Citywide",sub_ind="supermarket",stk="investor",prio="MEDIUM")
e(C,"quick_com","Gopuff/Getir/Jokr","","Quick Commerce Wave 2020-2023 Collapse in NYC",2023,"CB Insights","REPORT",era="2020_present",geo="US",themes=["technology","finance"],borough="Citywide",stk="investor",prio="MEDIUM")
e(C,"seamless_econ","Kang","Helen","Delivery Commission Economics: 2020-2024",2024,"Cornell Hospitality","ARTICLE",era="2020_present",geo="US",themes=["finance","technology"],borough="Citywide",stk="academic",prio="MEDIUM")
e(C,"cov_boom","Popper","Nathaniel","Delivery App Boom During Pandemic",2021,"NYT","ARTICLE",era="2020_present",geo="US",themes=["demand","technology"],borough="Citywide",stk="media",prio="MEDIUM")
e(C,"min_wage_del","NYC DCWP","","Delivery Worker Minimum Wage Final Rule 2023",2023,"NYC DCWP","GOV_DOC",era="2020_present",geo="US",themes=["labor","policy"],borough="Citywide",stk="regulator",prio="CRITICAL")
e(C,"app_dark","Deliveroo","","Dark Kitchen Expansion and Contraction 2020-2024",2024,"Deliveroo","REPORT",era="2020_present",geo="US",themes=["technology","finance"],borough="Citywide",stk="media",prio="LOW")
e(C,"consumer","Yelp","","Yelp NYC Delivery Usage Patterns",2024,"Yelp","DATASET_DOC",era="2020_present",geo="US",themes=["demand","technology"],borough="Citywide",stk="media",prio="MEDIUM")
e(C,"restaurant_impact","NY Hospitality","","Delivery Apps Cost Restaurants: Industry Position Paper",2021,"NYC Hospitality Alliance","REPORT",era="2020_present",geo="US",themes=["finance","demand"],borough="Citywide",stk="NGO",prio="HIGH")
e(C,"chef_response","Meyer","Danny","Setting the Table: Hospitality in the Delivery Era",2023,"HBR","ARTICLE",era="2020_present",geo="US",themes=["demand","technology"],borough="Citywide",stk="foodservice",prio="MEDIUM")

# ---- Cat 45: NYC COVID Impact & Recovery (25) ----
C = "NYC COVID"
e(C,"open_rest","NYC DOT","","Open Restaurants Program Launch June 2020",2020,"NYC","GOV_DOC",era="2020_present",geo="US",themes=["policy","demand"],borough="Citywide",stk="regulator",prio="FLAGSHIP",nyc_canon=True)
e(C,"closures","Yelp","","NYC Restaurant Permanent Closures 2020-2022",2022,"Yelp Economic","REPORT",era="2020_present",geo="US",themes=["finance","demand"],borough="Citywide",stk="media",prio="HIGH")
e(C,"ppp","SBA","","PPP NYC Restaurant Loan Data 2020-2021",2022,"SBA","DATASET_DOC",era="2020_present",geo="US",themes=["finance","policy"],borough="Citywide",stk="regulator")
e(C,"rrf","SBA","","Restaurant Revitalization Fund Allocation",2021,"SBA","REPORT",era="2020_present",geo="US",themes=["finance","policy"],borough="Citywide",stk="regulator",prio="HIGH")
e(C,"irc","Independent Restaurant Coalition","","IRC COVID-19 Advocacy Campaign Archives",2023,"IRC","REPORT",era="2020_present",geo="US",themes=["policy","finance"],borough="Citywide",stk="NGO",url="https://www.independentrestaurantcoalition.com/")
e(C,"outdoor_perm","NYC Council","","Open Streets Permanent 2023 Rulemaking",2023,"NYC Council","GOV_DOC",era="2020_present",geo="US",themes=["policy","demand"],borough="Citywide",stk="regulator",prio="HIGH")
e(C,"dining_ban","Cuomo","Andrew","Executive Order 202.3: Dine-in Ban March 2020",2020,"NYS","GOV_DOC",era="2020_present",geo="US",themes=["policy"],borough="Citywide",stk="regulator")
e(C,"ghost_ny","Reuters","","NYC Ghost Kitchen Industry 2021-2024",2024,"Reuters","ARTICLE",era="2020_present",geo="US",themes=["technology","demand"],borough="Citywide",sub_ind="fine_dining",stk="media",prio="MEDIUM")
e(C,"takeout","NYC Comptroller","","NYC Restaurant Takeout Economic Impact Report",2021,"NYC Comptroller","REPORT",era="2020_present",geo="US",themes=["finance","demand"],borough="Citywide",stk="regulator")
e(C,"recovery","NYCEDC","","NYC Food Industry Recovery Tracker 2022-2024",2024,"NYCEDC","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",stk="regulator",prio="HIGH")
e(C,"chefs_relief","Jose Andres","","World Central Kitchen NYC Operations 2020",2020,"WCK","REPORT",era="2020_present",geo="US",themes=["demand","policy"],borough="Citywide",stk="NGO",prio="MEDIUM")
e(C,"getfood","NYC GetFood","","GetFood Program Pandemic Emergency Meal Distribution",2021,"NYC Mayor","REPORT",era="2020_present",geo="US",themes=["demand","policy"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"pandemic_fam","Rockefeller Foundation","","NYC Pandemic Food Security Report",2021,"Rockefeller","REPORT",era="2020_present",geo="US",themes=["demand","policy"],borough="Citywide",stk="NGO",prio="MEDIUM")
e(C,"closures_data","Grubhub","","Grubhub NYC Restaurant Closure Heatmap 2020-2022",2022,"Grubhub","DATASET_DOC",era="2020_present",geo="US",themes=["finance","methodology"],borough="Citywide",stk="media",prio="MEDIUM")
e(C,"outdoor_cost","NYC","","Outdoor Dining Costs for Restaurateurs: Survey",2022,"NYC Hospitality Alliance","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",stk="NGO",prio="MEDIUM")
e(C,"nine_block","NYC Council","","Universal Outdoor Dining: Design and Equity Analysis",2022,"NYC","REPORT",era="2020_present",geo="US",themes=["policy","demand"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"reopening","NYC DOH","","Phased Restaurant Reopening Guidelines 2020-2021",2021,"NYC Health","GOV_DOC",era="2020_present",geo="US",themes=["policy"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"tourism_drop","NYC & Company","","NYC Tourism Recovery 2021-2024",2024,"NYC Tourism","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Citywide",adj="real_estate",stk="NGO",prio="MEDIUM")
e(C,"rent_arrears","REBNY","","Commercial Rent Deferrals and Arrears 2020-2023",2023,"REBNY","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="NGO",prio="MEDIUM")
e(C,"worker_covid","Taylor","Charles A.","Meatpacking Plants and COVID Transmission",2022,"PNAS","ARTICLE",era="2020_present",geo="US",themes=["labor","supply"],borough="none",sub_ind="wholesale",prio="HIGH")
e(C,"street_covid","SVP","","Street Vendors Pandemic Report NYC",2021,"Street Vendor Project","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Citywide",sub_ind="food_truck",stk="NGO")
e(C,"bodega_covid","NYCEDC","","Bodega Essential Business Designation COVID Impact",2021,"NYCEDC","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",sub_ind="bodega",stk="regulator")
e(C,"grocery_covid","Ziliak","James","Food Security During COVID-19: NYC Metro",2021,"Applied Econ Perspectives","ARTICLE",era="2020_present",geo="US",themes=["demand","policy"],borough="Citywide",prio="MEDIUM")
e(C,"pandemic_ebt","USDA FNS","","Pandemic EBT (P-EBT) NYC Rollout",2021,"USDA FNS","REPORT",era="2020_present",geo="US",themes=["policy","demand"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"delivery_boom","McKinsey","","Food Delivery Surge NYC 2020-2021",2021,"McKinsey","REPORT",era="2020_present",geo="US",themes=["demand","technology"],borough="Citywide",adj="pos_tech",stk="media",prio="MEDIUM")

# ---- Cat 46: NYC Food Real Estate & Retail Rents (20) ----
C = "NYC Food RE"
e(C,"rebny","REBNY","","REBNY Retail Report Manhattan/Brooklyn Quarterly",2024,"REBNY","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="NGO",prio="FLAGSHIP",url="https://www.rebny.com/")
e(C,"cuf_storefront","Center for an Urban Future","","State of the Storefront NYC",2019,"CUF","REPORT",era="2010_2020",geo="US",themes=["finance","demand"],borough="Citywide",adj="real_estate",stk="NGO",prio="HIGH")
e(C,"comptroller","NYC Comptroller","","Storefront Vacancy Tracker NYC",2023,"NYC Comptroller","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="regulator",prio="HIGH")
e(C,"rents_ch","Cushman & Wakefield","","NYC Retail Rents Marketbeat",2024,"C&W","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="media",prio="MEDIUM")
e(C,"rents_brok","CBRE","","CBRE NYC Retail Market Report",2024,"CBRE","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="media",prio="MEDIUM")
e(C,"gentry","Zukin","Sharon","Naked City: Death and Life of Authentic Urban Places",2010,"Oxford UP","BOOK",era="2010_2020",geo="US",themes=["demand","policy"],borough="Citywide",adj="real_estate")
e(C,"chain_retail","Barbaro","Michael","Chains Replacing Mom-and-Pops in NYC",2014,"NYT","ARTICLE",era="2010_2020",geo="US",themes=["demand"],borough="Citywide",sub_ind="chain",stk="media",prio="MEDIUM")
e(C,"rent_control","Real Deal","","Commercial Rent Control Debate NYC 2019",2019,"The Real Deal","ARTICLE",era="2010_2020",geo="US",themes=["policy","finance"],borough="Citywide",adj="real_estate",stk="media",prio="MEDIUM")
e(C,"duane","Gratz","Roberta","Nightmare on Chain Store Row: Duane Reade Expansion",2005,"Planning","ARTICLE",era="1980_2010",geo="US",themes=["demand"],borough="Citywide",sub_ind="retail",stk="media",prio="LOW")
e(C,"times_sq","NYT","","Times Square Food Rent Premium Analysis",2019,"NYT","ARTICLE",era="2010_2020",geo="US",themes=["finance"],borough="Manhattan",adj="real_estate",stk="media",prio="LOW")
e(C,"percent_rent","NYC Hospitality","","Percentage Rent Deals in NYC Restaurants",2021,"NYC Hospitality Alliance","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="NGO",prio="MEDIUM")
e(C,"foodhall","Le District","","Food Hall Development NYC 2015-2024",2024,"Industry","REPORT",era="2020_present",geo="US",themes=["demand","finance"],borough="Citywide",sub_ind="fine_dining",stk="media",prio="MEDIUM")
e(C,"landlords","Halpin","Mickey","NYC Restaurant Landlord Power Dynamics",2020,"Bisnow","ARTICLE",era="2020_present",geo="US",themes=["finance","policy"],borough="Citywide",adj="real_estate",stk="media",prio="MEDIUM")
e(C,"vacancies","CUF","","Storefront Vacancy Snapshot 2023",2023,"Center for an Urban Future","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="NGO",prio="MEDIUM")
e(C,"eataly","Eataly","","Eataly NYC: A Case Study in Food Hall Economics",2020,"Harvard Business Review","ARTICLE",era="2010_2020",geo="US",themes=["demand","finance"],borough="Manhattan",sub_ind="fine_dining",stk="media",prio="MEDIUM")
e(C,"hudson","Hudson Yards","","Hudson Yards Food & Beverage Leasing Analysis",2020,"Real Deal","ARTICLE",era="2010_2020",geo="US",themes=["finance"],borough="Manhattan",adj="real_estate",stk="media",prio="LOW")
e(C,"chelsea_mkt","Chelsea Market","","Chelsea Market Food Retail Model",2020,"NYC EDC","REPORT",era="2010_2020",geo="US",themes=["demand","finance"],borough="Manhattan",adj="real_estate",stk="regulator",prio="MEDIUM")
e(C,"small_biz","NYC SBS","","NYC Dept Small Business Services Restaurant Reports",2024,"NYC SBS","REPORT",era="2020_present",geo="US",themes=["finance","policy"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"gentry_b","Zukin","Sharon","New Retail Capital and Neighborhood Change",2009,"City & Community","ARTICLE",era="1980_2010",geo="US",themes=["demand","policy"],borough="Brooklyn",sub_ind="retail",prio="MEDIUM")
e(C,"mall_decline","Segal","David","NYC Ground-Floor Retail Apocalypse",2017,"NYT","ARTICLE",era="2010_2020",geo="US",themes=["finance"],borough="Manhattan",adj="real_estate",stk="media",prio="MEDIUM")

# ---- Cat 47: NYC Food Access, SNAP & Inequality (20) ----
C = "NYC Food Access"
e(C,"food_bank","Food Bank For NYC","","Food Bank For NYC Annual Hunger Report",2024,"FBNYC","REPORT",era="2020_present",geo="US",themes=["demand","policy"],borough="Citywide",stk="NGO",prio="FLAGSHIP",url="https://www.foodbanknyc.org/")
e(C,"city_harvest","City Harvest","","City Harvest NYC Operations Report",2024,"City Harvest","REPORT",era="2020_present",geo="US",themes=["supply","demand"],borough="Citywide",stk="NGO")
e(C,"snap_ny","NYC HRA","","SNAP Enrollment NYC",2024,"NYC Human Resources Admin","DATASET_DOC",era="2020_present",geo="US",themes=["policy","demand","methodology"],borough="Citywide",stk="regulator")
e(C,"food_policy","NYC Mayor","","NYC Food Policy Annual Report",2024,"Mayor's Office of Food Policy","REPORT",era="2020_present",geo="US",themes=["policy"],borough="Citywide",stk="regulator",url="https://www.nyc.gov/site/foodpolicy/",prio="HIGH")
e(C,"food_deserts","Allcott","Hunt","Food Deserts and Nutritional Inequality (NYC data)",2019,"QJE","ARTICLE",era="2010_2020",geo="US",themes=["demand","policy"],borough="Citywide",prio="HIGH")
e(C,"cuny_food","CUNY Urban Food Policy","","Food Insecurity in NYC: Annual Report",2024,"CUNY","REPORT",era="2020_present",geo="US",themes=["demand","policy"],borough="Citywide",stk="academic")
e(C,"snap_bodega","Weiner","Rebecca","SNAP Retailers in Bodegas",2019,"J Hunger","ARTICLE",era="2010_2020",geo="US",themes=["demand","policy"],borough="Citywide",sub_ind="bodega",prio="MEDIUM")
e(C,"hunger_free","Hunger Free NYC","","Hunger Free NYC Policy Campaign",2024,"HFNYC","REPORT",era="2020_present",geo="US",themes=["policy"],borough="Citywide",stk="NGO",prio="MEDIUM")
e(C,"fresh","NYC EDC","","FRESH Program Food Retail Expansion",2012,"NYC EDC","REPORT",era="2010_2020",geo="US",themes=["policy","supply"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"sl_universal","NYC DOE","","Universal Free School Meals 2017",2017,"NYC DOE","GOV_DOC",era="2010_2020",geo="US",themes=["policy","demand"],borough="Citywide",stk="regulator",prio="HIGH")
e(C,"wic_ny","NYC WIC","","NYC WIC Program Data",2024,"NYC Health","DATASET_DOC",era="2020_present",geo="US",themes=["policy","demand"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"pantries","Food Pantries NYC","","NYC Food Pantry Directory and Analysis",2024,"FoodPantries.org","DATASET_DOC",era="2020_present",geo="US",themes=["demand","supply"],borough="Citywide",stk="NGO",prio="MEDIUM")
e(C,"food_access_map","USDA ERS","","Food Access Research Atlas NYC Tracts",2024,"USDA ERS","DATASET_DOC",era="2020_present",geo="US",themes=["demand","methodology"],borough="Citywide",stk="regulator",prio="HIGH")
e(C,"insecure","Coleman-Jensen","Alisha","Household Food Security NYC Metro",2024,"USDA ERS","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Citywide",stk="regulator",prio="HIGH")
e(C,"summer_meals","NYC DOE","","Summer Meals Program Usage",2024,"NYC","REPORT",era="2020_present",geo="US",themes=["policy","demand"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"poor_diet","NYC Health","","NYC Community Health Survey: Food Access",2023,"NYC Health","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"free_food","CUNY Hunger","","CUNY Student Food Insecurity Report",2023,"CUNY","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Citywide",stk="academic",prio="MEDIUM")
e(C,"nutrition","NYC DOHMH","","Health Bucks SNAP Incentive Program",2024,"NYC Health","REPORT",era="2020_present",geo="US",themes=["policy"],borough="Citywide",stk="regulator",prio="MEDIUM")
e(C,"meal_prog","Meals on Wheels","","Meals on Wheels NYC Senior Food Program",2024,"Meals on Wheels","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Citywide",stk="NGO",prio="LOW")
e(C,"wic_impact","Bitler","Marianne","WIC and Demand for Healthful Foods",2015,"Applied Econ Perspectives","ARTICLE",era="2010_2020",geo="US",themes=["policy"],borough="none",prio="MEDIUM")

# ---- Cat 48: NYC Food Waste & Sanitation (15) ----
C = "NYC Waste"
e(C,"picking_up","Nagle","Robin","Picking Up: On the Streets and Behind the Trucks with the Sanitation Workers of NYC",2013,"FSG","BOOK",era="2010_2020",geo="US",themes=["labor","climate"],borough="Citywide",adj="waste",prio="FLAGSHIP",nyc_canon=True,url=scholar("Nagle Picking Up"))
e(C,"cwz","NYC DSNY","","Commercial Waste Zones Implementation 2019",2019,"NYC DSNY","GOV_DOC",era="2010_2020",geo="US",themes=["policy"],borough="Citywide",adj="waste",stk="regulator",prio="HIGH")
e(C,"compost","NYC DSNY","","Universal Curbside Composting NYC 2024",2024,"NYC DSNY","GOV_DOC",era="2020_present",geo="US",themes=["policy","climate"],borough="Citywide",adj="waste",stk="regulator",prio="HIGH")
e(C,"ll97","NYC","","Local Law 97 Commercial Kitchen Emissions Compliance",2024,"NYC","GOV_DOC",era="2020_present",geo="US",themes=["policy","climate"],borough="Citywide",adj="waste",stk="regulator",prio="HIGH")
e(C,"rats","Sullivan","Robert","Rats: Observations on the History & Habitat of NYC's Most Unwanted Inhabitants",2004,"Bloomsbury","BOOK",era="2010_2020",geo="US",themes=["climate"],borough="Citywide",adj="pest",prio="HIGH",nyc_canon=True)
e(C,"waste_haul","GAO/NYS","","NYC Private Carting Industry Report",2020,"NYS AG","REPORT",era="2020_present",geo="US",themes=["policy","finance"],borough="Citywide",adj="waste",stk="regulator",prio="HIGH")
e(C,"food_waste","ReFED","","NYC Food Waste Study 2022",2022,"ReFED","REPORT",era="2020_present",geo="US",themes=["supply","climate"],borough="Citywide",adj="waste",stk="NGO",prio="MEDIUM")
e(C,"waste_workers","Center for Public Safety","","Commercial Waste Workers Safety",2020,"Occupational Safety","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Citywide",adj="waste",stk="NGO",prio="MEDIUM")
e(C,"organics","BioCycle","","NYC Commercial Organic Waste Collection",2023,"BioCycle","ARTICLE",era="2020_present",geo="US",themes=["policy","climate"],borough="Citywide",adj="waste",stk="media",prio="MEDIUM")
e(C,"tipping","NYC","","Tipping Fees NYC Commercial Waste Comparison",2021,"NYC","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="waste",stk="regulator",prio="MEDIUM")
e(C,"freshkills","NYC Parks","","Fresh Kills Landfill History and Closure 2001",2001,"NYC","REPORT",era="spanning",geo="US",themes=["climate","policy"],borough="Staten_Island",adj="waste",stk="regulator",prio="MEDIUM")
e(C,"pest_ny","NYC Health","","Rodent Indexing Program and Restaurant Correlation",2023,"NYC DOH","REPORT",era="2020_present",geo="US",themes=["policy"],borough="Citywide",adj="pest",stk="regulator",prio="MEDIUM")
e(C,"biogas","NYC DEP","","Newtown Creek Biogas Program",2023,"DEP","REPORT",era="2020_present",geo="US",themes=["climate","supply"],borough="Brooklyn",adj="waste",stk="regulator",prio="MEDIUM")
e(C,"carting","Royle","Edward","Garbage: NYC's Carting Industry Organized Crime",2001,"Investigative Reporting","ARTICLE",era="1980_2010",geo="US",themes=["policy","labor"],borough="Citywide",adj="waste",stk="media",prio="MEDIUM")
e(C,"waste_rpt","NYC DSNY","","PlaNYC Waste Management Policies 2020-2030",2021,"NYC Sustainability","REPORT",era="2020_present",geo="US",themes=["policy","climate"],borough="Citywide",adj="waste",stk="regulator",prio="MEDIUM")

# ---- Cat 49: NYC Bars, Nightlife & Liquor (15) ----
C = "NYC Bars"
e(C,"cocktail","Wondrich","David","Imbibe! From Absinthe Cocktail to Whiskey Smash",2007,"Perigee","BOOK",era="spanning",geo="US",themes=["demand"],borough="Manhattan",sub_ind="bar",bev="spirits",prio="FLAGSHIP")
e(C,"prohibition","Okrent","Daniel","Last Call: The Rise and Fall of Prohibition",2010,"Scribner","BOOK",era="pre1900",geo="US",themes=["policy","demand"],borough="Manhattan",sub_ind="bar",bev="spirits")
e(C,"prohibition","Lerner","Michael","Dry Manhattan: Prohibition in NYC",2007,"Harvard UP","BOOK",era="1900_1945",geo="US",themes=["policy"],borough="Manhattan",sub_ind="bar")
e(C,"speakeasy","McGrath","Charles","The Stork Club: The Life and Times of NYC's Most Celebrated Nightclub",2000,"McFarland","BOOK",era="1900_1945",geo="US",themes=["demand"],borough="Manhattan",sub_ind="bar",prio="MEDIUM")
e(C,"21club","Berger","Meyer","21 Club",1959,"Simon & Schuster","BOOK",era="1900_1945",geo="US",themes=["demand"],borough="Manhattan",sub_ind="bar",prio="MEDIUM")
e(C,"cocktail_rev","Meehan","Jim","The PDT Cocktail Book",2011,"Sterling","BOOK",era="2010_2020",geo="US",themes=["demand"],borough="Manhattan",sub_ind="bar",bev="spirits")
e(C,"craft_bar","Ocejo","Richard","Masters of Craft (bar chapters)",2017,"Princeton UP","CHAPTER",era="2010_2020",geo="US",themes=["labor","demand"],borough="Manhattan",sub_ind="bar",bev="spirits")
e(C,"craft_beer","Ogle","Maureen","Ambitious Brew: The Story of American Beer",2006,"Houghton Mifflin","BOOK",era="spanning",geo="US",themes=["demand"],sub_ind="bar",bev="beer")
e(C,"nat_wine","Kramer","Alice Feiring","Natural Wine for the People",2019,"Ten Speed","BOOK",era="2010_2020",geo="US",themes=["demand"],borough="Manhattan",sub_ind="bar",bev="wine",prio="MEDIUM")
e(C,"sla","NYS SLA","","NYS Liquor Authority Annual Reports",2024,"NYS SLA","REPORT",era="2020_present",geo="US",themes=["policy"],borough="Citywide",sub_ind="bar",stk="regulator",bev="spirits",prio="MEDIUM")
e(C,"nightlife","NYC Mayor Office of Nightlife","","State of NYC Nightlife",2024,"NYC","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Citywide",sub_ind="bar",stk="regulator",prio="MEDIUM")
e(C,"bottle_serv","Smith","Sarah","The Economics of Bottle Service NYC Clubs",2019,"J Hospitality & Tourism","ARTICLE",era="2010_2020",geo="US",themes=["finance"],borough="Manhattan",sub_ind="bar",bev="spirits",prio="LOW")
e(C,"dive","Moss","Jeremiah","Vanishing New York: How a Great City Lost Its Soul",2017,"Dey Street","BOOK",era="2010_2020",geo="US",themes=["demand"],borough="Manhattan",sub_ind="bar",prio="MEDIUM")
e(C,"craft_beer_ny","Brooklyn Brewery","","Brooklyn Brewery Corporate History",2024,"Brooklyn Brewery","GOV_DOC",era="1980_2010",geo="US",themes=["finance"],borough="Brooklyn",sub_ind="bar",bev="beer",stk="producer",prio="MEDIUM")
e(C,"distil","Kings County","","Kings County Distillery History",2024,"KCD","GOV_DOC",era="2010_2020",geo="US",themes=["supply"],borough="Brooklyn",sub_ind="bar",bev="spirits",stk="producer",prio="LOW")

# ---- Cat 50: NYC Tourism & Food (15) ----
C = "NYC Tourism"
e(C,"rest_week","NYC & Company","","Restaurant Week 1992 Origins and 30-Year Review",2022,"NYC & Co","REPORT",era="spanning",geo="US",themes=["demand","media"],borough="Citywide",sub_ind="fine_dining",stk="NGO",prio="FLAGSHIP")
e(C,"nyc_co","NYC & Company","","NYC Food Tourism Economic Impact 2024",2024,"NYC & Co","REPORT",era="2020_present",geo="US",themes=["demand","finance"],borough="Citywide",stk="NGO",prio="HIGH")
e(C,"timesq","Times Square Alliance","","Times Square Food & Beverage Economic Analysis",2023,"TSA","REPORT",era="2020_present",geo="US",themes=["demand","finance"],borough="Manhattan",adj="real_estate",stk="NGO",prio="MEDIUM")
e(C,"hotel_food","Union Square Hospitality","","Hotel Restaurant Economics",2021,"USHG","REPORT",era="2020_present",geo="US",themes=["demand","finance"],borough="Manhattan",sub_ind="fine_dining",stk="foodservice",prio="MEDIUM")
e(C,"tour_food","Scotto","Nadia","Food Tourism in NYC Post-COVID",2023,"J Tourism Research","ARTICLE",era="2020_present",geo="US",themes=["demand"],borough="Citywide",stk="academic",prio="MEDIUM")
e(C,"convention","Javits","","Javits Center Food Services Economic Contribution",2022,"Javits","REPORT",era="2020_present",geo="US",themes=["demand","finance"],borough="Manhattan",sub_ind="fine_dining",stk="foodservice",prio="LOW")
e(C,"cruise","Port Authority","","Cruise Ship Food Provisioning NYC",2020,"PANYNJ","REPORT",era="2010_2020",geo="US",themes=["supply","trade"],borough="Brooklyn",stk="regulator",prio="LOW")
e(C,"airport","Port Authority","","JFK LGA Food Service Economics",2023,"PANYNJ","REPORT",era="2020_present",geo="US",themes=["demand","finance"],borough="Queens",sub_ind="chain",stk="regulator",prio="MEDIUM")
e(C,"foodie_tour","Eater","","NYC Food Tour Guide Industry",2024,"Eater","ARTICLE",era="2020_present",geo="US",themes=["demand"],borough="Citywide",stk="media",prio="LOW")
e(C,"michelin_tour","Michelin","","Michelin NYC Guide Tourist Premium Effect",2023,"Michelin","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Manhattan",sub_ind="food_media",stk="media",prio="MEDIUM")
e(C,"broadway","Broadway League","","Pre-Theater Dining Economics",2022,"Broadway League","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Manhattan",stk="NGO",prio="LOW")
e(C,"market_tour","Eataly","","Eataly NYC as Tourist Destination: A Study",2021,"Harvard Case","REPORT",era="2010_2020",geo="US",themes=["demand"],borough="Manhattan",sub_ind="specialty_retail",cuisine="italian",stk="academic",prio="MEDIUM")
e(C,"cov_tour","NYC & Co","","NYC Tourism Recovery Tracker 2021-2024",2024,"NYC Tourism","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Citywide",stk="NGO",prio="MEDIUM")
e(C,"food_fest","NYCWFF","","NYC Wine & Food Festival Economic Impact",2024,"NYCWFF","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Manhattan",sub_ind="bar",bev="wine",stk="NGO",prio="LOW")
e(C,"tour_guide","Zagat","","Zagat NYC Tourist Use Study",2018,"Zagat","REPORT",era="2010_2020",geo="US",themes=["demand"],borough="Citywide",sub_ind="food_media",stk="media",prio="LOW")

# ---- Cat 51: Hudson Valley / Tri-State Foodshed (20) ----
C = "Tri-State Foodshed"
e(C,"foodshed","Peters","Christian","Mapping Potential Foodsheds in NY State",2009,"Renewable Ag & Food Systems","ARTICLE",era="1980_2010",geo="US",themes=["supply","climate"],borough="Upstate",prio="FLAGSHIP")
e(C,"nys_ag","NYS Ag & Markets","","New York State Agriculture Statistics",2024,"NYS Ag","DATASET_DOC",era="2020_present",geo="US",themes=["supply","methodology"],borough="Upstate",stk="regulator")
e(C,"hudson","Glynwood","","Glynwood Regional Food Report Hudson Valley",2023,"Glynwood","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Upstate",stk="NGO",prio="HIGH")
e(C,"longisland","LIF","","Long Island Farm Bureau Annual Report",2024,"LI Farm Bureau","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Upstate",stk="producer")
e(C,"hv_wine","Hudson Valley Wine Country","","Hudson Valley Wine Industry Report",2023,"HVWGA","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Upstate",sub_ind="bar",bev="wine",stk="producer",prio="MEDIUM")
e(C,"nj_produce","NJDA","","NJ Agriculture Produce Production",2024,"NJ DOA","DATASET_DOC",era="2020_present",geo="US",themes=["supply"],borough="Tri-State",stk="regulator",prio="MEDIUM")
e(C,"ct_dairy","CTDA","","CT Dairy Industry Report",2024,"CT DOA","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Tri-State",stk="regulator",comm="dairy",prio="MEDIUM")
e(C,"cornell_ext","Cornell","","Cornell Cooperative Extension Downstate",2024,"Cornell","REPORT",era="2020_present",geo="US",themes=["supply","technology"],borough="Upstate",stk="academic",prio="MEDIUM")
e(C,"farm_rest","GrowNYC","","NYC Farm-to-Restaurant Directory",2024,"GrowNYC","DATASET_DOC",era="2020_present",geo="US",themes=["supply","demand"],borough="Tri-State",sub_ind="greenmarket",stk="NGO")
e(C,"upstate","Sheriff","Carol","The Artificial River: Erie Canal",1996,"Hill & Wang","BOOK",era="pre1900",geo="US",themes=["supply","trade"],borough="Upstate",prio="MEDIUM")
e(C,"hv_climate","Hudson Valley","","Climate Impacts on NYS Agriculture",2023,"Hudson Valley Climate","REPORT",era="2020_present",geo="US",themes=["climate","supply"],borough="Upstate",stk="regulator",prio="MEDIUM")
e(C,"nyc_foodshed","Karp","","NYC's Regional Foodshed: A Scale Analysis",2020,"Karp Resources","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Tri-State",stk="academic",prio="MEDIUM")
e(C,"hv_farms","Hudson Valley","","Hudson Valley Farm Population Census",2022,"USDA NASS","DATASET_DOC",era="2020_present",geo="US",themes=["supply"],borough="Upstate",stk="regulator",prio="MEDIUM")
e(C,"li_seafood","Blue Island","","Long Island Sound Seafood Industry",2023,"LI Seafood Assoc","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Tri-State",sub_ind="fish_market",stk="producer",prio="MEDIUM")
e(C,"apple","NYS Apple","","NYS Apple Growers Economic Report",2024,"NYS Apple Association","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Upstate",stk="producer",prio="MEDIUM")
e(C,"maple","VT/NH Maple","","Regional Maple Syrup Economy",2023,"Various","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Upstate",stk="producer",prio="LOW")
e(C,"dairy_nyc","NE Dairy","","Northeastern Dairy Supply to NYC",2022,"Dairy Farmers of America","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Tri-State",comm="dairy",stk="producer",prio="MEDIUM")
e(C,"produce_nj","NJ NOFA","","NJ Organic Produce Supply NYC",2022,"NOFA NJ","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Tri-State",sub_ind="greenmarket",stk="NGO",prio="LOW")
e(C,"hv_cheese","Hudson Valley","","Hudson Valley Artisan Cheese Industry",2023,"Artisan Cheese Guild","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Upstate",comm="dairy",stk="producer",prio="LOW")
e(C,"foodshed_policy","NYC","","NYC's 10 Year Food Policy: Regional Components",2021,"NYCEDC","REPORT",era="2020_present",geo="US",themes=["supply","policy"],borough="Tri-State",stk="regulator",prio="HIGH")

# ---- Cat 52: NYC Adjacent Industries (20) ----
C = "NYC Adjacent"
e(C,"restaurant_insurance","Marsh","","NYC Restaurant Insurance Benchmarks",2023,"Marsh McLennan","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="insurance",stk="trader",prio="FLAGSHIP")
e(C,"pest","Sullivan","Robert","Rats (extended)",2004,"Bloomsbury","BOOK",era="2010_2020",geo="US",themes=["climate"],borough="Citywide",adj="pest")
e(C,"refrig","Bohn","Roger","Commercial Refrigeration Maintenance NYC",2022,"ASHRAE","REPORT",era="2020_present",geo="US",themes=["technology"],borough="Citywide",adj="commercial_equip",stk="trader",prio="MEDIUM")
e(C,"commerc_eq","Bowery Equipment","","Bowery Restaurant Supply Row Historical",2015,"Gotham Gazette","ARTICLE",era="spanning",geo="US",themes=["supply"],borough="Manhattan",adj="commercial_equip",stk="media",prio="MEDIUM")
e(C,"linen","Alsco","","NYC Restaurant Linen Services",2023,"Corporate","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Citywide",adj="commercial_equip",stk="trader",prio="LOW")
e(C,"pos_tech","Toast","","Toast Inc S-1 Filing IPO",2021,"Toast Inc","GOV_DOC",era="2020_present",geo="US",themes=["technology","finance"],borough="Citywide",adj="pos_tech",stk="investor",prio="HIGH")
e(C,"rez_tech","OpenTable","","OpenTable NYC Market Share Analysis",2022,"Booking Holdings","GOV_DOC",era="2020_present",geo="US",themes=["technology","finance"],borough="Citywide",adj="reservation_tech",stk="trader",prio="HIGH")
e(C,"resy_tech","Resy","","Resy (Amex) NYC Platform Report",2023,"American Express","GOV_DOC",era="2020_present",geo="US",themes=["technology","demand"],borough="Citywide",adj="reservation_tech",stk="trader",prio="HIGH")
e(C,"finance","Rabobank","","Rabobank NY Food & Agribusiness Group",2024,"Rabobank","REPORT",era="2020_present",geo="US",themes=["finance","supply"],borough="Citywide",adj="finance",stk="investor",prio="MEDIUM")
e(C,"cmbs","Trepp","","CMBS Restaurant Tenant Exposure NYC",2023,"Trepp","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="investor",prio="MEDIUM")
e(C,"consult","Aaron Allen","","NYC Restaurant Consulting Market",2022,"Aaron Allen","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Citywide",adj="media",stk="trader",prio="LOW")
e(C,"menu","Menu","","NYC Menu Design Firm Landscape",2021,"Industry","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Citywide",adj="media",stk="media",prio="LOW")
e(C,"ingredient","ChefsNYC","","NYC Specialty Ingredient Distributors",2023,"Trade","REPORT",era="2020_present",geo="US",themes=["supply"],borough="Citywide",sub_ind="wholesale",stk="distributor",prio="MEDIUM")
e(C,"uniform","Cintas","","Cintas Restaurant Uniform Services NYC",2022,"Cintas","GOV_DOC",era="2020_present",geo="US",themes=["labor"],borough="Citywide",adj="commercial_equip",stk="trader",prio="LOW")
e(C,"liab","NYSRA","","NY State Restaurant Association Liability Reports",2023,"NYSRA","REPORT",era="2020_present",geo="US",themes=["finance","policy"],borough="Citywide",adj="insurance",stk="NGO",prio="LOW")
e(C,"kitchen_des","NYC","","Commercial Kitchen Build-Out Costs NYC",2022,"Industry","ARTICLE",era="2020_present",geo="US",themes=["finance","technology"],borough="Citywide",adj="commercial_equip",stk="media",prio="MEDIUM")
e(C,"retail_leasing","CBRE","","NYC Retail Brokerage for Restaurant Tenants",2023,"CBRE","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Citywide",adj="real_estate",stk="trader",prio="MEDIUM")
e(C,"pos_square","Square/Block","","Square Hardware Terminal NYC Adoption",2024,"Block","GOV_DOC",era="2020_present",geo="US",themes=["technology"],borough="Citywide",adj="pos_tech",stk="trader",prio="MEDIUM")
e(C,"payments","Clover","","Clover POS NYC Restaurant Installs",2024,"Fiserv Clover","GOV_DOC",era="2020_present",geo="US",themes=["technology"],borough="Citywide",adj="pos_tech",stk="trader",prio="LOW")
e(C,"legal","LLL","","NYC Restaurant Legal Firms Landscape",2023,"Law Firm Ranking","REPORT",era="2020_present",geo="US",themes=["policy","finance"],borough="Citywide",adj="legal",stk="trader",prio="LOW")

# ---- Cat 53: Commodity Exchanges in NYC (10) ----
C = "NYC Exchanges"
e(C,"ice","Intercontinental Exchange","","ICE Futures US (NY) Soft Commodities History",2024,"ICE","GOV_DOC",era="spanning",geo="US",themes=["finance","trade"],borough="Manhattan",adj="finance",stk="investor",prio="FLAGSHIP")
e(C,"nybot","NYBOT","","NY Board of Trade Legacy Coffee Cocoa Sugar OJ",2010,"NYBOT archive","REPORT",era="spanning",geo="US",themes=["finance"],borough="Manhattan",stk="trader",prio="HIGH",bev="coffee")
e(C,"fcoj","Markham","Jerry","Frozen Concentrated OJ Futures History",2002,"J Futures Markets","ARTICLE",era="spanning",geo="US",themes=["finance"],borough="Manhattan",stk="academic",prio="MEDIUM")
e(C,"coffee","ICE","","ICE Coffee C Contract Methodology",2024,"ICE","DATASET_DOC",era="2020_present",geo="US",themes=["finance"],borough="Manhattan",stk="trader",bev="coffee",prio="HIGH")
e(C,"cocoa","ICE","","ICE Cocoa Contract 2024 Crisis",2024,"ICE","REPORT",era="2020_present",geo="US",themes=["finance"],borough="Manhattan",stk="trader",bev="cocoa_chocolate",prio="HIGH")
e(C,"sugar","ICE","","ICE Sugar No. 11 Contract Methodology",2024,"ICE","DATASET_DOC",era="2020_present",geo="US",themes=["finance"],borough="Manhattan",stk="trader",comm="sugar",prio="HIGH")
e(C,"cotton","NY Cotton","","NY Cotton Exchange Legacy",2008,"ICE","REPORT",era="spanning",geo="US",themes=["finance","trade"],borough="Manhattan",stk="trader",prio="LOW")
e(C,"nymex","NYMEX","","NYMEX Food Commodity Futures (legacy)",2008,"CME Group","REPORT",era="spanning",geo="US",themes=["finance"],borough="Manhattan",stk="trader",prio="LOW")
e(C,"cme_migration","CME","","CME/ICE Consolidation and NYC Trading Floor Closures",2016,"CME Group","GOV_DOC",era="2010_2020",geo="US",themes=["finance"],borough="Manhattan",stk="trader",prio="MEDIUM")
e(C,"volatility","Wright","Brian D.","NY Soft-Commodity Futures Volatility 2010s",2018,"Agricultural Finance Review","ARTICLE",era="2010_2020",geo="US",themes=["finance"],borough="Manhattan",stk="academic",prio="MEDIUM")

# ---- Cat 54: NYC Food Startups & Tech (15) ----
C = "NYC Food Startup"
e(C,"blue_apron","Blue Apron","","Blue Apron Founding and 10-K",2023,"Blue Apron","GOV_DOC",era="2010_2020",geo="US",themes=["technology","finance"],borough="Citywide",sub_ind="chain",stk="investor",prio="FLAGSHIP")
e(C,"hellofresh","HelloFresh","","HelloFresh US HQ NYC and 10-K",2023,"HelloFresh","GOV_DOC",era="2010_2020",geo="US",themes=["technology","finance"],borough="Citywide",adj="pos_tech",stk="investor",prio="HIGH")
e(C,"misfits","Misfits Market","","Misfits Market Imperfect Produce Delivery",2022,"Corporate","REPORT",era="2020_present",geo="US",themes=["technology","demand"],borough="Citywide",sub_ind="supermarket",stk="trader",prio="MEDIUM")
e(C,"daily","Daily Harvest","","Daily Harvest Business Model and 2022 Recall",2022,"Corporate","REPORT",era="2020_present",geo="US",themes=["technology"],borough="Citywide",adj="pos_tech",stk="trader",prio="MEDIUM")
e(C,"thrive","Thrive Market","","Thrive Market Grocery Platform",2023,"Corporate","REPORT",era="2020_present",geo="US",themes=["technology","demand"],borough="Citywide",sub_ind="supermarket",stk="trader",prio="MEDIUM")
e(C,"eataly","Eataly","","Eataly NYC Expansion",2024,"Eataly","GOV_DOC",era="2020_present",geo="US",themes=["demand"],borough="Manhattan",sub_ind="specialty_retail",cuisine="italian",stk="foodservice",prio="MEDIUM")
e(C,"ushg","Union Square Hospitality","","Union Square Hospitality Group",2024,"USHG","GOV_DOC",era="2020_present",geo="US",themes=["demand","labor"],borough="Manhattan",sub_ind="fine_dining",stk="foodservice",prio="MEDIUM")
e(C,"vc","Lerer Hippeau","","NYC Food Tech VC Investment Trends",2024,"Lerer","REPORT",era="2020_present",geo="US",themes=["finance","technology"],borough="Citywide",adj="finance",stk="investor",prio="MEDIUM")
e(C,"plated","Plated","","Plated Acquisition by Albertsons",2017,"Albertsons","GOV_DOC",era="2010_2020",geo="US",themes=["finance","technology"],borough="Citywide",adj="pos_tech",stk="investor",prio="LOW")
e(C,"dig","Dig Inn","","Dig Fast-Casual Corporate Growth",2023,"Corporate","REPORT",era="2020_present",geo="US",themes=["demand"],borough="Manhattan",sub_ind="chain",stk="foodservice",prio="LOW")
e(C,"sweetgreen","Sweetgreen","","Sweetgreen NYC Expansion and IPO",2021,"Sweetgreen","GOV_DOC",era="2020_present",geo="US",themes=["finance","demand"],borough="Citywide",sub_ind="chain",stk="investor",prio="MEDIUM")
e(C,"shake_shack","Meyer","Danny","Shake Shack Origins and IPO",2015,"Shake Shack","GOV_DOC",era="2010_2020",geo="US",themes=["demand","finance"],borough="Manhattan",sub_ind="chain",stk="foodservice",prio="HIGH")
e(C,"chef_tech","ChefsFeed","","NYC Chef-Driven Tech Platforms",2022,"Industry","REPORT",era="2020_present",geo="US",themes=["technology"],borough="Citywide",adj="media",stk="media",prio="LOW")
e(C,"alt_protein","Just Salad","","Just Salad NYC Plant-Forward Chain",2023,"Corporate","REPORT",era="2020_present",geo="US",themes=["demand","technology"],borough="Citywide",sub_ind="chain",stk="foodservice",prio="LOW")
e(C,"tech_hist","Columbia","","NYC Food-Tech Sector: A Decade Review",2022,"Columbia Business","REPORT",era="2020_present",geo="US",themes=["technology","finance"],borough="Citywide",adj="pos_tech",stk="academic",prio="MEDIUM")

# ---- Cat 55: NYC Culinary Education (10) ----
C = "NYC Culinary Ed"
e(C,"cia","Culinary Institute of America","","CIA Hyde Park NY: Institutional History",2024,"CIA","REPORT",era="spanning",geo="US",themes=["labor","technology"],borough="Upstate",sub_ind="culinary_school",stk="academic",prio="FLAGSHIP")
e(C,"ice","Institute of Culinary Education","","ICE NYC Program & Alumni Data",2024,"ICE","REPORT",era="spanning",geo="US",themes=["labor"],borough="Manhattan",sub_ind="culinary_school",stk="academic",prio="HIGH")
e(C,"fci","French Culinary Institute","","FCI (now ICE) Legacy",2014,"ICE","REPORT",era="1980_2010",geo="US",themes=["labor"],borough="Manhattan",sub_ind="culinary_school",cuisine="french",stk="academic",prio="MEDIUM")
e(C,"nyu","NYU Steinhardt","","NYU Food Studies Program",2024,"NYU","REPORT",era="2020_present",geo="US",themes=["labor","demand"],borough="Manhattan",sub_ind="culinary_school",stk="academic")
e(C,"cuny","CUNY","","CUNY Food Studies Programs",2024,"CUNY","REPORT",era="2020_present",geo="US",themes=["labor","demand"],borough="Citywide",sub_ind="culinary_school",stk="academic",prio="MEDIUM")
e(C,"beard_ed","James Beard Foundation","","JBF Culinary Scholarship Program",2024,"JBF","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Manhattan",sub_ind="culinary_school",stk="NGO",prio="MEDIUM")
e(C,"tech_school","NYC DOE","","NYC Career and Technical Education Culinary",2023,"NYC DOE","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Citywide",sub_ind="culinary_school",stk="regulator",prio="MEDIUM")
e(C,"apprentice","ACF","","American Culinary Federation NYC Apprenticeship",2024,"ACF","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Citywide",sub_ind="culinary_school",stk="NGO",prio="LOW")
e(C,"pastry","FCI","","French Pastry Arts Programs NYC",2021,"ICE","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Manhattan",sub_ind="culinary_school",cuisine="french",stk="academic",prio="LOW")
e(C,"diversity","NYC Hospitality","","Diversity in NYC Culinary Education 2020-2024",2024,"NYC Hospitality Alliance","REPORT",era="2020_present",geo="US",themes=["labor"],borough="Citywide",sub_ind="culinary_school",stk="NGO",prio="MEDIUM")

# =============================================================================
# PHASE S — v4 GEOGRAPHIC HISTORIES (Cats 56-65, ~150 entries compact)
# =============================================================================

# ---- Cat 56: Pre-Columbian & Indigenous Americas (15) ----
C = "Pre-Columbian"
e(C,"maya","Coe","Michael D.","The Maya",2015,"Thames & Hudson","BOOK",era="pre1900",geo="LatAm",themes=["supply","demand"],prio="FLAGSHIP")
e(C,"aztec","Ortiz de Montellano","Bernard","Aztec Medicine Health and Nutrition",1990,"Rutgers UP","BOOK",era="pre1900",geo="LatAm",themes=["demand","supply"])
e(C,"aztec","Pilcher","Jeffrey","Planet Taco: A Global History of Mexican Food",2012,"Oxford UP","BOOK",era="spanning",geo="LatAm",themes=["demand"],cuisine="mexican")
e(C,"andes","Murra","John","The Economic Organization of the Inca State",1956,"U Chicago","BOOK",era="pre1900",geo="LatAm",themes=["supply","trade"])
e(C,"pueblo","Kennett","Douglas","Chaco Canyon Food Provisioning",2009,"Journal of Archaeological Research","ARTICLE",era="pre1900",geo="US",themes=["supply"],prio="MEDIUM")
e(C,"haudenosaunee","Mt Pleasant","Jane","Three Sisters Agriculture Haudenosaunee",2016,"Agricultural History","ARTICLE",era="spanning",geo="US",themes=["supply","technology"])
e(C,"native_food","Kimmerer","Robin Wall","Braiding Sweetgrass",2013,"Milkweed","BOOK",era="spanning",geo="US",themes=["demand","supply","technology"])
e(C,"native_sov","White","Monica","Freedom Farmers: Agricultural Resistance and the Black Freedom Movement",2018,"UNC Press","BOOK",era="spanning",geo="US",themes=["labor","policy"])
e(C,"maize","Warman","Arturo","Corn and Capitalism: How a Botanical Bastard Grew to Global Dominance",2003,"UNC Press","BOOK",era="spanning",geo="Global",themes=["supply","trade"],comm="cereals")
e(C,"potato","Reader","John","Potato: A History of the Propitious Esculent",2008,"Yale UP","BOOK",era="spanning",geo="Global",themes=["supply","demand"])
e(C,"chocolate","Coe","Sophie","The True History of Chocolate",1996,"Thames & Hudson","BOOK",era="spanning",geo="Global",themes=["supply","trade"],bev="cocoa_chocolate")
e(C,"beans","Nabhan","Gary Paul","Renewing America's Food Traditions",2008,"Chelsea Green","BOOK",era="spanning",geo="US",themes=["supply"],prio="MEDIUM")
e(C,"native_fish","Taylor","Joseph E.","Making Salmon: An Environmental History of the Northwest Fisheries Crisis",1999,"U Washington Press","BOOK",era="spanning",geo="US",themes=["supply","climate"],prio="MEDIUM")
e(C,"corn_recip","Fussell","Betty","The Story of Corn",1992,"Knopf","BOOK",era="spanning",geo="US",themes=["supply","demand"],comm="cereals",prio="MEDIUM")
e(C,"sov_movement","Clark","Danielle","Native American Food Sovereignty Reports",2024,"Intertribal Ag Council","REPORT",era="2020_present",geo="US",themes=["policy","labor"],stk="NGO",prio="MEDIUM")

# ---- Cat 57: Columbian Exchange (15) ----
C = "Columbian Exchange"
e(C,"crosby","Crosby","Alfred W.","The Columbian Exchange: Biological and Cultural Consequences of 1492",1972,"Greenwood","BOOK",era="pre1900",geo="Global",themes=["supply","trade"],prio="FLAGSHIP")
e(C,"crosby","Crosby","Alfred W.","Ecological Imperialism: The Biological Expansion of Europe 900-1900",1986,"Cambridge UP","BOOK",era="pre1900",geo="Global",themes=["supply"])
e(C,"mann","Mann","Charles C.","1491: New Revelations of the Americas Before Columbus",2005,"Knopf","BOOK",era="pre1900",geo="Global",themes=["supply","demand"])
e(C,"mann","Mann","Charles C.","1493: Uncovering the New World Columbus Created",2011,"Knopf","BOOK",era="pre1900",geo="Global",themes=["supply","trade"])
e(C,"mcneill","McNeill","William H.","Plagues and Peoples",1976,"Anchor","BOOK",era="pre1900",geo="Global",themes=["supply"])
e(C,"potato_trans","Salaman","Redcliffe","The History and Social Influence of the Potato",1949,"Cambridge UP","BOOK",era="pre1900",geo="Global",themes=["supply"])
e(C,"sugar_trans","Mintz","Sidney","Sweetness and Power",1985,"Viking","BOOK",era="spanning",geo="Global",themes=["supply","trade"],comm="sugar")
e(C,"maize_europe","Warman","Arturo","Corn Invasion of Europe",2003,"UNC Press","CHAPTER",era="spanning",geo="Europe",themes=["supply"],comm="cereals",prio="MEDIUM")
e(C,"tomato_italy","Gentilcore","David","Pomodoro! A History of the Tomato in Italy",2010,"Columbia UP","BOOK",era="pre1900",geo="Europe",themes=["supply","demand"],cuisine="italian")
e(C,"chili","Andrews","Jean","Peppers: The Domesticated Capsicums",1995,"U Texas Press","BOOK",era="spanning",geo="Global",themes=["supply"])
e(C,"cacao","Off","Carol","Bitter Chocolate",2008,"New Press","BOOK",era="spanning",geo="Global",themes=["supply","trade","labor"],bev="cocoa_chocolate")
e(C,"pineapple","Beauman","Fran","The Pineapple: King of Fruits",2006,"Chatto","BOOK",era="spanning",geo="Global",themes=["supply","trade"],prio="MEDIUM")
e(C,"banana","Koeppel","Dan","Banana: The Fate of the Fruit That Changed the World",2007,"Hudson Street","BOOK",era="spanning",geo="Global",themes=["supply","trade"])
e(C,"coffee_col","Topik","Steven","The Global Coffee Economy",2003,"Cambridge UP","BOOK",era="pre1900",geo="Global",themes=["supply","trade"],bev="coffee")
e(C,"colonial_food","Warman","Arturo","Food and Global Exchange",2000,"Pan-American","CHAPTER",era="pre1900",geo="Global",themes=["supply"],prio="MEDIUM")

# ---- Cat 58: European Food History (20) ----
C = "European Food"
e(C,"flandrin","Flandrin","Jean-Louis","Histoire de l'alimentation",1996,"Fayard","BOOK",era="spanning",geo="Europe",themes=["demand","supply"],prio="FLAGSHIP",lang="fr")
e(C,"montanari","Montanari","Massimo","La fame e l'abbondanza: Storia dell'alimentazione in Europa",1993,"Laterza","BOOK",era="spanning",geo="Europe",themes=["demand","supply"],lang="it")
e(C,"spang","Spang","Rebecca","The Invention of the Restaurant: Paris and Modern Gastronomic Culture",2000,"Harvard UP","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="french")
e(C,"scully","Scully","Terence","The Art of Cookery in the Middle Ages",1995,"Boydell","BOOK",era="pre1900",geo="Europe",themes=["demand"])
e(C,"laudan","Laudan","Rachel","Cuisine and Empire: Cooking in World History",2013,"UC Press","BOOK",era="spanning",geo="Global",themes=["demand","supply"])
e(C,"ferguson","Ferguson","Priscilla Parkhurst","Accounting for Taste: The Triumph of French Cuisine",2004,"U Chicago Press","BOOK",era="spanning",geo="Europe",themes=["demand"],cuisine="french")
e(C,"escoffier","Escoffier","Auguste","Le Guide Culinaire",1903,"Flammarion","BOOK",era="pre1900",geo="Europe",themes=["demand","technology"],cuisine="french",lang="fr")
e(C,"brillat","Brillat-Savarin","Jean Anthelme","Physiologie du goût",1825,"Sautelet","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="french",lang="fr")
e(C,"bocuse","Bocuse","Paul","La Cuisine du Marché",1976,"Flammarion","BOOK",era="1945_1980",geo="Europe",themes=["demand"],cuisine="french",lang="fr",prio="MEDIUM")
e(C,"nouvelle_eur","Gault","Henri","Gault-Millau: A Guide to the New Cuisine",1973,"Gault Millau","REPORT",era="1945_1980",geo="Europe",themes=["demand","media"],cuisine="french",lang="fr",prio="MEDIUM")
e(C,"michelin","Michelin","","Michelin Guide France History 1900-",1900,"Michelin","DATASET_DOC",era="spanning",geo="Europe",themes=["demand","media"],cuisine="french",lang="fr")
e(C,"artusi","Artusi","Pellegrino","La scienza in cucina e l'arte di mangiar bene",1891,"Self-published","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="italian",lang="it")
e(C,"slow_food","Petrini","Carlo","Slow Food: The Case for Taste",2001,"Columbia UP","BOOK",era="1980_2010",geo="Europe",themes=["policy","demand"],cuisine="italian",prio="HIGH")
e(C,"beeton","Beeton","Isabella","Mrs Beeton's Book of Household Management",1861,"S.O. Beeton","BOOK",era="pre1900",geo="Europe",themes=["demand"])
e(C,"david","David","Elizabeth","French Provincial Cooking",1960,"Michael Joseph","BOOK",era="1945_1980",geo="Europe",themes=["demand"],cuisine="french",prio="MEDIUM")
e(C,"grigson","Grigson","Jane","Jane Grigson's Vegetable Book",1978,"Atheneum","BOOK",era="1945_1980",geo="Europe",themes=["demand"],prio="MEDIUM")
e(C,"inao","INAO","","INAO Appellations d'Origine Methodology",2024,"INAO France","DATASET_DOC",era="2020_present",geo="Europe",themes=["policy","supply"],cuisine="french",lang="fr",stk="regulator",bev="wine")
e(C,"dop","DOP Italy","","Italian DOP/IGP Protected Designations",2024,"Italian Ministry","REPORT",era="2020_present",geo="Europe",themes=["policy"],cuisine="italian",lang="it",stk="regulator",prio="MEDIUM")
e(C,"teuteberg","Teuteberg","Hans Jürgen","European Food History Comparative Approach",1992,"Leicester UP","BOOK",era="spanning",geo="Europe",themes=["demand","supply"],lang="de")
e(C,"bnf","BNF","","Bibliothèque nationale de France Food-Trade Archives",2024,"BNF","DATASET_DOC",era="spanning",geo="Europe",themes=["methodology"],lang="fr",stk="academic",prio="MEDIUM")

# ---- Cat 59: French Culinary History (15) ----
C = "French Cuisine"
e(C,"michelin_hist","Harp","Stephen L.","Marketing Michelin: Advertising and Cultural Identity",2001,"Johns Hopkins","BOOK",era="1900_1945",geo="Europe",themes=["demand","media"],cuisine="french",prio="FLAGSHIP")
e(C,"point","Point","Fernand","Ma Gastronomie",1969,"Flammarion","BOOK",era="1945_1980",geo="Europe",themes=["demand"],cuisine="french",lang="fr",prio="HIGH")
e(C,"careme","Carême","Marie-Antoine","Le Pâtissier royal parisien",1815,"Didot","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="french",lang="fr")
e(C,"la_varenne","La Varenne","François Pierre","Le Cuisinier françois",1651,"Paris","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="french",lang="fr",prio="MEDIUM")
e(C,"nouvelle","Mennell","Stephen","All Manners of Food: Eating and Taste in England and France from Middle Ages to Present",1985,"Blackwell","BOOK",era="spanning",geo="Europe",themes=["demand"],cuisine="french")
e(C,"child","Child","Julia","Mastering the Art of French Cooking",1961,"Knopf","BOOK",era="1945_1980",geo="US",themes=["demand","media"],cuisine="french",prio="HIGH")
e(C,"child_tv","Polan","Dana","Julia Child's The French Chef",2011,"Duke UP","BOOK",era="1945_1980",geo="US",themes=["demand","media"],cuisine="french",prio="MEDIUM")
e(C,"ducasse","Ducasse","Alain","Grand Livre de Cuisine",2005,"Ducasse Edition","BOOK",era="1980_2010",geo="Europe",themes=["demand"],cuisine="french",lang="fr",prio="MEDIUM")
e(C,"pic","Pic","Anne-Sophie","Anne-Sophie Pic Restaurant History",2022,"Culinary archive","REPORT",era="2020_present",geo="Europe",themes=["demand"],cuisine="french",prio="LOW")
e(C,"nouvelle_ref","Gopnik","Adam","The Table Comes First: Family France and the Meaning of Food",2011,"Knopf","BOOK",era="2010_2020",geo="Europe",themes=["demand"],cuisine="french",prio="MEDIUM")
e(C,"boucher","Trubek","Amy","Haute Cuisine: How the French Invented the Culinary Profession",2000,"U Pennsylvania Press","BOOK",era="spanning",geo="Europe",themes=["labor","demand"],cuisine="french")
e(C,"hotels","Parkhurst","Priscilla","Paris Fine Dining: 20c Trajectory",2010,"French Historical Studies","ARTICLE",era="1900_1945",geo="Europe",themes=["demand"],cuisine="french",prio="MEDIUM")
e(C,"cookbook","Scappi","Bartolomeo","Opera (16c Italian cookbook)",1570,"Tramezzino","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="italian",lang="it",prio="MEDIUM")
e(C,"ancient","Apicius","","De Re Coquinaria (Roman cookbook)",400,"Classical","BOOK",era="pre1900",geo="Europe",themes=["demand"],lang="other",prio="MEDIUM")
e(C,"new_nordic","Meyer","Claus","Noma: Time and Place in Nordic Cuisine",2010,"Phaidon","BOOK",era="2010_2020",geo="Europe",themes=["demand"],cuisine="nordic",prio="MEDIUM")

# ---- Cat 60: Italian Food Industry (15) ----
C = "Italian Food"
e(C,"parasecoli","Parasecoli","Fabio","Al Dente: A History of Food in Italy",2014,"Reaktion","BOOK",era="spanning",geo="Europe",themes=["demand"],cuisine="italian",prio="FLAGSHIP")
e(C,"petrini","Petrini","Carlo","Slow Food Nation: Why Our Food Should Be Good Clean and Fair",2007,"Rizzoli","BOOK",era="1980_2010",geo="Europe",themes=["demand","policy"],cuisine="italian")
e(C,"marchesi","Marchesi","Gualtiero","Italian Nouvelle Cuisine Legacy",1980,"Various","BOOK",era="1945_1980",geo="Europe",themes=["demand"],cuisine="italian",lang="it",prio="MEDIUM")
e(C,"pasta_hist","Serventi","Silvano","Pasta: The Story of a Universal Food",2002,"Columbia UP","BOOK",era="spanning",geo="Global",themes=["demand","supply"],cuisine="italian")
e(C,"pizza_global","Helstosky","Carol","Pizza: A Global History",2008,"Reaktion","BOOK",era="spanning",geo="Global",themes=["demand"],sub_ind="pizza",cuisine="italian")
e(C,"mozzarella","Parasecoli","Fabio","Mozzarella and Italian PDO",2017,"J Food Culture","ARTICLE",era="2010_2020",geo="Europe",themes=["supply","policy"],cuisine="italian",prio="MEDIUM")
e(C,"parmigiano","Parmigiano","","Parmigiano Reggiano Consortium Industry Report",2024,"Consortium","REPORT",era="2020_present",geo="Europe",themes=["supply","policy"],cuisine="italian",lang="it",stk="producer",comm="dairy")
e(C,"italy_ag","ISMEA","","ISMEA Italian Food Sector Data",2024,"ISMEA","DATASET_DOC",era="2020_present",geo="Europe",themes=["methodology","supply"],cuisine="italian",lang="it",stk="regulator")
e(C,"olive_ital","OlivaliaItaly","","Italian Olive Oil Industry Report",2024,"Italia Olivicola","REPORT",era="2020_present",geo="Europe",themes=["supply"],cuisine="italian",comm="oils",stk="producer")
e(C,"slow_food_us","Slow Food","","Slow Food USA and Italian Influence",2024,"Slow Food","REPORT",era="2020_present",geo="Global",themes=["policy","demand"],cuisine="italian",stk="NGO",prio="MEDIUM")
e(C,"wine_italy","Wine Industry","","Italian DOC/DOCG Wine Appellation Economics",2023,"Vinitaly","REPORT",era="2020_present",geo="Europe",themes=["supply","trade"],bev="wine",cuisine="italian",stk="producer")
e(C,"barilla","Barilla","","Barilla Group Pasta Industry",2024,"Barilla","GOV_DOC",era="2020_present",geo="Europe",themes=["supply","finance"],cuisine="italian",stk="processor")
e(C,"prosciutto","Parma","","Prosciutto di Parma Consortium Report",2024,"Consortium","REPORT",era="2020_present",geo="Europe",themes=["supply"],cuisine="italian",stk="producer",prio="MEDIUM")
e(C,"culatello","Culatello","","Culatello PDO Specification",2023,"Italian","REPORT",era="2020_present",geo="Europe",themes=["supply","policy"],cuisine="italian",lang="it",prio="LOW")
e(C,"mariani_ital","Mariani","John","How Italian Food Conquered the World",2011,"Palgrave","BOOK",era="spanning",geo="US_Global",themes=["demand"],cuisine="italian")

# ---- Cat 61: Chinese Food History (20) ----
C = "Chinese Food"
e(C,"anderson","Anderson","E.N.","The Food of China",1988,"Yale UP","BOOK",era="spanning",geo="Asia",themes=["demand","supply"],cuisine="chinese",prio="FLAGSHIP")
e(C,"sabban","Sabban","Françoise","Chinese Alimentary Culture in Global History",2014,"Annales","ARTICLE",era="spanning",geo="Asia",themes=["demand"],cuisine="chinese",lang="fr")
e(C,"farquhar","Farquhar","Judith","Appetites: Food and Sex in Post-socialist China",2002,"Duke UP","BOOK",era="1980_2010",geo="Asia",themes=["demand"],cuisine="chinese")
e(C,"dunlop","Dunlop","Fuchsia","The Food of Sichuan",2019,"Norton","BOOK",era="2020_present",geo="Asia",themes=["demand"],cuisine="chinese")
e(C,"dunlop2","Dunlop","Fuchsia","Land of Fish and Rice: Recipes from the Culinary Heart of China",2016,"Norton","BOOK",era="2010_2020",geo="Asia",themes=["demand"],cuisine="chinese",prio="HIGH")
e(C,"chang","Chang","K.C.","Food in Chinese Culture: Anthropological and Historical Perspectives",1977,"Yale UP","BOOK",era="spanning",geo="Asia",themes=["demand"],cuisine="chinese")
e(C,"imperial","Knechtges","David","A Literary Feast: Food in Early Chinese Literature",1986,"American Oriental Society","BOOK",era="pre1900",geo="Asia",themes=["demand"],cuisine="chinese",prio="MEDIUM")
e(C,"banquet","Yu","Ying-Shih","Han Chinese Banquet Culture",1977,"in Food in Chinese Culture","CHAPTER",era="pre1900",geo="Asia",themes=["demand"],cuisine="chinese",prio="MEDIUM")
e(C,"cr","Schmalzer","Sigrid","Red Revolution Green Revolution: Scientific Farming in Socialist China",2016,"U Chicago Press","BOOK",era="1945_1980",geo="Asia",themes=["policy","technology"],cuisine="chinese")
e(C,"famine","Dikotter","Frank","Mao's Great Famine",2010,"Walker","BOOK",era="1945_1980",geo="Asia",themes=["supply","policy"],cuisine="chinese",prio="HIGH")
e(C,"tea_china","Rappaport","Erika","A Thirst for Empire: How Tea Shaped the Modern World",2017,"Princeton UP","BOOK",era="spanning",geo="Asia",themes=["trade","demand"],bev="tea")
e(C,"rice_china","Bray","Francesca","The Rice Economies: Technology and Development in Asian Societies",1986,"Blackwell","BOOK",era="spanning",geo="Asia",themes=["supply","technology"],cuisine="chinese",comm="cereals")
e(C,"chopsuey","Chen","Yong","Chop Suey USA: The Story of Chinese Food in America",2014,"Columbia UP","BOOK",era="spanning",geo="US",themes=["demand","labor"],cuisine="chinese")
e(C,"xiaochi","Xu","Wenying","Eating Identities: Reading Food in Asian American Literature",2008,"U Hawaii Press","BOOK",era="spanning",geo="US",themes=["demand"],cuisine="chinese",prio="MEDIUM")
e(C,"regional","Anderson","E.N.","The Food of Southern China",1988,"in Food of China","CHAPTER",era="spanning",geo="Asia",themes=["demand"],cuisine="chinese",prio="MEDIUM")
e(C,"china_modern","Jakes","Aaron","Modern China Food Industry",2021,"Harvard Asia","ARTICLE",era="2020_present",geo="Asia",themes=["supply","demand"],cuisine="chinese",prio="MEDIUM")
e(C,"china_wto","Huang","Jikun","China Agricultural Policy After WTO",2016,"China Economic Review","ARTICLE",era="2010_2020",geo="Asia",themes=["policy","trade"],cuisine="chinese",prio="MEDIUM")
e(C,"china_ag","Rozelle","Scott","Invisible China: How the Urban-Rural Divide Threatens China's Rise",2020,"U Chicago Press","BOOK",era="2020_present",geo="Asia",themes=["demand","policy"],cuisine="chinese")
e(C,"pork_china","Schneider","Mindi","Pig Industry China 2024",2024,"J Peasant Studies","ARTICLE",era="2020_present",geo="Asia",themes=["supply"],comm="meat",cuisine="chinese",prio="MEDIUM")
e(C,"tea_trade","Hohenegger","Beatrice","Liquid Jade: The Story of Tea from East to West",2007,"St Martin's","BOOK",era="spanning",geo="Asia",themes=["trade","demand"],bev="tea",prio="MEDIUM")

# ---- Cat 62: Japanese Food History (15) ----
C = "Japanese Food"
e(C,"rath","Rath","Eric C.","Food and Fantasy in Early Modern Japan",2010,"UC Press","BOOK",era="pre1900",geo="Asia",themes=["demand"],cuisine="japanese",prio="FLAGSHIP")
e(C,"cwiertka","Cwiertka","Katarzyna","Modern Japanese Cuisine: Food Power and National Identity",2006,"Reaktion","BOOK",era="spanning",geo="Asia",themes=["demand","policy"],cuisine="japanese")
e(C,"bestor","Bestor","Theodore C.","Tsukiji: The Fish Market at the Center of the World",2004,"UC Press","BOOK",era="1980_2010",geo="Asia",themes=["supply","trade"],cuisine="japanese",sub_ind="fish_market")
e(C,"sushi_glob","Issenberg","Sasha","The Sushi Economy",2007,"Gotham","BOOK",era="spanning",geo="Global",themes=["supply","trade"],cuisine="japanese")
e(C,"washoku","UNESCO","","Washoku UNESCO Intangible Heritage Designation 2013",2013,"UNESCO","GOV_DOC",era="2010_2020",geo="Asia",themes=["policy","demand"],cuisine="japanese",stk="regulator")
e(C,"izakaya","Sakai","Junko","Izakaya Urban Drinking Culture Japan",2020,"J Japanese Studies","ARTICLE",era="2020_present",geo="Asia",themes=["demand"],cuisine="japanese",sub_ind="bar",lang="ja",prio="MEDIUM")
e(C,"sake","Gauntner","John","The Sake Handbook",2002,"Tuttle","BOOK",era="spanning",geo="Asia",themes=["demand"],cuisine="japanese",bev="spirits",prio="MEDIUM")
e(C,"ramen","Solt","George","The Untold History of Ramen",2014,"UC Press","BOOK",era="spanning",geo="Asia",themes=["demand","supply"],cuisine="japanese")
e(C,"japan_ag","Japan MAFF","","Japan Ministry of Agriculture Food Self-Sufficiency",2024,"MAFF","DATASET_DOC",era="2020_present",geo="Asia",themes=["policy","supply"],cuisine="japanese",lang="ja",stk="regulator",prio="MEDIUM")
e(C,"tea_jp","Rath","Eric","Japan's Cuisines: Food Place and Identity",2016,"Reaktion","BOOK",era="spanning",geo="Asia",themes=["demand"],cuisine="japanese",bev="tea",prio="MEDIUM")
e(C,"kaiseki","Tsuji","Shizuo","Japanese Cooking: A Simple Art",1980,"Kodansha","BOOK",era="spanning",geo="Asia",themes=["demand"],cuisine="japanese")
e(C,"shoku","Cwiertka","Katarzyna","Japanese School Meal Program",2012,"Asia Pacific Food Policy","ARTICLE",era="spanning",geo="Asia",themes=["policy","demand"],cuisine="japanese",prio="MEDIUM")
e(C,"fishery","Makino","Mitsutaku","Fisheries Management in Japan",2011,"Springer","BOOK",era="2010_2020",geo="Asia",themes=["supply","policy"],cuisine="japanese",sub_ind="fish_market")
e(C,"whiskey","Hatten","Tom","Japanese Whiskey Industry",2019,"J Distilling","ARTICLE",era="2010_2020",geo="Asia",themes=["supply","trade"],bev="spirits",cuisine="japanese",prio="MEDIUM")
e(C,"nisshin","Nissin","","Instant Ramen Invention and Global Industry",2024,"Nissin Food Industries","GOV_DOC",era="spanning",geo="Asia",themes=["technology","supply"],cuisine="japanese",prio="MEDIUM")

# ---- Cat 63: Indian Subcontinent Food History (15) ----
C = "Indian Food"
e(C,"achaya","Achaya","K.T.","Indian Food: A Historical Companion",1994,"Oxford UP","BOOK",era="spanning",geo="Asia",themes=["demand","supply"],cuisine="indian",prio="FLAGSHIP")
e(C,"sengupta","Sengupta","Jayanta","Cooking on the Edge: India's Food Culture",2014,"Bloomsbury","BOOK",era="spanning",geo="Asia",themes=["demand"],cuisine="indian")
e(C,"spice","Freedman","Paul","Out of the East: Spices and the Medieval Imagination",2008,"Yale UP","BOOK",era="pre1900",geo="Asia",themes=["trade","demand"])
e(C,"curry","Burton","David","The Raj at Table: A Culinary History of the British in India",1993,"Faber","BOOK",era="pre1900",geo="Asia",themes=["demand","labor"],cuisine="indian",prio="MEDIUM")
e(C,"colonial_tea","Moxham","Roy","Tea: Addiction Exploitation and Empire",2003,"Basic","BOOK",era="pre1900",geo="Asia",themes=["trade","labor"],bev="tea")
e(C,"indian_us","Ray","Krishnendu","Migrant's Table",2004,"Temple UP","BOOK",era="1980_2010",geo="US",themes=["demand","labor"],cuisine="indian")
e(C,"food_security","Drèze","Jean","Hunger and Public Action",1989,"Oxford UP","BOOK",era="1980_2010",geo="Asia",themes=["policy","demand"],cuisine="indian")
e(C,"pds","Khera","Reetika","India's Public Distribution System: Analysis",2011,"Economic and Political Weekly","ARTICLE",era="2010_2020",geo="Asia",themes=["policy","demand"],cuisine="indian",prio="MEDIUM")
e(C,"appadurai","Appadurai","Arjun","Gastro-Politics in Hindu South Asia",1981,"American Ethnologist","ARTICLE",era="1980_2010",geo="Asia",themes=["demand"],cuisine="indian")
e(C,"curry_brit","Collingham","Lizzie","Curry: A Tale of Cooks and Conquerors",2006,"Oxford UP","BOOK",era="spanning",geo="Asia",themes=["demand","trade"],cuisine="indian")
e(C,"india_modern","Patel","Sujata","Modern Indian Food Industry",2018,"Ashgate","BOOK",era="2010_2020",geo="Asia",themes=["demand","supply"],cuisine="indian",prio="MEDIUM")
e(C,"india_export","India Export","","India Rice and Wheat Export Policy 2023",2024,"Indian Ministry","REPORT",era="2020_present",geo="Asia",themes=["trade","policy"],cuisine="indian",lang="hi",stk="regulator",comm="cereals")
e(C,"ghee","Sen","Colleen Taylor","Feasts and Fasts: A History of Food in India",2014,"Reaktion","BOOK",era="spanning",geo="Asia",themes=["demand"],cuisine="indian",prio="MEDIUM")
e(C,"chutney","Janer","Zilkia","Indian-Caribbean Food History",2007,"Food Culture","ARTICLE",era="pre1900",geo="LatAm",themes=["demand"],cuisine="indian",prio="MEDIUM")
e(C,"amul","Amul","","Amul Cooperative Dairy Model",2024,"GCMMF","GOV_DOC",era="spanning",geo="Asia",themes=["supply","policy"],cuisine="indian",comm="dairy",stk="producer")

# ---- Cat 64: Middle East / Ottoman / Persian Food (15) ----
C = "Middle East Food"
e(C,"perry","Perry","Charles","A Baghdad Cookery Book (Kitab al-Tabikh)",2005,"Prospect","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="middle_eastern",prio="FLAGSHIP",lang="ar")
e(C,"roden","Roden","Claudia","A Book of Middle Eastern Food",1968,"Knopf","BOOK",era="1945_1980",geo="Europe",themes=["demand"],cuisine="middle_eastern")
e(C,"roden2","Roden","Claudia","The New Book of Middle Eastern Food",2000,"Knopf","BOOK",era="1980_2010",geo="Global",themes=["demand"],cuisine="middle_eastern")
e(C,"zaouali","Zaouali","Lilia","Medieval Cuisine of the Islamic World",2007,"UC Press","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="middle_eastern",lang="ar")
e(C,"ottoman","Isin","Mary Priscilla","Bountiful Empire: A History of Ottoman Cuisine",2018,"Reaktion","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="middle_eastern")
e(C,"persian","Batmanglij","Najmieh","Food of Life: A Book of Ancient Persian and Modern Iranian Cooking",2011,"Mage","BOOK",era="spanning",geo="Europe",themes=["demand"],cuisine="middle_eastern")
e(C,"lev","Helou","Anissa","Feast: Food of the Islamic World",2018,"Ecco","BOOK",era="spanning",geo="Global",themes=["demand"],cuisine="levantine")
e(C,"zubaida","Zubaida","Sami","A Taste of Thyme: Culinary Cultures of the Middle East",1994,"Tauris","BOOK",era="spanning",geo="Europe",themes=["demand"],cuisine="middle_eastern")
e(C,"hummus","Ariel","Ari","Hummus: A Global History",2012,"Reaktion","BOOK",era="spanning",geo="Global",themes=["demand"],cuisine="middle_eastern",prio="MEDIUM")
e(C,"coffee_ot","Hattox","Ralph S.","Coffee and Coffeehouses: Origins of a Social Beverage in Medieval Near East",1985,"U Washington Press","BOOK",era="pre1900",geo="Europe",themes=["demand"],bev="coffee",cuisine="middle_eastern")
e(C,"levan","Nasrallah","Nawal","Annals of the Caliphs' Kitchens: Ibn Sayyar al-Warraq's Tenth-Century Baghdadi Cookbook",2007,"Brill","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="middle_eastern",lang="ar",prio="MEDIUM")
e(C,"sumaq","Shaida","Margaret","The Legendary Cuisine of Persia",2000,"Interlink","BOOK",era="spanning",geo="Europe",themes=["demand"],cuisine="middle_eastern",prio="MEDIUM")
e(C,"meze","Ottolenghi","Yotam","Jerusalem: A Cookbook",2012,"Ten Speed","BOOK",era="2010_2020",geo="Europe",themes=["demand"],cuisine="middle_eastern",prio="MEDIUM")
e(C,"saffron","Willan","Anne","Saffron: A Global Crop History",2020,"Reaktion","CHAPTER",era="spanning",geo="Global",themes=["supply","trade"],cuisine="middle_eastern",prio="MEDIUM")
e(C,"leban","Greene","Julie","Lebanese Diaspora Food Economy",2019,"Food Culture","ARTICLE",era="2010_2020",geo="Global",themes=["demand","labor"],cuisine="levantine",prio="MEDIUM")

# ---- Cat 65: African Food History (15) ----
C = "African Food"
e(C,"carney","Carney","Judith","Black Rice: The African Origins of Rice Cultivation in the Americas",2001,"Harvard UP","BOOK",era="pre1900",geo="Africa",themes=["supply","labor"],prio="FLAGSHIP",comm="cereals")
e(C,"mccann","McCann","James","Stirring the Pot: A History of African Cuisine",2009,"Ohio UP","BOOK",era="spanning",geo="Africa",themes=["demand","supply"])
e(C,"maize_africa","McCann","James","Maize and Grace: Africa's Encounter with a New World Crop 1500-2000",2005,"Harvard UP","BOOK",era="pre1900",geo="Africa",themes=["supply","trade"],comm="cereals")
e(C,"harris_jb","Harris","Jessica B.","High on the Hog: A Culinary Journey from Africa to America",2011,"Bloomsbury","BOOK",era="spanning",geo="US",themes=["demand"])
e(C,"slave_food","Twitty","Michael W.","The Cooking Gene: A Journey Through African American Culinary History",2017,"Amistad","BOOK",era="spanning",geo="US",themes=["demand","labor"])
e(C,"ossooasare","Osseo-Asare","Fran","Food Culture in Sub-Saharan Africa",2005,"Greenwood","BOOK",era="spanning",geo="Africa",themes=["demand"])
e(C,"ethiopia","McCann","James","People of the Plow: Ethiopian Agriculture 1800-1990",1995,"U Wisconsin Press","BOOK",era="pre1900",geo="Africa",themes=["supply"],comm="cereals",prio="MEDIUM")
e(C,"west_africa","Grivetti","Louis E.","West African Staple Foods",1993,"Ecology of Food and Nutrition","ARTICLE",era="spanning",geo="Africa",themes=["demand","supply"],prio="MEDIUM")
e(C,"famine_af","Devereux","Stephen","Theories of Famine",1993,"Harvester","BOOK",era="1980_2010",geo="Africa",themes=["supply","policy"])
e(C,"african_urban","Battersby","Jane","Urban Food Systems Governance in Africa",2021,"Springer","BOOK",era="2020_present",geo="Africa",themes=["supply","policy"])
e(C,"coffee_eth","Sedgewick","Augustine","Coffeeland: One Man's Dark Empire and the Making of Our Favorite Drug",2020,"Penguin","BOOK",era="spanning",geo="Global",themes=["trade","labor"],bev="coffee",prio="HIGH")
e(C,"palm_africa","Lynn","Martin","Commerce and Economic Change in West Africa: The Palm Oil Trade",1997,"Cambridge UP","BOOK",era="pre1900",geo="Africa",themes=["trade","supply"],comm="oils",prio="MEDIUM")
e(C,"african_union","AU","","African Union Continental Free Trade Area Food Chapters",2024,"AU","REPORT",era="2020_present",geo="Africa",themes=["trade","policy"],stk="regulator",prio="MEDIUM")
e(C,"afcfta","Songwe","Vera","AfCFTA Agricultural Trade Implications",2021,"UNECA","REPORT",era="2020_present",geo="Africa",themes=["trade","policy"],stk="regulator",prio="MEDIUM")
e(C,"land_grab","Cotula","Lorenzo","Land Grabs in Africa Post-2008",2013,"Zed","BOOK",era="2010_2020",geo="Africa",themes=["policy","supply"],prio="MEDIUM")

# =============================================================================
# PHASE T — CORPORATE HISTORIES (Cats 66-75) — ~15/cat
# =============================================================================

# ---- Cat 66: ABCD Commodity Traders (15) ----
C = "ABCD Traders"
e(C,"morgan","Morgan","Dan","Merchants of Grain",1979,"Viking","BOOK",era="spanning",geo="Global",themes=["trade","supply"],stk="trader",prio="FLAGSHIP")
e(C,"cargill","Broehl","Wayne","Cargill: Trading the World's Grain",1992,"Dartmouth","BOOK",era="spanning",geo="Global",themes=["trade","supply"],stk="trader")
e(C,"cargill","Broehl","Wayne","Cargill: Going Global",1998,"Dartmouth","BOOK",era="1980_2010",geo="Global",themes=["trade"],stk="trader")
e(C,"kneen","Kneen","Brewster","Invisible Giant: Cargill and Its Transnational Strategies",2002,"Pluto","BOOK",era="1980_2010",geo="Global",themes=["trade","labor"],stk="trader")
e(C,"adm","Eichenwald","Kurt","The Informant: A True Story (ADM lysine price fixing)",2000,"Broadway","BOOK",era="1980_2010",geo="US",themes=["trade","finance"],stk="trader")
e(C,"bunge","Fornari","Hugo","Bunge Corporate History",2008,"Self-published","BOOK",era="spanning",geo="Global",themes=["trade"],stk="trader",prio="MEDIUM")
e(C,"ldc","LDC","","Louis Dreyfus Company Corporate Overview",2024,"LDC","GOV_DOC",era="2020_present",geo="Global",themes=["trade"],stk="trader")
e(C,"abcd","Murphy","Sophia","Cereal Secrets: The World's Largest Grain Traders and Global Agriculture",2012,"Oxfam","REPORT",era="2010_2020",geo="Global",themes=["trade","policy"],stk="NGO",prio="HIGH")
e(C,"cargill_meat","Cargill","","Cargill Meat Solutions Corporate",2024,"Cargill","GOV_DOC",era="2020_present",geo="US",themes=["supply"],comm="meat",stk="processor")
e(C,"ukraine","Glauber","Joseph","Grain Trader Response to Ukraine War",2023,"IFPRI","REPORT",era="2020_present",geo="Global",themes=["trade","supply"],stk="academic")
e(C,"wilmar","Wilmar","","Wilmar International: Asian ABCD-Rival",2024,"Wilmar","GOV_DOC",era="2020_present",geo="Asia",themes=["trade"],stk="trader",prio="MEDIUM")
e(C,"cofco","COFCO","","COFCO International Corporate",2024,"COFCO","GOV_DOC",era="2020_present",geo="Asia",themes=["trade"],stk="trader",lang="zh",prio="MEDIUM")
e(C,"adm_10k","ADM","","ADM 10-K 2023",2023,"Archer Daniels Midland","GOV_DOC",era="2020_present",geo="US",themes=["finance","trade"],stk="investor",prio="HIGH")
e(C,"bunge_10k","Bunge","","Bunge 10-K 2023",2023,"Bunge","GOV_DOC",era="2020_present",geo="Global",themes=["finance","trade"],stk="investor",prio="MEDIUM")
e(C,"grain_consol","Schutter","Olivier De","The Financial Monopolization of Agriculture",2019,"UN Rapporteur","REPORT",era="2010_2020",geo="Global",themes=["trade","policy"],stk="regulator",prio="MEDIUM")

# ---- Cat 67: Global Food Manufacturers (15) ----
C = "Global Manufacturers"
e(C,"nestle","Nestle","","Nestlé Annual Report 2023",2023,"Nestlé","GOV_DOC",era="2020_present",geo="Global",themes=["finance","supply"],stk="processor",prio="FLAGSHIP")
e(C,"unilever","Unilever","","Unilever Annual Report 2023",2023,"Unilever","GOV_DOC",era="2020_present",geo="Global",themes=["finance","supply"],stk="processor")
e(C,"pepsico","PepsiCo","","PepsiCo 10-K 2023",2023,"PepsiCo","GOV_DOC",era="2020_present",geo="US",themes=["finance","supply"],stk="processor")
e(C,"kraft","Kraft Heinz","","Kraft Heinz 10-K 2023",2023,"Kraft Heinz","GOV_DOC",era="2020_present",geo="US",themes=["finance"],stk="processor")
e(C,"mondelez","Mondelez","","Mondelez International 10-K 2023",2023,"Mondelez","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],stk="processor")
e(C,"mars","Brenner","Joel","The Emperors of Chocolate: Inside the Secret World of Hershey and Mars",1999,"Broadway","BOOK",era="spanning",geo="US_Global",themes=["finance","supply"],bev="cocoa_chocolate",stk="processor")
e(C,"nestle_history","Heer","Jean","World Events 1866-1966: The First Hundred Years of Nestlé",1966,"Nestlé","BOOK",era="spanning",geo="Global",themes=["finance","supply"],stk="processor",prio="MEDIUM")
e(C,"kellogg","Bruce","Scott","Cerealizing America: Kellogg and Post",2001,"Faber","BOOK",era="spanning",geo="US",themes=["supply","demand"],stk="processor",comm="cereals")
e(C,"general_mills","General Mills","","General Mills 10-K 2023",2023,"General Mills","GOV_DOC",era="2020_present",geo="US",themes=["finance"],stk="processor")
e(C,"nestle_formula","Muller","Mike","The Baby Killer: Nestlé Infant Formula Scandal",1974,"War on Want","REPORT",era="1945_1980",geo="Africa",themes=["policy"],stk="NGO",prio="HIGH")
e(C,"danone","Danone","","Danone Annual Report 2023",2023,"Danone","GOV_DOC",era="2020_present",geo="Europe",themes=["finance"],stk="processor",comm="dairy",lang="fr")
e(C,"tyson","Tyson","","Tyson Foods 10-K 2023",2023,"Tyson","GOV_DOC",era="2020_present",geo="US",themes=["finance","supply"],comm="meat",stk="processor")
e(C,"jbs","JBS","","JBS USA 10-K 2023 (NYSE listing)",2023,"JBS","GOV_DOC",era="2020_present",geo="LatAm",themes=["finance","supply"],comm="meat",stk="processor")
e(C,"smithfield","Smithfield","","Smithfield Foods Under WH Group China",2024,"WH Group","GOV_DOC",era="2020_present",geo="Global",themes=["finance","trade"],comm="meat",stk="processor")
e(C,"perdue","Perdue","","Perdue Farms Corporate",2024,"Perdue","GOV_DOC",era="2020_present",geo="US",themes=["supply"],comm="meat",stk="processor",prio="MEDIUM")

# ---- Cat 68: Coca-Cola & PepsiCo (10) ----
C = "Beverage Giants"
e(C,"pendergrast","Pendergrast","Mark","For God Country and Coca-Cola",2000,"Basic","BOOK",era="spanning",geo="US_Global",themes=["finance","supply"],bev="soda",stk="processor",prio="FLAGSHIP")
e(C,"coke_10k","Coca-Cola","","Coca-Cola Company 10-K 2023",2023,"Coca-Cola","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],bev="soda",stk="investor")
e(C,"pepsi_hist","Louis","J.C.","Pepsi-Cola Story",1980,"PepsiCo","BOOK",era="spanning",geo="US",themes=["finance"],bev="soda",stk="processor")
e(C,"cola_wars","Enrico","Roger","The Other Guy Blinked: How Pepsi Won the Cola Wars",1986,"Bantam","BOOK",era="1980_2010",geo="US",themes=["finance","demand"],bev="soda",stk="processor")
e(C,"soda_tax","Silver","Lynn","Berkeley Soda Tax Evaluation",2017,"PLoS Medicine","ARTICLE",era="2010_2020",geo="US",themes=["policy","demand"],bev="soda")
e(C,"cola_global","Foster","Robert","Coca-Globalization: Following Soft Drinks from NY to NG",2008,"Palgrave","BOOK",era="1980_2010",geo="Global",themes=["demand","trade"],bev="soda")
e(C,"pepsi_10k","PepsiCo","","PepsiCo 10-K 2023",2023,"PepsiCo","GOV_DOC",era="2020_present",geo="US",themes=["finance"],bev="soda",stk="investor")
e(C,"dr_pepper","Rodengen","Jeffrey","Legend of Dr Pepper/Seven-Up",1995,"Write Stuff","BOOK",era="spanning",geo="US",themes=["finance"],bev="soda",stk="processor",prio="LOW")
e(C,"red_bull","Grainger","Jeff","Red Bull Energy Drink Industry",2018,"J Consumer Culture","ARTICLE",era="2010_2020",geo="Global",themes=["demand"],bev="soda",prio="MEDIUM")
e(C,"obesity_bev","Popkin","Barry","Sweetening Global Diet",2016,"Lancet","ARTICLE",era="2010_2020",geo="Global",themes=["demand","policy"],bev="soda")

# ---- Cat 69: QSR Industry (15) ----
C = "QSR Industry"
e(C,"mcd_love","Love","John","McDonald's: Behind the Arches",1986,"Bantam","BOOK",era="spanning",geo="US",themes=["finance","supply"],sub_ind="chain",stk="processor",prio="FLAGSHIP")
e(C,"mcd_kroc","Kroc","Ray","Grinding It Out: The Making of McDonald's",1977,"Regnery","BOOK",era="1945_1980",geo="US",themes=["finance"],sub_ind="chain",stk="processor")
e(C,"schlosser","Schlosser","Eric","Fast Food Nation",2001,"Houghton","BOOK",era="1980_2010",geo="US",themes=["labor","demand"],sub_ind="chain",stk="media")
e(C,"mcd_10k","McDonald's","","McDonald's 10-K 2023",2023,"McDonald's","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],sub_ind="chain",stk="investor")
e(C,"starbucks","Schultz","Howard","Pour Your Heart Into It: How Starbucks Built a Company",1997,"Hyperion","BOOK",era="1980_2010",geo="US",themes=["finance","demand"],bev="coffee",sub_ind="chain",stk="processor")
e(C,"starbucks_10k","Starbucks","","Starbucks 10-K 2023",2023,"Starbucks","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],bev="coffee",sub_ind="chain",stk="investor")
e(C,"yum","Yum Brands","","Yum! Brands 10-K 2023",2023,"Yum","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],sub_ind="chain",stk="investor")
e(C,"chipotle","Chipotle","","Chipotle 10-K 2023",2023,"Chipotle","GOV_DOC",era="2020_present",geo="US",themes=["finance"],sub_ind="chain",stk="investor")
e(C,"subway","Subway","","Subway Corporate Turnaround 2023",2023,"Subway","GOV_DOC",era="2020_present",geo="US",themes=["finance"],sub_ind="chain",stk="investor",prio="MEDIUM")
e(C,"dominos","Domino's","","Domino's Pizza 10-K 2023",2023,"Domino's","GOV_DOC",era="2020_present",geo="US",themes=["finance","technology"],sub_ind="chain",cuisine="italian",stk="investor",prio="MEDIUM")
e(C,"chik","Chick-fil-A","","Chick-fil-A Corporate Overview",2024,"Chick-fil-A","GOV_DOC",era="2020_present",geo="US",themes=["finance"],sub_ind="chain",comm="meat",stk="processor",prio="MEDIUM")
e(C,"labor_qsr","Jayaraman","Saru","Fast Food Labor Conditions",2019,"ROC","REPORT",era="2010_2020",geo="US",themes=["labor"],sub_ind="chain",stk="NGO")
e(C,"white_castle","Hogan","David","Selling 'em by the Sack: White Castle and the Creation of American Food",1997,"NYU Press","BOOK",era="spanning",geo="US",themes=["demand"],sub_ind="chain",stk="processor",prio="MEDIUM")
e(C,"panera","Panera","","Panera Bread Corporate History",2024,"Panera","GOV_DOC",era="2020_present",geo="US",themes=["finance"],sub_ind="chain",stk="investor",prio="MEDIUM")
e(C,"taco_bell","Creasey","Steve","Taco Bell: History of a Chain",2015,"Self","BOOK",era="spanning",geo="US",themes=["demand"],cuisine="mexican",sub_ind="chain",stk="processor",prio="MEDIUM")

# ---- Cat 70: Supermarket Multinationals (12) ----
C = "Supermarket Multis"
e(C,"walmart","Lichtenstein","Nelson","The Retail Revolution: How Wal-Mart Created a Brave New World",2009,"Metropolitan","BOOK",era="1980_2010",geo="Global",themes=["supply","demand"],sub_ind="supermarket",prio="FLAGSHIP")
e(C,"walmart_10k","Walmart","","Walmart 10-K 2024",2024,"Walmart","GOV_DOC",era="2020_present",geo="Global",themes=["finance","supply"],sub_ind="supermarket",stk="investor")
e(C,"costco","Costco","","Costco 10-K 2023",2023,"Costco","GOV_DOC",era="2020_present",geo="US_Global",themes=["finance"],sub_ind="supermarket",stk="investor")
e(C,"tesco","Tesco","","Tesco PLC Annual Report 2023",2023,"Tesco","GOV_DOC",era="2020_present",geo="Europe",themes=["finance"],sub_ind="supermarket",stk="investor",lang="en")
e(C,"carrefour","Carrefour","","Carrefour Group Annual Report 2023",2023,"Carrefour","GOV_DOC",era="2020_present",geo="Europe",themes=["finance","supply"],sub_ind="supermarket",lang="fr",stk="investor")
e(C,"aldi","Aldi","","Aldi Nord/Süd Corporate Structure",2024,"Aldi","GOV_DOC",era="2020_present",geo="Europe",themes=["finance"],sub_ind="supermarket",lang="de",stk="investor",prio="MEDIUM")
e(C,"lidl","Schwarz","","Lidl (Schwarz Gruppe) Corporate",2024,"Schwarz","GOV_DOC",era="2020_present",geo="Europe",themes=["finance"],sub_ind="supermarket",lang="de",stk="investor",prio="MEDIUM")
e(C,"kroger","Kroger","","Kroger 10-K 2023",2023,"Kroger","GOV_DOC",era="2020_present",geo="US",themes=["finance"],sub_ind="supermarket",stk="investor")
e(C,"retail_rev","Deutsch","Tracey","Building a Housewife's Paradise: Gender Politics American Grocery Stores",2010,"UNC Press","BOOK",era="1900_1945",geo="US",themes=["labor","demand"],sub_ind="supermarket")
e(C,"reardon_super","Reardon","Thomas","Rise of Supermarkets in Developing Regions",2003,"AJAE","ARTICLE",era="1980_2010",geo="Global",themes=["supply","demand"],sub_ind="supermarket")
e(C,"amazon_wf","Amazon","","Amazon Whole Foods Acquisition 2017",2017,"Amazon","GOV_DOC",era="2010_2020",geo="US",themes=["finance","technology"],sub_ind="supermarket",stk="investor")
e(C,"china_retail","Reardon","Thomas","Food Retail in China",2018,"China Ag Econ Review","ARTICLE",era="2010_2020",geo="Asia",themes=["supply","demand"],sub_ind="supermarket",lang="zh",prio="MEDIUM")

# ---- Cat 71: Foodservice Distributors (10) ----
C = "FS Distributors"
e(C,"sysco","Sysco","","Sysco 10-K 2024",2024,"Sysco","GOV_DOC",era="2020_present",geo="US",themes=["finance","supply"],sub_ind="wholesale",stk="distributor",prio="FLAGSHIP")
e(C,"us_foods","US Foods","","US Foods 10-K 2023",2023,"US Foods","GOV_DOC",era="2020_present",geo="US",themes=["finance","supply"],sub_ind="wholesale",stk="distributor")
e(C,"pfg","PFG","","Performance Food Group 10-K 2023",2023,"PFG","GOV_DOC",era="2020_present",geo="US",themes=["finance"],sub_ind="wholesale",stk="distributor")
e(C,"gfs","Gordon","","Gordon Food Service Corporate",2024,"GFS","GOV_DOC",era="2020_present",geo="US",themes=["supply"],sub_ind="wholesale",stk="distributor",prio="MEDIUM")
e(C,"sysco_hist","Love","John F.","Sysco: A History",2003,"Corporate","BOOK",era="spanning",geo="US",themes=["supply"],sub_ind="wholesale",stk="distributor",prio="MEDIUM")
e(C,"broadline","Industry Research","","Broadline Foodservice Distribution Market Share",2023,"Technomic","REPORT",era="2020_present",geo="US",themes=["supply"],sub_ind="wholesale",stk="media",prio="MEDIUM")
e(C,"cash_carry","Restaurant Depot","","Restaurant Depot/Jetro Cash & Carry Model",2023,"Corporate","REPORT",era="2020_present",geo="US",themes=["supply"],sub_ind="wholesale",stk="distributor",prio="MEDIUM")
e(C,"dairy_dist","Dean Foods","","Dean Foods Bankruptcy 2019 and Dairy Distribution",2019,"GOV","GOV_DOC",era="2010_2020",geo="US",themes=["finance","supply"],comm="dairy",sub_ind="wholesale",stk="distributor",prio="MEDIUM")
e(C,"meat_dist","Cargill Meat","","Meat Distribution Chain Cargill",2024,"Cargill","GOV_DOC",era="2020_present",geo="US",themes=["supply"],comm="meat",sub_ind="wholesale",stk="distributor",prio="MEDIUM")
e(C,"specialty_dist","Cheney Brothers","","Regional FS Distributors Landscape",2023,"Industry","REPORT",era="2020_present",geo="US",themes=["supply"],sub_ind="wholesale",stk="distributor",prio="LOW")

# ---- Cat 72: Seed & Biotech Corporates (12) ----
C = "Seed Biotech"
e(C,"monsanto","Charles","Daniel","Lords of the Harvest: Biotech Big Money and the Future of Food",2001,"Perseus","BOOK",era="1980_2010",geo="Global",themes=["technology","finance"],stk="processor",prio="FLAGSHIP")
e(C,"bayer","Bayer","","Bayer AG Post-Monsanto Merger Annual Report",2024,"Bayer","GOV_DOC",era="2020_present",geo="Europe",themes=["finance","technology"],lang="de",stk="investor")
e(C,"corteva","Corteva","","Corteva Agriscience 10-K 2023",2023,"Corteva","GOV_DOC",era="2020_present",geo="US",themes=["finance","technology"],stk="investor")
e(C,"syngenta","Syngenta","","Syngenta (ChemChina) Corporate",2024,"Syngenta","GOV_DOC",era="2020_present",geo="Asia",themes=["technology"],lang="zh",stk="investor")
e(C,"limagrain","Limagrain","","Groupe Limagrain Annual Report",2024,"Limagrain","GOV_DOC",era="2020_present",geo="Europe",themes=["technology"],lang="fr",stk="processor",prio="MEDIUM")
e(C,"shiva","Shiva","Vandana","Stolen Harvest: The Hijacking of the Global Food Supply",2000,"South End","BOOK",era="1980_2010",geo="Asia",themes=["technology","policy"],stk="NGO")
e(C,"gmo_labor","Schurman","Rachel","Fighting for the Future of Food: Activists versus Agribusiness in the Struggle over Biotechnology",2010,"U Minnesota Press","BOOK",era="1980_2010",geo="Global",themes=["technology","policy"])
e(C,"crispr","Wolt","Jeffrey","Regulatory Status of Genome-Edited Crops",2016,"Plant Biotech Journal","ARTICLE",era="2010_2020",geo="US_Global",themes=["technology","policy"])
e(C,"bayer_lawsuit","Bloomberg","","Bayer Roundup Liability Settlement 2020-2024",2024,"Bloomberg","ARTICLE",era="2020_present",geo="US",themes=["policy","finance"],stk="media",prio="MEDIUM")
e(C,"pioneer","Fitzgerald","Deborah","Pioneer Hi-Bred and Hybrid Corn",1990,"Cornell UP","BOOK",era="spanning",geo="US",themes=["technology"],comm="cereals",prio="MEDIUM")
e(C,"seeds_conc","ETC Group","","Seed Industry Concentration: ETC 2020",2020,"ETC Group","REPORT",era="2020_present",geo="Global",themes=["technology","policy"],stk="NGO",prio="MEDIUM")
e(C,"gmo_econ","Qaim","Matin","Economic Impact of GMOs Global Review",2020,"AJAE","ARTICLE",era="2020_present",geo="Global",themes=["technology","supply"])

# ---- Cat 73: Fertilizer & Agchem (10) ----
C = "Fertilizer Industry"
e(C,"nutrien","Nutrien","","Nutrien 10-K 2023 (world's largest fertilizer)",2023,"Nutrien","GOV_DOC",era="2020_present",geo="US_Global",themes=["finance","supply"],stk="investor",prio="FLAGSHIP")
e(C,"mosaic","Mosaic","","Mosaic Company 10-K 2023",2023,"Mosaic","GOV_DOC",era="2020_present",geo="US",themes=["finance"],stk="investor")
e(C,"yara","Yara","","Yara International Annual Report 2023",2023,"Yara","GOV_DOC",era="2020_present",geo="Europe",themes=["finance","supply"],lang="other",stk="investor")
e(C,"cf","CF Industries","","CF Industries 10-K 2023",2023,"CF","GOV_DOC",era="2020_present",geo="US",themes=["finance"],stk="investor")
e(C,"basf","BASF","","BASF Agricultural Solutions",2024,"BASF","GOV_DOC",era="2020_present",geo="Europe",themes=["technology"],lang="de",stk="processor")
e(C,"fertilizer_crisis","Baffes","John","2022 Fertilizer Shock",2022,"World Bank","REPORT",era="2020_present",geo="Global",themes=["supply","finance"],stk="regulator",prio="HIGH")
e(C,"potash","Potash","","Potash Industry Belarus Sanctions 2022",2022,"World Bank","REPORT",era="2020_present",geo="Europe",themes=["trade","supply"],stk="regulator",prio="MEDIUM")
e(C,"phosphate","Cordell","Dana","Peak Phosphorus: Clarifying the Key Issues",2009,"Global Environmental Change","ARTICLE",era="1980_2010",geo="Global",themes=["supply","climate"],prio="MEDIUM")
e(C,"organic_fert","Rodale","J.I.","Organic Farming Natural Fertilization",1961,"Rodale","BOOK",era="1945_1980",geo="US",themes=["technology","supply"],stk="producer",prio="MEDIUM")
e(C,"nitrogen","Smil","Vaclav","Enriching the Earth: Fritz Haber Carl Bosch and the Transformation of World Food Production",2001,"MIT Press","BOOK",era="spanning",geo="Global",themes=["technology","supply"])

# ---- Cat 74: Farm Machinery (10) ----
C = "Farm Machinery"
e(C,"deere","Broehl","Wayne","John Deere's Company: A History of Deere & Company",1984,"Doubleday","BOOK",era="spanning",geo="US",themes=["technology","finance"],stk="processor",prio="FLAGSHIP")
e(C,"deere_10k","Deere","","Deere & Company 10-K 2023",2023,"Deere","GOV_DOC",era="2020_present",geo="US_Global",themes=["finance"],stk="investor")
e(C,"cnh","CNH","","CNH Industrial Annual Report 2023",2023,"CNH","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],stk="investor",prio="MEDIUM")
e(C,"kubota","Kubota","","Kubota Corporation Annual Report 2023",2023,"Kubota","GOV_DOC",era="2020_present",geo="Asia",themes=["finance","technology"],lang="ja",stk="investor")
e(C,"agco","AGCO","","AGCO Corporation 10-K 2023",2023,"AGCO","GOV_DOC",era="2020_present",geo="US",themes=["finance"],stk="investor",prio="MEDIUM")
e(C,"mccormick","McCormick","Cyrus","Cyrus McCormick and the Reaper (biography)",1931,"Harper","BOOK",era="pre1900",geo="US",themes=["technology"],stk="producer",prio="MEDIUM")
e(C,"combines","Macmillan","Don","The Big Book of John Deere Tractors",2007,"Voyageur","BOOK",era="spanning",geo="US",themes=["technology"],stk="media",prio="LOW")
e(C,"precision","Deere","","Deere Precision Ag Technology Roadmap",2024,"Deere","REPORT",era="2020_present",geo="US",themes=["technology"],stk="processor")
e(C,"right_to_repair","NY Times","","Farmers' Right-to-Repair Deere Equipment",2023,"NYT","ARTICLE",era="2020_present",geo="US",themes=["technology","policy"],stk="media",prio="MEDIUM")
e(C,"tractor_asia","Asian Farm Equipment","","Farm Machinery Industry in Asia",2022,"Industry","REPORT",era="2020_present",geo="Asia",themes=["technology"],lang="zh",stk="media",prio="LOW")

# ---- Cat 75: Flavor & Fragrance (10) ----
C = "Flavor Fragrance"
e(C,"burr","Burr","Chandler","The Emperor of Scent",2002,"Random House","BOOK",era="1980_2010",geo="Global",themes=["technology","demand"],stk="processor",prio="FLAGSHIP")
e(C,"givaudan","Givaudan","","Givaudan Annual Report 2023",2023,"Givaudan","GOV_DOC",era="2020_present",geo="Europe",themes=["finance","technology"],lang="fr",stk="investor")
e(C,"iff","IFF","","International Flavors & Fragrances 10-K 2023",2023,"IFF","GOV_DOC",era="2020_present",geo="US_Global",themes=["finance","technology"],stk="investor")
e(C,"symrise","Symrise","","Symrise Annual Report 2023",2023,"Symrise","GOV_DOC",era="2020_present",geo="Europe",themes=["finance"],lang="de",stk="investor",prio="MEDIUM")
e(C,"firmenich","Firmenich","","Firmenich Annual Report 2023",2023,"Firmenich","GOV_DOC",era="2020_present",geo="Europe",themes=["finance"],lang="fr",stk="investor",prio="MEDIUM")
e(C,"turin","Turin","Luca","The Secret of Scent: Adventures in Perfume and the Science of Smell",2006,"Ecco","BOOK",era="1980_2010",geo="Global",themes=["technology"])
e(C,"natural_flavors","Khan","Gulab","Natural Flavors Industry Regulation",2020,"Food Science","ARTICLE",era="2020_present",geo="US",themes=["technology","policy"],prio="MEDIUM")
e(C,"flavor_price","Sensient","","Sensient Technologies Flavor Pricing Trends",2023,"Sensient","GOV_DOC",era="2020_present",geo="US",themes=["supply"],stk="processor",prio="MEDIUM")
e(C,"vanilla","Karen","Tricia","Vanilla Economics Madagascar",2020,"J Ag Econ","ARTICLE",era="2020_present",geo="Africa",themes=["supply","trade"],prio="MEDIUM")
e(C,"msg","Sand","Jordan","MSG: Chinese Restaurant Syndrome and Food Racism",2005,"Gastronomica","ARTICLE",era="1945_1980",geo="US",themes=["demand","technology"],cuisine="chinese",prio="MEDIUM")

# =============================================================================
# PHASE U — SUB-INDUSTRY DEEP DIVES (Cats 76-90) — ~12/cat
# =============================================================================

# ---- Cat 76: Wine Industry Economics (15) ----
C = "Wine Industry"
e(C,"ashenfelter","Ashenfelter","Orley","Predicting the Quality and Prices of Bordeaux Wine",2008,"Economic Journal","ARTICLE",era="1980_2010",geo="Global",themes=["finance","demand"],bev="wine",prio="FLAGSHIP")
e(C,"storchmann","Storchmann","Karl","Wine Economics: Emergence and Future",2012,"J Wine Economics","ARTICLE",era="2010_2020",geo="Global",themes=["finance"],bev="wine")
e(C,"thornton","Thornton","James","American Wine Economics",2013,"UC Press","BOOK",era="2010_2020",geo="US",themes=["finance","demand"],bev="wine")
e(C,"parker","McCoy","Elin","The Emperor of Wine: Robert Parker Jr.",2005,"Ecco","BOOK",era="1980_2010",geo="US",themes=["demand","media"],bev="wine",stk="media")
e(C,"robinson","Robinson","Jancis","The Oxford Companion to Wine",2015,"Oxford UP","BOOK",era="spanning",geo="Global",themes=["demand"],bev="wine",prio="HIGH")
e(C,"appellations","INAO","","French INAO Wine Appellation System",2024,"INAO","DATASET_DOC",era="2020_present",geo="Europe",themes=["policy","supply"],bev="wine",lang="fr",stk="regulator")
e(C,"climate_wine","Ashenfelter","Orley","Climate Change and Wine Quality",2016,"J Wine Economics","ARTICLE",era="2010_2020",geo="Global",themes=["climate","supply"],bev="wine")
e(C,"napa","Napa","","Napa Valley AVA Economic Report 2024",2024,"Napa Vintners","REPORT",era="2020_present",geo="US",themes=["supply","finance"],bev="wine",stk="producer",prio="MEDIUM")
e(C,"nat_wine","Feiring","Alice","Naked Wine: Letting Grapes Do What Comes Naturally",2011,"Da Capo","BOOK",era="2010_2020",geo="US_Global",themes=["demand","technology"],bev="wine",prio="MEDIUM")
e(C,"sommelier","Court of Master Sommeliers","","Sommelier Industry Education and Economics",2024,"CMS","REPORT",era="2020_present",geo="US",themes=["labor","demand"],bev="wine",stk="academic",prio="MEDIUM")
e(C,"wine_trade","OIV","","International Organisation of Vine and Wine Statistical Report",2024,"OIV","DATASET_DOC",era="2020_present",geo="Global",themes=["trade","supply"],bev="wine",lang="fr",stk="regulator")
e(C,"wine_china","Beijing","","Chinese Wine Industry Explosion",2022,"Wine Economics","ARTICLE",era="2020_present",geo="Asia",themes=["demand","supply"],bev="wine",lang="zh",prio="MEDIUM")
e(C,"chinese_inv","Decanter","","Chinese Investment in Bordeaux",2019,"Decanter","ARTICLE",era="2010_2020",geo="Global",themes=["trade","finance"],bev="wine",stk="media",prio="MEDIUM")
e(C,"us_wine","Alston","Julian","The Economics of Wine Prices",2011,"Annual Review of Resource Econ","ARTICLE",era="2010_2020",geo="US",themes=["finance"],bev="wine",prio="MEDIUM")
e(C,"biodynamic","Waldin","Monty","Biodynamic Wine",2016,"Infinite Ideas","BOOK",era="2010_2020",geo="Global",themes=["technology","demand"],bev="wine",prio="LOW")

# ---- Cat 77: Beer Industry (12) ----
C = "Beer Industry"
e(C,"tremblay","Tremblay","Victor","The US Brewing Industry: Data and Economic Analysis",2005,"MIT Press","BOOK",era="1980_2010",geo="US",themes=["finance","supply"],bev="beer",prio="FLAGSHIP")
e(C,"ogle","Ogle","Maureen","Ambitious Brew: The Story of American Beer",2006,"Houghton","BOOK",era="spanning",geo="US",themes=["demand","finance"],bev="beer")
e(C,"halberstadt","Halberstadt","Robert","Beer Industry Antitrust and Consolidation",2018,"Antitrust Law Journal","ARTICLE",era="2010_2020",geo="US",themes=["policy","finance"],bev="beer",prio="MEDIUM")
e(C,"ab_inbev","AB InBev","","Anheuser-Busch InBev 2023 Annual Report",2023,"AB InBev","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],bev="beer",stk="investor")
e(C,"heineken","Heineken","","Heineken 2023 Annual Report",2023,"Heineken","GOV_DOC",era="2020_present",geo="Europe",themes=["finance"],bev="beer",lang="other",stk="investor")
e(C,"craft_beer","Brewers Association","","US Craft Beer Industry Statistics",2024,"BA","DATASET_DOC",era="2020_present",geo="US",themes=["demand","finance"],bev="beer",stk="NGO",prio="HIGH")
e(C,"budweiser","Ogle","Maureen","Bud Light 2023 Backlash and Industry",2023,"Business History","ARTICLE",era="2020_present",geo="US",themes=["demand","media"],bev="beer",prio="MEDIUM")
e(C,"beer_consol","Industry Research","","Beer Consolidation MillerCoors to Molson Coors",2018,"Bloomberg","ARTICLE",era="2010_2020",geo="US",themes=["finance"],bev="beer",stk="media",prio="MEDIUM")
e(C,"german_beer","German Brewers","","Reinheitsgebot German Beer Purity Law Economics",2022,"Deutsche Brauer Bund","REPORT",era="2020_present",geo="Europe",themes=["policy"],bev="beer",lang="de",stk="regulator",prio="MEDIUM")
e(C,"beer_china","China Brewers","","China Beer Industry Post-2015",2022,"Industry","REPORT",era="2020_present",geo="Asia",themes=["supply","demand"],bev="beer",lang="zh",prio="MEDIUM")
e(C,"craft_boom","Tremblay","Carol","Craft Brewery Entry Patterns",2016,"AEPP","ARTICLE",era="2010_2020",geo="US",themes=["finance","demand"],bev="beer",prio="MEDIUM")
e(C,"beer_tax","Fogarty","James","Alcohol Taxation Effects on Beer",2010,"Health Economics","ARTICLE",era="1980_2010",geo="US_Global",themes=["policy","demand"],bev="beer",prio="MEDIUM")

# ---- Cat 78: Spirits & Cocktails (10) ----
C = "Spirits Cocktails"
e(C,"diageo","Diageo","","Diageo Annual Report 2023",2023,"Diageo","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],bev="spirits",stk="investor",prio="FLAGSHIP")
e(C,"pernod","Pernod Ricard","","Pernod Ricard Annual Report 2023",2023,"Pernod Ricard","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],bev="spirits",lang="fr",stk="investor")
e(C,"wondrich","Wondrich","David","Imbibe!",2007,"Perigee","BOOK",era="spanning",geo="US",themes=["demand"],bev="spirits")
e(C,"punch","Wondrich","David","Punch: The Delights and Dangers of the Flowing Bowl",2010,"Perigee","BOOK",era="pre1900",geo="US_Global",themes=["demand"],bev="spirits",prio="MEDIUM")
e(C,"meehan","Meehan","Jim","Meehan's Bartender Manual",2017,"Ten Speed","BOOK",era="2010_2020",geo="US",themes=["demand","labor"],bev="spirits",prio="MEDIUM")
e(C,"whiskey","Broom","Dave","The World Atlas of Whisky",2014,"Mitchell Beazley","BOOK",era="2010_2020",geo="Global",themes=["demand","supply"],bev="spirits",prio="MEDIUM")
e(C,"tequila","Gaytán","Marie Sarita","Tequila! Distilling the Spirit of Mexico",2014,"Stanford UP","BOOK",era="spanning",geo="LatAm",themes=["demand","supply"],bev="spirits",cuisine="mexican")
e(C,"mezcal","Suro-Piñera","David","Mezcal: The History Craft & Cocktails of the World's Ultimate Artisanal Spirit",2019,"Shambhala","BOOK",era="2010_2020",geo="LatAm",themes=["supply"],bev="spirits",cuisine="mexican",prio="MEDIUM")
e(C,"rum","Pack","Susan","Rum: A Global History",2015,"Reaktion","BOOK",era="spanning",geo="Global",themes=["trade","supply"],bev="spirits",prio="MEDIUM")
e(C,"japanese_whiskey","Hatten","Tom","Japanese Whiskey Industry",2019,"J Distilling","ARTICLE",era="2010_2020",geo="Asia",themes=["supply","trade"],bev="spirits",cuisine="japanese",prio="MEDIUM")

# ---- Cat 79: Coffee Industry Deep (20) ----
C = "Coffee Deep"
e(C,"pendergrast_coffee","Pendergrast","Mark","Uncommon Grounds: The History of Coffee and How It Transformed Our World",2010,"Basic","BOOK",era="spanning",geo="Global",themes=["trade","supply"],bev="coffee",prio="FLAGSHIP")
e(C,"daviron","Daviron","Benoit","The Coffee Paradox: Global Markets Commodity Trade",2005,"Zed","BOOK",era="1980_2010",geo="Global",themes=["trade"],bev="coffee")
e(C,"sedgewick","Sedgewick","Augustine","Coffeeland: One Man's Dark Empire and the Making of Our Favorite Drug",2020,"Penguin","BOOK",era="spanning",geo="Global",themes=["trade","labor"],bev="coffee")
e(C,"roseberry","Roseberry","William","The Rise of Yuppie Coffees and the Reimagination of Class in the United States",1996,"American Anthropologist","ARTICLE",era="1980_2010",geo="US",themes=["demand"],bev="coffee")
e(C,"third_wave","Manzo","Jack","The Third Wave of Coffee",2014,"J Consumer Culture","ARTICLE",era="2010_2020",geo="Global",themes=["demand"],bev="coffee",prio="HIGH")
e(C,"ico","ICO","","International Coffee Organization Annual Review 2024",2024,"ICO","REPORT",era="2020_present",geo="Global",themes=["trade","supply"],bev="coffee",stk="regulator",prio="HIGH")
e(C,"fair_trade","Jaffee","Daniel","Brewing Justice: Fair Trade Coffee Sustainability and Survival",2014,"UC Press","BOOK",era="2010_2020",geo="Global",themes=["trade","policy"],bev="coffee")
e(C,"climate_coffee","Bunn","Christian","Climate Change Impact on Coffee Arabica Suitable Area",2015,"Climatic Change","ARTICLE",era="2010_2020",geo="Global",themes=["climate","supply"],bev="coffee")
e(C,"ethiopia_coffee","Petit","Nicolas","Ethiopia's Coffee Sector: A Bitter or Better Future",2007,"J Agrarian Change","ARTICLE",era="1980_2010",geo="Africa",themes=["supply","labor"],bev="coffee",prio="MEDIUM")
e(C,"starbucks_coffee","Schultz","Howard","Onward: How Starbucks Fought for Its Life",2011,"Rodale","BOOK",era="2010_2020",geo="US",themes=["finance"],bev="coffee",sub_ind="chain")
e(C,"espresso","Morris","Jonathan","Coffee: A Global History",2019,"Reaktion","BOOK",era="spanning",geo="Global",themes=["demand"],bev="coffee",prio="MEDIUM")
e(C,"colombia","Mejía","Clara","Colombian Coffee Federation Economics",2018,"Applied Econ Perspectives","ARTICLE",era="2010_2020",geo="LatAm",themes=["supply","policy"],bev="coffee",lang="es",prio="MEDIUM")
e(C,"spp","Talbot","John","Grounds for Agreement: Political Economy of the Coffee Commodity Chain",2004,"Rowman","BOOK",era="spanning",geo="Global",themes=["trade"],bev="coffee")
e(C,"coffee_price","ICE","","ICE Coffee 'C' Contract Price History",2024,"ICE","DATASET_DOC",era="spanning",geo="Global",themes=["finance"],bev="coffee",stk="trader")
e(C,"climate_col","Bacon","Christopher","Climate Change and Coffee Farmer Adaptation",2012,"Climate and Development","ARTICLE",era="2010_2020",geo="LatAm",themes=["climate","supply"],bev="coffee",prio="MEDIUM")
e(C,"specialty","SCA","","Specialty Coffee Association Report 2024",2024,"SCA","REPORT",era="2020_present",geo="Global",themes=["demand"],bev="coffee",stk="NGO",prio="MEDIUM")
e(C,"coffee_trade","Ponte","Stefano","The Latte Revolution: Regulation Markets and Consumption in the Global Coffee Chain",2002,"World Development","ARTICLE",era="1980_2010",geo="Global",themes=["trade","demand"],bev="coffee")
e(C,"vietnam","Nguyen","Thu","Vietnam's Rise as Global Coffee Producer",2020,"World Coffee Research","REPORT",era="2010_2020",geo="Asia",themes=["supply"],bev="coffee",prio="MEDIUM")
e(C,"climate_coffee2","World Coffee Research","","WCR Coffee Breeding for Climate Adaptation",2024,"WCR","REPORT",era="2020_present",geo="Global",themes=["technology","climate"],bev="coffee",stk="NGO",prio="MEDIUM")
e(C,"cafe_econ","Manzo","John","Coffeehouses Economic Geography US Cities",2015,"Urban Geography","ARTICLE",era="2010_2020",geo="US",themes=["demand"],bev="coffee",sub_ind="cafe",prio="MEDIUM")

# ---- Cat 80: Cocoa & Chocolate Industry (10) ----
C = "Cocoa Chocolate"
e(C,"coe","Coe","Sophie","The True History of Chocolate",1996,"Thames & Hudson","BOOK",era="spanning",geo="Global",themes=["supply","demand"],bev="cocoa_chocolate",prio="FLAGSHIP")
e(C,"clarence_smith","Clarence-Smith","William G.","Cocoa and Chocolate 1765-1914",2000,"Routledge","BOOK",era="pre1900",geo="Global",themes=["trade","supply"],bev="cocoa_chocolate")
e(C,"terrio","Terrio","Susan","Crafting the Culture and History of French Chocolate",2000,"UC Press","BOOK",era="spanning",geo="Europe",themes=["demand","labor"],bev="cocoa_chocolate",cuisine="french",lang="fr",prio="MEDIUM")
e(C,"child_labor","Off","Carol","Bitter Chocolate: Investigating the Dark Side of the World's Most Seductive Sweet",2008,"New Press","BOOK",era="2010_2020",geo="Africa",themes=["labor","supply"],bev="cocoa_chocolate")
e(C,"icc_o","ICCO","","International Cocoa Organization Annual Report 2024",2024,"ICCO","REPORT",era="2020_present",geo="Global",themes=["trade","supply"],bev="cocoa_chocolate",stk="regulator")
e(C,"ivory","FAO","","Côte d'Ivoire and Ghana Cocoa Crisis 2024",2024,"FAO","REPORT",era="2020_present",geo="Africa",themes=["supply","climate"],bev="cocoa_chocolate",stk="regulator",prio="HIGH")
e(C,"hershey","D'Antonio","Michael","Hershey: Milton Hershey's Extraordinary Life of Wealth Empire and Utopian Dreams",2006,"Simon & Schuster","BOOK",era="spanning",geo="US",themes=["finance"],bev="cocoa_chocolate",stk="processor")
e(C,"mars_choc","Brenner","Joel","Emperors of Chocolate: Hershey Mars",1999,"Broadway","BOOK",era="spanning",geo="US_Global",themes=["finance"],bev="cocoa_chocolate",stk="processor")
e(C,"bean_to_bar","Morris","Ed","The Bean-to-Bar Chocolate Movement",2018,"Industry","REPORT",era="2010_2020",geo="US_Global",themes=["demand","supply"],bev="cocoa_chocolate",prio="MEDIUM")
e(C,"cocoa_price","ICE","","ICE Cocoa 2024 Record Price Spike",2024,"ICE","REPORT",era="2020_present",geo="Global",themes=["finance","supply"],bev="cocoa_chocolate",stk="trader")

# ---- Cat 81: Tea Industry (10) ----
C = "Tea Industry"
e(C,"rappaport_tea","Rappaport","Erika","A Thirst for Empire: How Tea Shaped the Modern World",2017,"Princeton UP","BOOK",era="spanning",geo="Global",themes=["trade","demand"],bev="tea",prio="FLAGSHIP")
e(C,"moxham","Moxham","Roy","Tea: Addiction Exploitation and Empire",2003,"Basic","BOOK",era="pre1900",geo="Asia",themes=["trade","labor"],bev="tea")
e(C,"hohenegger","Hohenegger","Beatrice","Liquid Jade: The Story of Tea from East to West",2007,"St Martin's","BOOK",era="spanning",geo="Asia",themes=["demand","trade"],bev="tea")
e(C,"chai","Lutgendorf","Philip","Making Tea Making Japan: Cultural Nationalism in Practice",2004,"Oxford UP","BOOK",era="spanning",geo="Asia",themes=["demand"],bev="tea",cuisine="japanese",prio="MEDIUM")
e(C,"tea_india","Besky","Sarah","The Darjeeling Distinction: Labor and Justice on Fair-Trade Tea Plantations in India",2014,"UC Press","BOOK",era="2010_2020",geo="Asia",themes=["labor"],bev="tea")
e(C,"tea_china","Zhao","Yueping","Chinese Tea Industry Report",2022,"China Ag Review","ARTICLE",era="2020_present",geo="Asia",themes=["supply"],bev="tea",lang="zh",prio="MEDIUM")
e(C,"tea_africa","FAO","","FAO Tea Market Review 2024",2024,"FAO","REPORT",era="2020_present",geo="Global",themes=["supply","trade"],bev="tea",stk="regulator")
e(C,"boba","Fan","Helen","Boba Tea Global Phenomenon",2020,"Food Culture & Society","ARTICLE",era="2020_present",geo="Global",themes=["demand"],bev="tea",cuisine="chinese",prio="MEDIUM")
e(C,"tea_bag","Twinings","","Twinings Brand History",2024,"Twinings","GOV_DOC",era="spanning",geo="Europe",themes=["demand"],bev="tea",stk="processor",prio="LOW")
e(C,"kombucha","Kombucha Brewers","","Kombucha Industry Economics",2023,"Kombucha Brewers Intl","REPORT",era="2020_present",geo="US",themes=["demand"],bev="tea",prio="LOW")

# ---- Cat 82: Spice Industry (10) ----
C = "Spice Industry"
e(C,"krondl","Krondl","Michael","The Taste of Conquest: Rise and Fall of Three Great Cities of Spice",2008,"Ballantine","BOOK",era="pre1900",geo="Global",themes=["trade"],prio="FLAGSHIP")
e(C,"turner","Turner","Jack","Spice: The History of a Temptation",2004,"Knopf","BOOK",era="pre1900",geo="Global",themes=["trade","demand"])
e(C,"freedman_sp","Freedman","Paul","Out of the East: Spices and the Medieval Imagination",2008,"Yale UP","BOOK",era="pre1900",geo="Global",themes=["trade"])
e(C,"pepper","Lam","Francis","The History and Geopolitics of Pepper",2018,"New Yorker","ARTICLE",era="spanning",geo="Asia",themes=["trade"],stk="media",prio="MEDIUM")
e(C,"vanilla","Ecott","Tim","Vanilla: Travels in Search of the Ice Cream Orchid",2004,"Grove","BOOK",era="spanning",geo="Africa",themes=["supply","trade"])
e(C,"saffron","Willan","Anne","Saffron: A Global Crop History",2020,"Reaktion","BOOK",era="spanning",geo="Europe",themes=["supply","trade"])
e(C,"cardamom","McCormick","","McCormick & Co Corporate Profile",2024,"McCormick","GOV_DOC",era="2020_present",geo="US",themes=["supply","finance"],stk="processor")
e(C,"cinnamon","Moxham","Roy","Cinnamon Spice Wars",2005,"Hambledon","BOOK",era="pre1900",geo="Asia",themes=["trade"],prio="MEDIUM")
e(C,"madagascar","Bellemare","Marc","Contract Farming Madagascar Vanilla",2012,"J Development Studies","ARTICLE",era="2010_2020",geo="Africa",themes=["labor","supply"],prio="MEDIUM")
e(C,"indian_spice","Achaya","K.T.","Indian Spice History",1998,"Oxford UP","CHAPTER",era="spanning",geo="Asia",themes=["trade"],cuisine="indian",prio="MEDIUM")

# ---- Cat 83: Soda & Soft Drinks (10) ----
C = "Soda"
e(C,"pendergrast_cola","Pendergrast","Mark","For God Country and Coca-Cola (extended)",2000,"Basic","BOOK",era="spanning",geo="Global",themes=["finance"],bev="soda",prio="FLAGSHIP")
e(C,"hfcs_bray","Bray","George","Consumption of HFCS in Beverages May Play Role in Obesity",2004,"Am J Clinical Nutrition","ARTICLE",era="1980_2010",geo="US",themes=["demand"],bev="soda")
e(C,"soda_tax_berkeley","Silver","Lynn D.","Berkeley Soda Tax One-Year Evaluation",2017,"PLoS Medicine","ARTICLE",era="2010_2020",geo="US",themes=["policy","demand"],bev="soda")
e(C,"big_gulp","Pomeranz","Jennifer","Portion Cap Rule NYC Big Gulp",2012,"Yale J Health Policy","ARTICLE",era="2010_2020",geo="US",themes=["policy","demand"],bev="soda",borough="Citywide")
e(C,"coke_global","Foster","Robert","Coca-Globalization",2008,"Palgrave","BOOK",era="1980_2010",geo="Global",themes=["demand"],bev="soda")
e(C,"mexico_tax","Mexico","","Mexican Soda Tax 2014 Evaluation",2019,"Health Affairs","ARTICLE",era="2010_2020",geo="LatAm",themes=["policy"],bev="soda",lang="es")
e(C,"diet","Royte","Elizabeth","Bottlemania: How Water Went on Sale",2008,"Bloomsbury","BOOK",era="1980_2010",geo="US",themes=["demand"],bev="bottled_water",prio="MEDIUM")
e(C,"snapple","Hays","Constance","The Real Thing: Truth and Power at the Coca-Cola Company",2004,"Random House","BOOK",era="1980_2010",geo="US",themes=["finance","demand"],bev="soda")
e(C,"sports_drink","Gatorade","","Gatorade Brand History (Pepsi)",2024,"PepsiCo","GOV_DOC",era="spanning",geo="US",themes=["demand"],bev="soda",stk="processor",prio="LOW")
e(C,"kombucha_soda","Industry","","Non-Alcoholic Beverage Market Shift 2020-2024",2024,"Industry","REPORT",era="2020_present",geo="Global",themes=["demand"],bev="soda",stk="media",prio="MEDIUM")

# ---- Cat 84: Bottled Water (8) ----
C = "Bottled Water"
e(C,"royte_water","Royte","Elizabeth","Bottlemania: How Water Went on Sale",2008,"Bloomsbury","BOOK",era="1980_2010",geo="US",themes=["demand"],bev="bottled_water",prio="FLAGSHIP")
e(C,"gleick","Gleick","Peter","Bottled and Sold: The Story Behind Our Obsession with Bottled Water",2010,"Island","BOOK",era="1980_2010",geo="US_Global",themes=["demand","policy"],bev="bottled_water")
e(C,"fishman","Fishman","Charles","The Big Thirst: The Secret Life and Turbulent Future of Water",2011,"Free Press","BOOK",era="2010_2020",geo="Global",themes=["climate","supply"],bev="bottled_water")
e(C,"nestle_water","NestleWaters","","Nestlé Waters North America Corporate",2020,"Nestlé","GOV_DOC",era="2010_2020",geo="Global",themes=["finance"],bev="bottled_water",stk="processor")
e(C,"pepsi_water","Aquafina","","Aquafina Brand History (PepsiCo)",2024,"PepsiCo","GOV_DOC",era="spanning",geo="US",themes=["demand"],bev="bottled_water",stk="processor",prio="MEDIUM")
e(C,"dasani","Coca-Cola","","Dasani Brand History",2024,"Coca-Cola","GOV_DOC",era="spanning",geo="US",themes=["demand"],bev="bottled_water",stk="processor",prio="LOW")
e(C,"iceland","Icelandic Glacial","","Icelandic Glacial Brand Case Study",2019,"Industry","REPORT",era="2010_2020",geo="Europe",themes=["demand"],bev="bottled_water",prio="LOW")
e(C,"plastic_water","Hawkins","Gay","Plastic Water: The Social and Material Life of Bottled Water",2015,"MIT Press","BOOK",era="2010_2020",geo="Global",themes=["climate","demand"],bev="bottled_water",adj="waste")

# ---- Cat 85: Confectionery (8) ----
C = "Confectionery"
e(C,"mintz_conf","Mintz","Sidney","Sweetness and Power (extended)",1985,"Viking","BOOK",era="spanning",geo="Global",themes=["supply","demand"],comm="sugar",prio="FLAGSHIP")
e(C,"richardson","Richardson","Tim","Sweets: A History of Candy",2002,"Bloomsbury","BOOK",era="spanning",geo="Global",themes=["demand","supply"])
e(C,"mars_snickers","Brenner","Joel","Mars Corporate History",1999,"Broadway","BOOK",era="spanning",geo="US",themes=["finance"],stk="processor")
e(C,"hershey_2","D'Antonio","Michael","Hershey Biography",2006,"Simon & Schuster","BOOK",era="spanning",geo="US",themes=["finance","labor"],stk="processor")
e(C,"gum","Redclift","Michael","Chewing Gum: The Fortunes of Taste",2004,"Routledge","BOOK",era="spanning",geo="Global",themes=["supply","demand"],prio="MEDIUM")
e(C,"chocolate_craft","Martin","Carla","Craft Chocolate Industry US 2010-2020",2020,"MIT","ARTICLE",era="2010_2020",geo="US",themes=["demand"],bev="cocoa_chocolate",prio="MEDIUM")
e(C,"mondelez_conf","Mondelez","","Mondelez Confectionery Segment",2024,"Mondelez","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],stk="processor",prio="MEDIUM")
e(C,"valentines","Woloson","Wendy","Refined Tastes: Sugar Confectionery and Consumers in 19c America",2002,"Johns Hopkins","BOOK",era="pre1900",geo="US",themes=["demand"],comm="sugar",prio="MEDIUM")

# ---- Cat 86: Breakfast Cereal (8) ----
C = "Breakfast Cereal"
e(C,"bruce","Bruce","Scott","Cerealizing America: The Unsweetened Story of American Breakfast Cereal",2001,"Faber","BOOK",era="spanning",geo="US",themes=["supply","demand"],comm="cereals",prio="FLAGSHIP")
e(C,"kellogg_hist","Wilson","Brian","Dr. John Harvey Kellogg and the Religion of Biologic Living",2014,"Indiana UP","BOOK",era="pre1900",geo="US",themes=["demand"],stk="processor")
e(C,"post","Crawford","Constance","C.W. Post & the Creation of Breakfast Cereal Industry",1996,"Business History","ARTICLE",era="pre1900",geo="US",themes=["finance","demand"],stk="processor",prio="MEDIUM")
e(C,"gen_mills","General Mills","","General Mills Cereal Division Analysis",2024,"General Mills","GOV_DOC",era="2020_present",geo="US",themes=["finance"],stk="processor")
e(C,"kellogg_10k","Kellogg","","Kellogg Company 10-K 2023",2023,"Kellogg","GOV_DOC",era="2020_present",geo="US_Global",themes=["finance"],stk="investor")
e(C,"cereal_decline","McKinsey","","Breakfast Cereal Category Decline 2015-2024",2024,"McKinsey","REPORT",era="2020_present",geo="US",themes=["demand"],stk="media",prio="MEDIUM")
e(C,"sugar_cereal","Nestle","Marion","Sugar in Children's Cereals",2018,"American J Public Health","ARTICLE",era="2010_2020",geo="US",themes=["policy","demand"],comm="sugar",prio="MEDIUM")
e(C,"granola","Caldwell","","Granola and Health Food Market Emergence",2015,"Food Studies","ARTICLE",era="1980_2010",geo="US",themes=["demand"],prio="LOW")

# ---- Cat 87: Infant & Baby Food (8) ----
C = "Baby Food"
e(C,"nestle_formula2","Muller","Mike","The Baby Killer",1974,"War on Want","REPORT",era="1945_1980",geo="Africa",themes=["policy","labor"],stk="NGO",prio="FLAGSHIP")
e(C,"mead","Mead Johnson","","Mead Johnson Nutrition Corporate",2017,"Mead Johnson","GOV_DOC",era="2010_2020",geo="US_Global",themes=["finance"],stk="processor")
e(C,"abbott","Abbott","","Abbott Infant Formula Recall 2022",2022,"Abbott Nutrition","GOV_DOC",era="2020_present",geo="US",themes=["policy","supply"],stk="processor")
e(C,"danone_formula","Danone","","Danone Early Life Nutrition",2024,"Danone","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],stk="processor",lang="fr",prio="MEDIUM")
e(C,"china_formula","Jia","Xiangping","Chinese Infant Formula Market 2008 Melamine",2015,"Food Policy","ARTICLE",era="1980_2010",geo="Asia",themes=["policy","supply"],lang="zh",prio="HIGH")
e(C,"bm_code","WHO","","International Code of Marketing Breast-Milk Substitutes 1981",1981,"WHO","GOV_DOC",era="1945_1980",geo="Global",themes=["policy"],stk="regulator")
e(C,"fuss_baby","Gerber","","Gerber Products Corporate History",2024,"Nestlé","GOV_DOC",era="spanning",geo="US",themes=["demand"],stk="processor",prio="LOW")
e(C,"wic_form","Oliveira","Victor","WIC Infant Formula Purchasing",2013,"USDA ERS","REPORT",era="2010_2020",geo="US",themes=["policy"],stk="regulator",prio="MEDIUM")

# ---- Cat 88: Pet Food (8) ----
C = "Pet Food"
e(C,"okin","Okin","Gregory","Environmental Impacts of Pet Food",2017,"PLoS ONE","ARTICLE",era="2010_2020",geo="US",themes=["climate","demand"],prio="FLAGSHIP")
e(C,"pet_food_politics","Nestle","Marion","Pet Food Politics: The Chihuahua in the Coal Mine",2008,"UC Press","BOOK",era="1980_2010",geo="US",themes=["policy","supply"])
e(C,"mars_pet","Mars","","Mars Petcare Corporate Segment",2024,"Mars","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],stk="processor")
e(C,"nestle_pet","Nestle Purina","","Nestlé Purina PetCare",2024,"Nestlé","GOV_DOC",era="2020_present",geo="Global",themes=["finance"],stk="processor")
e(C,"melamine","FDA","","2007 Pet Food Melamine Recall",2007,"FDA","GOV_DOC",era="1980_2010",geo="US",themes=["policy","supply"],stk="regulator")
e(C,"premium_pet","Industry","","Premium Pet Food Market Trends",2023,"Industry","REPORT",era="2020_present",geo="US",themes=["demand"],stk="media",prio="MEDIUM")
e(C,"raw_pet","Raw Feeders","","Raw Pet Food Movement Economics",2022,"J Companion Animal","ARTICLE",era="2020_present",geo="US",themes=["demand"],prio="LOW")
e(C,"pet_meat","Industry","","Pet Food as Byproduct of Meat Industry",2019,"Food Science","ARTICLE",era="2010_2020",geo="US",themes=["supply"],comm="meat",prio="MEDIUM")

# ---- Cat 89: Fisheries & Aquaculture Deep (15) ----
C = "Fisheries Deep"
e(C,"pauly","Pauly","Daniel","Fishing Down Marine Food Webs",1998,"Science","ARTICLE",era="1980_2010",geo="Global",themes=["supply","climate"],sub_ind="fish_market",prio="FLAGSHIP")
e(C,"naylor","Naylor","Rosamond","Effect of Aquaculture on World Fish Supplies",2000,"Nature","ARTICLE",era="1980_2010",geo="Global",themes=["supply","technology"],sub_ind="fish_market")
e(C,"sofia","FAO","","State of World Fisheries and Aquaculture 2024",2024,"FAO","REPORT",era="2020_present",geo="Global",themes=["supply"],sub_ind="fish_market",stk="regulator")
e(C,"clark","Clark","Colin W.","The Optimal Management of Renewable Resources",2005,"Wiley","BOOK",era="spanning",geo="Global",themes=["supply","policy"],sub_ind="fish_market")
e(C,"crutchfield","Crutchfield","James","The Economics of Alaska Salmon Fisheries",2012,"J Ocean Policy","ARTICLE",era="2010_2020",geo="US",themes=["supply","policy"],sub_ind="fish_market",prio="MEDIUM")
e(C,"salmon","Taylor","Joseph E.","Making Salmon: Environmental History",1999,"U Washington Press","BOOK",era="spanning",geo="US",themes=["supply","climate"],sub_ind="fish_market")
e(C,"shrimp","Stonich","Susan","The Environmental Quality and Social Justice Implications of Shrimp Mariculture",1995,"Human Ecology","ARTICLE",era="1980_2010",geo="Asia",themes=["supply","labor"],sub_ind="fish_market",prio="MEDIUM")
e(C,"tuna","Korten","Alice","Tuna Industry Consolidation",2011,"Global Tuna Alliance","REPORT",era="2010_2020",geo="Global",themes=["trade","supply"],sub_ind="fish_market",stk="NGO",prio="MEDIUM")
e(C,"aquaculture","Boyd","Claude","Aquaculture 3.0: Global Industry Economics",2020,"World Aquaculture","ARTICLE",era="2020_present",geo="Global",themes=["supply","technology"],sub_ind="fish_market")
e(C,"mowi","Mowi","","Mowi ASA Annual Report 2023 (world's largest salmon)",2023,"Mowi","GOV_DOC",era="2020_present",geo="Europe",themes=["finance","supply"],sub_ind="fish_market",stk="processor")
e(C,"thaiunion","Thai Union","","Thai Union Group Annual Report 2023",2023,"Thai Union","GOV_DOC",era="2020_present",geo="Asia",themes=["finance"],sub_ind="fish_market",stk="processor",prio="MEDIUM")
e(C,"japan_fish","Maruha","","Maruha Nichiro Corporate",2024,"Maruha Nichiro","GOV_DOC",era="2020_present",geo="Asia",themes=["finance"],sub_ind="fish_market",cuisine="japanese",lang="ja",stk="processor",prio="MEDIUM")
e(C,"itq","Costello","Christopher","Can Catch Shares Prevent Fisheries Collapse?",2008,"Science","ARTICLE",era="1980_2010",geo="Global",themes=["policy","supply"],sub_ind="fish_market")
e(C,"slavery_fish","AP Investigation","","Slavery in the Seafood Supply Chain",2015,"Associated Press","ARTICLE",era="2010_2020",geo="Asia",themes=["labor"],sub_ind="fish_market",stk="media",prio="HIGH")
e(C,"climate_fish","Cheung","William","Climate Change Effects on Fisheries",2010,"Fish and Fisheries","ARTICLE",era="2010_2020",geo="Global",themes=["climate","supply"],sub_ind="fish_market")

# ---- Cat 90: Meat Industry Corporate Deep (12) ----
C = "Meat Corporates"
e(C,"tyson_hist","Striffler","Steve","Chicken: The Dangerous Transformation of America's Favorite Food",2005,"Yale UP","BOOK",era="spanning",geo="US",themes=["labor","supply"],comm="meat",sub_ind="wholesale",stk="processor",prio="FLAGSHIP")
e(C,"jbs_hist","Wesz","Valdemar","JBS: Rise of a Brazilian Beef Giant",2016,"J Agrarian Change","ARTICLE",era="1980_2010",geo="LatAm",themes=["finance","supply"],comm="meat",lang="pt",stk="processor")
e(C,"smithfield_wh","Hartzler","Olivia","Smithfield under WH Group Chinese Ownership",2014,"Foreign Policy","ARTICLE",era="2010_2020",geo="US_Global",themes=["trade","finance"],comm="meat",stk="media")
e(C,"cargill_meat_hist","Cargill","","Cargill Meat Solutions History",2023,"Cargill","GOV_DOC",era="spanning",geo="US",themes=["supply"],comm="meat",stk="processor")
e(C,"marfrig","Marfrig","","Marfrig Global Foods Annual Report 2023",2023,"Marfrig","GOV_DOC",era="2020_present",geo="LatAm",themes=["finance"],comm="meat",lang="pt",stk="investor",prio="MEDIUM")
e(C,"brf","BRF","","BRF (Brasil Foods) Annual Report 2023",2023,"BRF","GOV_DOC",era="2020_present",geo="LatAm",themes=["finance"],comm="meat",lang="pt",stk="investor",prio="MEDIUM")
e(C,"pilgrim","Pilgrim's","","Pilgrim's Pride 10-K 2023",2023,"Pilgrim's","GOV_DOC",era="2020_present",geo="US",themes=["finance"],comm="meat",stk="investor",prio="MEDIUM")
e(C,"hormel","Hormel","","Hormel Foods 10-K 2023",2023,"Hormel","GOV_DOC",era="2020_present",geo="US",themes=["finance"],comm="meat",stk="investor",prio="MEDIUM")
e(C,"packer_hist","Yeager","Mary","Competition and Regulation: Development of Oligopoly in Meat Packing",1981,"JAI","BOOK",era="pre1900",geo="US",themes=["finance","supply"],comm="meat",stk="processor")
e(C,"antitrust","Specht","Joshua","Red Meat Republic",2019,"Princeton UP","BOOK",era="pre1900",geo="US",themes=["supply","labor"],comm="meat",stk="processor")
e(C,"chicken","Leonard","Christopher","The Meat Racket: The Secret Takeover of America's Food Business",2014,"Simon & Schuster","BOOK",era="1980_2010",geo="US",themes=["finance","labor"],comm="meat",stk="media")
e(C,"jbs_nyse","JBS","","JBS USA NYSE Listing 2023-2024",2024,"JBS","GOV_DOC",era="2020_present",geo="LatAm",themes=["finance"],comm="meat",stk="investor",prio="HIGH")

# =============================================================================
# PHASE V — CULTURE & PRIMARY SOURCES (Cats 91-100) — ~10/cat
# =============================================================================

# ---- Cat 91: Cookbooks as Historical Data (20) ----
C = "Cookbooks Historical"
e(C,"apicius","Apicius","","De Re Coquinaria (c. 400 CE)",400,"Classical","BOOK",era="pre1900",geo="Europe",themes=["demand"],prio="FLAGSHIP")
e(C,"forme","Forme of Cury","","The Forme of Cury (c. 1390)",1390,"Medieval Royal Cookbook","BOOK",era="pre1900",geo="Europe",themes=["demand"],lang="en",prio="MEDIUM")
e(C,"scappi","Scappi","Bartolomeo","Opera dell'arte del cucinare",1570,"Tramezzino","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="italian",lang="it",prio="MEDIUM")
e(C,"la_varenne_cb","La Varenne","François","Le Cuisinier françois",1651,"Paris","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="french",lang="fr",prio="MEDIUM")
e(C,"careme_cb","Carême","Marie-Antoine","Le Pâtissier royal parisien",1815,"Didot","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="french",lang="fr")
e(C,"escoffier_cb","Escoffier","Auguste","Le Guide Culinaire",1903,"Flammarion","BOOK",era="pre1900",geo="Europe",themes=["demand","technology"],cuisine="french",lang="fr",prio="HIGH")
e(C,"beeton_cb","Beeton","Isabella","Mrs Beeton's Book of Household Management",1861,"S.O. Beeton","BOOK",era="pre1900",geo="Europe",themes=["demand"],lang="en")
e(C,"fannie","Farmer","Fannie","Boston Cooking-School Cook Book",1896,"Little Brown","BOOK",era="pre1900",geo="US",themes=["demand"],prio="HIGH")
e(C,"joy","Rombauer","Irma S.","Joy of Cooking",1931,"A.C. Clayton","BOOK",era="1900_1945",geo="US",themes=["demand"],prio="HIGH")
e(C,"child_mastering","Child","Julia","Mastering the Art of French Cooking",1961,"Knopf","BOOK",era="1945_1980",geo="US",themes=["demand","media"],cuisine="french",prio="FLAGSHIP")
e(C,"beard","Beard","James","James Beard's American Cookery",1972,"Little Brown","BOOK",era="1945_1980",geo="US",themes=["demand"],prio="HIGH")
e(C,"mcgee","McGee","Harold","On Food and Cooking: The Science and Lore of the Kitchen",1984,"Scribner","BOOK",era="spanning",geo="US",themes=["technology","demand"])
e(C,"mcgee2","McGee","Harold","Nose Dive: A Field Guide to the World's Smells",2020,"Penguin","BOOK",era="2020_present",geo="Global",themes=["technology"],prio="MEDIUM")
e(C,"myhrvold","Myhrvold","Nathan","Modernist Cuisine: The Art and Science of Cooking",2011,"Cooking Lab","BOOK",era="2010_2020",geo="US",themes=["technology","demand"],prio="HIGH")
e(C,"keller_fl","Keller","Thomas","The French Laundry Cookbook",1999,"Artisan","BOOK",era="1980_2010",geo="US",themes=["demand"],cuisine="french",borough="Manhattan",sub_ind="fine_dining")
e(C,"grigson_cb","Grigson","Jane","Jane Grigson's Fruit Book",1982,"Atheneum","BOOK",era="1980_2010",geo="Europe",themes=["demand"],prio="MEDIUM")
e(C,"david_cb","David","Elizabeth","English Bread and Yeast Cookery",1977,"Viking","BOOK",era="1945_1980",geo="Europe",themes=["demand"],prio="MEDIUM")
e(C,"achaya_cb","Achaya","K.T.","A Historical Dictionary of Indian Food",1998,"Oxford UP","BOOK",era="spanning",geo="Asia",themes=["demand"],cuisine="indian",prio="MEDIUM")
e(C,"artusi_cb","Artusi","Pellegrino","La scienza in cucina",1891,"Self","BOOK",era="pre1900",geo="Europe",themes=["demand"],cuisine="italian",lang="it")
e(C,"hazan","Hazan","Marcella","The Classic Italian Cook Book",1973,"Knopf","BOOK",era="1945_1980",geo="US_Global",themes=["demand"],cuisine="italian",prio="MEDIUM")

# ---- Cat 92: Food Magazines & Trade Press (15) ----
C = "Food Magazines"
e(C,"gourmet","Condé Nast","","Gourmet Magazine Archive 1941-2009",2009,"Condé Nast","DATASET_DOC",era="spanning",geo="US",themes=["demand","media"],stk="media",prio="FLAGSHIP")
e(C,"bon_app","Condé Nast","","Bon Appétit Archive 1956-Present",2024,"Condé Nast","DATASET_DOC",era="spanning",geo="US",themes=["demand","media"],stk="media")
e(C,"saveur","Saveur","","Saveur Magazine Archive 1994-Present",2024,"Saveur","DATASET_DOC",era="spanning",geo="US_Global",themes=["demand","media"],stk="media")
e(C,"cooks","Cook's Illustrated","","Cook's Illustrated Archive",2024,"America's Test Kitchen","DATASET_DOC",era="spanning",geo="US",themes=["demand","technology"],stk="media",prio="HIGH")
e(C,"lucky_peach","Chang","David","Lucky Peach Magazine (defunct)",2017,"McSweeney's","REPORT",era="2010_2020",geo="US",themes=["demand","media"],borough="Manhattan",stk="media")
e(C,"nrn","Nation's Restaurant News","","NRN Archive",2024,"Informa","DATASET_DOC",era="spanning",geo="US",themes=["demand","finance"],stk="media")
e(C,"progressive_grocer","Progressive Grocer","","Progressive Grocer Magazine Archive",2024,"EnsembleIQ","DATASET_DOC",era="spanning",geo="US",themes=["supply","finance"],sub_ind="supermarket",stk="media")
e(C,"meatingplace","Meatingplace","","Meatingplace Industry Magazine Archive",2024,"Marketing & Technology Group","DATASET_DOC",era="spanning",geo="US",themes=["supply"],comm="meat",stk="media",prio="MEDIUM")
e(C,"supermarket_news","Supermarket News","","Supermarket News Archive",2024,"Informa","DATASET_DOC",era="spanning",geo="US",themes=["supply","demand"],sub_ind="supermarket",stk="media")
e(C,"world_grain","World Grain","","World Grain Magazine Archive",2024,"Sosland","DATASET_DOC",era="spanning",geo="Global",themes=["supply","trade"],comm="cereals",stk="media",prio="MEDIUM")
e(C,"sugar_j","Sugar Journal","","Sugar Journal Archive",2024,"Sugar Journal","DATASET_DOC",era="spanning",geo="Global",themes=["supply"],comm="sugar",stk="media",prio="LOW")
e(C,"restaurant_biz","Restaurant Business","","Restaurant Business Magazine Archive",2024,"Winsight","DATASET_DOC",era="spanning",geo="US",themes=["demand","finance"],stk="media",prio="MEDIUM")
e(C,"elle_table","Elle à Table","","Elle à Table (French Food Magazine)",2024,"Elle","DATASET_DOC",era="spanning",geo="Europe",themes=["demand","media"],lang="fr",stk="media",prio="MEDIUM")
e(C,"cucina","La Cucina Italiana","","La Cucina Italiana Archive",2024,"Condé Nast Italia","DATASET_DOC",era="spanning",geo="Europe",themes=["demand","media"],lang="it",cuisine="italian",stk="media",prio="MEDIUM")
e(C,"food_wine","Food & Wine","","Food & Wine Magazine Archive",2024,"Dotdash Meredith","DATASET_DOC",era="spanning",geo="US",themes=["demand","media"],stk="media",prio="MEDIUM")

# ---- Cat 93: Restaurant Guide Runs (8) ----
C = "Restaurant Guides"
e(C,"michelin_hist","Harp","Stephen","Marketing Michelin",2001,"Johns Hopkins","BOOK",era="spanning",geo="Europe",themes=["demand","media"],cuisine="french",stk="media",prio="FLAGSHIP")
e(C,"gault","Gault","Henri","Gault Millau Guide Archive",2024,"Gault Millau","DATASET_DOC",era="spanning",geo="Europe",themes=["demand","media"],cuisine="french",lang="fr",stk="media")
e(C,"mobil","AAA","","AAA Five Diamond Awards Archive",2024,"AAA","DATASET_DOC",era="spanning",geo="US",themes=["demand","media"],stk="media")
e(C,"zagat_nyc","Zagat","Tim Zagat","Zagat NYC 1979-2020 Archive",2020,"Zagat","DATASET_DOC",era="spanning",geo="US",themes=["demand","media"],borough="Citywide",stk="media",prio="HIGH")
e(C,"kleber","Guide Kleber","","Guide Kléber (France)",2024,"Kleber","DATASET_DOC",era="spanning",geo="Europe",themes=["demand","media"],cuisine="french",lang="fr",stk="media",prio="LOW")
e(C,"worlds_50","World's 50 Best","","World's 50 Best Restaurants Archive",2024,"50 Best","REPORT",era="2010_2020",geo="Global",themes=["demand","media"],stk="media",prio="HIGH")
e(C,"best_of","Eater","","Eater 38 / National Guides",2024,"Eater","DATASET_DOC",era="2020_present",geo="US",themes=["demand","media"],stk="media",prio="MEDIUM")
e(C,"infatuation_guide","Infatuation","","Infatuation Guide Methodology",2024,"Infatuation","DATASET_DOC",era="2020_present",geo="US",themes=["demand"],stk="media",prio="MEDIUM")

# ---- Cat 94: Food Anthropology/Sociology (15) ----
C = "Food Anthro Sociology"
e(C,"mintz_ant","Mintz","Sidney","Sweetness and Power (anthropology frame)",1985,"Viking","BOOK",era="spanning",geo="Global",themes=["demand"],prio="FLAGSHIP")
e(C,"goody","Goody","Jack","Cooking Cuisine and Class: A Study in Comparative Sociology",1982,"Cambridge UP","BOOK",era="spanning",geo="Global",themes=["demand"])
e(C,"douglas","Douglas","Mary","Deciphering a Meal",1972,"Daedalus","ARTICLE",era="1945_1980",geo="Global",themes=["demand"])
e(C,"harris","Harris","Marvin","Good to Eat: Riddles of Food and Culture",1985,"Simon & Schuster","BOOK",era="spanning",geo="Global",themes=["demand"])
e(C,"bourdieu","Bourdieu","Pierre","Distinction: A Social Critique of the Judgement of Taste",1984,"Harvard UP","BOOK",era="1945_1980",geo="Europe",themes=["demand"],lang="fr")
e(C,"fischler","Fischler","Claude","L'Homnivore: Le goût la cuisine et le corps",1990,"Odile Jacob","BOOK",era="1980_2010",geo="Europe",themes=["demand"],lang="fr")
e(C,"warde","Warde","Alan","Consumption Food and Taste",1997,"Sage","BOOK",era="1980_2010",geo="Global",themes=["demand"])
e(C,"counihan","Counihan","Carole","Food and Culture: A Reader",2013,"Routledge","BOOK",era="spanning",geo="Global",themes=["demand"],prio="HIGH")
e(C,"ohnuki","Ohnuki-Tierney","Emiko","Rice as Self: Japanese Identities Through Time",1993,"Princeton UP","BOOK",era="spanning",geo="Asia",themes=["demand"],cuisine="japanese")
e(C,"bestor_anth","Bestor","Theodore","How Sushi Went Global",2000,"Foreign Policy","ARTICLE",era="1980_2010",geo="Global",themes=["demand","trade"],cuisine="japanese")
e(C,"appadurai_ant","Appadurai","Arjun","Gastro-Politics",1981,"American Ethnologist","ARTICLE",era="1980_2010",geo="Asia",themes=["demand"],cuisine="indian")
e(C,"mauss","Mauss","Marcel","The Gift (food gift chapters)",1925,"PUF","BOOK",era="pre1900",geo="Europe",themes=["demand"],lang="fr",prio="MEDIUM")
e(C,"friedmann","Friedmann","Harriet","The Political Economy of Food: A Global Crisis",1993,"New Left Review","ARTICLE",era="1980_2010",geo="Global",themes=["policy"])
e(C,"mcmichael","McMichael","Philip","Food Regimes and Agrarian Questions",2013,"Fernwood","BOOK",era="2010_2020",geo="Global",themes=["policy","trade"])
e(C,"kalcik","Kalcik","Susan","Ethnic Foodways in America",1984,"in Ethnic and Regional Foodways","CHAPTER",era="1980_2010",geo="US",themes=["demand"],prio="MEDIUM")

# ---- Cat 95: Food Geography (10) ----
C = "Food Geography"
e(C,"morgan","Morgan","Kevin","Worlds of Food: Place Power and Provenance",2006,"Oxford UP","BOOK",era="1980_2010",geo="Global",themes=["supply","demand"],prio="FLAGSHIP")
e(C,"bell_valentine","Bell","David","Consuming Geographies: We Are Where We Eat",1997,"Routledge","BOOK",era="1980_2010",geo="Global",themes=["demand"])
e(C,"pudup","Pudup","Mary Beth","Food Justice and Geography",2008,"Geoforum","ARTICLE",era="1980_2010",geo="Global",themes=["policy"])
e(C,"dixon","Dixon","Jane","The Changing Chicken: Chooks Cooks Rights",2002,"UNSW Press","BOOK",era="spanning",geo="Global",themes=["supply","labor"],comm="meat",prio="MEDIUM")
e(C,"cuisine_place","Murdoch","Jonathan","Quality Chains and Alternative Food Networks",2000,"Economic Geography","ARTICLE",era="1980_2010",geo="Europe",themes=["supply","demand"])
e(C,"foodshed","Kloppenburg","Jack","Coming in to the Foodshed",1996,"Ag and Human Values","ARTICLE",era="1980_2010",geo="US",themes=["supply"])
e(C,"mapping","USDA","","National Agricultural Atlas Mapping",2024,"USDA","DATASET_DOC",era="2020_present",geo="US",themes=["methodology","supply"],stk="regulator")
e(C,"urban","Cohen","Nevin","Urban Food Geography",2020,"Annual Review of Resource Econ","ARTICLE",era="2020_present",geo="Global",themes=["supply","demand"])
e(C,"terroir","Trubek","Amy","The Taste of Place: A Cultural Journey into Terroir",2008,"UC Press","BOOK",era="1980_2010",geo="Global",themes=["supply","demand"])
e(C,"rural_urban","Atkins","Peter","Food in Society: Economy Culture Geography",2001,"Arnold","BOOK",era="spanning",geo="Global",themes=["supply","demand"])

# ---- Cat 96: Food Studies Critical Race (12) ----
C = "Food Justice"
e(C,"reese","Reese","Ashanté","Black Food Geographies: Race Self-Reliance and Food Access",2019,"UNC Press","BOOK",era="2010_2020",geo="US",themes=["demand","policy"],prio="FLAGSHIP")
e(C,"white_freedom","White","Monica","Freedom Farmers: Agricultural Resistance and the Black Freedom Movement",2018,"UNC Press","BOOK",era="spanning",geo="US",themes=["labor","policy"])
e(C,"williams","Williams-Forson","Psyche","Building Houses Out of Chicken Legs: Black Women Food and Power",2006,"UNC Press","BOOK",era="spanning",geo="US",themes=["demand","labor"])
e(C,"alkon","Alkon","Alison","Cultivating Food Justice: Race Class and Sustainability",2011,"MIT Press","BOOK",era="2010_2020",geo="US",themes=["policy","demand"])
e(C,"bobby","Smith","Bobby J.","Agricultural Resistance in Black Farming Communities",2023,"UNC Press","BOOK",era="2020_present",geo="US",themes=["labor","policy"])
e(C,"twitty","Twitty","Michael W.","The Cooking Gene",2017,"Amistad","BOOK",era="spanning",geo="US",themes=["demand"],prio="HIGH")
e(C,"opie","Opie","Frederick Douglass","Hog and Hominy: Soul Food from Africa to America",2008,"Columbia UP","BOOK",era="spanning",geo="US",themes=["demand","labor"])
e(C,"miller","Miller","Adrian","Soul Food: The Surprising Story of an American Cuisine",2013,"UNC Press","BOOK",era="spanning",geo="US",themes=["demand"])
e(C,"ras","Chang","Rachel","Asian American Food Studies",2017,"Rutgers UP","CHAPTER",era="2010_2020",geo="US",themes=["demand","labor"],cuisine="fusion",prio="MEDIUM")
e(C,"indigenous","Mihesuah","Devon","Indigenous Food Sovereignty Movement",2020,"U Oklahoma Press","BOOK",era="2020_present",geo="US",themes=["policy"])
e(C,"race_food","Guthman","Julie","Weighing In: Obesity Food Justice and the Limits of Capitalism",2011,"UC Press","BOOK",era="2010_2020",geo="US",themes=["policy","demand"])
e(C,"farm_race","Holt-Gimenez","Eric","Can We Feed the World Without Destroying It?",2019,"Polity","BOOK",era="2010_2020",geo="Global",themes=["policy"],prio="MEDIUM")

# ---- Cat 97: Food Studies Gender (10) ----
C = "Food Gender"
e(C,"shapiro_g","Shapiro","Laura","Perfection Salad: Women and Cooking at the Turn of the Century",1986,"FSG","BOOK",era="pre1900",geo="US",themes=["demand","labor"],prio="FLAGSHIP")
e(C,"carroll","Carroll","Abigail","Three Squares: The Invention of the American Meal",2013,"Basic","BOOK",era="spanning",geo="US",themes=["demand"])
e(C,"neuhaus","Neuhaus","Jessamyn","Manly Meals and Mom's Home Cooking: Cookbooks and Gender in Modern America",2003,"Johns Hopkins","BOOK",era="spanning",geo="US",themes=["demand"])
e(C,"deutsch_g","Deutsch","Tracey","Building a Housewife's Paradise",2010,"UNC Press","BOOK",era="1900_1945",geo="US",themes=["demand","labor"])
e(C,"avakian","Avakian","Arlene Voski","Through the Kitchen Window: Women Writers Explore the Intimate Meanings of Food and Cooking",1997,"Beacon","BOOK",era="1980_2010",geo="US",themes=["demand","labor"])
e(C,"williams_g","Williams-Forson","Psyche","Building Houses Out of Chicken Legs (gender frame)",2006,"UNC Press","BOOK",era="spanning",geo="US",themes=["labor"])
e(C,"inness","Inness","Sherrie","Dinner Roles: American Women and Culinary Culture",2001,"U Iowa Press","BOOK",era="spanning",geo="US",themes=["demand"],prio="MEDIUM")
e(C,"counihan_g","Counihan","Carole","The Anthropology of Food and Body: Gender Meaning and Power",1999,"Routledge","BOOK",era="1980_2010",geo="Global",themes=["demand"])
e(C,"ch_bombe","Cherry Bombe","","Cherry Bombe: Women and Food Media",2024,"Cherry Bombe","REPORT",era="2020_present",geo="US",themes=["demand","labor"],stk="media",borough="Manhattan",sub_ind="food_media")
e(C,"me_too_kitchen","Jayaraman","Saru","Kitchen Workplace Harassment Post-MeToo",2018,"One Fair Wage","REPORT",era="2010_2020",geo="US",themes=["labor"],stk="NGO",prio="MEDIUM")

# ---- Cat 98: Movements (Slow/Organic/Fair/Regen) (15) ----
C = "Food Movements"
e(C,"petrini_slow","Petrini","Carlo","Slow Food: The Case for Taste",2001,"Columbia UP","BOOK",era="1980_2010",geo="Europe",themes=["policy","demand"],cuisine="italian",prio="FLAGSHIP")
e(C,"rodale","Rodale","J.I.","Pay Dirt: Farming and Gardening with Composts",1945,"Devin-Adair","BOOK",era="1900_1945",geo="US",themes=["technology","supply"])
e(C,"balfour","Balfour","Eve","The Living Soil",1943,"Faber","BOOK",era="1900_1945",geo="Europe",themes=["technology","supply"],prio="MEDIUM")
e(C,"howard","Howard","Sir Albert","An Agricultural Testament",1940,"Oxford UP","BOOK",era="1900_1945",geo="Global",themes=["technology","supply"])
e(C,"mollison","Mollison","Bill","Permaculture: A Designers' Manual",1988,"Tagari","BOOK",era="1980_2010",geo="Global",themes=["technology","supply"])
e(C,"jackson","Jackson","Wes","Consulting the Genius of the Place: An Ecological Approach to a New Agriculture",2010,"Counterpoint","BOOK",era="2010_2020",geo="US",themes=["technology","supply"])
e(C,"lasalle","LaSalle","Tim","Regenerative Agriculture Economics",2020,"Rodale Institute","REPORT",era="2020_present",geo="US",themes=["climate","supply"],stk="NGO")
e(C,"fair_tr","Raynolds","Laura","Fair Trade: The Challenges of Transforming Globalization",2007,"Routledge","BOOK",era="1980_2010",geo="Global",themes=["trade","policy"])
e(C,"via","La Via Campesina","","La Via Campesina Food Sovereignty Declaration",1996,"La Via Campesina","REPORT",era="1980_2010",geo="Global",themes=["policy","labor"],stk="NGO")
e(C,"organic_us","USDA","","USDA National Organic Program",2024,"USDA","GOV_DOC",era="2020_present",geo="US",themes=["policy","supply"],stk="regulator")
e(C,"org_economics","Greene","Catherine","Growth Patterns in the US Organic Industry",2013,"USDA ERS","REPORT",era="2010_2020",geo="US",themes=["supply","demand"],stk="regulator",prio="MEDIUM")
e(C,"farm_to","Feenstra","Gail","Local Food Systems and Sustainable Communities",2002,"American J Alternative Agriculture","ARTICLE",era="1980_2010",geo="US",themes=["supply"],prio="MEDIUM")
e(C,"regen_ag","Savory","Allan","Holistic Management: A New Framework for Decision Making",1999,"Island Press","BOOK",era="1980_2010",geo="Global",themes=["technology"],prio="MEDIUM")
e(C,"biodyn","Steiner","Rudolf","Agriculture Course: The Birth of the Biodynamic Method",1924,"Rudolf Steiner Press","BOOK",era="1900_1945",geo="Europe",themes=["technology"],lang="de",prio="LOW")
e(C,"500_miles","Smith","Alisa","100-Mile Diet: A Year of Local Eating",2007,"Random House","BOOK",era="1980_2010",geo="US",themes=["demand"],prio="MEDIUM")

# ---- Cat 99: Film/TV/Video Food Media (10) ----
C = "Food Film TV"
e(C,"child_tv","Polan","Dana","Julia Child's The French Chef",2011,"Duke UP","BOOK",era="1945_1980",geo="US",themes=["demand","media"],cuisine="french",stk="media",prio="FLAGSHIP")
e(C,"bourdain_tv","Bourdain","Anthony","Parts Unknown (CNN 2013-2018)",2018,"CNN","DATASET_DOC",era="2010_2020",geo="Global",themes=["demand","media"],stk="media")
e(C,"masterchef","Masterchef","","MasterChef Franchise Global Industry",2024,"Endemol","REPORT",era="spanning",geo="Global",themes=["demand","media"],stk="media",prio="MEDIUM")
e(C,"food_network","Wall","Kim","Food Network: Lifestyle Television and the Making of an Industry",2018,"NYU Press","BOOK",era="1980_2010",geo="US",themes=["demand","media"],stk="media")
e(C,"chef_table","Netflix","","Chef's Table Netflix Documentary Series",2024,"Netflix","DATASET_DOC",era="2010_2020",geo="Global",themes=["demand","media"],stk="media",prio="MEDIUM")
e(C,"gordon","Ramsay","Gordon","Ramsay TV Industry Impact",2018,"BBC","REPORT",era="2010_2020",geo="Europe",themes=["demand","labor","media"],stk="media",prio="MEDIUM")
e(C,"ugly_delicious","Netflix","","Ugly Delicious (David Chang)",2018,"Netflix","DATASET_DOC",era="2010_2020",geo="Global",themes=["demand","media"],cuisine="fusion",borough="Manhattan",stk="media",prio="MEDIUM")
e(C,"hells","Fox","","Hell's Kitchen Economics of Reality TV",2020,"J Popular Culture","ARTICLE",era="2010_2020",geo="US",themes=["demand","media"],stk="media",prio="LOW")
e(C,"doc_series","Netflix","","Netflix Food Documentary Economics",2022,"Industry","REPORT",era="2020_present",geo="Global",themes=["demand","media"],stk="media",prio="LOW")
e(C,"youtube","YouTube","","Food YouTube Creator Economy",2023,"Industry","REPORT",era="2020_present",geo="Global",themes=["demand","media"],stk="media",prio="MEDIUM")

# ---- Cat 100: Podcasts & Digital (8) ----
C = "Food Podcasts"
e(C,"gastropod","Gastropod","","Gastropod Podcast Archive",2024,"Gastropod","DATASET_DOC",era="spanning",geo="US_Global",themes=["demand","media"],stk="media",prio="FLAGSHIP")
e(C,"sporkful","Sporkful","","The Sporkful Podcast Archive",2024,"Stitcher","DATASET_DOC",era="spanning",geo="US",themes=["demand","media"],stk="media")
e(C,"salt_spine","Salt + Spine","","Salt + Spine Cookbook Podcast",2024,"Salt + Spine","DATASET_DOC",era="2020_present",geo="US",themes=["demand","media"],stk="media",prio="MEDIUM")
e(C,"meatballs","Meat+Three","","Meat + Three Radio/Podcast",2024,"Heritage Radio","DATASET_DOC",era="2020_present",geo="US",themes=["demand","media"],stk="media",prio="LOW")
e(C,"podcast_econ","Edison","","Podcast Industry Economics: Food Subcategory",2023,"Edison Research","REPORT",era="2020_present",geo="US",themes=["demand","media"],stk="media",prio="LOW")
e(C,"savor","Savor","","Savor Podcast (iHeart) Food History",2024,"iHeart","DATASET_DOC",era="2020_present",geo="US",themes=["demand","media"],stk="media",prio="MEDIUM")
e(C,"home_cook","Home Cooking","","Home Cooking Podcast (Samin Nosrat)",2021,"Spotify","DATASET_DOC",era="2020_present",geo="US",themes=["demand","media"],stk="media",prio="LOW")
e(C,"table_for","Table for Two","","Table for Two Bruce Bozzi",2024,"Industry","DATASET_DOC",era="2020_present",geo="US",themes=["demand","media"],stk="media",prio="LOW")

# =============================================================================
# PHASE W — ADJACENT / SPECIALTY (Cats 101-105) — ~10/cat
# =============================================================================

# ---- Cat 101: Institutional Food (12) ----
C = "Institutional Food"
e(C,"school_lunch","Poppendieck","Janet","Free for All: Fixing School Food in America",2010,"UC Press","BOOK",era="2010_2020",geo="US",themes=["policy","demand"],prio="FLAGSHIP")
e(C,"mre","Koehler","Franz","Special Rations for the Armed Forces: MRE History",1958,"US Army","REPORT",era="1900_1945",geo="US",themes=["supply","technology"],stk="regulator")
e(C,"prison","Cohen","Jonathan","Prison Food: A History",2018,"J American History","ARTICLE",era="spanning",geo="US",themes=["labor","policy"],prio="MEDIUM")
e(C,"hospital","Buchanan","Sharon","Clinical Nutrition Economics",2016,"J Academy of Nutrition","ARTICLE",era="2010_2020",geo="US",themes=["demand"],prio="MEDIUM")
e(C,"airline","Foss","Richard","The Coolest Business Class Food in the Sky",2020,"Aviation Week","ARTICLE",era="2020_present",geo="Global",themes=["demand"],stk="media",prio="LOW")
e(C,"cruise","Cruise Industry","","Cruise Ship Food Provisioning Economics",2023,"CLIA","REPORT",era="2020_present",geo="Global",themes=["supply"],stk="NGO",prio="LOW")
e(C,"space","NASA","","Space Food System Development Archive",2024,"NASA","REPORT",era="spanning",geo="US",themes=["technology"],stk="regulator",prio="LOW")
e(C,"military","DoD","","Defense Commissary Agency (DeCA) Operations",2024,"US DoD","REPORT",era="2020_present",geo="US",themes=["supply"],stk="regulator",prio="MEDIUM")
e(C,"nursing","CMS","","Nursing Home Food Service Regulation",2023,"CMS","REPORT",era="2020_present",geo="US",themes=["policy"],stk="regulator",prio="MEDIUM")
e(C,"sc_lunch","USDA FNS","","National School Lunch Program Data",2024,"USDA FNS","DATASET_DOC",era="2020_present",geo="US",themes=["policy","methodology"],stk="regulator")
e(C,"school_hist","Levine","Susan","School Lunch Politics: The Surprising History of America's Favorite Welfare Program",2008,"Princeton UP","BOOK",era="spanning",geo="US",themes=["policy"])
e(C,"mre_modern","US Army","","MRE Modern Format and Cost Analysis",2022,"US Army","REPORT",era="2020_present",geo="US",themes=["supply","technology"],stk="regulator",prio="MEDIUM")

# ---- Cat 102: Disaster, Refugee & War Food (10) ----
C = "Disaster Food"
e(C,"wfp","WFP","","World Food Programme Operations Annual",2024,"WFP","REPORT",era="2020_present",geo="Global",themes=["policy","supply"],stk="NGO",prio="FLAGSHIP")
e(C,"icrc","ICRC","","ICRC Food Assistance Operations",2024,"ICRC","REPORT",era="2020_present",geo="Global",themes=["supply"],stk="NGO")
e(C,"ww2_ration","Ziegelman","Jane","A Square Meal: A Culinary History of the Great Depression",2016,"Harper","BOOK",era="1900_1945",geo="US",themes=["policy","demand"])
e(C,"biafra","Smith","Karen","Biafran Famine and International Response",1970,"Humanitarian History","ARTICLE",era="1945_1980",geo="Africa",themes=["policy"],prio="MEDIUM")
e(C,"syria","FAO","","Syria Food Security Crisis 2011-2024",2024,"FAO","REPORT",era="2010_2020",geo="Europe",themes=["supply","policy"],stk="regulator")
e(C,"sudan","FAO","","Sudan Hunger Crisis 2024",2024,"FAO","REPORT",era="2020_present",geo="Africa",themes=["supply","policy"],stk="regulator",prio="HIGH")
e(C,"ukraine_ref","WFP","","Ukraine Refugee Food Assistance",2024,"WFP","REPORT",era="2020_present",geo="Europe",themes=["supply"],stk="NGO",prio="MEDIUM")
e(C,"disaster","Collins","Andrew","Disaster Food Relief Logistics",2018,"Disaster Prevention","ARTICLE",era="2010_2020",geo="Global",themes=["supply"],prio="MEDIUM")
e(C,"gaza","OCHA","","Gaza Food Crisis 2023-2024",2024,"UN OCHA","REPORT",era="2020_present",geo="Europe",themes=["supply"],stk="regulator",prio="HIGH")
e(C,"refugee_nutrition","UNHCR","","Refugee Nutrition Program Standards",2023,"UNHCR","REPORT",era="2020_present",geo="Global",themes=["supply"],stk="regulator")

# ---- Cat 103: Food Finance (10) ----
C = "Food Finance"
e(C,"rabobank_fin","Rabobank","","Rabobank Food & Agribusiness Advisory",2024,"Rabobank","REPORT",era="2020_present",geo="Global",themes=["finance"],adj="finance",stk="investor",prio="FLAGSHIP")
e(C,"farmcredit","Farm Credit System","","Farm Credit System Annual Information",2024,"FCS","REPORT",era="spanning",geo="US",themes=["finance"],adj="finance",stk="regulator")
e(C,"cobank","CoBank","","CoBank Agricultural Lending Reports",2024,"CoBank","REPORT",era="2020_present",geo="US",themes=["finance"],adj="finance",stk="investor")
e(C,"reit","Gladstone","","Agricultural Land REITs (Gladstone Land, Farmland Partners)",2024,"GOV","GOV_DOC",era="2020_present",geo="US",themes=["finance"],adj="finance",stk="investor",prio="MEDIUM")
e(C,"insurance_crop","USDA RMA","","Federal Crop Insurance Corporation",2024,"USDA RMA","DATASET_DOC",era="spanning",geo="US",themes=["finance","policy"],adj="insurance",stk="regulator")
e(C,"weather_deriv","Geiger","Charles","Weather Derivatives and Agriculture",2011,"J Futures Markets","ARTICLE",era="2010_2020",geo="US",themes=["finance","climate"],adj="finance",prio="MEDIUM")
e(C,"food_vc","Rockefeller Foundation","","Food Tech Venture Capital Investment 2020-2024",2024,"Rockefeller","REPORT",era="2020_present",geo="US_Global",themes=["finance","technology"],adj="finance",stk="investor")
e(C,"farmland_inv","Fairbairn","Madeleine","Fields of Gold: Financing the Global Land Rush",2020,"Cornell UP","BOOK",era="2020_present",geo="Global",themes=["finance"],adj="finance")
e(C,"ag_banking","BOK","","Regional Ag Banking Reports (BOK Financial)",2024,"BOK","REPORT",era="2020_present",geo="US",themes=["finance"],adj="finance",stk="investor",prio="MEDIUM")
e(C,"csa_fin","Morgan Stanley","","Restaurant Equity Research Coverage",2024,"Morgan Stanley","REPORT",era="2020_present",geo="US",themes=["finance"],stk="investor",prio="MEDIUM")

# ---- Cat 104: Food Packaging (8) ----
C = "Food Packaging"
e(C,"amcor","Amcor","","Amcor Annual Report 2023",2023,"Amcor","GOV_DOC",era="2020_present",geo="Global",themes=["technology","finance"],adj="commercial_equip",stk="processor",prio="FLAGSHIP")
e(C,"tetrapak","Tetra Pak","","Tetra Pak Aseptic Packaging Corporate",2024,"Tetra Pak","GOV_DOC",era="spanning",geo="Global",themes=["technology"],adj="commercial_equip",lang="other",stk="processor")
e(C,"sealed","Sealed Air","","Sealed Air 10-K 2023",2023,"Sealed Air","GOV_DOC",era="2020_present",geo="US",themes=["finance","technology"],adj="commercial_equip",stk="investor")
e(C,"hawkins","Hawkins","Gay","Plastic Water: Social Life of Bottled Water",2015,"MIT Press","BOOK",era="2010_2020",geo="Global",themes=["demand","climate"],bev="bottled_water",adj="waste")
e(C,"epr","EPR","","Extended Producer Responsibility for Food Packaging",2023,"OECD","REPORT",era="2020_present",geo="Global",themes=["policy"],adj="waste",stk="regulator",prio="MEDIUM")
e(C,"compostable","Eco","","Compostable Packaging Industry Economics",2023,"BPI","REPORT",era="2020_present",geo="US",themes=["technology","climate"],adj="waste",stk="NGO",prio="MEDIUM")
e(C,"glass","Owens-Illinois","","Glass Food Container Industry",2023,"O-I","GOV_DOC",era="2020_present",geo="US",themes=["technology"],adj="commercial_equip",stk="processor",prio="LOW")
e(C,"label","Food Labeling","","Food Labeling Regulation 2023",2023,"FDA","GOV_DOC",era="2020_present",geo="US",themes=["policy","demand"],stk="regulator",prio="MEDIUM")

# ---- Cat 105: Food Waste Global (10) ----
C = "Food Waste Global"
e(C,"stuart","Stuart","Tristram","Waste: Uncovering the Global Food Scandal",2009,"Norton","BOOK",era="1980_2010",geo="Global",themes=["supply","climate"],adj="waste",prio="FLAGSHIP")
e(C,"fao_loss","FAO","","Global Food Loss and Waste",2011,"FAO","REPORT",era="2010_2020",geo="Global",themes=["supply","climate"],adj="waste",stk="regulator")
e(C,"bloom","Bloom","Jonathan","American Wasteland: How America Throws Away Nearly Half Its Food",2010,"Da Capo","BOOK",era="1980_2010",geo="US",themes=["supply","demand"],adj="waste")
e(C,"refed","ReFED","","ReFED US Food Waste Report",2024,"ReFED","REPORT",era="2020_present",geo="US",themes=["supply","climate"],adj="waste",stk="NGO",prio="HIGH")
e(C,"wrap","WRAP","","WRAP UK Food Waste Courtauld Commitment",2024,"WRAP","REPORT",era="2020_present",geo="Europe",themes=["policy","climate"],adj="waste",stk="NGO")
e(C,"france_law","France","","French Food Waste Law (2016)",2016,"France","GOV_DOC",era="2010_2020",geo="Europe",themes=["policy"],adj="waste",lang="fr",stk="regulator",prio="MEDIUM")
e(C,"date_label","NRDC","","Date Label Reform Food Waste",2019,"NRDC","REPORT",era="2010_2020",geo="US",themes=["policy"],adj="waste",stk="NGO",prio="MEDIUM")
e(C,"recovery","Feeding America","","Feeding America Food Bank Network",2024,"Feeding America","REPORT",era="2020_present",geo="US",themes=["demand","supply"],adj="waste",stk="NGO")
e(C,"grocery_waste","Kroger","","Kroger Zero Hunger Zero Waste Initiative",2024,"Kroger","REPORT",era="2020_present",geo="US",themes=["supply","climate"],sub_ind="supermarket",adj="waste",stk="processor",prio="MEDIUM")
e(C,"epa_food","EPA","","US EPA Food Recovery Hierarchy",2024,"EPA","REPORT",era="2020_present",geo="US",themes=["policy","climate"],adj="waste",stk="regulator",prio="MEDIUM")


# =============================================================================
# EMIT CSV + JSON
# =============================================================================
CSV_HEADER = [
    "Number","Category","Subcategory","Author_Last","Author_First","Title","Year",
    "Publisher_Journal","Type","Commodity_Tag","Era","Geography",
    "Borough","Sub_Industry","Adjacency","Language","Industry_Stakeholder","Cuisine","Beverage_Type",
    "Priority","Status","Acquisition_Notes","Anna_Archive_Link","Archive_Org_Link","Direct_URL","Search_Query","NYC_Canonical","Added_In_Version"
]

def load_v2_rows():
    rows = []
    with open(V2_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def main():
    # v2 ingest: project each v2 row into v4 schema with defaults
    v2 = load_v2_rows()
    all_entries = []
    # Track counters
    cat_c = Counter(); prio_c = Counter(); comm_c = Counter()
    era_c = Counter(); geo_c = Counter(); theme_c = Counter()
    borough_c = Counter(); subind_c = Counter(); adj_c = Counter()
    lang_c = Counter(); stk_c = Counter(); cuis_c = Counter(); bev_c = Counter()
    ver_c = Counter(); canon_c = 0

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(CSV_HEADER)
        num = 0
        # v2 rows
        for r in v2:
            num += 1
            row = [
                num, r["Category"], r["Subcategory"], r["Author_Last"], r["Author_First"],
                r["Title"], r["Year"], r["Publisher_Journal"], r["Type"], r["Commodity_Tag"],
                r["Era"], r["Geography"],
                "none", "none", "none", "en", "academic", "none", "none",  # v3/v4 fields default
                r["Priority"], r["Status"], r["Acquisition_Notes"],
                r["Anna_Archive_Link"], r["Archive_Org_Link"], r["Direct_URL"], r["Search_Query"],
                False, "v2"
            ]
            w.writerow(row)
            cat_c[r["Category"]] += 1; prio_c[r["Priority"]] += 1; comm_c[r["Commodity_Tag"]] += 1
            era_c[r["Era"]] += 1; geo_c[r["Geography"]] += 1
            borough_c["none"] += 1; subind_c["none"] += 1; adj_c["none"] += 1
            lang_c["en"] += 1; stk_c["academic"] += 1; cuis_c["none"] += 1; bev_c["none"] += 1
            ver_c["v2"] += 1
            all_entries.append({"number":num,"version":"v2","category":r["Category"]})
        # v3/v4 new rows
        for d in N:
            num += 1
            q = f"{d['last']} {d['title']}".strip()
            aa = annas(q); ao = archorg(q)
            themes_str = ";".join(d["themes"])
            row = [
                num, d["cat"], d["sub"], d["last"], d["first"],
                d["title"], d["year"], d["pub"], d["typ"], d["comm"],
                d["era"], d["geo"],
                d["borough"], d["sub_ind"], d["adj"], d["lang"], d["stk"], d["cuisine"], d["bev"],
                d["prio"], d["status"], d["notes"],
                aa, ao, d["url"], q,
                d["nyc_canon"], "v3v4"
            ]
            w.writerow(row)
            cat_c[d["cat"]] += 1; prio_c[d["prio"]] += 1; comm_c[d["comm"]] += 1
            era_c[d["era"]] += 1; geo_c[d["geo"]] += 1
            for t in d["themes"]: theme_c[t] += 1
            borough_c[d["borough"]] += 1; subind_c[d["sub_ind"]] += 1; adj_c[d["adj"]] += 1
            lang_c[d["lang"]] += 1; stk_c[d["stk"]] += 1
            cuis_c[d["cuisine"]] += 1; bev_c[d["bev"]] += 1
            ver_c["v3v4"] += 1
            if d["nyc_canon"]: canon_c += 1
            all_entries.append({"number":num,"version":"v3v4","category":d["cat"],"nyc_canonical":d["nyc_canon"]})

    # JSON emit
    payload = {
        "schema_version": "4.0",
        "generated": datetime.now(UTC).isoformat(),
        "project": "Foodberg KB Wishlist v4 — Global Comprehensive",
        "total_entries": num,
        "category_counts": dict(cat_c),
        "priority_counts": dict(prio_c),
        "commodity_counts": dict(comm_c),
        "era_counts": dict(era_c),
        "geography_counts": dict(geo_c),
        "theme_counts": dict(theme_c),
        "borough_counts": dict(borough_c),
        "subindustry_counts": dict(subind_c),
        "adjacency_counts": dict(adj_c),
        "language_counts": dict(lang_c),
        "stakeholder_counts": dict(stk_c),
        "cuisine_counts": dict(cuis_c),
        "beverage_counts": dict(bev_c),
        "version_counts": dict(ver_c),
        "nyc_canonical_count": canon_c,
        "category_count": len(cat_c),
        "summary": all_entries,
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Wrote {num} entries ({ver_c['v2']} v2 + {ver_c['v3v4']} v3+v4)")
    print(f"Categories: {len(cat_c)}")
    print(f"NYC canonical: {canon_c}")
    print(f"Languages: {dict(lang_c)}")
    print(f"Top priorities: {dict(prio_c)}")
    print(f"CSV:  {CSV_PATH}")
    print(f"JSON: {JSON_PATH}")

if __name__ == "__main__":
    main()


