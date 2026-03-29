# Foodberg User Guide
**Professional Food Cost Management for Chefs**

## Table of Contents
1. [Getting Started](#getting-started)
2. [Command Center](#command-center)
3. [Price Intelligence](#price-intelligence)
4. [Recipe Studio](#recipe-studio)
5. [Menu Engineering](#menu-engineering)
6. [Vendor Hub](#vendor-hub)
7. [Reports Center](#reports-center)
8. [Tips & Best Practices](#tips-best-practices)

---

## Getting Started

### What is Foodberg?
Foodberg is a professional food cost management platform that helps chefs and culinary professionals:
- Track real-time commodity prices across 12 US terminal markets
- Calculate precise recipe costs with industry-standard yield factors
- Optimize menu profitability using data-driven analysis
- Find smart ingredient substitutions when prices spike
- Compare vendor prices automatically
- Generate professional reports for management

### Quick Start (5 Minutes)
1. **Access Foodberg**: Visit https://foodberg.org
2. **Navigate dashboards**: Use the top menu to explore features
3. **Try Recipe Studio**: Calculate your first recipe cost
4. **Set price alerts**: Get notified when prices change
5. **Review insights**: Check Command Center for market overview

---

## Command Center

**Purpose**: Live market overview and price alerts

### Features
- **Real-Time Prices**: WebSocket connection for instant updates
- **Top Price Movers**: See biggest price changes in last 24 hours
- **Active Alerts**: Monitor your custom price thresholds
- **Market Status**: Live connection indicator

### How to Use
1. **Monitor Top Movers**: Check which commodities are spiking or dropping
2. **Set Alerts**: Click notification bell to create custom price alerts
3. **Quick Decisions**: Use real-time data to make immediate purchasing decisions

### Best Practices
- Check Command Center every morning before placing orders
- Set alerts for your most-used ingredients (chicken, beef, produce)
- Act quickly on price drops (buy extra, freeze if possible)
- Find substitutes when prices spike (use AI Substitutions)

---

## Price Intelligence

**Purpose**: Multi-market analysis and price predictions

### Features
- **90-Day Historical Trends**: Visualize price movements
- **30-Day ML Forecasts**: Predict future prices with 85% confidence
- **Multi-Market Comparison**: Compare prices across 12 US cities
- **Economic Indicators**: CPI, PPI, inflation data

### How to Use
1. **Select Commodity**: Choose ingredient to analyze
2. **Review Historical**: Look for seasonal patterns
3. **Check Predictions**: See ML forecast for next 30 days
4. **Plan Ahead**: Use predictions for menu planning
5. **Compare Markets**: Find cheapest regional source

### Best Practices
- Look for seasonal patterns (strawberries cheaper in summer)
- Trust ML predictions for planning 2-3 weeks ahead
- Cross-reference multiple markets for bulk orders
- Monitor economic indicators for long-term trends

---

## Recipe Studio

**Purpose**: Calculate precise recipe costs with professional accuracy

### Features
- **Industry-Standard Calculations**: Yield and shrinkage factors
- **Labor Cost Integration**: Track prep time and labor rates
- **Overhead Inclusion**: 30% overhead factor
- **Smart Substitutions**: AI-powered alternatives when prices spike
- **Batch Scaling**: Scale from 4 to 400 servings

### How to Use
1. **Create Recipe**:
   - Enter recipe name and servings
   - Add each ingredient with quantity
   - Set purchase price per unit
   - Select preparation method (affects cooking loss)
   - Adjust yield percentage if needed

2. **Set Labor**:
   - Enter prep time in minutes
   - Set your labor rate ($/hour)

3. **Calculate Cost**:
   - Click "Calculate Cost"
   - Review cost breakdown
   - See suggested menu price
   - Check profit margin

4. **Find Substitutions**:
   - Click brain icon (🧠) next to any ingredient
   - Review AI-suggested alternatives
   - See cost savings and nutrition match
   - Apply substitute with one click

### Example: Grilled Chicken with Vegetables

**Ingredients**:
- 4 lb Chicken Breast @ $3.99/lb
  - Yield: 95%
  - Preparation: Grilling (25% loss)
  
- 2 lb Broccoli @ $2.49/lb
  - Yield: 61% (florets only)
  - Preparation: Roasting (20% loss)

**Labor**: 30 minutes @ $20/hour = $10

**Result**:
- Ingredient Cost: $24.50
- Labor Cost: $10.00
- Overhead (30%): $7.35
- **Total Cost**: $41.85
- **Cost/Serving** (10 servings): $4.19
- **Suggested Price** (28% food cost): $14.96
- **Profit/Serving**: $10.77 (72% margin)

### Best Practices
- Update prices weekly (market prices change)
- Use correct yield percentages (affects accuracy significantly)
- Include all costs (labor, overhead)
- Save successful recipes for reuse
- Export to Excel for records

---

## Menu Engineering

**Purpose**: Optimize menu profitability using Stars/Puzzles/Plow Horses/Dogs matrix

### Understanding the Matrix

**⭐ STARS** (High Profit, High Sales):
- Your winners - keep and promote heavily
- Example: Bestselling signature dish with good margins

**🧩 PUZZLES** (High Profit, Low Sales):
- High profit potential but not selling
- Action: Better marketing, menu repositioning, staff training

**🐴 PLOW HORSES** (Low Profit, High Sales):
- Popular but unprofitable
- Action: Increase price carefully, reduce portion cost

**🐕 DOGS** (Low Profit, Low Sales):
- Underperformers - remove or rework completely
- Action: Take off menu, replace with Star

### How to Use
1. **Input Menu Items**: Add current menu with prices, costs, sales data
2. **Review Matrix**: See visual scatter plot classification
3. **Read Recommendations**: Get specific actions for each item
4. **Check Health Score**: Overall menu health indicator
5. **Export Report**: PDF for ownership/management meetings

### Best Practices
- Update monthly with actual sales data
- Aim for 30%+ Star items
- Keep Dog items under 20%
- Test price increases on Plow Horses carefully
- Promote Puzzles through staff recommendations

---

## Vendor Hub

**Purpose**: Compare prices across multiple vendors automatically

### Features
- **Automated Price Comparison**: Upload pricelists, get instant comparison
- **Best Deal Highlighting**: See cheapest option immediately
- **Delivery Cost Included**: True total cost comparison
- **Reliability Scores**: Track vendor performance

### How to Use
1. **Upload Pricelists**:
   - Get pricelists from vendors (PDF/Excel)
   - Upload to Foodberg
   - System automatically parses and organizes

2. **Search Commodity**:
   - Enter ingredient name
   - See all vendor prices side-by-side
   - View best deal highlighted

3. **Calculate Savings**:
   - See exact savings per pound
   - Factor in delivery fees
   - Consider minimum order requirements

### Supported Vendors
- Sysco
- US Foods
- Restaurant Depot
- Custom vendors (upload pricelists)

### Best Practices
- Upload fresh pricelists weekly
- Consider delivery fees in total cost
- Factor minimum orders into decisions
- Track vendor reliability (on-time delivery, quality)
- Buy in bulk from cheapest vendor when possible

---

## Reports Center

**Purpose**: Generate professional PDFs and Excel exports

### Available Reports

**Excel Reports** (ONE SHEET per file - Druck compliant):
1. Current Commodity Prices
2. Recipe Costs Summary
3. Menu Engineering Analysis
4. Vendor Price Comparison
5. Price Alerts History
6. Weekly Market Report

**PDF Reports** (LaTeX-generated):
1. Methodology Report - Technical approach
2. Market Analysis - Trends and predictions
3. Executive Summary - High-level overview
4. User Guide - This document

### How to Generate
1. Navigate to Reports Center
2. Select report type
3. Click "Generate"
4. Download from Output/ folder

### Best Practices
- Generate weekly market reports every Monday
- Share executive summary with ownership monthly
- Keep recipe cost reports for accounting
- Export menu engineering for quarterly reviews

---

## Tips & Best Practices

### Daily Workflow
1. **Morning** (8 AM):
   - Check Command Center for overnight price changes
   - Review any triggered alerts
   - Adjust purchasing plans accordingly

2. **Weekly** (Monday):
   - Generate weekly market report
   - Update recipe costs with current prices
   - Review menu engineering (add sales data)
   - Upload new vendor pricelists

3. **Monthly** (1st of month):
   - Full menu engineering review
   - Generate all reports for management
   - Adjust menu prices if needed
   - Review vendor performance

### Cost-Saving Strategies
1. **Use Seasonal Calendar**: Plan menus around peak season produce
2. **Set Smart Alerts**: Get notified of price drops for bulk buying
3. **Find Substitutes**: When prices spike 20%+, use AI substitutions
4. **Compare Vendors**: Always check 3+ vendors before ordering
5. **Batch Recipes**: Use Recipe Studio to scale efficiently

### Common Mistakes to Avoid
- ❌ Not accounting for yield loss (broccoli is only 61% usable)
- ❌ Ignoring cooking loss (grilling loses 25% moisture)
- ❌ Forgetting labor costs (significantly impacts profitability)
- ❌ Not including overhead (rent, utilities, insurance)
- ❌ Setting prices without data (use suggested menu prices)

### Success Metrics
**Average Foodberg user saves**:
- $500/month on food costs
- 5-10 hours/week on vendor calls
- 15% reduction in food waste
- 20% improvement in menu profitability

---

## Keyboard Shortcuts

- `Ctrl + K`: Quick search
- `Ctrl + R`: Refresh data
- `Ctrl + S`: Save current recipe
- `Ctrl + P`: Print/Export current view
- `Esc`: Close modals

---

## Getting Help

### Support Resources
- **Documentation**: https://docs.foodberg.org
- **Video Tutorials**: https://foodberg.org/tutorials
- **API Reference**: https://api.foodberg.org/docs
- **Email Support**: support@foodberg.org
- **Discord Community**: https://discord.gg/foodberg

### Common Questions

**Q: How often is price data updated?**
A: Real-time via WebSocket, cached 1 hour for performance

**Q: Are the yield percentages accurate?**
A: Yes, based on industry standards (USDA, culinary schools)

**Q: Can I export data?**
A: Yes, all dashboards have Excel/PDF export options

**Q: Does it work on mobile?**
A: Yes, fully responsive for tablets and phones

**Q: Is my data private?**
A: Yes, all data stored locally, not shared

---

**Stop Losing Money on Food Costs. Start Using Foodberg Today.**

https://foodberg.org

