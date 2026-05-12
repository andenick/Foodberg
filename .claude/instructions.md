<!-- Druck Standards v1.0.0 - October 8, 2025 -->

# Multi-LLM Agent Instructions for Arcanum Projects
## Comprehensive Universal Agent Configuration Template

**Version**: 1.1
**Created**: October 8, 2025
**Updated**: October 18, 2025 (Multi-LLM Enhancement)
**Purpose**: Universal template for .claude configuration files managed by Druck
**Managed By**: Druck (Arcanum Folder Manager)
**Platform Compatibility: Claude Code, GLM-4.6, Perplexity

---

## How to Use This Template

**For New Projects**:
1. Copy this file to your project root as `.claude/instructions.md`
2. Customize the project-specific sections (marked with [CUSTOMIZE])
3. Keep all Arcanum standards sections intact
4. Update as project evolves

**For Existing Projects**:
1. Review current .claude configuration
2. Integrate missing standards from this template
3. Preserve project-specific customizations
4. Validate against Druck standards

---

## MULTI-LLM COMPATIBILITY (UNIVERSAL AGENT STANDARDS)

### Platform-Agnostic Development
This project supports all LLM platforms equally:
- **Claude Code**: Primary development environment
- **GLM-4.6**: Use `glmcc` launcher for full compatibility

- **Perplexity**: Enhanced research capabilities across all platforms

### Universal DALM Processing
All platforms use identical DALM (Direct Agent LLM Method) procedures:
- **File Size Limits**: 1MB max per chunk, 10 pages max per segment
- **Processing Method**: Universal DALM orchestrator handles all LLMs
- **Attribution Tracking**: All platforms log which LLM processed each document
- **Quality Standards**: Identical validation regardless of LLM used

### Cross-Platform Commands
All Arcanum slash commands work identically across platforms:
- `/readystart` - Initialize any agent with project context
- `/status` - Check workspace status across all platforms
- `/workspace` - Navigate and understand project structure
- `/library-index` - Process research materials (Robert integration)
- `/latex-report` - Generate professional reports
- `/methodology` - Apply research frameworks
- `/research` - Execute systematic research workflows

### Performance Standards
- **Instance Limits**: Maximum 4 concurrent instances across ALL platforms
- **Resource Monitoring**: Druck tracks usage regardless of LLM platform
- **Quality Assurance**: Identical standards for all platforms

---

## CRITICAL ARCANUM STANDARDS (DO NOT MODIFY)

### Excel File Requirements - NON-NEGOTIABLE

**MANDATORY**: ONE SHEET PER FILE - NO EXCEPTIONS

Every Excel file in `Output/Data/` MUST:
- ✅ Have EXACTLY one sheet (not 2, not 3, EXACTLY 1)
- ✅ Use machine-readable column names (valid Python identifiers preferred)
- ✅ Use professional Black & White formatting only
- ✅ Have descriptive filenames (e.g., `treasury_monthly_data.xlsx`)

**Test Before Handoff**:
```python
import pandas as pd
excel_file = pd.ExcelFile('Output/Data/your_file.xlsx')
assert len(excel_file.sheet_names) == 1, "FAILED: Multiple sheets detected"
```

**Why This Matters**: Violated in 0% of successful projects. This is Nick's #1 requirement.

### LaTeX PDF Requirements - NON-NEGOTIABLE

**MANDATORY**: ALL FINAL REPORTS IN LATEX

Every report must:
- ✅ Have LaTeX source (.tex) in `Technical/docs/`
- ✅ Have compiled PDF in `Output/PDFs/`
- ✅ Embed all visualizations (no separate image files)
- ✅ Meet academic publication quality standards

**Four Standard Reports** (analytical projects):
1. Methodology Report - Technical approach
2. Analysis Report - Detailed findings
3. Executive Summary - Non-technical overview
4. Reporting Strategy - Complete output catalog

**Templates**: Available in `docs/latex_templates/`

### Project Structure - Shaikh Tonak Pattern (95% Success Rate)

