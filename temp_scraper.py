import urllib.request
import urllib.parse
import re

req = urllib.request.Request(
    'https://html.duckduckgo.com/html/?q=urllib',
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
)
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    match = re.search(r'a class="result__url" href="([^"]+)"', html)
    if match:
        result = match.group(1)
        if "uddg=" in result:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(result).query)
            if 'uddg' in parsed:
                print("FOUND:", parsed['uddg'][0])
        else:
            print("FOUND:", result)
    else:
        print("NOT FOUND")
except Exception as e:
    print("ERROR:", e)
