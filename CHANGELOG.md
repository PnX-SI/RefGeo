# CHANGELOG

## 1.5.7 (2026-02-18)

**🚀 Nouveautés**

- Mise à jour des dépendances

## 1.5.6 (2025-09-25)

**🐛 Corrections**

- Correction du build du package Python à l'origine de l'échec des tests sur GeoNature (par @jacquesfize)

## 1.5.5 (2025-05-21)

**🚀 Nouveautés**

- Ajout d'une colonne `description` dans la table `l_areas` (#35 par @juggler31)
- Ajout de la compatibilité avec Debian 13 et Python 3.13 (#38 par @bouttier)

**🐛 Corrections**

- Ajout des valeurs manquantes dans `size_hierarchy` pour les mailles 2, 20 et 50 (#39 par @jacquesfize)

## 1.5.4 (2024-10-23)

- Ajout des nouvelles mailles officielles de l'INPN en métropole (2x2km, 20x20km, 50x50km), utilisées par la nouvelle version du référentiel de sensibilité (#24, par @lpofredc)
- Ajout des commandes `flask ref_geo activate` et `flask ref_geo deactivate` pour activer/desactiver des zonages dans le référentiel géographique (#29) :
  - par type de zonage : `flask ref_geo activate --area-type COM --area-type DEP`
  - par nom de zonage ; `flask ref_geo activate --area-name Ain --area-name Hautes-Alpes`
  - par code de zonage (voir `l_areas.area_code`) : `flask ref_geo activate --area-code 01`
  - par géométrie : `flask ref_geo activate --area-type in-polygon 'POLYGON ((-1.653442 49.628504, -1.588898 49.628504, -1.588898 49.653849, -1.653442 49.653849, -1.653442 49.628504))'`
- Amélioration de la route de recherche par commune : pouvoir saisir un nom de commune sans saisir les tirets séparateurs de mots ou les caractères accentués (#31, par @ch-cbna)
- Amélioration de la fonction de détermination de l'altitude à partir d'une géométrie `ref_geo.fct_get_altitude_intersection(geom)` (#9 par @jbrieuclp)

**🐛 Corrections**

- Correction d'une erreur sur le paramètre `limit` de la route `/areas` (#33, par @gildeluermoz)
- Modification d'un import Python (#30, par @edelclaux)

**⚠️ Notes de version**

Si vous n'utilisez pas GeoNature, pour ajouter les nouvelles mailles, exécuter les commandes suivantes :

```sh
source venv/bin/activate
export SQLALCHEMY_DATABASE_URI="postgresql://user:password@localhost:543database"
cd src/ref_geo/migrations
alembic upgrade ref_geo_inpn_grids_2@head  # Insertion des mailles 2x2km métropole, fournies par l’INPN
alembic upgrade ref_geo_inpn_grids_20@head  # Insertion des mailles 20x20km métropole, fournies par l’INPN
alembic upgrade ref_geo_inpn_grids_50@head  # Insertion des mailles 50x50km métropole, fournies par l’INPN
```

## 1.5.3 (2024-05-23)

**🐛 Corrections**

- Correction de l'intégration des paramètres de type `list` dans la route `/areas` (#26)

## 1.5.2 (2024-09-10)

**🚀 Nouveautés**

- Possibilité d'appeler la route `GET/areas` sans retourner les géométries (#22)

## 1.5.1 (2024-01-29)

- Ajout de la hiérachisation des types de zonages géographiques, avec l'ajout du champs `ref_geo.bib_areas_types.size_hierarchy` (#11)
- Remplacement du champs `l_areas.geojson_4326` par `l_areas.geom_4326` et création de triggers permettant de garder en cohérence les champs `geom` et `geom_4326` (#6)
- Mise à jour SQLAlchemy version 1.3 à 1.4 (#16)
- Mise à jour de Flask version 2 à 3
- Abandon du support de Debian 10 (#12)
- Mise à jour du linter Black à la version 24 (#19)

**🐛 Corrections**

- Correction des caractères `¼` et `½` en `Œ` et `œ` dans les noms des communes (branche alembic `ref_geo_fr_municipalities`) (#8)

## 1.4.0 (2023-09-14)

**🚀 Nouveautés**

- Ajout d'un référentiel de couches de _points_ (table des types de points et table de géometries + modèles) (#12)
- Ajout de tables de correspondance entre les linéaires et les zonages (+ relations associées dans les modèles) (#12)

**⚠️ Notes de version**

- Les nouvelles tables de correspondances `ref_geo.cor_areas` et `ref_geo.cor_linear_area` ne sont pas remplies par défaut pour ne pas alourdir la base de données et ses calculs, alors qu'elles ne sont pas utilisées actuellement par GeoNature
- Exemple de requête pour remplir la table `ref_geo.cor_area_linear` pour les régions, départements et communes :

  ```
  INSERT INTO ref_geo.cor_linear_area (id_linear, id_area)
  SELECT  id_linear, id_area
    FROM ref_geo.l_areas la
    JOIN ref_geo.l_linears ll ON la.geom && ll.geom
    JOIN ref_geo.bib_areas_types bat ON bat.id_type =la.id_type
    WHERE bat.type_code IN ('DEP', 'REG', 'COM')
  ```

## 1.3.0 (2023-03-03)

**🚀 Nouveautés**

- Ajout des routes historiquement créées pour GeoNature
- Possibilité de lancer le RefGeo comme application Flask autonome
- Support de SQLAlchemy 1.4
- Intégration continue avec `pytest`

## 1.2.1 (2022-11-21)

**🐛 Corrections**

- Marquage du champs géométrique `ref_geo.l_areas.geojson_4326` comme différé afin de ne pas le renvoyer en raison de son poids sauf si demandé explicitement.

## 1.2.0 (2022-10-20)

**🚀 Nouveautés**

- Ajout de tables et de modèles pour un référentiel geographique de linéaires
  - Peut être organisé en tronçons (stockés dans `ref_geo.l_linears`) qui peuvent appartenir à un groupe de linéaires (`ref_geo.t_linear_groups`)
  - Par exemple les tronçons d'autoroute `A7_40727085` et `A7_40819117` appartiennent au groupe `Autoroute A7`
- Ajout d'une fonction `get_local_srid` pour récupérer le SRID local automatiquement à partir des données, à partir de la fonction `FIND_SRID`

## 1.1.1 (2022-08-31)

**🚀 Nouveautés**

- Ajout de la sous-commande `ref_geo info` permettant de lister les zones par types.
- Mise-à-jour des dépendances :
  - Utils-Flask-SQLAlchemy 0.3.0
  - Utils-Flask-SQLAlchemy-Geo 0.2.4

**🐛 Corrections**

- Ajout des champs manquants au modèle `LAreas`.

## 1.1.0 (2022-06-03)

**🚀 Nouveautés**

- Ajout des modèles SQLAlchemy géographiques

**🐛 Corrections**

- Auto-détection du SRID local sans accéder aux paramètres de GeoNature

## 1.0.1 (2022-03-04)

**🐛 Corrections**

- Correction du trigger de calcule de l’altitude min / max.

## 1.0.0 (2022-03-04)

Externalisation du référentiel géographique de GeoNature 2.9.2.

**🚀 Nouveautés**

- Le SRID local est déterminé automatiquement à partir du SRID de la colonne `ref_geo.l_areas.geom`.
