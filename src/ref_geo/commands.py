import os
import pprint
from contextlib import ExitStack
from zlib import adler32
import pathlib
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import fiona
import click
from flask.cli import with_appcontext
from sqlalchemy import func, select
import sqlalchemy as sa
from owslib.feature.wfs200 import WebFeatureService_2_0_0
from owslib.wfs import WebFeatureService
from shapely.geometry import shape
from geoalchemy2.shape import from_shape

from ref_geo.env import db
from ref_geo.models import BibAreasTypes, LAreas
from ref_geo.utils import (
    create_temporary_grids_table,
    get_local_srid,
    insert_areas_from_temporary_table,
    insert_grids_from_temporary_table,
)
from utils_flask_sqla.utils import open_remote_file

BASE_URL = "https://geonature.fr/data/"


@click.group(help="Manage geographical referential.")
def ref_geo():
    pass


@ref_geo.command()
@with_appcontext
def info():
    click.echo("RefGeo - type de zonages")
    stmt = (
        select(
            BibAreasTypes,
            func.count(LAreas.id_area).label("count"),
            func.count(LAreas.id_area).filter(LAreas.enable.is_(True)).label("count_enabled"),
            func.min(LAreas.meta_create_date).label("create_date_min"),
            func.max(LAreas.meta_create_date).label("create_date_max"),
        )
        .join(LAreas)
        .group_by(BibAreasTypes.id_type)
        .order_by(BibAreasTypes.type_code)
    )
    fmt1 = "  {:5s} {:20s} {:>17s}    {:>10s}    {}"
    fmt2 = "  {:5s} {:20s} {:17d}    {:10d}    {:%Y-%m-%d} - {:%Y-%m-%d}"
    click.echo(
        fmt1.format(
            "code", "description", "nombre de zonages", "activés", "date de création des zonages"
        )
    )
    for area_type, count, count_enabled, create_date_min, create_date_max in db.session.execute(
        stmt
    ).all():
        click.echo(
            fmt2.format(
                area_type.type_code,
                area_type.type_name,
                count,
                count_enabled,
                create_date_min,
                create_date_max,
            )
        )


def compute_where_clause(
    *where_clauses,
    area_code=None,
    area_name=None,
    area_type_code=None,
    in_polygon=None,
    out_polygon=None,
    confirm=True,
):
    """
    Generate a filter to match a subset of areas of the geographical referential.
    Filters are cumulative (areas must match all filters).

    Parameters
    ----------
    *where_clauses: list of where clauses
        List of additionnal where clauses
    area_code : list of str
        List of area codes to match.
    area_name : list of str
        List of area names to match.
    area_type_code : list of str
        List of area types to activate or deactivate. The type codes are
        checked in the `bib_areas_types` table.
    in_polygon : str
        WKT polygon defined in WGS84 coordinate reference system. The
        areas inside the polygon will match.
    out_polygon : str
        WKT polygon defined in WGS84 coordinate reference system. The
        areas outside the polygon will match.
    confirm : bool
        If True, a summary of matched obs will be displayed and the user is asked to continue.
    """

    where_clauses = list(where_clauses)
    if area_code:
        where_clauses += [LAreas.area_code.in_(area_code)]
    if area_name:
        where_clauses += [LAreas.area_name.in_(area_name)]
    if area_type_code:
        where_clauses += [LAreas.area_type.has(BibAreasTypes.type_code.in_(area_type_code))]
    if in_polygon:
        where_clauses += [
            func.ST_Intersects(LAreas.geom_4326, func.ST_GeomFromText(in_polygon, 4326))
        ]
    if out_polygon:
        where_clauses += [
            sa.not_(func.ST_Intersects(LAreas.geom_4326, func.ST_GeomFromText(out_polygon, 4326)))
        ]
    if not where_clauses:
        raise click.UsageError("No filters provided!")

    where_clause = sa.and_(*where_clauses)

    if confirm:
        stmt = (
            select(
                BibAreasTypes,
                func.count(LAreas.id_area).label("count"),
            )
            .join(
                LAreas,
                sa.and_(BibAreasTypes.id_type == LAreas.id_type, where_clause),
            )
            .group_by(BibAreasTypes.id_type)
            .order_by(BibAreasTypes.type_code)
        )
        click.echo("Your filters matched this number of areas:")
        for area_type, count in db.session.execute(stmt).all():
            click.echo(f"  {area_type.type_code:5s} {count}")
        click.confirm("Continue?", abort=True)

    return where_clause