**USE THIS STRUCTURE**:

```
Foodberg/
├── Output/                          # USER-FACING DELIVERABLES
│   ├── Data/                        # Excel files (.xlsx) - ONE SHEET EACH
│   ├── PDFs/                        # LaTeX-generated reports
│   └── README.md                    # User quick start guide
├── Technical/                       # IMPLEMENTATION DETAILS
│   ├── src/                         # Source code & data generation
│   ├── data/                        # Raw and processing data
│   ├── docs/                        # LaTeX source files (.tex)
│   ├── scripts/                     # Automation & PDF compilation
│   ├── configs/                     # Configuration files
│   ├── archive/                     # Development history
│   └── README.md                    # Technical implementation
├── HANDOFF_DOCUMENTATION.md         # AGENT TRANSFER GUIDE
├── PROJECT_INDEX.md                 # COMPLETE NAVIGATION
├── README.md                        # Project overview
└── .claude/                         # Claude configuration
    ├── settings.local.json
    └── instructions.md              # This file
```

### Completion Rating Standards

**Use Honest, Evidence-Based Ratings**:

**Formula**:
```
Completion % =
  (Core Functionality Working × 50%) +
  (Output Formats Correct × 20%) +
  (Documentation Complete × 15%) +
  (Testing/Validation Done × 10%) +
  (Production Polish × 5%)
```

**Critical Principle**: Architecture ≠ Functionality

**Reality Checks Before Claiming 90%+**:
1. Does main feature work in fresh environment? (If NO → max 80%)
2. Are there Excel files with multiple sheets? (If YES → max 75%)
3. Do LaTeX PDFs exist in Output/PDFs/? (If NO → max 70%)
4. Does it require special hardware for basic function? (Document clearly)
5. Will it work if next agent runs main script now? (If NO → max 75%)

**Quality Tiers**:
- **95-100%**: MISSION ACCOMPLISHED - Everything works, tested, professional
- **85-94%**: EXCELLENT - Core complete, minor polish needed
- **75-84%**: GOOD - Functional with known issues
- **65-74%**: FUNCTIONAL PROTOTYPE - Works but not production-ready
- **50-64%**: ARCHITECTURE COMPLETE - Structure done, functionality partial
- **< 50%**: IN PROGRESS - Core features incomplete

### Validation Requirements - MANDATORY

**Before Handoff, MUST Complete**:

1. **Fresh Environment Test**:
```bash
# Create clean copy, remove cache, reinstall deps, run main command
# If this fails → completion cannot exceed 80%
```

2. **Excel Format Validation**:
```python
# Every Excel file must pass one-sheet test
```

3. **Functionality Test**:
```bash
# Primary use case must work without manual intervention
```

4. **Documentation Check**:
- [ ] HANDOFF_DOCUMENTATION.md complete
- [ ] PROJECT_INDEX.md lists all files
- [ ] README.md explains project clearly

5. **Accuracy Validation** (if applicable):
- Document targets vs actuals
- Quantify gaps
- Explain limitations

### Communication Standards

**When Receiving Feedback**:

```markdown
You're absolutely correct. I made a [error type] by [specific mistake].

**Core Issue**: [One sentence problem statement]

**Corrective Action Plan**:
1. [Immediate fix] - [Timeline]
2. [Systematic improvement] - [Timeline]
3. [Prevention mechanism] - [Timeline]

This correction prevents [downstream problems] and ensures [quality outcome].

**Lesson Integration**: [How this improves future work]
```

**Do**:
- ✅ Acknowledge errors immediately
- ✅ Provide systematic fixes
- ✅ Use TodoWrite tool proactively
- ✅ Update progress regularly
- ✅ Test before claiming completion

**Don't**:
- ❌ Make excuses or defensive responses
- ❌ Claim completion without testing
- ❌ Create Excel files with multiple sheets
- ❌ Use Markdown for final reports (LaTeX only)
- ❌ Reorganize without testing paths

---

