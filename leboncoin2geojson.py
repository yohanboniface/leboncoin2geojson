#!/usr/bin/env python
"""
Get your Le Bon Coin results in GeoJSON.

Usage:
    leboncoin2geojson.py <url> [options]

Options:
    --help      shows this message and exit

"""

import re
import os
import json

from urllib.parse import urlparse, parse_qs

from docopt import docopt
import requests

from pyquery import PyQuery as pq

GEOCODER = os.environ.get('GEOCODER', 'http://france.photon.fluv.io/api/?')


def get_position(where):
    print('Getting position for', where)
    r = requests.get(GEOCODER, params={'q': where})
    gj = r.json()
    return gj['features'][0]['geometry']['coordinates']


def clean(s):
    return re.sub('\s+', ' ', s)


def to_geojson(url):
    # parsed = urlparse(url)
    # params = parse_qs(parsed.query)
    # url = '{scheme}://{netloc}'.format(scheme=parsed.scheme, netloc=parsed.netloc)
    r = requests.get(url, params={}, headers={'user-agent': 'PutThemOnAMapAmigos'})
    doc = pq(r.text)
    results = doc('.list-lbc a')
    features = []
    for el in map(pq, results):
        img = el('.image img')
        if not img:
            continue
        name = el.attr('title')
        print('Processing', name)
        url = el.attr('href')
        price = el('.price').text()
        where = clean(el('.placement').text()).split('/')
        if len(where) == 1:
            continue  # Only departement
        city, dep = where
        coords = get_position(city.strip())
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coords
            },
            "properties": {
                "name": name,
                "url": url,
                "price": price,
                "img": img.attr('src'),
                "city": city,
                "dep": dep
            }
        })
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    return geojson


if __name__ == "__main__":
    args = docopt(__doc__, version='0.0.1')
    geojson = to_geojson(args['<url>'])
    print(json.dumps(geojson))
