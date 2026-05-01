"""
Foodberg KB Wishlist generator.

Writes:
  - 2026.04.12_Foodberg_Wishlist.csv
  - 2026.04.12_Foodberg_Wishlist.json

Single source of truth: the ENTRIES list below.
Each entry: (category, subcategory, author_last, author_first, title, year,
             publisher_journal, type, commodity_tag, priority, status,
             acquisition_notes, direct_url, relevance_to_foodberg)

Anna's Archive + archive.org links are auto-generated from title + author.
"""
from __future__ import annotations
import csv
import json
import urllib.parse
from collections import Counter
from datetime import datetime
from pathlib import Path

OUT_DIR = Path(__file__).parent
CSV_PATH = OUT_DIR / "2026.04.12_Foodberg_Wishlist.csv"
JSON_PATH = OUT_DIR / "2026.04.12_Foodberg_Wishlist.json"


def annas(query: str) -> str:
    return "https://annas-archive.org/search?q=" + urllib.parse.quote_plus(query)


def archorg(query: str) -> str:
    return "https://archive.org/search?query=" + urllib.parse.quote_plus(query)


def scholar(query: str) -> str:
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote_plus(query)


# ---------------------------------------------------------------------------
# ENTRIES — each tuple:
# (category, subcategory, last, first, title, year, publisher, type, commodity,
#  priority, status, notes, direct_url, relevance)
# ---------------------------------------------------------------------------

E: list[tuple] = []

def add(cat, sub, last, first, title, year, pub, typ, comm, prio, status, notes, url, rel):
    E.append((cat, sub, last, first, title, year, pub, typ, comm, prio, status, notes, url, rel))


# =============================================================================
# CATEGORY 1 — AGRICULTURAL ECONOMICS: FOUNDATIONS (target 30)
# =============================================================================
C = "Ag Econ Foundations"
add(C,"price_theory","Tomek","William G.","Agricultural Product Prices",2014,"Cornell UP","BOOK","none","CRITICAL","NEEDED","5th ed., with Kaiser; standard text","",scholar("Tomek Kaiser Agricultural Product Prices"))
add(C,"price_theory","Gardner","Bruce L.","The Economics of Agricultural Policy",2002,"Harvard UP","BOOK","none","CRITICAL","NEEDED","Foundational US ag-policy text","","Root understanding of how US farm policy shapes the prices Foodberg displays")
add(C,"price_theory","Schultz","Theodore W.","Agriculture in an Unstable Economy",1945,"McGraw-Hill","BOOK","none","HIGH","NEEDED","Nobelist; classic on farm-price instability","","Explains why farm prices swing so much")
add(C,"price_theory","Cochrane","Willard W.","Farm Prices: Myth and Reality",1958,"U Minnesota Press","BOOK","none","HIGH","NEEDED","Coined 'agricultural treadmill'","",scholar("Cochrane Farm Prices Myth and Reality"))
add(C,"supply_response","Nerlove","Marc","The Dynamics of Supply: Estimation of Farmers' Response to Price",1958,"Johns Hopkins","BOOK","none","HIGH","NEEDED","Founding work on supply response","",scholar("Nerlove Dynamics of Supply farmers response"))
add(C,"supply_response","Askari","Hossein","Agricultural Supply Response: A Survey",1976,"Praeger","BOOK","none","MEDIUM","NEEDED","Cross-country supply response survey","","")
add(C,"futures_markets","Working","Holbrook","The Theory of Price of Storage",1949,"American Economic Review","ARTICLE","none","CRITICAL","NEEDED","Seminal storage/futures paper","https://www.jstor.org/stable/1812975","Why grain prices have seasonal patterns")
add(C,"futures_markets","Kaldor","Nicholas","Speculation and Economic Stability",1939,"Review of Economic Studies","ARTICLE","none","HIGH","NEEDED","Convenience yield concept","https://www.jstor.org/stable/2967593","")
add(C,"futures_markets","Deaton","Angus","Competitive Storage and Commodity Price Dynamics",1992,"Journal of Political Economy","ARTICLE","none","CRITICAL","NEEDED","With Laroque; modern storage model","https://www.jstor.org/stable/2138602","Explains commodity-price serial correlation")
add(C,"futures_markets","Wright","Brian D.","The Economics of Grain Price Volatility",2011,"Applied Econ Perspectives & Policy","ARTICLE","cereals","HIGH","NEEDED","Post-2008 retrospective","https://doi.org/10.1093/aepp/ppq033","")
add(C,"futures_markets","Irwin","Scott H.","Index Funds, Financialization, and Commodity Futures Markets",2011,"Applied Econ Perspectives & Policy","ARTICLE","multi","HIGH","NEEDED","With Sanders","https://doi.org/10.1093/aepp/ppq032","Financialization of food commodities debate")
add(C,"futures_markets","Garcia","Philip","Estimated and Implied Volatility in Agricultural Futures",2005,"Journal of Ag & Applied Econ","ARTICLE","cereals","MEDIUM","NEEDED","Vol transmission","",scholar("Garcia volatility agricultural futures"))
add(C,"hedging_storage","Williams","Jeffrey C.","Storage and Commodity Markets",1991,"Cambridge UP","BOOK","none","HIGH","NEEDED","With Wright; storage-theory treatise","",scholar("Williams Wright Storage Commodity Markets"))
add(C,"hedging_storage","Pirrong","Craig","Commodity Price Dynamics: A Structural Approach",2011,"Cambridge UP","BOOK","none","MEDIUM","NEEDED","Modern commodity pricing","","")
add(C,"market_structure","Sexton","Richard J.","Market Power, Misconceptions, and Modern Agricultural Markets",2013,"AJAE","ARTICLE","multi","HIGH","NEEDED","Presidential address","https://doi.org/10.1093/ajae/aas102","Why concentration matters for prices chefs pay")
add(C,"market_structure","MacDonald","James M.","Concentration and Competition in U.S. Agribusiness",2017,"USDA ERS EIB-175","REPORT","multi","HIGH","NEEDED","Comprehensive concentration survey","https://www.ers.usda.gov/publications/pub-details/?pubid=84417","")
add(C,"price_theory","Just","Richard E.","The Welfare Economics of Public Policy",2004,"Edward Elgar","BOOK","none","MEDIUM","NEEDED","With Hueth, Schmitz; welfare tools","","")
add(C,"price_theory","Timmer","C. Peter","Food Policy Analysis",1983,"Johns Hopkins (World Bank)","BOOK","none","HIGH","NEEDED","With Falcon, Pearson; classic food policy text","",scholar("Timmer Falcon Pearson Food Policy Analysis"))
add(C,"price_theory","Norton","George W.","Economics of Agricultural Development",2015,"Routledge","BOOK","none","MEDIUM","NEEDED","With Alwang, Masters; 3rd ed","","")
add(C,"supply_response","Muth","John F.","Rational Expectations and the Theory of Price Movements",1961,"Econometrica","ARTICLE","none","HIGH","NEEDED","Motivated by hog-cycle problem","https://www.jstor.org/stable/1909635","")
add(C,"futures_markets","Hull","John C.","Options, Futures, and Other Derivatives",2021,"Pearson","BOOK","none","LOW","NEEDED","Reference derivative text","","Context for how commodity futures work")
add(C,"futures_markets","Geman","Helyette","Commodities and Commodity Derivatives",2005,"Wiley","BOOK","none","LOW","NEEDED","Quant reference","","")
add(C,"hedging_storage","Working","Holbrook","Futures Trading and Hedging",1953,"American Economic Review","ARTICLE","none","MEDIUM","NEEDED","Working's hedging-pressure theory","https://www.jstor.org/stable/1812835","")
add(C,"market_structure","Bain","Joe S.","Industrial Organization",1968,"Wiley","BOOK","none","LOW","NEEDED","Classic IO text; SCP paradigm","","Useful for packer-concentration arguments")
add(C,"price_theory","Barrett","Christopher B.","Displaced Distortions: Financial Market Failures and Seemingly Inefficient Resource Allocation",2008,"Ag Econ","ARTICLE","none","MEDIUM","NEEDED","Credit-constrained farmer decisions","","")
add(C,"supply_response","Askari","Hossein","Estimating Agricultural Supply Response with the Nerlove Model",1977,"International Economic Review","ARTICLE","none","LOW","NEEDED","Methodological note","","")
add(C,"futures_markets","Pindyck","Robert S.","The Dynamics of Commodity Spot and Futures Markets: A Primer",2001,"Energy Journal","ARTICLE","none","MEDIUM","NEEDED","Convenient survey","",scholar("Pindyck dynamics commodity spot futures primer"))
add(C,"price_theory","Myers","Robert J.","On the Costs of Food Price Fluctuations in Low-Income Countries",2006,"Food Policy","ARTICLE","none","MEDIUM","NEEDED","Welfare costs of volatility","","")
add(C,"market_structure","Hendrickson","Mary","Consolidation in the Food and Agriculture System",2001,"U Missouri","REPORT","multi","MEDIUM","NEEDED","Heffernan report tradition","",scholar("Hendrickson Heffernan consolidation food agriculture"))
add(C,"price_theory","Johnson","D. Gale","World Agriculture in Disarray",1973,"Fontana","BOOK","none","HIGH","NEEDED","Classic critique of trade-distorting policy","","")

