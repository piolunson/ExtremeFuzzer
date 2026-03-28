import requests, itertools, os, string, re, random, threading, shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin

# ===================== COLORS =====================
R='\033[91m'; G='\033[92m'; Y='\033[93m'; B='\033[94m'
M='\033[95m'; C='\033[96m'; DIM='\033[2m'; RST='\033[0m'; BLD='\033[1m'

BANNER = f"""{C}{BLD}
  ███████╗██╗   ██╗███████╗███████╗███████╗██████╗
  ██╔════╝██║   ██║╚══███╔╝╚══███╔╝██╔════╝██╔══██╗
  █████╗  ██║   ██║  ███╔╝   ███╔╝ █████╗  ██████╔╝
  ██╔══╝  ██║   ██║ ███╔╝   ███╔╝  ██╔══╝  ██╔══██╗
  ██║     ╚██████╔╝███████╗███████╗███████╗██║  ██║
  ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝{RST}
  {Y}v13.0  |  Web Fuzzer & Scraper  |  by piolunson{RST}
"""

HELP = f"""
{Y}{BLD}--- EXTREME FUZZER v13.0 - FULL DOCS ---{RST}

{G}[URL TAGS]{RST}
  <brute>   Brute-force chars (a-z, 0-9), requires -l
  <char>    Lowercase letters only, requires -l
  <upper>   Uppercase letters only, requires -l
  <num>     Digits only, requires -l
  <hex>     Hex chars (0-9, a-f), requires -l
  <tld>     TLD list (.pl, .com, ...)
  <word>    Keyword list
  <year>    Current year (e.g. 2025)
  <month>   Current month (e.g. 06)
  <day>     Current day (e.g. 14)
  {{1-9}}     Numeric range
  [a,b,c]   Inline custom list

{G}[SCAN]{RST}
  scan <pattern> <phrase> [options]
    -l <n>        Brute length (default: 1)
    -t <n>        Threads (default: 20, max: 100)
    -c            Clear found.txt before scan
    -v            Verbose mode (show failed codes)
    -r <n>        Retries on error (default: 2)
    -to <s>       Timeout in seconds (default: 3)
    -s <n>        Match by status code (e.g. -s 200)
    -o <file>     Save results to custom file
    -x <codes>    Ignore codes (e.g. -x 403,404)
    -ua <string>  Custom User-Agent string
    -wl           Use loaded wordlist as <word>
    --no-https    Use HTTP instead of HTTPS
    --head        Use HEAD instead of GET (faster)

{G}[HTML / SCRAPER]{RST}
  html <url> <mode> [--flags]

  -links          All href links
    --ext           External links only (other domains)
    --int           Internal links only (same domain)
    --no-anchor     Hide #fragment links
    --no-mailto     Hide mailto: links
    --no-js         Hide javascript: links
    --abs           Force absolute URLs

  -images         Image src attributes
    --ext           External images only
    --int           Internal images only
    --no-svg        Hide .svg files
    --no-ico        Hide .ico files

  -text           Plain text (no HTML tags)
    --min <n>       Only lines longer than n chars
    --no-empty      Hide empty/whitespace lines (default)
    --headings      Only heading tags (h1-h6)

  -emails         Email addresses found on page
    --unique        Deduplicate (default)
    --domain <d>    Only emails from specific domain

  -phones         Phone numbers on page
    --intl          International format only (+XX)

  -js             JavaScript file references
    --ext           External JS only
    --int           Internal JS only
    --inline        Also show inline <script> blocks

  -css            CSS file references
    --ext           External CSS only
    --int           Internal CSS only

  -meta           Meta tags and title
  -forms          Forms and input fields
  -headers        HTTP response headers
  -status         HTTP status code only
  -size           Response size in bytes
  -words          Word count on page
  -all            Run all modes at once

{G}[WORDLIST]{RST}
  wl load <file>    Load wordlist from file
  wl show           Show loaded wordlist (first 50)
  wl save <file>    Save current <word> list to file
  wl add <word>     Add word to <word> list
  wl del <word>     Remove word from <word> list
  wl clear          Clear loaded wordlist
  wl count          Show wordlist count

{G}[FILES]{RST}
  cat               Print found.txt
  rm                Delete found.txt
  ls                List files in directory
  grep <phrase>     Search in found.txt
  export <file>     Copy found.txt to another file
  stats             Show session statistics

{G}[LISTS]{RST}
  set <list> v1,v2  Update a built-in list
  show <list>       Print a list's contents

{G}[PIPE]{RST}
  html <url> <mode> [--flags] | grep <phrase>

{G}[OTHER]{RST}
  clear / cls       Clear screen
  help              Show this help
  exit              Quit
"""

