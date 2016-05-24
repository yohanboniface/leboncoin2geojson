#!/usr/bin/env python
"""
Get your Le Bon Coin results in GeoJSON.

Usage:
    leboncoin2geojson.py <url> [options]

Options:
    --help                  shows this message and exit
    --max_pages=<int>       max pages to process [default: 5]
    --geocoder=<url>        geocoder to user [default: http://api-adresse.data.gouv.fr/search/?]

"""

import re
import json

from urllib.parse import urlparse, parse_qs

from docopt import docopt
import requests

from pyquery import PyQuery as pq

GEOCODER = ""
MAX_PAGES = 5


def get_position(where):
    print('Getting position for', where)
    r = requests.get(GEOCODER, params={'q': where, 'limit': 1})
    gj = r.json()
    return gj['features'][0]['geometry']['coordinates'] if gj['features'] else None  # noqa


def clean(s):
    return re.sub('\s+', ' ', s)


def process_page(url, params, features=None, page=1):
    if features is None:
        features = []
    params['o'] = page
    print('# Page', page)
    r = requests.get(url, params=params, headers={'user-agent': 'PutThemOnAMapAmigos'})
    doc = pq(r.text)
    results = doc('.list-lbc a')
    features = []
    for el in map(pq, results):
        img = el('.image img')
        if not img:
            continue
        name = el.attr('title')
        print('Processing', name)
        href = el.attr('href')
        price = el('.price').text()
        where = clean(el('.placement').text()).split('/')
        if len(where) == 1:
            continue  # Only departement
        city, dep = where
        coords = get_position(" ".join([city.strip(), dep.strip()]))
        if not coords:
            print('{} not found'.format(name))
            continue
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coords
            },
            "properties": {
                "name": name,
                "url": href,
                "price": price,
                "img": img.attr('src'),
                "city": city,
                "dep": dep
            }
        })
    more_page = doc('#paging li:last a')
    if more_page and page < MAX_PAGES:
        features.extend(process_page(url, params, features, page + 1))
    return features


def to_geojson(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    url = '{scheme}://{netloc}{path}'.format(
        scheme=parsed.scheme,
        netloc=parsed.netloc,
        path=parsed.path,
    )
    features = process_page(url, params)
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    return geojson


if __name__ == "__main__":
    args = docopt(__doc__, version='0.0.1')
    MAX_PAGES = int(args['--max_pages'])
    GEOCODER = args['--geocoder']
    url = args['<url>']
    print('## Processing url', url)
    print('## max pages to process:', MAX_PAGES)
    geojson = to_geojson(url)
    print(json.dumps(geojson))