# =============================================================================
# CATEGORY 2 — US COMMODITY POLICY (target 30)
# =============================================================================
C = "US Commodity Policy"
add(C,"farm_bills","Imhoff","Daniel","The Farm Bill: A Citizen's Guide",2019,"Island Press","BOOK","multi","CRITICAL","NEEDED","Most accessible Farm Bill primer","",scholar("Imhoff Farm Bill Citizen's Guide"))
add(C,"farm_bills","Hanrahan","Charles","The 2018 Farm Bill: Summary and Side-by-Side Comparison",2019,"CRS Report R45525","REPORT","multi","HIGH","NEEDED","Congressional Research Service","https://crsreports.congress.gov/product/pdf/R/R45525","")
add(C,"farm_bills","Schnepf","Randy","U.S. Farm Policy: History and Recent Trends",2019,"CRS Report","REPORT","multi","HIGH","NEEDED","Historical context of programs","https://crsreports.congress.gov/product/pdf/R/R45525","")
add(C,"farm_bills","Bowers","Douglas E.","History of Agricultural Price-Support and Adjustment Programs, 1933-84",1984,"USDA ERS AIB-485","REPORT","multi","HIGH","NEEDED","Gardner co-author; historical reference","",archorg("USDA agricultural price support programs 1933 1984"))
add(C,"subsidies_supports","Gardner","Bruce L.","American Agriculture in the Twentieth Century: How It Flourished and What It Cost",2002,"Harvard UP","BOOK","multi","CRITICAL","NEEDED","Definitive 20c US ag history","",scholar("Gardner American Agriculture Twentieth Century"))
add(C,"subsidies_supports","Orden","David","Policy Reform in American Agriculture",1999,"U Chicago Press","BOOK","multi","HIGH","NEEDED","With Paarlberg, Roe; FAIR Act analysis","","")
add(C,"subsidies_supports","Sumner","Daniel A.","Economic Analysis of U.S. Cotton Subsidy Programs",2006,"AJAE","ARTICLE","none","MEDIUM","NEEDED","WTO case context","","")
add(C,"biofuels_policy","Tyner","Wallace E.","The Integration of Energy and Agricultural Markets",2010,"Ag Econ","ARTICLE","cereals","HIGH","NEEDED","Corn-ethanol market linkage","","")
add(C,"biofuels_policy","Carter","Colin A.","The Effect of the U.S. Ethanol Mandate on Corn Prices",2017,"Ag Econ","ARTICLE","cereals","CRITICAL","NEEDED","With Rausser, Smith","https://doi.org/10.1111/agec.12316","Key paper on how ethanol policy moved corn prices Foodberg tracks")
add(C,"biofuels_policy","Babcock","Bruce A.","The Impact of US Biofuel Policies on Agricultural Price Levels and Volatility",2011,"ICTSD Issue Paper","REPORT","cereals","HIGH","NEEDED","Volatility focus","","")
add(C,"biofuels_policy","Schnepf","Randy","Renewable Fuel Standard (RFS): An Overview",2019,"CRS Report R43325","REPORT","cereals","HIGH","NEEDED","RFS policy primer","https://crsreports.congress.gov/product/pdf/R/R43325","")
add(C,"sugar_dairy_policy","Beghin","John C.","The Cost of the US Sugar Program Revisited",2017,"Applied Econ Perspectives & Policy","ARTICLE","sugar","HIGH","NEEDED","Welfare cost updates","","")
add(C,"sugar_dairy_policy","Schnepf","Randy","U.S. Sugar Program Fundamentals",2018,"CRS Report R44347","REPORT","sugar","HIGH","NEEDED","Tariff-rate quota mechanics","https://crsreports.congress.gov/product/pdf/R/R44347","")
add(C,"sugar_dairy_policy","Cessna","Jerry","The Dairy Margin Protection Program",2019,"USDA ERS","REPORT","dairy","MEDIUM","NEEDED","DMC program analysis","","")
add(C,"sugar_dairy_policy","Manchester","Alden C.","The Public Role in the Dairy Economy",1983,"Westview","BOOK","dairy","MEDIUM","NEEDED","Foundational FMMO history","","")
add(C,"conservation_policy","Claassen","Roger","Grassland to Cropland Conversion in the Northern Plains",2011,"USDA ERS ERR-120","REPORT","none","LOW","NEEDED","CRP & land-use","https://www.ers.usda.gov/publications","")
add(C,"farm_bills","Schnepf","Randy","Agriculture and the 2014 Farm Bill",2014,"CRS","REPORT","multi","MEDIUM","NEEDED","","","")
add(C,"subsidies_supports","Glauber","Joseph W.","The Growth of the Federal Crop Insurance Program",2013,"AJAE","ARTICLE","multi","HIGH","NEEDED","Crop insurance expansion","","")
add(C,"subsidies_supports","Smith","Vincent H.","Agricultural Subsidies in the WTO Green Box",2009,"Cambridge UP","BOOK","multi","MEDIUM","NEEDED","With Meléndez-Ortiz, Bellmann","","")
add(C,"biofuels_policy","de Gorter","Harry","The Economics of Biofuel Policies",2015,"Palgrave","BOOK","cereals","MEDIUM","NEEDED","With Drabik, Just","","")
add(C,"biofuels_policy","Hochman","Gal","Corn Ethanol and U.S. Biofuel Policy 10 Years Later",2018,"Applied Econ Perspectives & Policy","ARTICLE","cereals","MEDIUM","NEEDED","Retrospective","","")
add(C,"sugar_dairy_policy","Bryant","Henry","US Sugar Import Policy",2014,"Choices Magazine","ARTICLE","sugar","MEDIUM","NEEDED","Accessible overview","https://www.choicesmagazine.org/","")
add(C,"conservation_policy","Hellerstein","Daniel","The Conservation Reserve Program: 30 Years of Soil Conservation",2017,"USDA ERS EIB-169","REPORT","none","LOW","NEEDED","CRP land-supply effects","https://www.ers.usda.gov/publications/pub-details/?pubid=83915","")
add(C,"farm_bills","Coppess","Jonathan W.","The Fault Lines of Farm Policy: A History of the Farm Bill",2018,"U Nebraska Press","BOOK","multi","HIGH","NEEDED","Political-history approach","",scholar("Coppess Fault Lines Farm Policy"))
add(C,"subsidies_supports","Paarlberg","Robert","Food Politics: What Everyone Needs to Know",2020,"Oxford UP","BOOK","multi","HIGH","NEEDED","3rd ed.; accessible","",scholar("Paarlberg Food Politics"))
add(C,"biofuels_policy","Tyner","Wallace E.","The US Ethanol and Biofuels Boom: Its Origins, Current Status, and Future Prospects",2008,"BioScience","ARTICLE","cereals","MEDIUM","NEEDED","Early retrospective","","")
add(C,"sugar_dairy_policy","Bozic","Marin","Price Discovery in Federal Milk Marketing Orders",2012,"AJAE","ARTICLE","dairy","LOW","NEEDED","FMMO mechanics","","")
add(C,"subsidies_supports","Alston","Julian M.","A Global Perspective on Agricultural R&D",2010,"U Queensland","WORKING_PAPER","multi","LOW","NEEDED","R&D spending & productivity","","")
add(C,"farm_bills","Jurenas","Remy","Sugar Provisions of the 2008 Farm Bill",2008,"CRS","REPORT","sugar","LOW","NEEDED","","","")
add(C,"subsidies_supports","Westcott","Paul C.","USDA Agricultural Baseline Projections",2020,"USDA ERS","REPORT","multi","MEDIUM","NEEDED","Annual 10-year projections","https://www.ers.usda.gov/publications/pub-details/?pubid=103310","Projections feed directly into WASDE forecasts Foodberg displays")

