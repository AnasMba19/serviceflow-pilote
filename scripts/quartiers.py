"""Abords des immeubles Gecina, depuis l'API WFS de la Geoplateforme IGN (BD TOPO, Licence Ouverte 2.0).
- batiments a moins de 200 m, avec leur hauteur (relief 3D) ; empreinte exacte de l'immeuble Gecina et son identifiant RNB
- troncons de rue a moins de 600 m, avec leur nom (noms affiches sur la carte)
Entree : data/paris-geo.json (couche immeubles). Sortie : data/quartiers.json. Execute par la GitHub Action."""
import json, math, urllib.parse, urllib.request
import numpy as np
import shapely
from shapely.geometry import shape, mapping, Point

WFS = 'https://data.geopf.fr/wfs/ows'
geo = json.load(open('data/paris-geo.json'))
imm = [(f['properties']['code'], *f['geometry']['coordinates']) for f in geo['layers']['immeubles']['features']]
# Cuisine du chef : meme traitement (emprise exacte en 3D, batiments et rues autour), sous le code CUISINE.
for f in (geo['layers'].get('livraison') or {}).get('features', []):
    if f['properties'].get('kind') == 'cuisine':
        imm.append(('CUISINE', *f['geometry']['coordinates']))

def fetch(typ, lat, lng, dx, dy):
    feats, start = [], 0
    while True:
        q = {'SERVICE': 'WFS', 'VERSION': '2.0.0', 'REQUEST': 'GetFeature', 'TYPENAMES': 'BDTOPO_V3:' + typ,
             'OUTPUTFORMAT': 'application/json', 'SRSNAME': 'EPSG:4326', 'COUNT': '2000', 'STARTINDEX': str(start), 'SORTBY': 'cleabs',
             'BBOX': f'{lat - dy:.6f},{lng - dx:.6f},{lat + dy:.6f},{lng + dx:.6f},urn:ogc:def:crs:EPSG::4326'}
        with urllib.request.urlopen(WFS + '?' + urllib.parse.urlencode(q), timeout=120) as r:
            page = json.load(r)['features']
        feats += page
        if len(page) < 2000: return feats
        start += 2000

def to_m(lat0, lng0):
    kx, ky = math.cos(math.radians(lat0)) * 111320, 110540
    return lambda g: shapely.transform(g, lambda c: np.column_stack(((c[:, 0] - lng0) * kx, (c[:, 1] - lat0) * ky)))

def r5(g):
    def rnd(c):
        if isinstance(c[0], (list, tuple)): return [rnd(x) for x in c]
        return [round(c[0], 5), round(c[1], 5)]
    m = mapping(g)
    return {'type': m['type'], 'coordinates': rnd(m['coordinates'])}

bati, rues, rnb = {}, {}, {}
for code, lng, lat in imm:
    proj = to_m(lat, lng)
    here = Point(0, 0)
    best = None
    for f in fetch('batiment', lat, lng, 0.0042, 0.0028):
        p = f['properties']; g = shapely.force_2d(shape(f['geometry']))
        d = proj(g).distance(here)
        if d > 200: continue
        cle = p['cleabs']
        if cle not in bati:
            bati[cle] = {'g': g.simplify(0.000004, preserve_topology=True), 'h': round(p.get('hauteur') or 12)}
        # Immeuble Gecina : la plus grande emprise a moins de 35 m du point de l'adresse (bureaux = grands volumes).
        # La cuisine est un restaurant en pied d'immeuble : le batiment qui contient l'adresse (ou le plus proche).
        if d <= 35:
            score = -d if code == 'CUISINE' else proj(g).area
            if best is None or score > best[0]:
                best = (score, cle, p.get('identifiants_rnb'), p.get('hauteur'))
    if best:
        bati[best[1]]['code'] = code
        rnb[code] = {'rnb': best[2], 'hauteur': best[3]}
    for f in fetch('troncon_de_route', lat, lng, 0.009, 0.006):
        p = f['properties']
        if (p.get('position_par_rapport_au_sol') or '0').startswith('-') or p.get('nature') in ('Escalier', 'Bac ou liaison maritime'): continue
        g = shapely.force_2d(shape(f['geometry']))
        if proj(g).distance(here) > 600 or p['cleabs'] in rues: continue
        rues[p['cleabs']] = {'g': g.simplify(0.00001, preserve_topology=True), 'n': p.get('nom_voie_ban_gauche') or p.get('nom_voie_ban_droite'),
                             'i': int(p.get('importance') or 5)}
    print(code, len(bati), len(rues))

def fc(items, props):
    return {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': r5(v['g']), 'properties': props(v)} for v in items]}

out = {
    'source': 'IGN BD TOPO via Geoplateforme WFS (Licence Ouverte 2.0)',
    'bati3d': fc(bati.values(), lambda v: {k: v[k] for k in ('h', 'code') if k in v}),
    'rues_locales': fc(rues.values(), lambda v: {k: v[k] for k in ('n', 'i') if v.get(k) is not None}),
    'rnb': rnb,
}
json.dump(out, open('data/quartiers.json', 'w'), separators=(',', ':'), ensure_ascii=False)
print('bati', len(bati), 'rues', len(rues), 'rnb', rnb)
