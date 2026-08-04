"""
NYC Canonical Acquisition Script v2
Fixes: IA file enumeration, correct download paths, browser-based AA fallback.
"""

import csv
import json
import os
import re
import sys
import io
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PROJ = Path(os.environ.get("FOODBERG_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
WISHLIST_PATH = os.environ.get("FOODBERG_WISHLIST_CSV", str(PROJ / "Outputs" / "wishlist.csv"))
OUTPUT_DIR = Path(os.environ.get("FOODBERG_ACQ_OUT", PROJ / "Inputs" / "NYC_Canonical"))
LOG_PATH = Path(os.environ.get("FOODBERG_ACQ_LOG", PROJ / "Technical" / "acquisition_log.md"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503])))
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'})

def safe_filename(title, author, year):
    author_c = author.split(',')[0].strip().replace(' ', '_') if author else "Unknown"
    t = re.sub(r'[<>:"/\\|?*]', '', title[:100])
    t = re.sub(r'\s+', ' ', t).strip()
    return f"{author_c} - {t} ({year}).pdf"

# ---- INTERNET ARCHIVE with metadata API ----
def find_ia_pdf(identifier):
    """Look up actual files in an IA item and find the best PDF."""
    meta_url = f"https://archive.org/metadata/{identifier}"
    try:
        r = session.get(meta_url, timeout=30)
        data = r.json()
        files = data.get('files', [])
        pdfs = [f for f in files if f.get('name', '').lower().endswith('.pdf') 
                and 'format' in f 
                and f['format'].lower() == 'pdf']
        if not pdfs:
            pdfs = [f for f in files if f.get('name', '').lower().endswith('.pdf')]
        if not pdfs:
            return None
        # Prefer ones without "_text" or "_djvu"
        good = [p for p in pdfs if '_text' not in p.get('name','') and '_djvu' not in p.get('name','')]
        chosen = good[0] if good else pdfs[0]
        return chosen['name']
    except Exception:
        return None

def try_ia_download(title, author, year, dest_path):
    """Search IA and download PDF."""
    q = f'title:"{title}"'
    if author:
        q += f' AND creator:"{author}"'
    search_url = f"https://archive.org/advancedsearch.php?q={urllib.parse.quote(q)}&fl[]=identifier,title,creator,year,mediatype,downloads&sort[]=downloads+desc&rows=8&output=json"
    try:
        r = session.get(search_url, timeout=30)
        docs = r.json().get('response', {}).get('docs', [])
    except:
        return False, 0, "IA search failed"
    
    for doc in docs:
        ident = doc.get('identifier', '')
        if not ident:
            continue
        pdf_name = find_ia_pdf(ident)
        if not pdf_name:
            continue
        url = f"https://archive.org/download/{ident}/{urllib.parse.quote(pdf_name)}"
        try:
            r2 = session.get(url, stream=True, timeout=180, allow_redirects=True)
            r2.raise_for_status()
            dl = 0
            with open(dest_path, 'wb') as f:
                for chunk in r2.iter_content(8192):
                    f.write(chunk)
                    dl += len(chunk)
            if dl >= 50000:
                return True, dl, f"IA {ident}"
            else:
                os.remove(dest_path)
        except Exception:
            continue
    return False, 0, f"No PDF (searched {len(docs)} items)"

# ---- DIRECT URL (try actual web page for NYC gov documents) ----
def try_direct_download(url, dest_path):
    """Download from direct URL, including trying PDF variant."""
    if not url or 'scholar.google.com' in url:
        return False, 0, "Skip"
    try:
        r = session.get(url, stream=True, timeout=60, allow_redirects=True)
        r.raise_for_status()
        ct = r.headers.get('content-type', '')
        
        # If it's already a PDF
        if 'application/pdf' in ct:
            dl = 0
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
                    dl += len(chunk)
            if dl >= 50000:
                return True, dl, "Direct PDF"
            os.remove(dest_path)
            return False, 0, "Too small"
        
        # If it's HTML, look for PDF links
        if 'text/html' in ct:
            html = r.text[:50000]
            # Find PDF links in the page
            pdf_links = re.findall(r'href="([^"]+\.pdf)"', html)
            from urllib.parse import urljoin
            for pl in pdf_links[:5]:
                pdf_url = urljoin(url, pl)
                try:
                    r2 = session.get(pdf_url, stream=True, timeout=60)
                    r2.raise_for_status()
                    if 'application/pdf' in r2.headers.get('content-type', ''):
                        dl = 0
                        with open(dest_path, 'wb') as f:
                            for chunk in r2.iter_content(8192):
                                f.write(chunk)
                                dl += len(chunk)
                        if dl >= 50000:
                            return True, dl, f"Linked PDF from page"
                except:
                    continue
        return False, 0, f"Not PDF (content-type: {ct})"
    except Exception as e:
        return False, 0, str(e)[:80]