# =============================================================================
# CATEGORY 3 — FOOD PRICE HISTORY LONG-RUN (target 40)
# =============================================================================
C = "Food Price History"
add(C,"pre_1900","Cronon","William","Nature's Metropolis: Chicago and the Great West",1991,"Norton","BOOK","cereals","CRITICAL","NEEDED","CBOT origin story","",scholar("Cronon Nature's Metropolis"))
add(C,"pre_1900","Rothenberg","Winifred B.","From Market-Places to a Market Economy",1992,"U Chicago Press","BOOK","multi","MEDIUM","NEEDED","Early New England ag markets","","")
add(C,"pre_1900","Atack","Jeremy","A New Economic View of American History",1994,"Norton","BOOK","multi","MEDIUM","NEEDED","With Passell; standard","","")
add(C,"pre_1900","Fogel","Robert W.","Railroads and American Economic Growth",1964,"Johns Hopkins","BOOK","cereals","LOW","NEEDED","Social-saving for grain transport","","")
add(C,"20c_inflation","Cochrane","Willard W.","The Development of American Agriculture: A Historical Analysis",1993,"U Minnesota Press","BOOK","multi","CRITICAL","NEEDED","Standard US ag history","",scholar("Cochrane Development American Agriculture"))
add(C,"20c_inflation","Schertz","Lyle P.","Another Revolution in U.S. Farming?",1979,"USDA ESCS","REPORT","multi","HIGH","NEEDED","Post-1973 transformation","",archorg("Schertz Another Revolution US Farming"))
add(C,"20c_inflation","Davis","Joseph S.","Wheat and the AAA",1935,"Brookings","BOOK","cereals","MEDIUM","NEEDED","Early New Deal ag policy","",archorg("Davis Wheat AAA Brookings 1935"))
add(C,"1970s_shock","Schertz","Lyle P.","World Food: Prices and the Poor",1973,"Foreign Affairs","ARTICLE","multi","HIGH","NEEDED","Start of 1973-74 food crisis framing","","")
add(C,"1970s_shock","Johnson","D. Gale","The World Food Situation: Developments During the 1970s",1976,"AJAE","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"1970s_shock","USDA","","The World Food Situation and Prospects to 1985",1974,"USDA FAER-98","REPORT","multi","MEDIUM","NEEDED","Original govt response doc","",archorg("USDA World Food Situation Prospects 1985"))
add(C,"1970s_shock","Luttrell","Clifton B.","The Russian Wheat Deal — Hindsight vs. Foresight",1973,"St. Louis Fed Review","ARTICLE","cereals","HIGH","NEEDED","Great Grain Robbery","https://research.stlouisfed.org/publications/review/1973/10/01/the-russian-wheat-deal-hindsight-vs-foresight","Explains why grain prices spiked in the 1970s")
add(C,"1970s_shock","Morgan","Dan","Merchants of Grain",1979,"Viking","BOOK","cereals","HIGH","NEEDED","Cargill/Continental grain giants","",scholar("Morgan Merchants of Grain"))
add(C,"2008_crisis","Headey","Derek","Anatomy of a Crisis: The Causes and Consequences of Surging Food Prices",2008,"Ag Econ","ARTICLE","multi","CRITICAL","NEEDED","With Fan; canonical 2008 paper","","Why food prices doubled in 2007-2008")
add(C,"2008_crisis","Abbott","Philip C.","What's Driving Food Prices?",2008,"Farm Foundation","REPORT","multi","CRITICAL","NEEDED","With Hurt, Tyner; landmark","",scholar("Abbott Hurt Tyner What's Driving Food Prices"))
add(C,"2008_crisis","Mitchell","Donald","A Note on Rising Food Prices",2008,"World Bank WP 4682","WORKING_PAPER","multi","HIGH","NEEDED","Attributed 75% to biofuels (controversial)","https://documents.worldbank.org/en/publication/documents-reports/documentdetail/229961468140943023","")
add(C,"2008_crisis","Trostle","Ronald","Global Agricultural Supply and Demand: Factors Contributing to the Recent Increase in Food Commodity Prices",2008,"USDA ERS WRS-0801","REPORT","multi","HIGH","NEEDED","USDA's crisis analysis","https://www.ers.usda.gov/publications/pub-details/?pubid=40470","")
add(C,"2008_crisis","Piesse","Jenifer","Three Bubbles and a Panic: An Explanatory Review of Recent Food Commodity Price Events",2009,"Food Policy","ARTICLE","multi","HIGH","NEEDED","With Thirtle","","")
add(C,"2008_crisis","Gilbert","Christopher L.","How to Understand High Food Prices",2010,"Journal of Ag Econ","ARTICLE","multi","HIGH","NEEDED","Financialization hypothesis","","")
add(C,"2011_spike","Tadesse","Getaw","Drivers and Triggers of International Food Price Spikes and Volatility",2014,"Food Policy","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"2011_spike","Lagi","Marco","The Food Crises and Political Instability in North Africa and the Middle East",2011,"NECSI","WORKING_PAPER","multi","MEDIUM","NEEDED","Food prices → Arab Spring","https://arxiv.org/abs/1108.2455","")
add(C,"2022_spike","Glauber","Joseph W.","The War in Ukraine, Agricultural Trade and Risks to Global Food Security",2022,"IFPRI","REPORT","cereals","HIGH","NEEDED","With Laborde","https://www.ifpri.org/blog/war-ukraine-agricultural-trade-and-risks-global-food-security","Most recent crisis visible in 2022 Foodberg data")
add(C,"2022_spike","FAO","","The Importance of Ukraine and the Russian Federation for Global Agricultural Markets",2022,"FAO","REPORT","cereals","HIGH","NEEDED","Info note","https://www.fao.org/3/cb9236en/cb9236en.pdf","")
add(C,"2022_spike","Carriquiry","Miguel","Russia's Invasion of Ukraine: Consequences for Global Agriculture",2022,"Applied Econ Perspectives & Policy","ARTICLE","cereals","HIGH","NEEDED","","","")
add(C,"secular_trends","Grilli","Enzo R.","Primary Commodity Prices, Manufactured Goods Prices, and the Terms of Trade of Developing Countries",1988,"World Bank Economic Review","ARTICLE","multi","HIGH","NEEDED","With Yang; Prebisch-Singer data","https://doi.org/10.1093/wber/2.1.1","")
add(C,"secular_trends","Erten","Bilge","Super-Cycles of Commodity Prices Since the Mid-Nineteenth Century",2013,"World Development","ARTICLE","multi","HIGH","NEEDED","With Ocampo","","")
add(C,"secular_trends","Pfaffenzeller","Stephan","A Short Note on Updating the Grilli and Yang Commodity Price Index",2007,"World Bank Economic Review","ARTICLE","multi","MEDIUM","NEEDED","Index-update methodology","","")
add(C,"secular_trends","Deaton","Angus","Commodity Prices and Growth in Africa",1999,"Journal of Economic Perspectives","ARTICLE","multi","MEDIUM","NEEDED","Resource curse + prices","https://doi.org/10.1257/jep.13.3.23","")
add(C,"2008_crisis","Sumner","Daniel A.","Recent Commodity Price Movements in Historical Perspective",2009,"AJAE","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"2008_crisis","Tangermann","Stefan","Policy Solutions to Agricultural Market Volatility",2011,"ICTSD","REPORT","multi","MEDIUM","NEEDED","","","")
add(C,"secular_trends","Baffes","John","A Framework for Analyzing the Interplay Among Food, Fuel, and Other Commodity Prices",2010,"World Bank Research Observer","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"20c_inflation","Rasmussen","Wayne D.","25 Years of Change in Farm Production and Efficiency, 1950-75",1978,"USDA SB-616","REPORT","multi","LOW","NEEDED","","",archorg("USDA 25 Years Change Farm Production Efficiency"))
add(C,"20c_inflation","Hurt","Chris","History of the Hog Cycle",2000,"Purdue Extension","REPORT","meat","MEDIUM","NEEDED","","","")
add(C,"pre_1900","Mintz","Sidney W.","Sweetness and Power: The Place of Sugar in Modern History",1985,"Viking","BOOK","sugar","CRITICAL","NEEDED","Sugar-history classic","",scholar("Mintz Sweetness and Power"))
add(C,"pre_1900","Kurlansky","Mark","Salt: A World History",2002,"Walker","BOOK","none","MEDIUM","NEEDED","Commodity history","",scholar("Kurlansky Salt World History"))
add(C,"pre_1900","Kurlansky","Mark","Cod: A Biography of the Fish That Changed the World",1997,"Walker","BOOK","meat","MEDIUM","NEEDED","","","")
add(C,"pre_1900","Kurlansky","Mark","Milk! A 10,000-Year Food Fracas",2018,"Bloomsbury","BOOK","dairy","MEDIUM","NEEDED","","","")
add(C,"secular_trends","Fogel","Robert W.","The Escape from Hunger and Premature Death, 1700-2100",2004,"Cambridge UP","BOOK","none","MEDIUM","NEEDED","Nutrition + economic history","","")
add(C,"1970s_shock","Tweeten","Luther","Foundations of Farm Policy",1979,"U Nebraska Press","BOOK","multi","MEDIUM","NEEDED","Classic ag-policy text","","")
add(C,"2008_crisis","Meyer","Seth","Prospects for Returning to More Normal World Agricultural Commodity Markets",2010,"Ag Econ","ARTICLE","multi","LOW","NEEDED","","","")
add(C,"2022_spike","Laborde","David","Implications of the War in Ukraine for Agricultural Markets",2022,"IFPRI","REPORT","cereals","HIGH","NEEDED","","","")

# =============================================================================
# CATEGORY 4 — CEREALS & GRAINS (target 35)
# =============================================================================
C = "Cereals Grains"
add(C,"wheat","Olmstead","Alan L.","The Red Queen and the Hard Reds: Productivity Growth in American Wheat, 1800-1940",2002,"Journal of Economic History","ARTICLE","cereals","HIGH","NEEDED","With Rhode","","Historical context for wheat prices in US")
add(C,"wheat","Malenbaum","Wilfred","The World Wheat Economy, 1885-1939",1953,"Harvard UP","BOOK","cereals","MEDIUM","NEEDED","Classic wheat-market history","",archorg("Malenbaum World Wheat Economy"))
add(C,"wheat","Chattopadhyay","Sumit","The Global Wheat Market: Production, Trade, and Pricing",2020,"Routledge","BOOK","cereals","MEDIUM","NEEDED","","","")
add(C,"corn","Walters","Alan A.","The Global Corn Economy",2015,"Elsevier","BOOK","cereals","HIGH","NEEDED","","","")
add(C,"corn","Carter","Colin A.","Biofuels and Agricultural Commodity Prices: A Review of the Evidence Base",2016,"Ecological Economics","ARTICLE","cereals","HIGH","NEEDED","With Rausser, Smith","","")
add(C,"corn","Hertel","Thomas W.","Impacts of US Ethanol Mandate on World Agriculture",2010,"AJAE","ARTICLE","cereals","HIGH","NEEDED","","","")
add(C,"corn","Wright","Brian D.","Global Biofuels: Key to the Puzzle of Grain Market Behavior",2014,"J Econ Perspectives","ARTICLE","cereals","CRITICAL","NEEDED","","https://doi.org/10.1257/jep.28.1.73","")
add(C,"rice","Slayton","Tom","Rice Crisis Forensics: How Asian Governments Carelessly Set the World Rice Market on Fire",2009,"Center for Global Development WP 163","WORKING_PAPER","cereals","CRITICAL","NEEDED","Classic on 2008 rice spike","https://www.cgdev.org/publication/rice-crisis-forensics-how-asian-governments-carelessly-set-world-rice-market-fire","")
add(C,"rice","Timmer","C. Peter","Managing the World Rice Market",2010,"AJAE","ARTICLE","cereals","HIGH","NEEDED","","","")
add(C,"rice","Dawe","David","The Rice Crisis: Markets, Policies and Food Security",2010,"Earthscan/FAO","BOOK","cereals","HIGH","NEEDED","","","")
add(C,"soybeans","Chern","Wen S.","The US-China Soybean Trade and the 2018 Tariffs",2019,"Choices Magazine","ARTICLE","cereals","HIGH","NEEDED","Trade war","","")
add(C,"soybeans","Taheripour","Farzad","The Impact of Considering Land Intensification and Updated Land Use Data on Biofuels Carbon Savings",2016,"Environmental Research Letters","ARTICLE","cereals","MEDIUM","NEEDED","","","")
add(C,"soybeans","Gale","Fred","The Rise of China's Demand for Soybeans",2019,"USDA ERS","REPORT","cereals","HIGH","NEEDED","","https://www.ers.usda.gov/publications","China as price-mover in soybean markets")
add(C,"cbot_futures","Lurie","Jonathan","The Chicago Board of Trade, 1859-1905",1979,"U Illinois Press","BOOK","cereals","HIGH","NEEDED","Institutional history","",scholar("Lurie Chicago Board Trade 1859 1905"))
add(C,"cbot_futures","Santos","Joseph","A History of Futures Trading in the United States",2008,"EH.net Encyclopedia","ARTICLE","none","MEDIUM","NEEDED","","https://eh.net/encyclopedia/a-history-of-futures-trading-in-the-united-states/","")
add(C,"cbot_futures","Williams","Jeffrey C.","The Origin of Futures Markets",1982,"Agricultural History","ARTICLE","cereals","MEDIUM","NEEDED","","","")
add(C,"yield_weather","Schlenker","Wolfram","Nonlinear Temperature Effects Indicate Severe Damages to U.S. Crop Yields Under Climate Change",2009,"PNAS","ARTICLE","cereals","CRITICAL","NEEDED","With Roberts","https://doi.org/10.1073/pnas.0906865106","Climate-yield key paper")
add(C,"yield_weather","Lobell","David B.","The Influence of Climate Change on Global Crop Productivity",2012,"Plant Physiology","ARTICLE","cereals","HIGH","NEEDED","With Gourdji","","")
add(C,"yield_weather","Deschênes","Olivier","The Economic Impacts of Climate Change: Evidence from Agricultural Output and Random Fluctuations in Weather",2007,"AER","ARTICLE","cereals","HIGH","NEEDED","With Greenstone","","")
add(C,"corn","FAO","","World Food Situation: Cereal Supply and Demand Brief",2024,"FAO","REPORT","cereals","MEDIUM","NEEDED","Monthly series","https://www.fao.org/worldfoodsituation/csdb/en/","")
add(C,"wheat","USDA","","Wheat Outlook (monthly)",2024,"USDA ERS","REPORT","cereals","HIGH","NEEDED","Primary WASDE-linked publication","https://www.ers.usda.gov/publications/periodicals/","")
add(C,"corn","USDA","","Feed Outlook (monthly)",2024,"USDA ERS","REPORT","cereals","HIGH","NEEDED","Corn + sorghum","https://www.ers.usda.gov/publications/periodicals/","")
add(C,"rice","USDA","","Rice Outlook (monthly)",2024,"USDA ERS","REPORT","cereals","HIGH","NEEDED","","https://www.ers.usda.gov/publications/periodicals/","")
add(C,"soybeans","USDA","","Oil Crops Outlook (monthly)",2024,"USDA ERS","REPORT","cereals","HIGH","NEEDED","Soy + other oilseeds","https://www.ers.usda.gov/publications/periodicals/","")
add(C,"wheat","Irwin","Scott H.","The Financialization of Commodity Futures Markets and the Adequacy of Speculation",2012,"Ag Applied Econ","ARTICLE","cereals","HIGH","NEEDED","With Sanders","","")
add(C,"corn","Hayes","Dermot J.","Corn Belt Economic Outlook",2024,"Iowa State CARD","REPORT","cereals","MEDIUM","NEEDED","","https://www.card.iastate.edu/","")
add(C,"soybeans","Westhoff","Patrick","The Economics of Food: How Feeding and Fueling the Planet Affects Food Prices",2010,"FT Press","BOOK","multi","HIGH","NEEDED","Accessible","",scholar("Westhoff Economics of Food"))
add(C,"yield_weather","Burke","Marshall","The Economic Impacts of Climate Change in the United States",2015,"Nature Climate Change","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"wheat","Cooke","Bryce","Recent Convergence Performance of CBOT Corn, Soybean, and Wheat Futures Contracts",2011,"AJAE","ARTICLE","cereals","MEDIUM","NEEDED","With Robles","","")
add(C,"cbot_futures","Sanders","Dwight R.","A Speculative Bubble in Commodity Futures Prices? Cross-Sectional Evidence",2010,"Ag Econ","ARTICLE","cereals","MEDIUM","NEEDED","With Irwin","","")
add(C,"yield_weather","Roberts","Michael J.","The Effect of the Price of Corn on Corn Yield",2013,"Ag Econ","ARTICLE","cereals","MEDIUM","NEEDED","","","")
add(C,"corn","Du","Xiaodong","Speculation and Volatility Spillover in the Crude Oil and Agricultural Commodity Markets",2011,"Energy Econ","ARTICLE","cereals","MEDIUM","NEEDED","","","")
add(C,"rice","Headey","Derek","Rethinking the Global Food Crisis: The Role of Trade Shocks",2011,"Food Policy","ARTICLE","cereals","HIGH","NEEDED","","","")
add(C,"wheat","Kornher","Lukas","Explaining Wheat Price Volatility in Global Markets",2019,"Applied Econ Perspectives & Policy","ARTICLE","cereals","MEDIUM","NEEDED","","","")
add(C,"cbot_futures","Carlton","Dennis W.","Futures Markets: Their Purpose, Their History, Their Growth",1984,"Journal of Futures Markets","ARTICLE","cereals","LOW","NEEDED","","","")

# =============================================================================
# CATEGORY 5 — MEAT & LIVESTOCK (target 30)
# =============================================================================
C = "Meat Livestock"
add(C,"packer_concentration","MacDonald","James M.","Consolidation in U.S. Meatpacking",2000,"USDA ERS AER-785","REPORT","meat","CRITICAL","NEEDED","Canonical packer-concentration study","https://www.ers.usda.gov/publications/pub-details/?pubid=41108","Why 4 firms dominate US beef — affects the prices Foodberg shows")
add(C,"packer_concentration","Wise","Timothy A.","Still Waiting for the Farm Boom",2014,"Tufts GDAE","REPORT","meat","MEDIUM","NEEDED","","","")
add(C,"packer_concentration","Crespi","John M.","Packer Concentration, Captive Supplies, and the Meat Markets",2013,"Ag Econ","ARTICLE","meat","HIGH","NEEDED","","","")
add(C,"beef_cattle","Schroeder","Ted C.","Economic Impact of COVID-19 on the US Beef Industry",2020,"Agribusiness","ARTICLE","meat","HIGH","NEEDED","","","")
add(C,"beef_cattle","Peel","Derrell S.","Cattle Market Outlook",2024,"OSU Extension","REPORT","meat","MEDIUM","NEEDED","","","")
add(C,"beef_cattle","Horowitz","Roger","Putting Meat on the American Table: Taste, Technology, Transformation",2006,"Johns Hopkins","BOOK","meat","HIGH","NEEDED","Meat industrialization history","",scholar("Horowitz Putting Meat American Table"))
add(C,"pork","Plain","Ronald L.","Hog Market Volatility",2000,"Review of Ag Econ","ARTICLE","meat","MEDIUM","NEEDED","","","")
add(C,"pork","Key","Nigel","Production Contracts and Productivity in the U.S. Hog Sector",2005,"AJAE","ARTICLE","meat","MEDIUM","NEEDED","With McBride","","")
add(C,"poultry","Goodwin","Harold L.","The US Poultry Industry: A Success Story in Productivity Enhancement",2004,"Choices Magazine","ARTICLE","meat","MEDIUM","NEEDED","","","")
add(C,"poultry","MacDonald","James M.","The Economic Organization of US Broiler Production",2008,"USDA ERS EIB-38","REPORT","meat","HIGH","NEEDED","Vertical integration","https://www.ers.usda.gov/publications/pub-details/?pubid=44237","")
add(C,"feed_costs","Marsh","John M.","Cross-Sector Relationships Between the Corn Feed Grains and Livestock and Poultry Economies",2007,"Journal of Ag Applied Econ","ARTICLE","meat","HIGH","NEEDED","Feed-cost pass-through","","Corn prices → meat prices causal chain")
add(C,"feed_costs","Pozo","Veronica F.","Dynamic Relationships in the Beef Market",2013,"Ag Econ","ARTICLE","meat","MEDIUM","NEEDED","","","")
add(C,"livestock_policy","Hahn","William F.","Beef and Pork Values and Price Spreads Explained",2004,"USDA ERS LDP-M-118-01","REPORT","meat","HIGH","NEEDED","Farm-to-retail margins","https://www.ers.usda.gov/publications","Understanding margin structure in meat prices")
add(C,"livestock_policy","Mathews","Kenneth H.","U.S. Beef Industry: Cattle Cycles, Price Spreads, and Packer Concentration",1999,"USDA ERS TB-1874","REPORT","meat","HIGH","NEEDED","","",archorg("USDA Beef Industry Cattle Cycles Price Spreads"))
add(C,"livestock_policy","Lusk","Jayson L.","Animal Welfare Economics",2011,"Applied Econ Perspectives & Policy","ARTICLE","meat","MEDIUM","NEEDED","With Norwood","","")
add(C,"beef_cattle","USDA","","Livestock, Dairy, and Poultry Outlook (monthly)",2024,"USDA ERS","REPORT","multi","HIGH","NEEDED","LDP-M monthly","https://www.ers.usda.gov/publications/periodicals/","")
add(C,"packer_concentration","Azzam","Azzeddine M.","Captive Supplies, Market Conduct, and the Open-Market Price",1998,"AJAE","ARTICLE","meat","MEDIUM","NEEDED","","","")
add(C,"pork","Lawrence","John D.","Pork Industry Concentration",2006,"Iowa State","REPORT","meat","MEDIUM","NEEDED","","","")
add(C,"poultry","Ollinger","Michael","Structural Change in U.S. Chicken and Turkey Slaughter",2000,"USDA ERS AER-787","REPORT","meat","MEDIUM","NEEDED","","","")
add(C,"beef_cattle","Martin","Michael","A History of the Beef Industry",2015,"TAMU","WORKING_PAPER","meat","MEDIUM","NEEDED","","","")
add(C,"feed_costs","Tonsor","Glynn T.","Assessing Beef Demand Determinants",2015,"K-State","REPORT","meat","MEDIUM","NEEDED","","","")
add(C,"beef_cattle","Schroeder","Ted C.","Beef Demand Determinants",2000,"Journal of Ag Applied Econ","ARTICLE","meat","MEDIUM","NEEDED","","","")
add(C,"livestock_policy","Peel","Derrell S.","Beef Cattle Growing and Backgrounding Programs",2003,"OSU","REPORT","meat","LOW","NEEDED","","","")
add(C,"packer_concentration","Saitone","Tina L.","An Empirical Investigation of Imperfect Competition in Commodity Procurement",2015,"AJAE","ARTICLE","meat","MEDIUM","NEEDED","","","")
add(C,"pork","Mayen","Carlos D.","The Impact of Avian Influenza on Egg and Poultry Prices",2009,"J Ag Applied Econ","ARTICLE","meat","LOW","NEEDED","","","")
add(C,"poultry","Muth","Mary K.","Industry Concentration in U.S. Meatpacking",2007,"RTI","REPORT","meat","LOW","NEEDED","","","")
add(C,"beef_cattle","Rude","James","The Effects of Mandatory Country-of-Origin Labeling on Cattle and Beef Markets",2015,"Ag Econ","ARTICLE","meat","LOW","NEEDED","COOL","","")
add(C,"feed_costs","Marsh","John M.","Derived Demand and Price Volatility in the Beef and Pork Sectors",1994,"J Ag Resource Econ","ARTICLE","meat","MEDIUM","NEEDED","","","")
add(C,"livestock_policy","Kalaitzandonakes","Nicholas","Price Transmission Dynamics Between ADM and Nearby Illinois Markets for Corn",1999,"J Agribusiness","ARTICLE","meat","LOW","NEEDED","","","")
add(C,"beef_cattle","Elam","Emmett","Relationship of Cattle Futures Prices to Cash Prices",1988,"J Futures Markets","ARTICLE","meat","LOW","NEEDED","","","")

# =============================================================================
# CATEGORY 6 — DAIRY (target 20)
# =============================================================================
C = "Dairy"
add(C,"us_dairy_policy","Bozic","Marin","Risk Management in the Dairy Sector",2013,"U Minnesota","REPORT","dairy","HIGH","NEEDED","","","")
add(C,"us_dairy_policy","Novakovic","Andrew M.","The Economics of Milk Pricing",2005,"Cornell","REPORT","dairy","HIGH","NEEDED","","","")
add(C,"us_dairy_policy","Manchester","Alden C.","The Transformation of US Dairying in the 20th Century",1997,"USDA ERS","REPORT","dairy","HIGH","NEEDED","","",archorg("USDA Manchester Transformation Dairying"))
add(C,"milk_markets","Chouinard","Hayley H.","Milk Marketing Order Winners and Losers",2010,"Applied Econ Perspectives & Policy","ARTICLE","dairy","MEDIUM","NEEDED","","","")
add(C,"milk_markets","Cakir","Metin","Market Power in Federal Milk Marketing Orders",2014,"Ag Econ","ARTICLE","dairy","MEDIUM","NEEDED","","","")
add(C,"global_dairy","Cessna","Jerry","The Growth of New Zealand Dairy and Dairy Trade",2016,"USDA ERS LDPM-264-01","REPORT","dairy","HIGH","NEEDED","","https://www.ers.usda.gov/publications","NZ as world dairy price-maker")
add(C,"global_dairy","OECD","","OECD-FAO Agricultural Outlook: Dairy Chapter",2024,"OECD","REPORT","dairy","HIGH","NEEDED","Annual 10-year outlook","https://www.oecd.org/agriculture/oecd-fao-agricultural-outlook/","")
add(C,"cheese_butter","Cropp","Bob","A Century of Dairy Marketing in the US",2001,"U Wisconsin","REPORT","dairy","MEDIUM","NEEDED","","","")
add(C,"us_dairy_policy","Stephenson","Mark W.","Dairy Margin Coverage Program Analysis",2019,"Cornell","REPORT","dairy","MEDIUM","NEEDED","","","")
add(C,"milk_markets","Nicholson","Charles F.","The World Dairy Situation",2018,"Cornell","REPORT","dairy","MEDIUM","NEEDED","","","")
add(C,"global_dairy","Zhou","Jehan","Factors Driving Changes in China's Dairy Industry",2018,"China Ag Econ Review","ARTICLE","dairy","MEDIUM","NEEDED","","","")
add(C,"cheese_butter","Capps","Oral","Consumer Demand for Cheese and Butter",2014,"J Ag Applied Econ","ARTICLE","dairy","LOW","NEEDED","","","")
add(C,"us_dairy_policy","USDA","","Dairy Products Prices (NASS)",2024,"USDA NASS","DATASET_DOC","dairy","HIGH","NEEDED","Weekly dairy price survey docs","https://www.nass.usda.gov/Publications/","Source for FMMO pricing — directly feeds Foodberg")
add(C,"milk_markets","Balagtas","Joseph V.","Impacts of US Dairy Policy on Milk and Dairy Product Prices",2003,"Purdue","WORKING_PAPER","dairy","LOW","NEEDED","","","")
add(C,"global_dairy","Fonterra","","Global Dairy Trade Methodology",2024,"Fonterra","DATASET_DOC","dairy","MEDIUM","NEEDED","GDT auction methodology","https://www.globaldairytrade.info/","GDT sets global dairy benchmark prices")
add(C,"us_dairy_policy","Sumner","Daniel A.","Economic Impacts of Elimination of US Dairy Price Supports",2003,"J Dairy Science","ARTICLE","dairy","LOW","NEEDED","","","")
add(C,"cheese_butter","Dhar","Tirtha P.","Market Structure and Pricing of Dairy Products in US",2003,"AJAE","ARTICLE","dairy","LOW","NEEDED","","","")
add(C,"milk_markets","Awokuse","Titus O.","Price Volatility Spillovers in the Wheat, Corn, and Milk Markets",2013,"Ag Resource Econ Review","ARTICLE","dairy","LOW","NEEDED","","","")
add(C,"us_dairy_policy","USDA","","Federal Milk Marketing Orders Statistics",2024,"USDA AMS","DATASET_DOC","dairy","HIGH","NEEDED","","https://www.ams.usda.gov/resources/marketing-order-statistics","")
add(C,"global_dairy","IFCN","","IFCN Dairy Report 2024",2024,"International Farm Comparison Network","REPORT","dairy","MEDIUM","NEEDED","Global dairy benchmark","https://ifcndairy.org/","")

# =============================================================================
# CATEGORY 7 — OILS & FATS (target 20)
# =============================================================================
C = "Oils Fats"
add(C,"palm_oil","Byerlee","Derek","The Tropical Oil Crop Revolution",2017,"Oxford UP","BOOK","oils","CRITICAL","NEEDED","With Falcon, Naylor","",scholar("Byerlee Falcon Naylor Tropical Oil Crop Revolution"))
add(C,"palm_oil","Corley","R. H. V.","The Oil Palm",2016,"Wiley","BOOK","oils","HIGH","NEEDED","With Tinker; 5th ed","","")
add(C,"palm_oil","Rival","Alain","Palms of Controversies: Oil Palm and Development Challenges",2013,"CIRAD","BOOK","oils","MEDIUM","NEEDED","With Levang","","")
add(C,"soy_oil","Goldsmith","Peter D.","Economics of Soybean Production, Marketing, and Utilization",2008,"in Soybeans: Chemistry, Production, Processing, and Utilization","CHAPTER","oils","MEDIUM","NEEDED","","","")
add(C,"soy_oil","Gallagher","Paul W.","A Reassessment of the Contribution of U.S. Corn Ethanol and Soybean Biodiesel",2019,"Biofuels Bioproducts Biorefining","ARTICLE","oils","MEDIUM","NEEDED","","","")
add(C,"canola_sunflower","FAOSTAT","","Oilcrops Production and Trade Database Documentation",2024,"FAO","DATASET_DOC","oils","MEDIUM","NEEDED","","https://www.fao.org/faostat/","")
add(C,"olive_oil","Mili","Samir","The Olive Oil Sector: A Comparative Analysis of Spain and Italy",2006,"New Medit","ARTICLE","oils","MEDIUM","NEEDED","","","")
add(C,"olive_oil","International Olive Council","","World Olive Oil Figures",2024,"IOC","DATASET_DOC","oils","MEDIUM","NEEDED","","https://www.internationaloliveoil.org/","")
add(C,"tropical_cycles","Baffes","John","Oil Spills on Other Commodities",2007,"World Bank WP 4333","WORKING_PAPER","multi","HIGH","NEEDED","Energy-food linkage","","")
add(C,"palm_oil","Sayer","Jeffrey","Sustainable Production of Palm Oil for the 21st Century",2012,"Environmental Research Letters","ARTICLE","oils","MEDIUM","NEEDED","","","")
add(C,"soy_oil","Masuda","Tadayoshi","An Analysis of Rising Food Prices: Global Demand, Supply, and Production of Oilseeds",2009,"Japanese J Rural Econ","ARTICLE","oils","LOW","NEEDED","","","")
add(C,"tropical_cycles","USDA","","Oilseeds: World Markets and Trade (monthly)",2024,"USDA FAS","REPORT","oils","HIGH","NEEDED","","https://www.fas.usda.gov/data/oilseeds-world-markets-and-trade","")
add(C,"palm_oil","Pirker","Johannes","What Are the Limits to Oil Palm Expansion?",2016,"Global Environmental Change","ARTICLE","oils","MEDIUM","NEEDED","","","")
add(C,"soy_oil","Fabiosa","Jacinto F.","Land-Use Credits to Corn Ethanol: Accounting for Distillers' Grains",2009,"CARD Iowa State","WORKING_PAPER","oils","LOW","NEEDED","","","")
add(C,"olive_oil","Carbone","Anna","The Performance of Protected Designations of Origin: An Ideal Benchmark for the Italian Olive Oil Sector",2018,"Cambridge University Press","ARTICLE","oils","LOW","NEEDED","","","")
add(C,"canola_sunflower","Schnepf","Randy","Rising Farm Input Costs and Impacts on Production",2022,"CRS","REPORT","oils","MEDIUM","NEEDED","","","")
add(C,"tropical_cycles","Headey","Derek","The Impact of the Global Food Crisis on the Poor",2011,"Food Policy","ARTICLE","oils","MEDIUM","NEEDED","","","")
add(C,"palm_oil","Cramb","Rob","The Oil Palm Complex: Smallholders, Agribusiness and the State in Indonesia and Malaysia",2016,"NUS Press","BOOK","oils","HIGH","NEEDED","","","")
add(C,"soy_oil","Brown","Lester R.","Outgrowing the Earth: The Food Security Challenge in an Age of Falling Water Tables",2005,"Earth Policy Institute","BOOK","multi","MEDIUM","NEEDED","","","")
add(C,"olive_oil","Kashiwagi","Kenichi","Olive Oil Price Volatility in Tunisia and Spain",2020,"New Medit","ARTICLE","oils","LOW","NEEDED","","","")

# =============================================================================
# CATEGORY 8 — SUGAR & SWEETENERS (target 15)
# =============================================================================
C = "Sugar Sweeteners"
add(C,"cane_beet","Abbott","Philip C.","Economic Development of the World's Sugar Industry",2011,"in Encyclopedia of Agricultural Economics","CHAPTER","sugar","MEDIUM","NEEDED","","","")
add(C,"cane_beet","Galloway","J. H.","The Sugar Cane Industry: An Historical Geography",1989,"Cambridge UP","BOOK","sugar","HIGH","NEEDED","","",scholar("Galloway Sugar Cane Industry Historical Geography"))
add(C,"hfcs","Beghin","John C.","US Sugar Policy: Analysis and Options",2013,"Iowa State CARD","WORKING_PAPER","sugar","CRITICAL","NEEDED","With Elobeid","","Why US sugar is 2x world price — affects every chef buying sugar")
add(C,"hfcs","Haley","Stephen L.","Modeling the U.S. Sweetener Sector",1998,"USDA ERS TB-1873","REPORT","sugar","HIGH","NEEDED","","",archorg("USDA Modeling US Sweetener Sector"))
add(C,"hfcs","Bray","George A.","Consumption of High-Fructose Corn Syrup in Beverages May Play a Role in the Epidemic of Obesity",2004,"Am J Clinical Nutrition","ARTICLE","sugar","LOW","NEEDED","","","")
add(C,"us_sugar_program","Jurenas","Remy","U.S. Sugar Program Overview",2016,"CRS","REPORT","sugar","HIGH","NEEDED","","","")
add(C,"us_sugar_program","Haley","Stephen L.","The U.S. Sugar Program and Its Effects",2016,"USDA ERS","REPORT","sugar","HIGH","NEEDED","","","")
add(C,"global_sugar","Rutherford","Ardian","The World Sugar Market",2010,"Blackwell","BOOK","sugar","MEDIUM","NEEDED","","","")
add(C,"global_sugar","Yadav","A. K.","Sugar Markets and Sugar Price Dynamics",2019,"Review of Ag Econ","ARTICLE","sugar","MEDIUM","NEEDED","","","")
add(C,"global_sugar","LMC International","","LMC Sweeteners Analysis",2024,"LMC","REPORT","sugar","LOW","NEEDED","Trade-press benchmark","","")
add(C,"cane_beet","Otter","Chris","Diet for a Large Planet",2020,"U Chicago Press","BOOK","sugar","MEDIUM","NEEDED","","","")
add(C,"us_sugar_program","USDA","","Sugar and Sweeteners Outlook",2024,"USDA ERS","REPORT","sugar","HIGH","NEEDED","Monthly","https://www.ers.usda.gov/publications/periodicals/","")
add(C,"hfcs","Philpott","Tom","Perilous Bounty: The Looming Collapse of American Farming",2020,"Bloomsbury","BOOK","multi","MEDIUM","NEEDED","","","")
add(C,"global_sugar","ISO","","World Sugar Statistical Yearbook",2024,"International Sugar Organization","DATASET_DOC","sugar","MEDIUM","NEEDED","","https://www.isosugar.org/","")
add(C,"cane_beet","Aurand","Joseph","A Brief History of the US Sugar Industry",2019,"USDA","REPORT","sugar","LOW","NEEDED","","","")

# =============================================================================
# CATEGORY 9 — PRODUCE / FRUITS / VEGETABLES (target 20)
# =============================================================================
C = "Produce"
add(C,"seasonality","Richards","Timothy J.","Retail Competition and the Price of Fruit",2006,"J Ag Resource Econ","ARTICLE","produce","MEDIUM","NEEDED","","","")
add(C,"seasonality","Lucier","Gary","Vegetables and Pulses Yearbook",2024,"USDA ERS","DATASET_DOC","produce","HIGH","NEEDED","Annual","https://www.ers.usda.gov/data-products/vegetables-and-pulses-data","")
add(C,"labor_costs","Martin","Philip","Labor Shortages Ahead: Agriculture and H-2A Visa Program",2016,"UC Davis","REPORT","produce","CRITICAL","NEEDED","","",scholar("Philip Martin H-2A agricultural labor"))
add(C,"labor_costs","Charlton","Diane","Declining International Migration of Mexican Farm Workers",2016,"J Political Economy","ARTICLE","produce","HIGH","NEEDED","With Taylor","","")
add(C,"cold_chain","Sheffi","Yossi","Logistics Clusters",2012,"MIT Press","BOOK","produce","MEDIUM","NEEDED","","","")
add(C,"cold_chain","Saenz-Segura","Fernando","Cold Chain Management for Produce in Developing Countries",2013,"WUR","WORKING_PAPER","produce","LOW","NEEDED","","","")
add(C,"specialty_crops","USDA","","Fruit and Tree Nuts Yearbook Tables",2024,"USDA ERS","DATASET_DOC","produce","HIGH","NEEDED","","https://www.ers.usda.gov/data-products/fruit-and-tree-nuts-data","")
add(C,"specialty_crops","Cook","Roberta","Supermarket Challenges and Opportunities for Fresh Fruit and Vegetable Producers",2011,"Choices Magazine","ARTICLE","produce","MEDIUM","NEEDED","","","")
add(C,"water_ag","Cooley","Heather","California Agricultural Water Use: Key Background Information",2015,"Pacific Institute","REPORT","produce","HIGH","NEEDED","","",scholar("Cooley California agricultural water use"))
add(C,"water_ag","Howitt","Richard","Economic Analysis of the 2014 Drought for California Agriculture",2014,"UC Davis","REPORT","produce","HIGH","NEEDED","","","")
add(C,"seasonality","Park","Timothy A.","Choice Behavior for US Fresh Vegetable Consumers",2011,"J Ag Applied Econ","ARTICLE","produce","LOW","NEEDED","","","")
add(C,"labor_costs","Zahniser","Steven","Farm Labor and Immigration Policy",2018,"USDA ERS","REPORT","produce","HIGH","NEEDED","","","")
add(C,"specialty_crops","Cook","Roberta","Trends in the Marketing of Fresh Produce and Fresh-Cut Products",2011,"UC Davis","REPORT","produce","MEDIUM","NEEDED","","","")
add(C,"cold_chain","Mercier","Stephanie","Grocery Retailing and Wholesaling",2019,"Farm Foundation","REPORT","produce","LOW","NEEDED","","","")
add(C,"water_ag","Lund","Jay","Water Markets in California",2014,"UC Davis","REPORT","produce","MEDIUM","NEEDED","","","")
add(C,"seasonality","Gopinath","Munisamy","Price Transmission in Fresh Fruit and Vegetable Markets",2012,"J Ag Applied Econ","ARTICLE","produce","LOW","NEEDED","","","")
add(C,"specialty_crops","Calvin","Linda","Fresh Fruit and Vegetable Imports and the U.S. Market",2009,"USDA ERS","REPORT","produce","MEDIUM","NEEDED","","","")
add(C,"labor_costs","Fan","Maoyong","The Role of H-2A in US Agriculture",2015,"AJAE","ARTICLE","produce","MEDIUM","NEEDED","","","")
add(C,"water_ag","Schwabe","Kurt","The Role of Water in the California Economy",2015,"UC ANR","REPORT","produce","LOW","NEEDED","","","")
add(C,"seasonality","Pollack","Susan","ERS Fruit and Vegetable Prices Data Product",2024,"USDA ERS","DATASET_DOC","produce","HIGH","NEEDED","","https://www.ers.usda.gov/data-products/fruit-and-vegetable-prices/","Core fruit+veg price dataset")

# =============================================================================
# CATEGORY 10 — GLOBAL FOOD SYSTEMS (target 35)
# =============================================================================
C = "Global Food Systems"
add(C,"green_revolution","Evenson","Robert E.","Assessing the Impact of the Green Revolution, 1960 to 2000",2003,"Science","ARTICLE","multi","CRITICAL","NEEDED","With Gollin","https://doi.org/10.1126/science.1078710","Green Revolution's price effect — bedrock of modern food-price reality")
add(C,"green_revolution","Hazell","Peter B. R.","The Asian Green Revolution",2009,"IFPRI DP 911","WORKING_PAPER","multi","HIGH","NEEDED","","","")
add(C,"green_revolution","Pingali","Prabhu L.","Green Revolution: Impacts, Limits, and the Path Ahead",2012,"PNAS","ARTICLE","multi","HIGH","NEEDED","","https://doi.org/10.1073/pnas.0912953109","")
add(C,"green_revolution","Perkins","John H.","Geopolitics and the Green Revolution",1997,"Oxford UP","BOOK","multi","MEDIUM","NEEDED","","","")
add(C,"green_revolution","Cullather","Nick","The Hungry World: America's Cold War Battle Against Poverty in Asia",2010,"Harvard UP","BOOK","multi","HIGH","NEEDED","Green Revolution as Cold War project","",scholar("Cullather Hungry World"))
add(C,"fao_fpi_methods","FAO","","The FAO Food Price Index (FFPI) Methodology Paper",2013,"FAO","DATASET_DOC","multi","CRITICAL","NEEDED","","https://www.fao.org/worldfoodsituation/foodpricesindex/en/","How the FPI Foodberg displays is computed")
add(C,"fao_fpi_methods","FAO","","The State of Food and Agriculture (SOFA) — annual",2024,"FAO","REPORT","multi","HIGH","NEEDED","Flagship","https://www.fao.org/publications/sofa/","")
add(C,"fao_fpi_methods","FAO","","The State of Food Security and Nutrition (SOFI) — annual",2024,"FAO","REPORT","multi","HIGH","NEEDED","Flagship","https://www.fao.org/publications/sofi/","")
add(C,"fao_fpi_methods","FAO","","Food Outlook (biannual)",2024,"FAO","REPORT","multi","HIGH","NEEDED","Short-term market outlook","https://www.fao.org/giews/reports/food-outlook/en/","")
add(C,"food_crises","Sen","Amartya","Poverty and Famines: An Essay on Entitlement and Deprivation",1981,"Oxford UP","BOOK","multi","CRITICAL","NEEDED","Nobelist","",scholar("Sen Poverty and Famines Entitlement"))
add(C,"food_crises","Davis","Mike","Late Victorian Holocausts: El Niño Famines",2001,"Verso","BOOK","multi","HIGH","NEEDED","","",scholar("Davis Late Victorian Holocausts"))
add(C,"food_security","Maxwell","Simon","Food Security: A Post-Modern Perspective",1996,"Food Policy","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"food_security","Barrett","Christopher B.","Measuring Food Insecurity",2010,"Science","ARTICLE","multi","HIGH","NEEDED","","https://doi.org/10.1126/science.1182768","")
add(C,"food_security","Clapp","Jennifer","Food",2020,"Polity","BOOK","multi","CRITICAL","NEEDED","3rd ed","",scholar("Jennifer Clapp Food Polity"))
add(C,"food_security","Patel","Raj","Stuffed and Starved: The Hidden Battle for the World Food System",2007,"Melville House","BOOK","multi","HIGH","NEEDED","","",scholar("Patel Stuffed and Starved"))
add(C,"food_security","Lappé","Frances Moore","Diet for a Small Planet",1971,"Ballantine","BOOK","multi","MEDIUM","NEEDED","","","")
add(C,"super_cycles","Radetzki","Marian","The Anatomy of Three Commodity Booms",2006,"Resources Policy","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"super_cycles","Cashin","Paul","The Long-Run Behavior of Commodity Prices",2002,"IMF Staff Papers","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"super_cycles","Jacks","David S.","From Boom to Bust: A Typology of Real Commodity Prices",2019,"Cliometrica","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"green_revolution","Shiva","Vandana","The Violence of the Green Revolution",1991,"Zed","BOOK","multi","MEDIUM","NEEDED","Critique","","")
add(C,"green_revolution","Borlaug","Norman","Nobel Lecture: The Green Revolution, Peace, and Humanity",1970,"Nobel Foundation","CHAPTER","multi","LOW","NEEDED","","https://www.nobelprize.org/prizes/peace/1970/borlaug/lecture/","")
add(C,"fao_fpi_methods","Minot","Nicholas","Transmission of World Food Price Changes to Markets in Sub-Saharan Africa",2011,"IFPRI DP 1059","WORKING_PAPER","multi","MEDIUM","NEEDED","","","")
add(C,"fao_fpi_methods","Baffes","John","World Bank Commodity Price Data (Pink Sheet) — Methodology",2024,"World Bank","DATASET_DOC","multi","HIGH","NEEDED","","https://www.worldbank.org/en/research/commodity-markets","")
add(C,"food_crises","Pinstrup-Andersen","Per","Food Policy for Developing Countries",2011,"Cornell UP","BOOK","multi","HIGH","NEEDED","","","")
add(C,"food_security","von Braun","Joachim","High Food Prices: The What, Who, and How of Proposed Policy Actions",2008,"IFPRI","REPORT","multi","HIGH","NEEDED","","","")
add(C,"food_security","Timmer","C. Peter","Food Security in Asia and the Pacific: The Rapidly Changing Role of Rice",2014,"Asia Pacific Policy Studies","ARTICLE","cereals","MEDIUM","NEEDED","","","")
add(C,"super_cycles","Reinhart","Carmen M.","Commodity Super-Cycles: What Are They and What Lies Ahead?",2016,"IMF","WORKING_PAPER","multi","HIGH","NEEDED","","","")
add(C,"super_cycles","Gruss","Bertrand","Commodity Terms of Trade: A New Database",2019,"IMF WP 19/21","WORKING_PAPER","multi","MEDIUM","NEEDED","","https://www.imf.org/en/Publications/WP/Issues/2019/01/24","")
add(C,"green_revolution","Herdt","Robert W.","A Retrospective View of Technology's Contribution to Agricultural Development",2012,"Annual Review of Resource Econ","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"fao_fpi_methods","Abbott","Philip C.","Tracking the Drivers of Global Food Prices",2017,"Applied Econ Perspectives & Policy","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"food_crises","Ó Gráda","Cormac","Famine: A Short History",2009,"Princeton UP","BOOK","multi","MEDIUM","NEEDED","","",scholar("Ó Gráda Famine Short History"))
add(C,"food_security","Godfray","H. Charles J.","Food Security: The Challenge of Feeding 9 Billion People",2010,"Science","ARTICLE","multi","HIGH","NEEDED","","https://doi.org/10.1126/science.1185383","")
add(C,"super_cycles","Kilian","Lutz","Not All Oil Price Shocks Are Alike",2009,"American Economic Review","ARTICLE","multi","HIGH","NEEDED","","https://doi.org/10.1257/aer.99.3.1053","Oil shock transmission to food")
add(C,"green_revolution","Otsuka","Keijiro","Sustainable Development of Rural Asia",2016,"World Development","ARTICLE","multi","LOW","NEEDED","","","")
add(C,"food_crises","Ravallion","Martin","Famines and Economics",1997,"J Economic Literature","ARTICLE","multi","MEDIUM","NEEDED","","","")

# =============================================================================
# CATEGORY 11 — TRADE & GEOPOLITICS (target 25)
# =============================================================================
C = "Trade Geopolitics"
add(C,"wto_doha","Anderson","Kym","Distortions to Agricultural Incentives",2009,"World Bank","BOOK","multi","CRITICAL","NEEDED","","","Defining analysis of trade distortions shaping food prices")
add(C,"wto_doha","Josling","Tim","Agriculture in the GATT",1996,"Macmillan","BOOK","multi","HIGH","NEEDED","With Tangermann, Warley","","")
add(C,"wto_doha","Martin","Will","Export Restrictions and Price Insulation During Commodity Price Booms",2014,"AJAE","ARTICLE","multi","HIGH","NEEDED","With Anderson","","")
add(C,"export_bans","Martin","Will","The Role of Rice Export Restrictions in the World Rice Price Spike of 2007/08",2011,"World Bank","WORKING_PAPER","cereals","HIGH","NEEDED","With Anderson","","")
add(C,"export_bans","Headey","Derek","Rethinking the Global Food Crisis: The Role of Trade Shocks",2011,"Food Policy","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"nafta_usmca","Zahniser","Steven","NAFTA at 20: North America's Free-Trade Area and Its Impact on Agriculture",2015,"USDA ERS WRS-15-01","REPORT","multi","HIGH","NEEDED","","https://www.ers.usda.gov/publications/pub-details/?pubid=40485","")
add(C,"nafta_usmca","Villarreal","M. Angeles","USMCA Agricultural Provisions",2020,"CRS","REPORT","multi","MEDIUM","NEEDED","","","")
add(C,"china_trade","Grant","Jason H.","Agricultural Trade in the Age of Trump",2021,"Applied Econ Perspectives & Policy","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"china_trade","Li","Minghao","China's Soybean Imports: Policy Impacts",2020,"CARD Iowa State","WORKING_PAPER","cereals","HIGH","NEEDED","","","")
add(C,"china_trade","Fukase","Emiko","China's Emerging Role as a Net Food Importer",2020,"Applied Econ Perspectives & Policy","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"russia_ukraine","Glauber","Joseph W.","The Russia-Ukraine War After a Year: Impacts on Fertilizer Production, Wheat, Corn, Vegetable Oil, and Rice",2023,"IFPRI","REPORT","multi","CRITICAL","NEEDED","","https://www.ifpri.org/blog/","")
add(C,"russia_ukraine","Welsh","Caitlin","The War in Ukraine and Global Food Security",2022,"CSIS","REPORT","cereals","HIGH","NEEDED","","https://www.csis.org/","")
add(C,"russia_ukraine","Behnassi","Mohamed","Implications of the Russia-Ukraine War for Global Food Security",2022,"Nature Human Behaviour","ARTICLE","cereals","HIGH","NEEDED","","","")
add(C,"export_bans","Piesse","Jenifer","Policy Responses to Food Crisis",2010,"Food Policy","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"wto_doha","Bureau","Jean-Christophe","Agricultural Market Access: The Key to Doha Success",2008,"OECD","REPORT","multi","MEDIUM","NEEDED","","","")
add(C,"nafta_usmca","Burfisher","Mary E.","NAFTA: What Have We Learned?",2016,"USDA ERS","REPORT","multi","MEDIUM","NEEDED","","","")
add(C,"china_trade","Sumner","Daniel A.","Rising China and Global Agriculture",2020,"U California","REPORT","multi","MEDIUM","NEEDED","","","")
add(C,"russia_ukraine","FAO","","Impact of the War in Ukraine on Food Security",2024,"FAO","REPORT","cereals","HIGH","NEEDED","Ongoing updates","https://www.fao.org/","")
add(C,"export_bans","Giordani","Paolo E.","Food Prices and the Multiplier Effect of Trade Policy",2016,"J International Economics","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"wto_doha","Hertel","Thomas W.","Potential Impacts of a Doha Round on Global Food Prices",2007,"World Economy","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"nafta_usmca","Zahniser","Steven","The Growing Corn Economies of Mexico and the U.S.",2013,"USDA ERS FDS-13D-01","REPORT","cereals","MEDIUM","NEEDED","","","")
add(C,"china_trade","Gale","Fred","China's Foreign Agricultural Investments",2015,"USDA ERS","REPORT","multi","LOW","NEEDED","","","")
add(C,"russia_ukraine","Liefert","William M.","Russia's Transformation From Agricultural Importer to Major Grain Exporter",2020,"USDA ERS","REPORT","cereals","HIGH","NEEDED","","","")
add(C,"wto_doha","Hoekman","Bernard","The Political Economy of the World Trading System",2009,"Oxford UP","BOOK","multi","LOW","NEEDED","3rd ed","","")
add(C,"china_trade","Carter","Colin A.","The Impact of the US-China Trade War on US Agriculture",2019,"Applied Econ Perspectives & Policy","ARTICLE","multi","HIGH","NEEDED","","","")

# =============================================================================
# CATEGORY 12 — CLIMATE, LAND & INPUTS (target 25)
# =============================================================================
C = "Climate Land Inputs"
add(C,"fertilizer_inputs","Huang","Wen-yuan","Impact of Rising Natural Gas Prices on US Ammonia Supply",2007,"USDA ERS WRS-0702","REPORT","none","HIGH","NEEDED","","https://www.ers.usda.gov/publications/pub-details/?pubid=40488","Explains why fertilizer and food prices follow gas prices")
add(C,"fertilizer_inputs","Brunelle","Thierry","Fertilizer Use and Markets",2019,"OECD","REPORT","none","MEDIUM","NEEDED","","","")
add(C,"fertilizer_inputs","IFA","","Fertilizer Outlook 2024",2024,"International Fertilizer Association","REPORT","none","HIGH","NEEDED","","https://www.ifastat.org/","")
add(C,"drought_weather","Boyer","Christopher N.","The Impact of the 2012 US Drought on Corn and Soybean Prices",2013,"Southern Ag Econ Assoc","WORKING_PAPER","cereals","MEDIUM","NEEDED","","","")
add(C,"drought_weather","Trenberth","Kevin E.","Global Warming and Changes in Drought",2014,"Nature Climate Change","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"climate_yields","Lobell","David B.","Extreme Heat Effects on Wheat Senescence",2012,"Nature Climate Change","ARTICLE","cereals","HIGH","NEEDED","","","")
add(C,"climate_yields","Ortiz-Bobea","Ariel","Anthropogenic Climate Change Has Slowed Global Agricultural Productivity Growth",2021,"Nature Climate Change","ARTICLE","multi","CRITICAL","NEEDED","","https://doi.org/10.1038/s41558-021-01000-1","")
add(C,"climate_yields","IPCC","","AR6 WGII Chapter 5: Food, Fibre, and Other Ecosystem Products",2022,"IPCC","REPORT","multi","CRITICAL","NEEDED","","https://www.ipcc.ch/report/ar6/wg2/","")
add(C,"climate_yields","Cline","William R.","Global Warming and Agriculture: Impact Estimates by Country",2007,"Peterson Institute","BOOK","multi","MEDIUM","NEEDED","","","")
add(C,"energy_food","Baffes","John","More on the Energy/Nonenergy Price Link",2010,"Applied Economics Letters","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"energy_food","Chen","Sheng-Tung","Modeling the Relationship Between the Oil Price and Global Food Prices",2010,"Applied Energy","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"energy_food","Nazlioglu","Saban","Oil Price and Agricultural Commodity Prices: Evidence from Semiparametric Granger Causality",2011,"Energy Economics","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"land_use","Searchinger","Timothy","Use of U.S. Croplands for Biofuels Increases Greenhouse Gases Through Emissions From Land-Use Change",2008,"Science","ARTICLE","multi","HIGH","NEEDED","","https://doi.org/10.1126/science.1151861","")
add(C,"land_use","Foley","Jonathan A.","Solutions for a Cultivated Planet",2011,"Nature","ARTICLE","multi","HIGH","NEEDED","","https://doi.org/10.1038/nature10452","")
add(C,"fertilizer_inputs","Gellings","Clark W.","Energy Efficiency in Fertilizer Production and Use",2009,"EOLSS","CHAPTER","none","LOW","NEEDED","","","")
add(C,"drought_weather","Diffenbaugh","Noah S.","Assessing the Vulnerability of Agriculture to Climate Change",2015,"Climatic Change","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"climate_yields","Fisher","Anthony C.","The Economic Impacts of Climate Change: Evidence from Agricultural Output and Random Fluctuations in Weather: Comment",2012,"AER","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"energy_food","Tyner","Wallace E.","The Integration of Energy and Agricultural Markets",2010,"Ag Econ","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"land_use","Plevin","Richard J.","Greenhouse Gas Emissions from Biofuels' Indirect Land Use Change Are Uncertain but May Be Much Greater Than Previously Estimated",2010,"Environmental Science & Technology","ARTICLE","multi","LOW","NEEDED","","","")
add(C,"fertilizer_inputs","Schnitkey","Gary","Nitrogen Fertilizer Prices and Natural Gas Prices",2022,"farmdoc daily","ARTICLE","none","HIGH","NEEDED","","https://farmdocdaily.illinois.edu/","")
add(C,"drought_weather","USDA","","Drought in the United States: Causes and Issues for Congress",2014,"CRS","REPORT","multi","MEDIUM","NEEDED","","","")
add(C,"climate_yields","Hsiang","Solomon","Estimating Economic Damage from Climate Change in the United States",2017,"Science","ARTICLE","multi","HIGH","NEEDED","","","")
add(C,"energy_food","Zhang","Zibin","Food Versus Fuel: What Do Prices Tell Us?",2010,"Energy Policy","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"land_use","Hertel","Thomas W.","Global Climate Impacts on Agriculture, Land Use, and Land Conversion",2010,"AJAE","ARTICLE","multi","MEDIUM","NEEDED","","","")
add(C,"climate_yields","Nelson","Gerald C.","Climate Change Effects on Agriculture: Economic Responses to Biophysical Shocks",2014,"PNAS","ARTICLE","multi","HIGH","NEEDED","","https://doi.org/10.1073/pnas.1222465110","")

# =============================================================================
# CATEGORY 13 — CHEF / RESTAURANT ECONOMICS (target 25)
# =============================================================================
C = "Chef Restaurant Econ"
add(C,"menu_engineering","Kasavana","Michael L.","Menu Engineering: A Practical Guide to Menu Analysis",1982,"Hospitality Publishers","BOOK","none","CRITICAL","NEEDED","With Smith; foundational","",scholar("Kasavana Smith Menu Engineering"))
add(C,"menu_engineering","Miller","Jack E.","Menu Pricing and Strategy",2019,"Wiley","BOOK","none","HIGH","NEEDED","","","")
add(C,"menu_engineering","Pavesic","David V.","Psychological Aspects of Menu Pricing",1989,"International Journal of Hospitality Management","ARTICLE","none","HIGH","NEEDED","","","")
add(C,"menu_engineering","Taylor","John Jasper","Menu Analysis: A Review of Techniques and Approaches",2012,"FIU Hospitality Review","ARTICLE","none","MEDIUM","NEEDED","","","")
add(C,"food_cost_mgmt","Dopson","Lea R.","Food and Beverage Cost Control",2019,"Wiley","BOOK","none","HIGH","NEEDED","With Hayes; standard textbook","",scholar("Dopson Hayes Food Beverage Cost Control"))
add(C,"food_cost_mgmt","Schmidgall","Raymond S.","Hospitality Industry Managerial Accounting",2011,"AHLEI","BOOK","none","MEDIUM","NEEDED","","","")
add(C,"food_cost_mgmt","Miller","Jack E.","The Restaurant Manager's Handbook",2016,"Atlantic Publishing","BOOK","none","MEDIUM","NEEDED","","","")
add(C,"vendor_procurement","Feinstein","Andrew H.","Purchasing: Selection and Procurement for the Hospitality Industry",2020,"Wiley","BOOK","none","HIGH","NEEDED","","","")
add(C,"vendor_procurement","Reynolds","Dennis","Hospitality Services: Food and Lodging",2012,"Cengage","BOOK","none","LOW","NEEDED","","","")
add(C,"inflation_passthrough","Piccoli","Gabriele","Restaurant Pricing and Inflation",2023,"Cornell Hospitality Quarterly","ARTICLE","none","HIGH","NEEDED","","","")
add(C,"inflation_passthrough","Anderson","Eric T.","Price Stickiness: Evidence from Restaurant Menus",2015,"NBER WP","WORKING_PAPER","none","HIGH","NEEDED","","","")
add(C,"inflation_passthrough","Kim","Dongsoo","Menu Prices and Inflation",2018,"Journal of Foodservice Business Research","ARTICLE","none","MEDIUM","NEEDED","","","")
add(C,"foodservice_econ","Enz","Cathy A.","Hospitality Strategic Management: Concepts and Cases",2010,"Wiley","BOOK","none","MEDIUM","NEEDED","","","")
add(C,"foodservice_econ","National Restaurant Association","","Restaurant Industry Forecast (annual)",2024,"NRA","REPORT","none","HIGH","NEEDED","","https://restaurant.org/","")
add(C,"foodservice_econ","Technomic","","Foodservice Price Index",2024,"Technomic","DATASET_DOC","none","HIGH","NEEDED","Trade benchmark","https://www.technomic.com/","")
add(C,"menu_engineering","Bowen","John T.","Food Menu Analysis",1990,"International J Hospitality Management","ARTICLE","none","MEDIUM","NEEDED","With Morris","","")
add(C,"food_cost_mgmt","Kwong","Lok Yiu Lina","The Application of Menu Engineering and Design",2005,"J Foodservice Business Research","ARTICLE","none","LOW","NEEDED","","","")
add(C,"vendor_procurement","Gregoire","Mary B.","Foodservice Organizations: A Managerial and Systems Approach",2019,"Pearson","BOOK","none","MEDIUM","NEEDED","","","")
add(C,"inflation_passthrough","Kelchen","Robert","How Restaurants Pass Through Input Costs",2022,"Choices Magazine","ARTICLE","none","MEDIUM","NEEDED","","","")
add(C,"foodservice_econ","Parsa","H. G.","Why Restaurants Fail",2005,"Cornell Hospitality Quarterly","ARTICLE","none","LOW","NEEDED","","","")
add(C,"food_cost_mgmt","Keiser","James","Controlling and Analyzing Costs in Food Service Operations",2015,"Pearson","BOOK","none","MEDIUM","NEEDED","","","")
add(C,"menu_engineering","LeBruto","Stephen M.","Menu Engineering: A Model Including Labor",1995,"FIU Hospitality Review","ARTICLE","none","LOW","NEEDED","","","")
add(C,"inflation_passthrough","BLS","","CPI Food Away From Home: Methodology",2024,"BLS","DATASET_DOC","none","HIGH","NEEDED","","https://www.bls.gov/cpi/factsheets/food-price-changes.htm","")
add(C,"vendor_procurement","Sysco","","Sysco Annual Report 10-K",2023,"Sysco Corp","GOV_DOC","none","MEDIUM","NEEDED","Largest US foodservice distributor","https://investors.sysco.com/","")
add(C,"foodservice_econ","Muller","Christopher","Hospitality Brand Strategies",2014,"Routledge","BOOK","none","LOW","NEEDED","","","")

# =============================================================================
# CATEGORY 14 — DATA SOURCE METHODOLOGY (target 20)
# =============================================================================
C = "Data Source Methodology"
add(C,"wasde_methods","USDA","","World Agricultural Supply and Demand Estimates (WASDE): Overview",2024,"USDA","DATASET_DOC","multi","CRITICAL","NEEDED","Monthly flagship","https://www.usda.gov/oce/commodity/wasde","Primary dataset feeding Foodberg")
add(C,"wasde_methods","USDA","","WASDE Methodology and Procedures",2019,"USDA WAOB","DATASET_DOC","multi","CRITICAL","NEEDED","","https://www.usda.gov/oce/commodity/wasde","")
add(C,"wasde_methods","Irwin","Scott H.","Market Reaction to USDA Reports",2008,"Ag Finance Review","ARTICLE","multi","HIGH","NEEDED","With Good","","")
add(C,"wasde_methods","Isengildina-Massa","Olga","Accuracy of USDA Forecasts of Corn, Soybean, and Wheat Ending Stocks",2015,"J Ag Applied Econ","ARTICLE","cereals","HIGH","NEEDED","","","")
add(C,"cpi_ppi_methods","BLS","","CPI Detailed Methodology: Food",2024,"BLS","DATASET_DOC","none","CRITICAL","NEEDED","","https://www.bls.gov/cpi/additional-resources/","Explains BLS food CPI Foodberg uses")
add(C,"cpi_ppi_methods","BLS","","Handbook of Methods: Chapter 17 — CPI",2024,"BLS","DATASET_DOC","none","HIGH","NEEDED","","https://www.bls.gov/opub/hom/cpi/","")
add(C,"cpi_ppi_methods","Reed","Stephen B.","One Hundred Years of Price Change: The Consumer Price Index and the American Inflation Experience",2014,"Monthly Labor Review","ARTICLE","none","HIGH","NEEDED","","https://www.bls.gov/opub/mlr/2014/article/one-hundred-years-of-price-change.htm","")
add(C,"cpi_ppi_methods","Boskin","Michael J.","Toward a More Accurate Measure of the Cost of Living",1996,"Boskin Commission Report","REPORT","none","MEDIUM","NEEDED","","","")
add(C,"fao_methods","FAO","","FAOSTAT Methodology",2024,"FAO","DATASET_DOC","multi","HIGH","NEEDED","","https://www.fao.org/faostat/","")
add(C,"fao_methods","FAO","","FAO Food Price Index Technical Note",2020,"FAO","DATASET_DOC","multi","CRITICAL","NEEDED","","https://www.fao.org/worldfoodsituation/foodpricesindex/en/","How the FPI in Foodberg is constructed")
add(C,"wb_methods","World Bank","","Commodity Markets Outlook Methodology",2024,"World Bank","DATASET_DOC","multi","HIGH","NEEDED","","https://www.worldbank.org/en/research/commodity-markets","Pink Sheet methodology")
add(C,"wb_methods","Baffes","John","The Great Plunge in Oil Prices: Causes, Consequences, and Policy Responses",2015,"World Bank PRN","REPORT","multi","MEDIUM","NEEDED","","","")
add(C,"series_construction","St. Louis Fed","","FRED Data: Agricultural Prices Receipts Indexes",2024,"FRED","DATASET_DOC","multi","HIGH","NEEDED","","https://fred.stlouisfed.org/categories/32305","Primary FRED food-price categories used by Foodberg")
add(C,"series_construction","Federal Reserve","","FRED API Documentation",2024,"St. Louis Fed","DATASET_DOC","none","HIGH","NEEDED","","https://fred.stlouisfed.org/docs/api/fred/","")
add(C,"series_construction","Jacks","David S.","From Boom to Bust: A Typology of Real Commodity Prices in the Long Run",2019,"Cliometrica","ARTICLE","multi","MEDIUM","NEEDED","Data series construction","","")
add(C,"wasde_methods","Hoffman","Linwood A.","Forecasting the Commodity Storage and Marketing Margins",2015,"USDA ERS","REPORT","cereals","MEDIUM","NEEDED","","","")
add(C,"cpi_ppi_methods","Hamilton","Bruce W.","Using Engel's Law to Estimate CPI Bias",2001,"AER","ARTICLE","none","LOW","NEEDED","","","")
add(C,"fao_methods","FAO","","Global Information and Early Warning System (GIEWS) Methodology",2024,"FAO","DATASET_DOC","multi","MEDIUM","NEEDED","","https://www.fao.org/giews/","")
add(C,"wb_methods","World Bank","","Food Security Update (quarterly)",2024,"World Bank","REPORT","multi","MEDIUM","NEEDED","","https://www.worldbank.org/en/topic/agriculture/brief/food-security-update","")
add(C,"series_construction","Officer","Lawrence H.","Two Centuries of Compensation for U.S. Production Workers in Manufacturing",2009,"MeasuringWorth","DATASET_DOC","none","LOW","NEEDED","Deflation context","https://www.measuringworth.com/","")


# ---------------------------------------------------------------------------
# EMIT CSV
# ---------------------------------------------------------------------------
CSV_HEADER = [
    "Number","Category","Subcategory","Author_Last","Author_First","Title","Year",
    "Publisher_Journal","Type","Commodity_Tag","Priority","Status",
    "Acquisition_Notes","Anna_Archive_Link","Archive_Org_Link","Direct_URL","Search_Query"
]


def main() -> None:
    rows = []
    cat_counter = Counter()
    prio_counter = Counter()
    comm_counter = Counter()

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_HEADER)
        for i, e in enumerate(E, start=1):
            (cat, sub, last, first, title, year, pub, typ, comm, prio, status,
             notes, url, rel) = e
            query = f"{last} {title}".strip()
            aa = annas(query)
            ao = archorg(query)
            writer.writerow([
                i, cat, sub, last, first, title, year, pub, typ, comm, prio,
                status, notes, aa, ao, url, query
            ])
            cat_counter[cat] += 1
            prio_counter[prio] += 1
            comm_counter[comm] += 1
            rows.append({
                "id": f"FB-{sub[:4].upper()}-{i:04d}",
                "number": i,
                "category": cat,
                "subcategory": sub,
                "author_last": last,
                "author_first": first,
                "title": title,
                "year": year,
                "publisher_journal": pub,
                "type": typ,
                "commodity_tag": comm,
                "priority": prio,
                "status": status,
                "acquisition_notes": notes,
                "anna_archive_link": aa,
                "archive_org_link": ao,
                "direct_url": url,
                "search_query": query,
                "relevance_to_foodberg": rel,
                "verified": False,
                "acquired": False,
            })

    payload = {
        "schema_version": "1.0",
        "generated": datetime.utcnow().isoformat(),
        "project": "Foodberg — Historical Food Price Explorer",
        "total_entries": len(rows),
        "category_counts": dict(cat_counter),
        "priority_counts": dict(prio_counter),
        "commodity_counts": dict(comm_counter),
        "entries": rows,
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(rows)} entries")
    print(f"  CSV:  {CSV_PATH}")
    print(f"  JSON: {JSON_PATH}")
    print(f"\nCategory counts:")
    for k, v in sorted(cat_counter.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")
    print(f"\nPriority counts:")
    for k, v in sorted(prio_counter.items()):
        print(f"  {v:4d}  {k}")
    print(f"\nCommodity counts:")
    for k, v in sorted(comm_counter.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")


if __name__ == "__main__":
    main()
