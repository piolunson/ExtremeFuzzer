# ExtremeFuzzer

![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python)
![Version](https://img.shields.io/badge/version-13.0-cyan?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Android%20(Pydroid%203)-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

A single-file Python terminal tool for **URL fuzzing**, **web scraping**, and **directory/subdomain discovery** — with a clean interactive shell, threaded scanner, and rich filtering flags.

> ⚠️ **For educational and authorized testing only.** Do not scan systems you don't own or have permission to test.

---

## Features

- 🔍 **URL Fuzzer** — generate thousands of URLs using tags like `<word>`, `<brute>`, `<num>`, ranges `{1-5}`, inline lists `[a,b,c]`
- 🌐 **Web Scraper** — extract links, images, emails, phones, JS/CSS files, meta tags, forms, headers and more
- 🏷️ **Filtering flags** — every scraper mode has `--` flags (e.g. `--ext`, `--int`, `--no-anchor`, `--headings`)
- 📋 **Wordlist support** — load external `.txt` wordlists, manage them live
- ⚡ **Threaded scanner** — up to 100 threads, retries, custom timeout, HEAD mode
- 🔗 **Pipe engine** — `html <url> -links --ext | grep github`
- 💾 **Session stats**, result export, `grep` on output file

---

## Installation

```bash
git clone https://github.com/piolunson/ExtremeFuzzer
cd ExtremeFuzzer
pip install requests
python extreme_fuzzer_v13.py
```

**Pydroid 3 (Android):**
1. Install `requests` via Pydroid's pip
2. Open `extreme_fuzzer_v13.py` and tap ▶

---

## Quick Start

```
fuzzer> html example.com -links --ext
fuzzer> html example.com -emails --domain gmail.com
fuzzer> html example.com -js --inline
fuzzer> scan <word>.example.com "" -s 200 -t 30
fuzzer> scan api.example.com/<word> "json" -t 20 -v
fuzzer> scan srv-{1-10}.example.com "" -s 200
```

---

## URL Tags

| Tag | Description | Requires `-l` |
|---|---|---|
| `<brute>` | All a-z + 0-9 combinations | ✅ |
| `<char>` | Lowercase letters only | ✅ |
| `<upper>` | Uppercase letters only | ✅ |
| `<num>` | Digits only | ✅ |
| `<hex>` | Hex characters | ✅ |
| `<word>` | Built-in keyword list | ❌ |
| `<tld>` | TLD list (.com, .pl, ...) | ❌ |
| `<year>` | Current year | ❌ |
| `<month>` | Current month | ❌ |
| `<day>` | Current day | ❌ |
| `{1-9}` | Numeric range | ❌ |
| `[a,b,c]` | Inline list | ❌ |

---

## Scan Options

```
scan <pattern> <phrase> [options]

  -l <n>        Brute length (default: 1)
  -t <n>        Threads (default: 20, max: 100)
  -r <n>        Retries (default: 2)
  -to <s>       Timeout seconds (default: 3)
  -s <n>        Match by HTTP status code
  -o <file>     Output file (default: found.txt)
  -x <codes>    Ignore status codes (e.g. -x 403,404)
  -ua <string>  Custom User-Agent
  -wl           Use loaded wordlist as <word>
  -v            Verbose (show all status codes)
  -c            Clear output file before scan
  --no-https    Use HTTP instead of HTTPS
  --head        Use HEAD requests (faster, no body)
```

---

## Scraper Modes & Flags

### `-links`
```
html <url> -links [--flags]

  --ext         External links only (other domains)
  --int         Internal links only (same domain)
  --no-anchor   Hide #fragment links
  --no-mailto   Hide mailto: links
  --no-js       Hide javascript: links
  --abs         Force absolute URLs
```

### `-images`
```
  --ext         External images only
  --int         Internal images only
  --no-svg      Hide .svg files
  --no-ico      Hide .ico files
```

### `-text`
```
  --headings    Only h1–h6 content
  --min <n>     Only lines longer than n characters
```

### `-emails`
```
  --domain <d>  Only emails from specific domain
```

### `-phones`
```
  --intl        International format only (+XX...)
```

### `-js`
```
  --ext         External scripts only
  --int         Internal scripts only
  --inline      Also show inline <script> blocks
```

### `-css`
```
  --ext         External stylesheets only
  --int         Internal stylesheets only
```

### Other modes
| Mode | Description |
|---|---|
| `-meta` | Title, description, all meta tags |
| `-forms` | Form elements and inputs |
| `-headers` | HTTP response headers |
| `-status` | Status code + size |
| `-size` | Response size in bytes / KB |
| `-words` | Total and unique word count |
| `-all` | Run all modes at once |

---

## Wordlist Commands

```
wl load <file>    Load wordlist from .txt file
wl show           Show first 50 words
wl save <file>    Save built-in word list to file
wl add <word>     Add word to built-in list
wl del <word>     Remove word from built-in list
wl clear          Clear loaded wordlist
wl count          Show counts
```

Use `-wl` in scan to use the loaded wordlist instead of built-in `<word>`:
```
fuzzer> wl load rockyou_short.txt
fuzzer> scan example.com/<word> "" -wl -s 200
```

---

## Pipe Engine

```
html <url> <mode> [--flags] | grep <phrase>
```

Examples:
```
html example.com -links --ext | grep github
html example.com -emails | grep admin
html example.com -js --ext | grep cdn
```

---

## File Commands

```
cat             Print found.txt
rm              Delete found.txt
ls              List current directory
grep <phrase>   Search in found.txt
export <file>   Copy found.txt to another file
stats           Show session statistics
set <list> ...  Update a built-in list
show <list>     Print a built-in list
```

---

## Examples

```bash
# Find admin panels on subdomains
scan <word>.target.com "Login" -t 50 -s 200

# Brute-force 3-char paths
scan target.com/<char> "" -l 3 -s 200 --head

# Scrape all external links
html target.com -links --ext --no-anchor

# Extract emails from a specific domain
html target.com -emails --domain target.com

# Find JS files loaded from CDNs
html target.com -js --ext | grep cdn

# Scan with custom wordlist
wl load paths.txt
scan target.com/<word> "" -wl -t 40 -v
```

---

## Requirements

- Python 3.8+
- `requests` library (`pip install requests`)

No other dependencies — single file, runs anywhere Python does.

---

## License

MIT — see [LICENSE](LICENSE)