def change_area_activation_status(where_clause, enable):
    rowcount = db.session.execute(
        sa.update(LAreas)
        .where(where_clause)
        .where(LAreas.enable != enable)
        .values(enable=enable)
        .execution_options(synchronize_session=False)
    ).rowcount
    click.echo(f"{rowcount} areas have been {'activated' if enable else 'deactivated'}")
    db.session.commit()


@ref_geo.command(help="Deactivate geographical data")
@click.option("--area-code", "-a", multiple=True, help="Areas' code to deactivate")
@click.option("--area-name", "-n", multiple=True, help="Areas' name to deactivate")
@click.option(
    "--area-type-code",
    "-t",
    multiple=True,
    help="Areas’ type to deactivate",
)
@click.option(
    "--in-polygon",
    "-p",
    help="Indicate a polygon in which areas will be deactivated. Must be in WKT format (SRID 4326)",
)
@click.option(
    "--out-polygon",
    "-o",
    help="Indicate a polygon in which areas will be kept. Must be in WKT format (SRID 4326)",
)
@with_appcontext
def deactivate(**kwargs):
    click.echo("RefGeo : deactivating areas...")
    change_area_activation_status(compute_where_clause(**kwargs), False)


@ref_geo.command(help="Activate geographical data")
@click.option("--area-code", "-a", multiple=True, help="Areas' code to activate")
@click.option("--area-name", "-n", multiple=True, help="Areas' name to activate")
@click.option(
    "--area-type-code",
    "-t",
    multiple=True,
    help="Area type to activate (check `type_code` in `bib_areas_types` table)",
)
@click.option(
    "--in-polygon",
    "-i",
    help="Indicate a polygon in which areas will be activated. Must be in WKT format (SRID 4326)",
)
@click.option(
    "--out-polygon",
    "-o",
    help="Indicate a polygon in which areas will be kept. Must be in WKT format (SRID 4326)",
)
@with_appcontext
def activate(**kwargs):
    click.echo("RefGeo : activating areas...")
    change_area_activation_status(compute_where_clause(**kwargs), True)


@ref_geo.command(help="Delete geographical data")
@click.option("--area-code", "-a", multiple=True, help="Areas' code to delete")
@click.option("--area-name", "-n", multiple=True, help="Areas' name to delete")
@click.option("--area-type-code", "-t", multiple=True, help="Areas' type to delete")
@click.option(
    "--in-polygon",
    "-i",
    help="Indicate a polygon in which areas will be deleted. Must be in WKT format (SRID 4326)",
)
@click.option(
    "--out-polygon",
    "-o",
    help="Indicate a polygon in which areas will be kept. Must be in WKT format (SRID 4326)",
)
@with_appcontext
def delete(**kwargs):

    rowcount = db.session.execute(
        sa.delete(LAreas)
        .where(compute_where_clause(**kwargs))
        .execution_options(synchronize_session=False)
    ).rowcount
    click.confirm(f"{rowcount} areas have been deleted, commit?", abort=True)
    db.session.commit()


@ref_geo.group(name="import", help="Import geographical data")
def ref_geo_import():
    pass


