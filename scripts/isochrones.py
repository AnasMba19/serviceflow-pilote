"""Zones livrables depuis la cuisine : isochrones 10, 20 et 30 minutes a velo et en voiture (hors trafic).
Moteur Valhalla (licence MIT), serveur de demonstration de FOSSGIS e.V. (usage raisonnable, identifiant client envoye).
Entree : data/paris-geo.json (couche livraison). Sortie : data/isochrones.json. Execute par la GitHub Action."""
import json, urllib.parse, urllib.request

geo = json.load(open('data/paris-geo.json'))
k = next((f for f in (geo['layers'].get('livraison') or {}).get('features', []) if f['properties'].get('kind') == 'cuisine'), None)
out = {'source': 'Valhalla (MIT) sur OpenStreetMap (ODbL), serveur FOSSGIS', 'type': 'FeatureCollection', 'features': []}
if k:
    lon, lat = k['geometry']['coordinates']
    for costing, mode in (('bicycle', 'velo'), ('auto', 'voiture')):
        q = {'locations': [{'lat': lat, 'lon': lon}], 'costing': costing, 'contours': [{'time': 10}, {'time': 20}, {'time': 30}],
             'polygons': True, 'denoise': 0.5, 'generalize': 60}
        req = urllib.request.Request('https://valhalla1.openstreetmap.de/isochrone?json=' + urllib.parse.quote(json.dumps(q, separators=(',', ':'))),
                                     headers={'X-Client-Id': 'la-table-gecina-pilote', 'User-Agent': 'la-table-gecina-pilote'})
        with urllib.request.urlopen(req, timeout=60) as r:
            fc = json.load(r)
        for f in fc['features']:
            def rnd(c):
                return [rnd(x) for x in c] if isinstance(c[0], list) else [round(c[0], 5), round(c[1], 5)]
            out['features'].append({'type': 'Feature', 'geometry': {'type': f['geometry']['type'], 'coordinates': rnd(f['geometry']['coordinates'])},
                                    'properties': {'mode': mode, 'min': int(f['properties']['contour'])}})
json.dump(out, open('data/isochrones.json', 'w'), separators=(',', ':'))
print('isochrones', len(out['features']))
