CHANGELOG
=========

1.5.0 (2024-01-29)
------------------

- Ajout de la hiérachisation des types de zonages géographiques, avec l'ajout du champs `ref_geo.bib_areas_types.size_hierarchy` (#11)
- Remplacement du champs `l_areas.geojson_4326` par `l_areas.geom_4326` et création de triggers permettant de garder en cohérence les champs `geom` et `geom_4326` (#6)
- Mise à jour SQLAlchemy version 1.3 à 1.4 (#16)
- Mise à jour de Flask version 2 à 3
- Abandon du support de Debian 10 (#12)
- Mise à jour du linter Black à la version 24 (#19)

**🐛 Corrections**

- Correction des caractères `¼` et `½` en `Œ` et  `œ` dans les noms des communes (branche alembic `ref_geo_fr_municipalities`) (#8)


1.4.0 (2023-09-14)
------------------

**🚀 Nouveautés**

- Ajout d'un référentiel de couches de *points* (table des types de points et table de géometries + modèles) (#12)
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

1.3.0 (2023-03-03)
------------------

**🚀 Nouveautés**

- Ajout des routes historiquement créées pour GeoNature
- Possibilité de lancer le RefGeo comme application Flask autonome
- Support de SQLAlchemy 1.4
- Intégration continue avec ``pytest``


1.2.1 (2022-11-21)
------------------

**🐛 Corrections**

* Marquage du champs géométrique ``ref_geo.l_areas.geojson_4326`` comme différé afin de ne pas le renvoyer en raison de son poids sauf si demandé explicitement.


1.2.0 (2022-10-20)
------------------

**🚀 Nouveautés**

* Ajout de tables et de modèles pour un référentiel geographique de linéaires
    * Peut être organisé en tronçons (stockés dans ``ref_geo.l_linears``) qui peuvent appartenir à un groupe de linéaires (``ref_geo.t_linear_groups``)
    * Par exemple les tronçons d'autoroute ``A7_40727085`` et ``A7_40819117`` appartiennent au groupe ``Autoroute A7``
* Ajout d'une fonction ``get_local_srid`` pour récupérer le SRID local automatiquement à partir des données, à partir de la fonction ``FIND_SRID``


1.1.1 (2022-08-31)
------------------

**🚀 Nouveautés**

* Ajout de la sous-commande ``ref_geo info`` permettant de lister les zones par types.
* Mise-à-jour des dépendances :
    * Utils-Flask-SQLAlchemy 0.3.0
    * Utils-Flask-SQLAlchemy-Geo 0.2.4

**🐛 Corrections**

* Ajout des champs manquants au modèle ``LAreas``.


1.1.0 (2022-06-03)
------------------

**🚀 Nouveautés**

* Ajout des modèles SQLAlchemy géographiques

**🐛 Corrections**

* Auto-détection du SRID local sans accéder aux paramètres de GeoNature


1.0.1 (2022-03-04)
------------------

**🐛 Corrections**

* Correction du trigger de calcule de l’altitude min / max.


1.0.0 (2022-03-04)
------------------

Externalisation du référentiel géographique de GeoNature 2.9.2.

**🚀 Nouveautés**

* Le SRID local est déterminé automatiquement à partir du SRID de la colonne ``ref_geo.l_areas.geom``.