GRIDS = {
    "m1": {
        "filename": "inpn_grids_1.csv.xz",
        "temp_table_name": "temp_grids_1",
        "area_type": "M1",
        "versions": ["2020"],
    },
    "m2": {
        "filename": "inpn_grids_2.csv.xz",
        "temp_table_name": "temp_grids_2",
        "area_type": "M2",
        "versions": ["2024"],
    },
    "m5": {
        "filename": "inpn_grids_5.csv.xz",
        "temp_table_name": "temp_grids_5",
        "area_type": "M5",
        "versions": ["2020"],
    },
    "m10": {
        "filename": "inpn_grids_10.csv.xz",
        "temp_table_name": "temp_grids_10",
        "area_type": "M10",
        "versions": ["2020"],
    },
    "m20": {
        "filename": "inpn_grids_20.csv.xz",
        "temp_table_name": "temp_grids_20",
        "area_type": "M20",
        "versions": ["2024"],
    },
    "m50": {
        "filename": "inpn_grids_50.csv.xz",
        "temp_table_name": "temp_grids_50",
        "area_type": "M50",
        "versions": ["2024"],
    },
}


@ref_geo_import.command()
@click.option(
    "--kind",
    type=click.Choice(["m1", "m2", "m5", "m10", "m20", "m50"], case_sensitive=False),
    required=True,
)
@click.option("--version")
@click.option("--enable/--disable", default=True)
@click.option("--base-url", default=f"{BASE_URL}inpn/layers/")
@with_appcontext
def inpn_grids(kind, version, enable, base_url):
    schema = "ref_geo"
    kind = SimpleNamespace(**GRIDS[kind])
    if version is None:
        version = sorted(kind.versions)[-1]
        click.echo(f"Selecting version '{version}'")
    if version not in kind.versions:
        raise click.BadParameter(
            f"This referential exists only in following versions: {kind.versions}"
        )
    base_url = f"{base_url}{version}/"

    grids_count = db.session.execute(
        sa.select(sa.func.count(LAreas.id_area)).where(
            LAreas.area_type.has(BibAreasTypes.type_code == kind.area_type)
        )
    ).scalar()
    if grids_count:
        click.confirm(
            f"There are already {grids_count} existing grids, are you sure you want to continue?",
            abort=True,
        )

    click.echo("Create temporary grids table…")
    create_temporary_grids_table(db.session, schema, kind.temp_table_name)
    cursor = db.session.connection().connection.cursor()
    with open_remote_file(base_url, kind.filename) as geofile:
        click.echo("Inserting grids data in temporary table…")
        cursor.copy_expert(f"COPY {schema}.{kind.temp_table_name} FROM STDIN", geofile)
    click.echo("Copy grids in l_areas…")
    insert_areas_from_temporary_table(
        db.session, schema, kind.temp_table_name, kind.area_type, enable
    )
    insert_grids_from_temporary_table(db.session, schema, kind.temp_table_name)
    click.echo("Dropping temporary grids table…")
    db.session.execute(f"DROP TABLE {schema}.{kind.temp_table_name}")
    click.echo("Committing…")
    db.session.commit()