# ---- MAIN ----
def acquire_all():
    with open(WISHLIST_PATH, 'r', encoding='utf-8') as f:
        items = [row for row in csv.DictReader(f) if row.get('NYC_Canonical','').strip() == 'True']
    print(f"Loaded {len(items)} NYC Canonical items", flush=True)

    results = []
    for item in items:
        title = item['Title'].strip()
        al = item.get('Author_Last','').strip()
        af = item.get('Author_First','').strip()
        year = item.get('Year','').strip()
        num = item.get('Number','').strip()
        priority = item.get('Priority','').strip()
        direct_url = item.get('Direct_URL','').strip()
        author_full = f"{al}, {af}" if af else al
        filename = safe_filename(title, al, year)
        dest = OUTPUT_DIR / filename

        print(f"\n{'='*60}", flush=True)
        print(f"#{num} [{priority}] {author_full} -- {title} ({year})", flush=True)

        result = {'num':num,'priority':priority,'title':title,'author':author_full,
                  'year':year,'filename':filename,'status':'NOT_FOUND','size_kb':0,
                  'channel':'','detail':'','channels_tried':[]}

        if dest.exists():
            result.update(status='ALREADY_EXISTS', size_kb=dest.stat().st_size/1024, channel='existing')
            print(f"  [SKIP] Already exists ({result['size_kb']:.0f} KB)", flush=True)
            results.append(result)
            continue

        # 1. Direct URL
        if direct_url and 'scholar.google.com' not in direct_url:
            print(f"  [1] Direct: {direct_url}", flush=True)
            ok, sz, detail = try_direct_download(direct_url, dest)
            result['channels_tried'].append('direct')
            if ok:
                result.update(status='DOWNLOADED', size_kb=sz/1024, channel='direct', detail=detail)
                print(f"  [OK] {sz/1024:.0f} KB via {detail}", flush=True)
                results.append(result)
                continue
            print(f"  [FAIL] {detail}", flush=True)

        # 2. Internet Archive (proper file enumeration)
        print(f"  [2] IA Search...", flush=True)
        ok, sz, detail = try_ia_download(title, author_full, year, dest)
        result['channels_tried'].append('internet_archive')
        if ok:
            result.update(status='DOWNLOADED', size_kb=sz/1024, channel='internet_archive', detail=detail)
            print(f"  [OK] {sz/1024:.0f} KB via {detail}", flush=True)
            results.append(result)
            continue
        print(f"  [FAIL] {detail}", flush=True)

        # 3. Anna's Archive marked for browser
        aa_link = item.get('Anna_Archive_Link','').strip()
        if aa_link:
            result['channels_tried'].append('annas_archive (need browser)')
            result['aa_link'] = aa_link
        result['detail'] = f"Tried: {', '.join(result['channels_tried'])}"
        print(f"  [MISS] Needs browser-based AA attempt", flush=True)
        results.append(result)

    return results

def build_log(results):
    d = [r for r in results if r['status']=='DOWNLOADED']
    nf = [r for r in results if r['status']=='NOT_FOUND']
    ex = [r for r in results if r['status']=='ALREADY_EXISTS']
    fg = [r for r in results if r.get('priority')=='FLAGSHIP']
    
    lines = [
        "# NYC Canonical Acquisition Log",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Items:** {len(results)} | **Downloaded:** {len(d)} | **Already:** {len(ex)} | **Not found:** {len(nf)}",
        f"**Output:** `{OUTPUT_DIR}`\n",
    ]
    
    if fg:
        lines.append("## FLAGSHIP Items")
        lines.append("| # | Title | Author | Status | Size |")
        lines.append("|---|-------|--------|--------|------|")
        for r in fg:
            st = "OK" if r['status']=='DOWNLOADED' else ("SKIP" if r['status']=='ALREADY_EXISTS' else "MISS")
        sz = f"{r['size_kb']:.0f} KB" if r['size_kb'] else "-"
        lines.append(f"| {r['num']} | {r['title'][:55]} | {r['author'][:25]} | {st} | {sz} |")
        lines.append("")
    if d:
        lines.append("## Downloaded")
        lines.append("| # | Title | Author | Channel | Size |")
        lines.append("|---|-------|--------|---------|------|")
        for r in d:
            lines.append(f"| {r['num']} | {r['title'][:55]} | {r['author'][:25]} | {r['channel']} | {r['size_kb']:.0f} KB |")
        lines.append("")
    if nf:
        lines.append("## Not Found (need browser-based Anna's Archive)")
        lines.append("| # | Title | Author | Channels Tried | AA Link |")
        lines.append("|---|-------|--------|----------------|---------|")
        for r in nf:
            ch = ', '.join(r['channels_tried'])
            aa = r.get('aa_link','')[:80] if r.get('aa_link') else '-'
            lines.append(f"| {r['num']} | {r['title'][:50]} | {r['author'][:22]} | {ch} | {aa} |")
        lines.append("")
    lines.append("## All Items")
    lines.append("| # | Priority | Title | Author | Year | Status | Size | Channel |")
    lines.append("|---|----------|-------|--------|------|--------|------|---------|")
    for r in sorted(results, key=lambda x: int(x['num'])):
        st = {"DOWNLOADED":"OK","ALREADY_EXISTS":"SKIP","NOT_FOUND":"MISS"}.get(r['status'], r['status'])
        lines.append(f"| {r['num']} | {r['priority']} | {r['title'][:45]} | {r['author'][:22]} | {r['year']} | {st} | {r['size_kb']:.0f if r['size_kb'] else '-'} KB | {r['channel']} |")
    return '\n'.join(lines)

if __name__ == '__main__':
    results = acquire_all()
    log = build_log(results)
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write(log)
    d = sum(1 for r in results if r['status']=='DOWNLOADED')
    nf = sum(1 for r in results if r['status']=='NOT_FOUND')
    print(f"\nDONE: {d} downloaded, {nf} not found", flush=True)