## PROJECT-SPECIFIC CONFIGURATION [CUSTOMIZE]

### Project Details

**Name**: Foodberg
**Type**: Web Application / Data Processing Platform
**Purpose**: Professional food cost management platform for chefs and culinary professionals to track real-time commodity prices, optimize recipes, and reduce food costs by $500/month on average
**Primary User**: Professional chefs, restaurant owners, culinary professionals

### Specific Requirements

**Data Sources**:
- **USDA Market News**: Terminal market prices across 12 US markets (FREE API)
- **FRED**: Federal Reserve economic data (FREE API)
- **FAO**: UN Food & Agriculture prices (FREE API)
- **World Bank**: Global commodities data (FREE API)
- **API Ninja**: Food data - 10K requests/month (FREE tier)
- **Sysco API**: Vendor pricing (requires business account)
- **US Foods**: Vendor pricing (requires partnership)

**Output Deliverables**:
- **Recipe Cost Analysis**: Excel files with cost breakdowns (Output/Data/recipe_costs.xlsx)
- **Menu Engineering Reports**: PDF profitability matrices (Output/PDFs/menu_engineering.pdf)
- **Price Intelligence Dashboard**: Real-time web interface
- **Vendor Comparison Reports**: Excel files with best deal recommendations (Output/Data/vendor_comparisons.xlsx)
- **Market Trend Analysis**: LaTeX reports with forecasting (Output/PDFs/market_trends.pdf)

**Accuracy Targets**:
- **Price Data Accuracy**: 99%+ for USDA official sources
- **Recipe Cost Calculations**: 95%+ accuracy with proper yield factors
- **Menu Profitability Analysis**: 90%+ accuracy with industry-standard margins
- **Price Forecasting**: 85%+ accuracy for 30-day predictions

**Performance Targets**:
- **Processing Speed**: < 500ms API response time (p95)
- **Load Time**: < 2 seconds initial page load
- **Real-Time Updates**: < 100ms WebSocket latency
- **Resource Usage**: < 1GB RAM, < 0.5 CPU cores typical

### Technology Stack [CUSTOMIZE]

**Languages**:
- **TypeScript**: 5.9.3 (Frontend - React 19)
- **Python**: 3.11+ (Backend - FastAPI)

**Key Dependencies**:
- **React**: 19.1.1 (Frontend framework)
- **FastAPI**: 0.104+ (Backend API framework)
- **Tailwind CSS**: 3.4.0 (Styling)
- **Recharts**: 3.0+ (Data visualization)
- **Zustand**: 4.4+ (State management)
- **Pandas**: 2.1.3 (Data processing)
- **scikit-learn**: 1.3+ (ML price predictions)
- **WebSockets**: Real-time price updates

**External Services**:
- **Netlify**: Frontend hosting (FREE tier)
- **Render**: Backend hosting (FREE tier)
- **Cloudflare**: CDN (FREE tier)
- **Redis**: Caching layer (optional)
- **USDA API**: Market price data (FREE)
- **OpenAI API**: AI-powered features (paid)

### Development Workflow [CUSTOMIZE]

**Environment Setup**:
```bash
# 1. Clone repository
git clone <repository-url>
cd Foodberg

# 2. Backend setup
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# OR: source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# 3. Frontend setup (new terminal)
cd frontend
npm install

# 4. Environment configuration
# Copy .env.template to .env for backend
# Copy .env.template to .env.local for frontend
```

**Running Locally**:
```bash
# Option 1: Use START_DEV.bat (Windows)
START_DEV.bat

# Option 2: Manual startup
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Testing**:
```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend
pytest

# End-to-end tests
npm run test:e2e
```

**Building/Compilation**:
```bash
# Frontend production build
cd frontend
npm run build

