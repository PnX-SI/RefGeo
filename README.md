# Référentiel géographique

Prérequis : vous devez installer l’extension PostGIS dans votre base de données.

Création et remplissage du référentiel géographique :

```sh
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install psycopg2  # for postgresql database
export SQLALCHEMY_DATABASE_URI="postgresql://user:password@localhost:5432database"
cd src/ref_geo/migrations
alembic -x local-srid=2154 upgrade ref_geo@head
alembic upgrade ref_geo_fr_municipalities@head  # Insertion des communes françaises
alembic upgrade ref_geo_fr_departments@head  # Insertion des départements français
alembic upgrade ref_geo_fr_regions@head  # Insertion des régions françaises
alembic upgrade ref_geo_fr_regions_1970@head  # Insertion des anciennes régions françaises
alembic upgrade ref_geo_inpn_grids_1@head  # Insertion du maillage 1×1km de l’hexagone fourni par l’INPN
alembic upgrade ref_geo_inpn_grids_2@head  # Insertion du maillage 2x2km de l’hexagone fourni par l’INPN
alembic upgrade ref_geo_inpn_grids_5@head  # Insertion du maillage 5×5km de l’hexagone fourni par l’INPN
alembic upgrade ref_geo_inpn_grids_10@head  # Insertion du maillage 10×10km de l’hexagone fourni par l’INPN
alembic upgrade ref_geo_inpn_grids_20@head  # Insertion du maillage 20x20km de l’hexagone fourni par l’INPN
alembic upgrade ref_geo_inpn_grids_50@head  # Insertion du maillage 50x50km de l’hexagone fourni par l’INPN
```