@ref_geo_import.command()
@click.option("--version", default="2026-05")
@click.option("--enable/--disable", default=True)
@click.option("--base-url", default=f"{BASE_URL}ign/")
@with_appcontext
def fr_epci(version, enable, base_url):
    schema = "ref_geo"
    filename = f"epci_fr_{version}.csv.xz"
    temp_table_name = "temp_fr_epci"
    click.echo("Ensure EPCI type exists in bib_areas_types…")
    epci_type = db.session.execute(
        select(BibAreasTypes).where(BibAreasTypes.type_code == "EPCI")
    ).scalar_one_or_none()
    if not epci_type:
        with db.session.begin_nested():
            epci_type = BibAreasTypes(
                type_code="EPCI",
                type_name="EPCI",
                type_desc="Établissement public de coopération intercommunale",
                size_hierarchy=25000,
            )
            db.session.add(epci_type)
        click.echo(f"EPCI type created (id_type={epci_type.id_type})")

    epci_count = db.session.execute(
        sa.select(sa.func.count(LAreas.id_area)).where(LAreas.id_type == epci_type.id_type)
    ).scalar()
    if epci_count:
        click.confirm(
            f"There are already {epci_count} existing EPCI, are you sure you want to continue?",
            abort=True,
        )

    click.echo("Update EPCI type referential name & version")
    with db.session.begin_nested():
        epci_type.ref_name = "IGN admin_express"
        epci_type.num_version = version

    click.echo("Create temporary EPCI table…")
    db.session.execute(f"""
        CREATE TABLE {schema}.{temp_table_name} (
            WKT public.geometry(MultiPolygon,4326),
            fid integer NOT NULL,
            cleabs text,
            nom_officiel text,
            nom_officiel_en_majuscules text,
            nature text,
            codes_insee_des_communes_membres text,
            codes_insee_des_departements_membres text,
            code_siren text
        )
    """)
    db.session.execute(f"""
        ALTER TABLE ONLY {schema}.{temp_table_name}
            ADD CONSTRAINT {temp_table_name}_pkey PRIMARY KEY (fid)
    """)
    with open_remote_file(base_url, filename) as csvfile:
        click.echo("Inserting EPCI data in temporary table…")
        db.session.connection().connection.cursor().copy_expert(
            f"COPY {schema}.{temp_table_name} FROM STDIN DELIMITER ',' CSV HEADER", csvfile
        )
    click.echo(f"Insert EPCI in l_areas…")
    rowcount = db.session.execute(f"""
        INSERT INTO {schema}.l_areas (id_type, area_code, area_name, geom, geom_4326, enable)
        SELECT
            {epci_type.id_type},
            code_siren,
            nom_officiel,
            ST_Transform(WKT, Find_SRID('{schema}', 'l_areas', 'geom')),
            ST_Transform(WKT, 4326),
            {str(enable).upper()}
        FROM {schema}.{temp_table_name}
    """).rowcount
    click.echo("Re-indexing…")
    # TODO: may be use codes_insee_des_communes_membres & codes_insee_des_departements_membres to populate cor_areas
    db.session.execute(f"REINDEX INDEX {schema}.index_l_areas_geom")
    click.echo("Dropping temporary EPCI table…")
    db.session.execute(f"DROP TABLE {schema}.{temp_table_name}")
    click.echo("Committing…")
    db.session.commit()