# LaTeX PDF generation
pdflatex -output-directory=Output/PDFs Technical/docs/menu_engineering_report.tex
pdflatex -output-directory=Output/PDFs Technical/docs/market_trends_analysis.tex
```

### Known Issues and Limitations [UPDATE REGULARLY]

**Current Known Issues**:
1. **Vendor API Integration**: Sysco and US Foods require business accounts for API access. Impact: Limited vendor comparison data. Solution: Implement manual price import workflows while pursuing business partnerships.
2. **Real-Time Data Latency**: USDA Market News API has 15-minute update delays. Impact: Slightly outdated price information. Solution: Implement WebSocket buffering and predictive pricing for interim periods.

**Limitations**:
1. **Geographic Coverage**: Currently focused on US terminal markets (12 markets). Reason: Data availability and API limitations. Future enhancement: Expand to international markets through FAO and local agricultural APIs.
2. **AI Feature Dependencies**: Smart ingredient substitutions require OpenAI API. Reason: Advanced NLP capabilities needed for taste matching. Future enhancement: Develop local models for common substitution patterns.

**Dependencies**:
- **Hardware**: Standard development machine sufficient. No GPU required for core functionality.
- **Software**: Requires Python 3.11+, Node.js 18+, LaTeX distribution (for PDF reports)
- **External**: USDA API key (free), OpenAI API key (paid for AI features), optional Redis for caching

---

## WORKING WITH NICK - CRITICAL PATTERNS

### Nick's Priorities (In Order)

1. **Accuracy and Correctness** - Results must be verifiable and correct
2. **Professional Quality** - "Bloomberg-level" standards expected
3. **Complete Documentation** - Everything documented for future use
4. **Production Readiness** - No prototype quality accepted
5. **Mobile Consideration** - Always consider tablet/phone usage (if applicable)

### Nick's Working Style

**Expects**:
- Vision-driven: Start with concepts, implement technically
- Iterative: Progressive refinements with feedback
- Proactive: Anticipate related improvements
- Systematic: Organized, documented, professional

**Appreciates**:
- TodoWrite usage for progress tracking
- Evidence-based claims with measurements
- Honest assessment of limitations
- Clear next steps with time estimates

**Dislikes** (Based on Project Analysis):
- Overstated completion percentages
- Prototype quality presented as production-ready
- Excel files with multiple sheets
- Markdown reports instead of LaTeX PDFs
- Architecture without tested functionality

### Communication Patterns That Work

**Progress Updates**:
```markdown
## Status: [Clear one-line summary]

### Completed ✓
- [Achievement with metrics]

### In Progress ⏳
- [Current work - X% complete]

### Blocked 📋
- [Issue needing decision]

### Next Steps
1. [Action with timeline]
```

**Error Acknowledgment**:
- Immediate, specific, systematic correction
- No defensiveness
- Include prevention mechanism

---

## QUALITY GATES

### Before Claiming 85%+ Completion

**ALL must be true**:
- [ ] Fresh environment test passed
- [ ] Primary functionality works without errors
- [ ] All Excel files have ONE sheet
- [ ] LaTeX PDFs exist in Output/PDFs/
- [ ] Documentation comprehensive (all required files exist)
- [ ] Accuracy metrics documented (if applicable)
- [ ] Known issues documented with solutions
- [ ] Next agent can continue immediately

### Before Claiming "MISSION ACCOMPLISHED"

**ALL must be true**:
- [ ] 95%+ completion justified with evidence
- [ ] All accuracy targets met or gaps < 5%
- [ ] Professional quality validated
- [ ] Mobile-responsive (if web app)
- [ ] Multi-layer validation complete
- [ ] Performance targets met
- [ ] Comprehensive handoff documentation
- [ ] No critical issues remain

---

## VALIDATION CHECKLIST

### Pre-Handoff Validation [RUN EVERY TIME]

```bash
# 1. Fresh Environment Test
python Technical/scripts/validate.py

# 2. Excel Format Check
python -c "
import pandas as pd
import glob
for f in glob.glob('Output/Data/*.xlsx'):
    xl = pd.ExcelFile(f)
    assert len(xl.sheet_names) == 1, f'{f} has multiple sheets'
print('✓ All Excel files validated')
"

