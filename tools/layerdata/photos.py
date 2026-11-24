#!/usr/bin/env python3
"""Download free CC0 / public-domain photos from Openverse for the layer-data generator (no key needed, slow and polite).
  python3 tools/layerdata/photos.py --out photos --n 800
Only licences cc0 and pdm are requested; each file's source is written to photos/SOURCES.tsv."""
import argparse, json, os, time, urllib.parse, urllib.request

TOPICS = ('coffee food bakery people portrait city street beach mountain forest flower fashion shoes car interior office '
          'laptop phone concert crowd fitness yoga sky sunset texture wall fabric fruit market dog cat bird travel '
          'architecture product bottle book desk plant ocean river snow night lights').split()
UA = {'User-Agent': 'ShoofLayerData/1.0 (https://shoof.pages.dev)'}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=800)
    ap.add_argument('--topics', default='', help='space-separated search words (default: a general mix)')
    a = ap.parse_args()
    topics = a.topics.split() or TOPICS
    os.makedirs(a.out, exist_ok=True)
    seen, n = set(os.listdir(a.out)), len([f for f in os.listdir(a.out) if f.endswith('.jpg')])
    src = open(os.path.join(a.out, 'SOURCES.tsv'), 'a')
    page, fails = 1, 0
    while n < a.n and page < 40:
        for t in topics:
            if n >= a.n:
                break
            q = urllib.parse.urlencode({'q': t, 'license': 'cc0,pdm', 'page_size': 20, 'page': page, 'mature': 'false'})
            try:
                res = json.loads(get('https://api.openverse.org/v1/images/?' + q))['results']
            except Exception as ex:
                fails += 1
                print('search failed', t, ex)
                if fails >= 5 and n == 0:
                    print('Openverse not reachable: the generator will draw photo-like pictures instead')
                    return
                time.sleep(10)
                continue
            fails = 0
            for r in res:
                fn = r['id'] + '.jpg'
                if fn in seen or (r.get('width') or 0) < 400:
                    continue
                try:
                    b = get(f"https://api.openverse.org/v1/images/{r['id']}/thumb/")
                    open(os.path.join(a.out, fn), 'wb').write(b)
                    src.write(f"{fn}\t{r.get('license')}\t{r.get('foreign_landing_url') or r.get('url')}\n")
                    seen.add(fn)
                    n += 1
                except Exception:
                    pass
                time.sleep(0.3)
            time.sleep(3.2)   # anonymous limit is about 20 searches a minute
        page += 1
        print(n, 'photos', flush=True)
    print('done', n)


if __name__ == '__main__':
    main()