MODES = {'-links','-images','-text','-meta','-forms','-emails',
         '-phones','-js','-css','-headers','-status','-size','-words','-all'}

class ExtremeFuzzer:
    def __init__(self):
        self.lists = {
            'tld':   ['pl','com','net','org','io','dev','online','xyz','eu','info','biz','co'],
            'word':  ['admin','test','api','v1','v2','dev','mail','shop','wp','old','new',
                      'index','backup','login','panel','dashboard','static','cdn','ftp',
                      'beta','staging','app','mobile','m','secure','portal','uploads','assets'],
            'brute': string.ascii_lowercase + string.digits,
            'char':  string.ascii_lowercase,
            'upper': string.ascii_uppercase,
            'num':   string.digits,
            'hex':   '0123456789abcdef'
        }
        self.output_file = 'found.txt'
        self.wordlist    = []
        self.lock        = threading.Lock()
        self.stats       = {'scanned':0,'hits':0,'errors':0,'start':datetime.now()}
        self.ua_list     = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
            'Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/109.0 Firefox/119.0',
            'curl/8.1.2'
        ]

    # =================== SCRAPER ===================
    def _filter_urls(self, urls, base_url, flags):
        """Apply --ext / --int / domain filters to a set of URL strings."""
        base_domain = urlparse(base_url).netloc.lower()
        result = set()
        for u in urls:
            abs_u = urljoin(base_url, u)
            parsed = urlparse(abs_u)
            netloc = parsed.netloc.lower()
            is_internal = (netloc == '' or netloc == base_domain
                           or netloc.endswith('.' + base_domain))
            if '--ext' in flags and is_internal: continue
            if '--int' in flags and not is_internal: continue
            result.add(abs_u if ('--abs' in flags or '--ext' in flags or '--int' in flags) else u)
        return result

    def get_web_data(self, url, mode=None, flags=None):
        if flags is None: flags = []
        if not url.startswith('http'): url = 'https://' + url
        try:
            r = requests.get(url, headers={'User-Agent': random.choice(self.ua_list)}, timeout=7)
            html = r.text

            # ----- LINKS -----
            if mode == '-links':
                raw   = re.findall(r'href=["\']([^"\']+)["\']', html)
                links = set()
                for href in raw:
                    abs_href = urljoin(url, href)
                    p = urlparse(abs_href)
                    if '--no-anchor' in flags and p.fragment and not p.scheme: continue
                    if '--no-anchor' in flags and abs_href.startswith('#'): continue
                    if '--no-mailto' in flags and abs_href.startswith('mailto:'): continue
                    if '--no-js'     in flags and abs_href.startswith('javascript:'): continue
                    links.add(abs_href)
                base_domain = urlparse(url).netloc.lower()
                if '--ext' in flags:
                    links = {h for h in links if urlparse(h).netloc.lower() not in ('', base_domain)
                             and not urlparse(h).netloc.lower().endswith('.' + base_domain)}
                elif '--int' in flags:
                    links = {h for h in links if urlparse(h).netloc.lower() in ('', base_domain)
                             or urlparse(h).netloc.lower().endswith('.' + base_domain)}
                lines = sorted(links)
                return f"{DIM}Found: {len(lines)} links{RST}\n" + "\n".join(lines)

            # ----- IMAGES -----
            elif mode == '-images':
                exts = r'\.(?:jpg|jpeg|png|gif|webp'
                if '--no-svg' not in flags: exts += '|svg'
                if '--no-ico' not in flags: exts += '|ico'
                exts += ')'
                raw = set(re.findall(rf'src=["\']([^"\']*{exts}[^"\']*)["\']', html, re.I))
                raw |= set(re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I))
                if '--ext' in flags or '--int' in flags:
                    raw = self._filter_urls(raw, url, flags)
                return f"{DIM}Found: {len(raw)} images{RST}\n" + "\n".join(sorted(raw))

            # ----- TEXT -----
            elif mode == '-text':
                if '--headings' in flags:
                    found = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', html, re.I|re.DOTALL)
                    clean_h = [re.sub(r'<[^>]+>','',h).strip() for h in found]
                    return "\n".join(h for h in clean_h if h)
                clean = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL|re.I)
                clean = re.sub(r'<[^>]+>', '', clean)
                lines = [l.strip() for l in clean.splitlines()]
                if '--no-empty' in flags or '--no-empty' not in flags:  # default: hide empty
                    lines = [l for l in lines if l]
                min_len = 0
                if '--min' in flags:
                    try: min_len = int(flags[flags.index('--min') + 1])
                    except: pass
                if min_len: lines = [l for l in lines if len(l) >= min_len]
                return "\n".join(lines)

            # ----- EMAILS -----
            elif mode == '-emails':
                found = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', html))
                if '--domain' in flags:
                    try:
                        domain = flags[flags.index('--domain') + 1]
                        found = {e for e in found if e.endswith('@' + domain)}
                    except: pass
                result = sorted(found)
                return f"{DIM}Found: {len(result)} emails{RST}\n" + ("\n".join(result) or "None found")

            # ----- PHONES -----
            elif mode == '-phones':
                if '--intl' in flags:
                    found = set(re.findall(r'\+\d{1,3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{3,4}', html))
                else:
                    found = set(re.findall(r'(?:\+\d{1,3}|00\d{2})?[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{3}', html))
                result = sorted(found)
                return f"{DIM}Found: {len(result)} phones{RST}\n" + ("\n".join(result) or "None found")

            # ----- JS -----
            elif mode == '-js':
                src_files = set(re.findall(r'src=["\']([^"\']*\.js(?:\?[^"\']*)?)["\']', html, re.I))
                if '--ext' in flags or '--int' in flags:
                    src_files = self._filter_urls(src_files, url, flags)
                result_lines = sorted(src_files)
                if '--inline' in flags:
                    inlines = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', html, re.DOTALL|re.I)
                    result_lines += [f"\n{DIM}--- inline script ---{RST}\n" + s.strip()
                                     for s in inlines if s.strip()]
                return f"{DIM}Found: {len(src_files)} JS files{RST}\n" + "\n".join(result_lines)

            # ----- CSS -----
            elif mode == '-css':
                raw = set(re.findall(r'href=["\']([^"\']*\.css(?:\?[^"\']*)?)["\']', html, re.I))
                if '--ext' in flags or '--int' in flags:
                    raw = self._filter_urls(raw, url, flags)
                return f"{DIM}Found: {len(raw)} CSS files{RST}\n" + "\n".join(sorted(raw))

            # ----- OTHER MODES (unchanged logic) -----
            elif mode == '-meta':
                title = re.findall(r'<title>(.*?)</title>', html, re.I)
                desc  = re.findall(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.I)
                metas = re.findall(r'<meta[^>]+>', html, re.I)
                return (f"TITLE: {title[0] if title else 'N/A'}\n"
                        f"DESC:  {desc[0]  if desc  else 'N/A'}\n"
                        + "\n".join(metas))
            elif mode == '-forms':
                forms  = re.findall(r'<form[^>]*>.*?</form>', html, re.DOTALL|re.I)
                inputs = re.findall(r'<input[^>]*>', html, re.I)
                return (f"FORMS ({len(forms)}):\n" + "\n---\n".join(forms)
                        + f"\n\nINPUTS ({len(inputs)}):\n" + "\n".join(inputs))
            elif mode == '-headers':
                return "\n".join(f"{k}: {v}" for k,v in r.headers.items())
            elif mode == '-status':
                return f"HTTP {r.status_code} ({len(r.content)} B)"
            elif mode == '-size':
                b = len(r.content)
                return f"{b} bytes ({b // 1024} KB)"
            elif mode == '-words':
                clean = re.sub(r'<[^>]+>','',re.sub(r'<(script|style).*?>.*?</\1>','',html,flags=re.DOTALL|re.I))
                words = re.findall(r'\b\w+\b', clean)
                return f"Total: {len(words)} | Unique: {len(set(w.lower() for w in words))}"
            elif mode == '-all':
                out = []
                for m in ['-status','-headers','-meta','-emails','-phones','-links','-images','-js','-css']:
                    out.append(f"\n{Y}=== {m} ==={RST}\n" + self.get_web_data(url, m, flags))
                return "\n".join(out)
            return html
        except Exception as e:
            return f"{R}Connection error: {e}{RST}"

    # =================== URL GENERATOR ===================
    def generate_urls(self, pattern, length, use_wl=False, use_https=True):
        now = datetime.now()
        p = (pattern
             .replace('<year>',  now.strftime('%Y'))
             .replace('<month>', now.strftime('%m'))
             .replace('<day>',   now.strftime('%d')))
        ranges  = re.findall(r'\{(\d+)-(\d+)\}', p)
        for a,b in ranges: p = p.replace(f'{{{a}-{b}}}', '{range}', 1)
        customs = re.findall(r'\[([^\]]+)\]', p)
        for cl in customs: p = p.replace(f'[{cl}]', '{custom}', 1)

        wl = self.wordlist if use_wl and self.wordlist else self.lists['word']
        ph = {
            '<brute>': ["".join(i) for i in itertools.product(self.lists['brute'], repeat=length)] if '<brute>' in p else [''],
            '<char>':  ["".join(i) for i in itertools.product(self.lists['char'],  repeat=length)] if '<char>'  in p else [''],
            '<num>':   ["".join(i) for i in itertools.product(self.lists['num'],   repeat=length)] if '<num>'   in p else [''],
            '<upper>': ["".join(i) for i in itertools.product(self.lists['upper'], repeat=length)] if '<upper>' in p else [''],
            '<hex>':   ["".join(i) for i in itertools.product(self.lists['hex'],   repeat=length)] if '<hex>'   in p else [''],
            '<tld>':   self.lists['tld'],
            '<word>':  wl,
            '{range}': [[str(i) for i in range(int(a), int(b)+1)] for a,b in ranges],
            '{custom}':[cl.split(',') for cl in customs],
        }
        segs = re.split(r'(<[^>]+>|\{range\}|\{custom\})', p)
        opts_list = []
        ph_range  = list(ph['{range}'])
        ph_custom = list(ph['{custom}'])
        for s in segs:
            if s == '{range}':   opts_list.append(ph_range.pop(0)  if ph_range  else [s])
            elif s == '{custom}':opts_list.append(ph_custom.pop(0) if ph_custom else [s])
            elif s in ph:        opts_list.append(ph[s])
            elif s:              opts_list.append([s])
        proto = 'https://' if use_https else 'http://'
        return [proto + "".join(combo) for combo in itertools.product(*opts_list)]

    # =================== FETCH ===================
    def fetch(self, url, phrase, opts, total):
        retries      = opts.get('retries', 2)
        timeout      = opts.get('timeout', 3)
        verbose      = opts.get('verbose', False)
        use_head     = opts.get('head', False)
        target_code  = opts.get('status', None)
        ignore_codes = opts.get('ignore', [])
        out_file     = opts.get('outfile', self.output_file)
        ua           = opts.get('ua') or random.choice(self.ua_list)
        method       = requests.head if use_head else requests.get

        for attempt in range(retries + 1):
            try:
                resp = method(url, headers={'User-Agent': ua}, timeout=timeout, allow_redirects=True)
                if resp.status_code in ignore_codes: break
                hit = (resp.status_code == target_code) if target_code else \
                      (resp.status_code < 400 and phrase.lower() in resp.text.lower())
                if hit:
                    srv  = resp.headers.get('Server', 'Hidden')
                    ct   = resp.headers.get('Content-Type', '?')[:30]
                    sz   = len(resp.content)
                    line = f"{url} | {resp.status_code} | SRV:{srv} | {sz}B | {datetime.now().strftime('%H:%M:%S')}"
                    print(f"\n{G}{BLD}[HIT]{RST} {url} {DIM}| {resp.status_code} | {srv} | {sz}B | {ct}{RST}")
                    with self.lock:
                        self.stats['hits'] += 1
                        with open(out_file, 'a', encoding='utf-8') as f: f.write(line + '\n')
                elif verbose:
                    print(f"{DIM}[-] {resp.status_code}: {url}{RST}")
                break
            except requests.exceptions.Timeout:
                if attempt == retries:
                    with self.lock: self.stats['errors'] += 1
            except Exception:
                with self.lock: self.stats['errors'] += 1
                break

        with self.lock:
            self.stats['scanned'] += 1
            done = self.stats['scanned']
            hits = self.stats['hits']
            errs = self.stats['errors']
            pct  = int(done / total * 20) if total else 0
            bar  = f"[{'#'*pct}{'.'*(20-pct)}]"
            if not verbose:
                print(f"\r{C}{bar}{RST} {done}/{total} {G}HIT:{hits}{RST} {R}ERR:{errs}{RST}  ", end='', flush=True)

    # =================== WORDLIST ===================
    def wl_cmd(self, parts):
        if len(parts) < 2: print(f"{R}Missing subcommand. Use: wl load/show/save/add/del/clear/count{RST}"); return
        sub = parts[1]
        if sub == 'load':
            if len(parts) < 3: print(f"{R}Provide file path{RST}"); return
            path = parts[2]
            if not os.path.exists(path): print(f"{R}File not found: {path}{RST}"); return
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.wordlist = [l.strip() for l in f if l.strip()]
            print(f"{G}Loaded {len(self.wordlist)} words from {path}{RST}")
        elif sub == 'show':
            if not self.wordlist: print(f"{Y}Wordlist is empty{RST}"); return
            for i,w in enumerate(self.wordlist[:50], 1): print(f"  {DIM}{i:3}.{RST} {w}")
            if len(self.wordlist) > 50: print(f"  {DIM}... and {len(self.wordlist)-50} more{RST}")
        elif sub == 'save':
            if len(parts) < 3: print(f"{R}Provide file path{RST}"); return
            with open(parts[2], 'w', encoding='utf-8') as f: f.write("\n".join(self.lists['word']))
            print(f"{G}Saved {len(self.lists['word'])} words to {parts[2]}{RST}")
        elif sub == 'add':
            if len(parts) < 3: return
            self.lists['word'].append(parts[2])
            print(f"{G}Added: {parts[2]}{RST}")
        elif sub == 'del':
            if len(parts) < 3: return
            if parts[2] in self.lists['word']:
                self.lists['word'].remove(parts[2])
                print(f"{Y}Removed: {parts[2]}{RST}")
            else: print(f"{R}Word not found in list{RST}")
        elif sub == 'clear':
            self.wordlist = []
            print(f"{Y}Wordlist cleared{RST}")
        elif sub == 'count':
            print(f"{C}Loaded wordlist: {len(self.wordlist)} | Built-in word list: {len(self.lists['word'])}{RST}")

    # =================== STATS ===================
    def show_stats(self):
        elapsed = datetime.now() - self.stats['start']
        size    = os.path.getsize(self.output_file) if os.path.exists(self.output_file) else 0
        print(f"""
{Y}{BLD}=== SESSION STATS ==={RST}
  Scanned   : {C}{self.stats['scanned']}{RST}
  Hits      : {G}{self.stats['hits']}{RST}
  Errors    : {R}{self.stats['errors']}{RST}
  Session   : {DIM}{str(elapsed).split('.')[0]}{RST}
  Output    : {self.output_file}  ({size} B)
""")

    # =================== MAIN HANDLER ===================
    def handle_input(self, cmd):
        # PIPE ENGINE
        if '|' in cmd:
            left, right = cmd.split('|', 1)
            left = left.strip(); right = right.strip()
            if left.startswith('html '):
                sp    = left.split()
                url   = sp[1]
                mode  = next((x for x in sp[2:] if x in MODES), None)
                flags = [x for x in sp[2:] if x.startswith('--')]
                content = self.get_web_data(url, mode, flags)
                phrase  = right.replace('grep','',1).strip().strip("'\"")
                count   = 0
                for line in content.splitlines():
                    if phrase.lower() in line.lower():
                        print(f"{B}[M]{RST} {line.strip()[:160]}"); count += 1
                print(f"{DIM}Matched: {count}{RST}")
            return

        parts  = cmd.split()
        if not parts: return
        action = parts[0].lower()

        # HTML SCRAPER
        if action == 'html':
            if len(parts) < 2: print(f"{R}Usage: html <url> <mode> [--flags]{RST}"); return
            url   = parts[1]
            mode  = next((x for x in parts[2:] if x in MODES), None)
            flags = [x for x in parts[2:] if x.startswith('--')]
            print(self.get_web_data(url, mode, flags))

        # SCANNER
        elif action == 'scan':
            if len(parts) < 3: print(f"{R}Usage: scan <pattern> <phrase> [options]{RST}"); return
            pat = parts[1]; find = parts[2]
            def gv(flag, cast=int, default=None):
                return cast(parts[parts.index(flag)+1]) if flag in parts else default
            l  = gv('-l',  int,   1)
            t  = min(gv('-t', int, 20), 100)
            r  = gv('-r',  int,   2)
            to = gv('-to', float, 3)
            sc = gv('-s',  int,   None)
            of = gv('-o',  str,   self.output_file)
            ua = gv('-ua', str,   None)
            ix = [int(x) for x in parts[parts.index('-x')+1].split(',')] if '-x' in parts else []
            use_wl    = '-wl'        in parts
            use_https = '--no-https' not in parts
            use_head  = '--head'     in parts
            verbose   = '-v'         in parts
            if '-c' in parts and os.path.exists(of): os.remove(of)
            urls  = self.generate_urls(pat, l, use_wl=use_wl, use_https=use_https)
            count = len(urls)
            print(f"{C}Generated: {count} URLs | Threads: {t} | Retries: {r} | Timeout: {to}s{RST}")
            if count > 50000:
                if input(f"{Y}Large scan ({count} URLs), continue? [y/N]: {RST}").strip().lower() != 'y': return
            opts = {'retries':r,'timeout':to,'verbose':verbose,'head':use_head,
                    'status':sc,'ignore':ix,'outfile':of,'ua':ua}
            self.stats['scanned'] = self.stats['hits'] = self.stats['errors'] = 0
            with ThreadPoolExecutor(max_workers=t) as ex:
                futs = [ex.submit(self.fetch, u, find, opts, count) for u in urls]
                try:
                    for _ in as_completed(futs): pass
                except KeyboardInterrupt:
                    print(f"\n{Y}Interrupted by user{RST}")
            print(f"\n{G}Done! Hits: {self.stats['hits']}{RST}")

        # GREP
        elif action == 'grep':
            if len(parts) < 2: return
            phrase = ' '.join(parts[1:]).strip("'\"")
            if not os.path.exists(self.output_file): print(f"{R}No found.txt{RST}"); return
            count = 0
            with open(self.output_file, 'r') as f:
                for line in f:
                    if phrase.lower() in line.lower():
                        print(f"{B}>{RST} {line.strip()}"); count += 1
            print(f"{DIM}Found: {count}{RST}")

        elif action == 'wl':     self.wl_cmd(parts)
        elif action == 'stats':  self.show_stats()

        elif action == 'set':
            if len(parts) < 3: return
            self.lists[parts[1]] = parts[2].split(',')
            print(f"{G}List '{parts[1]}' updated ({len(self.lists[parts[1]])} items){RST}")

        elif action == 'show':
            key = parts[1] if len(parts) > 1 else 'word'
            lst = self.lists.get(key)
            if lst: print(f"{C}{key}{RST}: " + ', '.join(lst))
            else:   print(f"{R}Unknown list: {key}{RST}")

        elif action == 'export':
            if len(parts) < 2: return
            if os.path.exists(self.output_file):
                shutil.copy(self.output_file, parts[1])
                print(f"{G}Exported to {parts[1]}{RST}")

        elif action == 'cat':
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r') as f: print(f.read())
            else: print(f"{Y}No found.txt yet{RST}")

        elif action == 'rm':
            if os.path.exists(self.output_file):
                os.remove(self.output_file); print(f"{Y}Deleted found.txt{RST}")

        elif action == 'ls':
            for f in sorted(os.listdir('.')): print(f)

        elif action in ('clear','cls'):
            os.system('clear')

        else:
            print(f"{R}Unknown command: '{action}'. Type 'help' for docs.{RST}")

# =================== ENTRY POINT ===================
def main():
    f = ExtremeFuzzer()
    os.system('clear')
    print(BANNER)
    print(f"  {DIM}Type 'help' for full documentation{RST}\n")
    while True:
        try:
            c = input(f"{M}fuzzer{RST}{DIM}>{RST} ").strip()
            if not c: continue
            if c.lower() == 'exit': print(f"{Y}Bye!{RST}"); break
            if c.lower() == 'help': print(HELP); continue
            f.handle_input(c)
        except KeyboardInterrupt:
            print(f"\n{Y}Ctrl+C — type 'exit' to quit{RST}")
        except Exception as e:
            print(f"{R}[ERROR]{RST} {e}")

if __name__ == "__main__":
    main()