# 3. PDF Generation Check
ls Output/PDFs/*.pdf  # Should show at least 4 PDFs for analytical projects

# 4. LaTeX Sources Check
ls Technical/docs/*.tex  # Should show LaTeX source files

# 5. Documentation Check
for doc in HANDOFF_DOCUMENTATION.md PROJECT_INDEX.md README.md Output/README.md Technical/README.md; do
    if [ -f "$doc" ]; then
        echo "✓ $doc"
    else
        echo "❌ MISSING: $doc"
    fi
done
```

### Accuracy Validation [IF APPLICABLE]

```python
# Run accuracy validation
from Technical.scripts.accuracy_validator import AccuracyValidator

targets = {
    'metric1': 95.0,
    'metric2': 90.0,
    'metric3': 85.0
}

validator = AccuracyValidator('ProjectName', targets)
# [Test each metric]
report = validator.generate_report()

# Review report and document gaps
```

---

## RESOURCES

### Essential Druck Documentation

**Must Read Before Starting**:
1. `docs/AGENT_QUICK_START_GUIDE.md` - 15-minute orientation
2. `docs/AGENT_STANDARDS_AND_BEST_PRACTICES.md` - Complete standards
3. `docs/ARCANUM_BEST_PRACTICES_FRAMEWORK_UPDATED.md` - Proven patterns

**For Validation and Testing**:
4. `docs/VALIDATION_AND_TESTING_PROTOCOL.md` - Testing procedures
5. `docs/ACCURACY_AND_QUALITY_STANDARDS.md` - Quality requirements

**For Templates**:
6. `docs/latex_templates/` - Professional LaTeX templates

### Success Examples to Study

**High-Performing Projects** (95%+ completion):
- **Arthur**: `docs/` - Excellent handoff documentation
- **Druck**: `docs/` - Evidence-based completion
- **Robin**: `docs/` - Gold standard tool integration

**Patterns to Avoid** (from project analysis):
- Don't claim high completion with broken core features
- Don't create Excel files with multiple sheets
- Don't reorganize without testing paths
- Don't confuse architecture with functionality

---

## HANDOFF PREPARATION

### Required Documentation

**Before Handoff, Create/Update**:

1. **HANDOFF_DOCUMENTATION.md**:
   - Clear status (Mission Accomplished / In Progress / Needs Work)
   - Justified completion % with formula breakdown
   - Tested functionality with evidence
   - Known issues with solutions
   - Next steps with time estimates

2. **PROJECT_INDEX.md**:
   - Complete inventory of all deliverables
   - File locations with descriptions
   - Usage instructions
   - Development continuation guide

3. **README.md**:
   - Project purpose and value
   - Quick start (< 5 steps)
   - Key deliverables
   - Support information

4. **Output/README.md**:
   - User-facing guide
   - What the project delivers
   - How to use outputs
   - Simple, non-technical language

5. **Technical/README.md**:
   - Architecture overview
   - Setup instructions
   - Code organization
   - Maintenance procedures

### Final Checklist

**Complete Before Claiming Project Ready**:

- [ ] All validation tests pass
- [ ] Completion rating justified
- [ ] All required documentation exists
- [ ] Known issues documented
- [ ] Next steps clear
- [ ] Fresh environment test passed
- [ ] Excel files validated (one sheet each)
- [ ] LaTeX PDFs generated
- [ ] Accuracy metrics documented (if applicable)
- [ ] Ready for next agent to continue

---

## VERSION HISTORY [UPDATE AS PROJECT EVOLVES]

**Version 1.0** - [Date]
- Initial project setup
- [Key changes/decisions]

**Version 1.1** - [Date]
- [Changes made]
- [Decisions documented]

---

**This configuration file ensures compliance with Arcanum standards while allowing project-specific customization. Following these guidelines achieves 90%+ success rates with professional deliverables.**

---

*Template maintained by Druck - Arcanum Folder Manager*
*Version 1.0 - October 8, 2025*
*Based on comprehensive analysis of successful Arcanum projects*
