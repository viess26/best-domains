import io, ipaddress, socket, ssl, sys, time, zipfile, urllib.request
from concurrent.futures import ThreadPoolExecutor

TOP_N = 5000
KEEP = 50
PORT = 443
BAD = ("porn", "xxx", "sex", "adult", "casino", "gambl")

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read()

nets = [ipaddress.ip_network(x) for x in get("https://www.cloudflare.com/ips-v4").decode().split()]

z = zipfile.ZipFile(io.BytesIO(get("https://tranco-list.eu/top-1m.csv.zip")))
rows = z.read(z.namelist()[0]).decode().splitlines()[:TOP_N]
domains = [r.split(",")[1] for r in rows if "," in r]
domains = [d for d in domains if not any(b in d for b in BAD)]
print("候选域名:", len(domains))

def is_cf(d):
    try:
        ip = socket.getaddrinfo(d, 443, socket.AF_INET, socket.SOCK_STREAM)[0][4][0]
        a = ipaddress.ip_address(ip)
        return d if any(a in n for n in nets) else None
    except Exception:
        return None

def test(d):
    best = None
    for _ in range(2):
        try:
            t = time.time()
            ctx = ssl.create_default_context()
            with socket.create_connection((d, PORT), timeout=4) as s:
                with ctx.wrap_socket(s, server_hostname=d):
                    pass
            ms = (time.time() - t) * 1000
            best = ms if best is None else min(best, ms)
        except Exception:
            return None
    return (best, d)

with ThreadPoolExecutor(100) as p:
    cf = [d for d in p.map(is_cf, domains) if d]
print("Cloudflare 域名:", len(cf))

with ThreadPoolExecutor(50) as p:
    ok = sorted(r for r in p.map(test, cf) if r)
print("端口可连通:", len(ok))

if not ok:
    sys.exit("没有可用域名，不更新文件")

with open("BestDomains", "w") as f:
    f.write("\n".join(f"{d}:{PORT}" for _, d in ok[:KEEP]) + "\n")
