# ServiceFlow Pilote — Politique de confidentialité

Page statique publiée via GitHub Pages : https://anasmba19.github.io/serviceflow-pilote/

Section « Suppression des données » : https://anasmba19.github.io/serviceflow-pilote/#suppression

## Contenu publié

- `carte/` : carte des occupants (commande par WhatsApp, suivi de commande en direct), installable sur le téléphone.
- `equipe/` : interface de l'équipe (cuisine, livraison, pilotage, santé du bot). Non indexée ; les données réelles exigent une connexion Supabase.
- `data/` : données cartographiques ouvertes, régénérées par la GitHub Action « Données cartographiques Paris » (modifier `data/geo.demande` pour la relancer).

## Données cartographiques (toutes ouvertes, sans clé)

| Fichier | Contenu | Source et licence |
|---|---|---|
| `data/paris-geo.json` | Grands axes, Seine, arrondissements, lignes et gares, immeubles Gecina et gares proches, cuisine du chef (OnePlace, Rungis) et trajets vers chaque immeuble | IGN BD TOPO (Licence Ouverte 2.0), IDFM (Licence Ouverte 2.0), Ville de Paris (ODbL), OSRM sur OpenStreetMap (ODbL) |
| `data/quartiers.json` | Bâtiments en 3D à moins de 200 m et rues nommées à moins de 600 m de chaque immeuble, emprise et identifiant RNB de chaque immeuble | IGN BD TOPO via le service WFS de la Géoplateforme (Licence Ouverte 2.0) |
| `data/relief.webp` | Ombrage du relief de Paris et de la petite couronne | Terrain Tiles, AWS Open Data (Mapzen) |
