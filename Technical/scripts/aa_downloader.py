"""
AA-based bulk downloader for NYC Canonical books.
Uses annas-archive.gd to search and download.
"""
import requests, re, time, sys, io
from pathlib import Path
from urllib.parse import quote

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
OUT = Path(r'D:\Arcanum\Projects\Foodberg\Inputs\NYC_Canonical')

def safe_fn(author, title, year):
    a = author.split(',')[0].replace(' ', '_')
    t = re.sub(r'[<>:"/\\|?*]', '', title[:80])
    t = re.sub(r'\s+', ' ', t).strip()
    return f"{a} - {t} ({year}).pdf"

def dl_file(url, dest, timeout=120):
    r = session.get(url, stream=True, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    ct = r.headers.get('content-type','')
    sz = 0
    with open(dest, 'wb') as f:
        for c in r.iter_content(8192):
            f.write(c)
            sz += len(c)
    if sz < 50000 or 'text/html' in ct:
        if dest.exists(): dest.unlink()
        return False, sz
    return True, sz

def search_aa(author, title):
    """Search AA and return (md5, search_html)."""
    q = f'{author} {title}'
    url = f'https://annas-archive.gd/search?q={quote(q)}'
    r = session.get(url, timeout=30)
    md5s = re.findall(r'/md5/([a-f0-9]{32})', r.text)
    return md5s[0] if md5s else None

def get_aa_download_url(md5):
    """Get direct download URL from AA MD5 page."""
    url = f'https://annas-archive.gd/md5/{md5}'
    r = session.get(url, timeout=30)
    html = r.text
    
    # Try to find download links - look for various patterns
    patterns = [
        r'href="(https?://[^"]*(?:slow|fast|partner|download|cloudflare|ipfs)[^"]*)"',
        r'href="(https?://[^"]*\.pdf[^"]*)"',
    ]
    
    all_urls = []
    for pat in patterns:
        all_urls.extend(re.findall(pat, html, re.IGNORECASE))
    
    # Also try direct partner download page
    partner_url = f'https://annas-archive.gd/md5/{md5}/libgen'
    try:
        r2 = session.get(partner_url, timeout=30)
        for pat in patterns:
            all_urls.extend(re.findall(pat, r2.text, re.IGNORECASE))
    except:
        pass
    
    return all_urls[:5] if all_urls else []

# Items to try (author_first_last, title, year)
items = [
    # Already searched and found MD5 patterns
    ('Ted Merwin', 'Pastrami on Rye: An Overstuffed History of the Jewish Deli', '2015'),
    ('Andrew F. Smith', 'New York City: A Food Biography', '2014'),
    ('Edwin G. Burrows', 'Gotham: A History of New York City to 1898', '1999'),
    ('Joseph Mitchell', 'Up in the Old Hotel', '1992'),
    ('Timothy Pachirat', 'Every Twelve Seconds', '2011'),
    ('Robin Nagle', 'Picking Up', '2013'),
    ('Yong Chen', 'Chop Suey USA', '2014'),
    ('Maria Balinska', 'The Bagel', '2008'),
    ('William Grimes', 'Appetite City', '2009'),
    ('Mark Kurlansky', 'The Big Oyster', '2006'),
    ('Jane Ziegelman', '97 Orchard', '2010'),
    ('Ruth Reichl', 'Garlic and Sapphires', '2005'),
    ('Danny Meyer', 'Setting the Table', '2006'),
    ('Hasia R. Diner', 'Hungering for America', '2001'),
    ('Robert Sullivan', 'Rats', '2004'),
    ('Richard E. Ocejo', 'Masters of Craft', '2017'),
    ('Sharon Zukin', 'Naked City', '2010'),
    ('Robert Sietsema', 'New York in a Dozen Dishes', '2015'),
    ('Thomas Keller', 'The French Laundry Cookbook', '1999'),
    ('Annie Hauck-Lawson', 'Gastropolis', '2008'),
    ('Andrew F. Smith', 'Savoring Gotham', '2015'),
    ('Ana Ramirez', 'Bodega', '2020'),
    ('Ryan Devlin', 'Street Vending', '2018'),
]

downloaded = 0
missing = 0

for author, title, year in items:
    a_short = author.split()[-1] if ' ' in author else author
    fn = safe_fn(a_short, title, year)
    dest = OUT / fn
    
    if dest.exists() and dest.stat().st_size > 50000:
        print(f'[SKIP] {a_short} - {title[:50]} (exists, {dest.stat().st_size/1024:.0f}KB)')
        downloaded += 1
        continue
    
    print(f'[SEARCH] {a_short} - {title[:50]}...', end=' ', flush=True)
    
    try:
        md5 = search_aa(author, title)
        if not md5:
            print('NO MD5')
            missing += 1
            time.sleep(1)
            continue
        
        print(f'MD5={md5[:12]}...', end=' ', flush=True)
        urls = get_aa_download_url(md5)
        
        if not urls:
            # Try direct libgen download as fallback
            direct = f'https://annas-archive.gd/md5/{md5}'
            try:
                r = session.get(direct, timeout=30, allow_redirects=True)
                ct = r.headers.get('content-type','')
                if 'pdf' in ct.lower() and len(r.content) > 50000:
                    with open(dest, 'wb') as f:
                        f.write(r.content)
                    print(f'OK {len(r.content)/1024:.0f}KB (direct)')
                    downloaded += 1
                    time.sleep(2)
                    continue
            except:
                pass
            print('NO DL URL')
            missing += 1
            time.sleep(1)
            continue
        
        # Try each download URL
        got_it = False
        for url in urls:
            try:
                ok, sz = dl_file(url, dest, timeout=60)
                if ok:
                    print(f'OK {sz/1024:.0f}KB')
                    downloaded += 1
                    got_it = True
                    break
            except:
                continue
        
        if not got_it:
            print(f'FAILED ({len(urls)} urls tried)')
            missing += 1
    except Exception as e:
        print(f'ERROR: {str(e)[:60]}')
        missing += 1
    
    time.sleep(2)  # Rate limit

print(f'\nDone: {downloaded} downloaded/skipped, {missing} not found')