@ref_geo_import.command()
@click.option("--url", default="https://data.geopf.fr/wfs/", help="The URL of the WFS API.")
@click.option(
    "--layer",
    "layer_id",
    help="Request the following layer from the WFS API. List available layers if not specified.",
)
@click.option(
    "--srid",
    type=int,
    help="Request the following SRID from the WFS API. List supported SRID by the server if not specified.",
)
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        path_type=pathlib.Path,
    ),
    help="Save the SHAPE-ZIP file to this directory. Re-use existing file from this directory if any.",
)
@click.option("--type-code", required=True)
@click.option("--type-name")
@click.option("--type-desc")
@click.option("--type-size-hierarchy", type=int)
@click.option(
    "--map",
    "mappings",
    type=str,
    multiple=True,
    help="Mapping propriété -> champ LAreas, ex: --map area_name=nom --map area_code=id",
)
@click.option(
    "--additional-data",
    "additional_data_fields",
    type=str,
    default="",
    help="Colonnes sources à stocker dans additional_data (JSONB), séparées par des virgules, ex: --additional-data surface,population",
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="Afficher les données sans les importer."
)
@click.option(
    "--verbose", is_flag=True, default=False, help="Afficher chaque feature qui va être importée."
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Désactiver les confirmations interactives.",
)
@with_appcontext
def wfs(
    url,
    layer_id,
    srid,
    type_code,
    type_name,
    type_desc,
    type_size_hierarchy,
    data_dir: pathlib.Path,
    mappings=(),
    additional_data_fields="",
    dry_run=False,
    verbose=False,
    non_interactive=False,
):
    # Fetching (or creating) the area type
    area_type = db.session.execute(
        select(BibAreasTypes).where(BibAreasTypes.type_code == type_code)
    ).scalar_one_or_none()
    if area_type is None:  # Création du type de zonage
        click.confirm("Le type de zonage n’existe pas, le créer ?", abort=True)
        while not type_name:
            type_name = click.prompt("Nom du type (requis) ")
        if not type_desc:
            type_desc = click.prompt("Description (optionel) ")
        if not type_size_hierarchy:
            type_size_hierarchy = int(click.prompt("Taille moyenne du rayon en km (optionel) "))
        with db.session.begin_nested():
            area_type = BibAreasTypes(
                type_code=type_code, type_name=type_name, type_desc=type_desc
            )
            db.session.add(area_type)
    else:  # Utilisation d’un type existant, vérification de la cohérence
        if (
            type_name
            and area_type.type_name != type_name
            and click.confirm(
                f"Le type de zonage existe mais utilise un autre nom ({area_type.type_name}), le mettre à jour ?"
            )
        ):
            area_type.type_name = type_name
        if (
            type_desc
            and area_type.type_desc != type_desc
            and click.confirm(
                f"Le type de zonage existe mais utilise une autre description ({area_type.type_desc}), la mettre à jour ?"
            )
        ):
            area_type.type_desc = type_name
        # TODO: mettre à jour ref_name / ref_version / num_version
        existing_count = db.session.execute(
            select(sa.func.count()).select_from(LAreas).where(LAreas.id_type == area_type.id_type)
        ).scalar()
        if existing_count:
            if non_interactive:
                raise click.ClickException(
                    f"Il y a déjà {existing_count} zonage(s) pour ce type ({type_code})."
                )
            click.confirm(
                f"Il y a déjà {existing_count} zonage(s) pour ce type ({type_code}). Continuer l’import ?",
                abort=True,
            )

    # Fetching the SHAPE-ZIP from the WFS API
    with ExitStack() as stack:
        if not data_dir and "DATA_DIRECTORY" in os.environ:
            data_dir = pathlib.Path(os.environ.get("DATA_DIRECTORY"))
        if not data_dir:
            data_dir = pathlib.Path(stack.enter_context(TemporaryDirectory()))
        data_dir.mkdir(exist_ok=True)
        # Be sure to reuse a file only if downloaded with same parameters.
        hash = "{:08x}".format(adler32(f"{url}-{layer_id}-{srid}".encode()))
        file_path = data_dir / f"{layer_id}-{hash}.shp.zip"
        if not file_path.is_file():
            wfs = WebFeatureService_2_0_0(url, version="2.0.0")
            click.echo("Service WFS :")
            click.echo(f"\tTitre : {wfs.identification.title}")
            if wfs.version != "2.0.0":
                raise click.ClickException(f"Version 2.0.0 attendue, obtenue : {wfs.version}")
            if (getfeature := wfs.getOperationByName("GetFeature")) is None:
                raise click.ClickException("Opération GetFeature non supportée.")
            if "SHAPE-ZIP" not in getfeature.parameters["outputFormat"]["values"]:
                raise click.ClickException("Format SHAPE-ZIP non supportée.")
            if not layer_id:
                click.echo("Voici la liste des couches disponibles :")
                fmt = "{:80s} | {:s}"
                click.echo(fmt.format("Titre", "Code"))
                for key, value in wfs.contents.items():
                    click.echo(fmt.format(value.title, key))
                layer_id = click.prompt("Choix de la couche")
            try:
                layer = wfs.contents[layer_id]
            except KeyError:
                raise click.ClickException(
                    f"La couche '{layer_id}' n’a pas été trouvé dans le flux."
                )
            click.echo("Couche :")
            click.echo(f"\tID : {layer.id}")
            click.echo(f"\tTitre : {layer.title}")
            click.echo(f"\tDescription : {layer.abstract}")
            schema = wfs.get_schema(layer.id)
            click.echo("\tSchéma :")
            for prop, proptype in schema["properties"].items():
                click.echo(f"\t\t{prop:16s} ({proptype})")
            if not srid:
                click.echo("\tSRS :")
                for srs in layer.crsOptions:
                    click.echo(f"\t\t{srs}")
                srid = click.prompt("Choix du SRID", type=int)
            srs = f"urn:ogc:def:crs:EPSG::{srid}"
            if srs not in layer.crsOptions:
                click.ClickException(f"Le SRS spécifié n’est pas supporté par le serveur")
            click.echo(f"\tSRS : {srs}")
            click.echo(f"Téléchargement de la couche dans {file_path}")
            response = wfs.getfeature(typename=[layer_id], outputFormat="SHAPE-ZIP", srsname=srs)
            with open(file_path, "wb") as f:
                f.write(response.read())
        else:
            click.echo(f"Réutilisation du fichier existant {file_path}")
        shp = stack.enter_context(fiona.open(file_path))

        click.echo("Propriétés du shapefile :")
        for prop, proptype in shp.schema["properties"].items():
            click.echo(f"\t\t{prop:16s} ({proptype})")

        field_mapping = {}
        for m in mappings:
            dest, _, source = m.partition("=")
            dest, source = dest.strip(), source.strip()
            if not dest or not source:
                raise click.ClickException(
                    f"Correspondance invalide : {m}. Format attendue : destination=source"
                )
            if source not in shp.schema["properties"]:
                raise click.ClickException(
                    f"Le champs source {source} n'est pas présent dans le shapefile."
                )
            if dest not in LAreas.__table__.columns:
                raise click.ClickException(
                    f"La destination {dest} n'est pas une colonne de LAreas."
                )
            field_mapping[dest] = source

        additional_data_fields = [
            f.strip() for f in additional_data_fields.split(",") if f.strip()
        ]
        for field in additional_data_fields:
            if field not in shp.schema["properties"]:
                raise click.ClickException(
                    f"Le champ supplémentaire {field} n'est pas présent dans le shapefile."
                )

        click.echo("Correspondance de champs :")
        for k, v in field_mapping.items():
            click.echo(f"\t{k:16s} <- {v:s}")
        click.echo("Champs additionnels :")
        for field in additional_data_fields:
            click.echo(f"\t{field}")

        warn_fields = {"area_name", "area_code", "description"}
        missing = warn_fields - set(field_mapping.keys())
        if missing and not non_interactive:
            click.confirm(
                f"Ces champs n'ont pas de correspondance : {', '.join(sorted(missing))}. "
                "Continuer l'import ?",
                abort=True,
            )

        if verbose:
            for feature in shp:
                click.echo(pprint.pformat(dict(feature["properties"])))

        if not non_interactive:
            click.confirm(f"{len(shp)} zonages vont être importés, continuer ?", abort=True)
        local_srid = get_local_srid(db.session)
        for feature in shp:
            properties = feature["properties"]
            area_kwargs = {
                dest: feature["properties"][source]
                for dest, source in field_mapping.items()
                if source in properties
            }
            additional_data = {
                field: feature["properties"][field]
                for field in additional_data_fields
                if field in properties
            }
            area = LAreas(
                id_type=area_type.id_type,
                additional_data=additional_data or None,
                **area_kwargs,
            )
            geom_wkb = from_shape(shape(feature["geometry"]), srid=shp.crs.to_epsg())
            if srid == 4326:
                area.geom_4326 = geom_wkb
                # geom computed through trigger
            elif srid == local_srid:
                area.geom = geom_wkb
                # geom_4326 computed through trigger
            else:
                area.geom = func.ST_Transform(geom_wkb, local_srid)
                area.geom_4326 = func.ST_Transform(geom_wkb, 4326)
            db.session.add(area)
            if verbose:
                click.echo(area.as_dict())

    if not dry_run:
        db.session.commit()


@ref_geo_import.command()
@click.option(
    "--data-dir",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        path_type=pathlib.Path,
    ),
    help="Save the SHAPE-ZIP file to this directory. Re-use existing file from this directory if any.",
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="Afficher les données sans les importer."
)
@click.option(
    "--verbose", is_flag=True, default=False, help="Afficher chaque feature qui va être importée."
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Désactiver les confirmations interactives.",
)
@click.pass_context
@with_appcontext
def fr_pnr(ctx, **kwargs):
    ctx.invoke(
        wfs,
        url="https://data.geopf.fr/wfs/",
        layer_id="patrinat_pnr:pnr",
        srid=2154,
        type_code="PNR",
        mappings=["area_code=id_mnhn", "area_name=nom_cite"],
        additional_data_fields="gest_site,operateur,territoire,area_sig,cd_sig,marin,src_geom,date_crea,p1_nature,p4_geologi",
        **kwargs,
    )
