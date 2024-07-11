import click
from flask.cli import with_appcontext
from sqlalchemy import func, select
import sqlalchemy as sa

from ref_geo.env import db
from ref_geo.models import BibAreasTypes, LAreas


@click.group(help="Manage geographical referential.")
def ref_geo():
    pass


@ref_geo.command()
@with_appcontext
def info():
    click.echo("RefGeo : nombre de zones par type")
    q = (
        select(BibAreasTypes, func.count(LAreas.id_area).label("count"))
        .join(LAreas)
        .group_by(BibAreasTypes.id_type)
        .order_by(BibAreasTypes.id_type)
    )
    for area_type, count in db.session.scalars(q).unique().all():
        click.echo("\t{}: {}".format(area_type.type_name, count))


def change_area_activation_status(
    area_code=None, area_name=None, area_type=None, in_polygon=None, enable=True
):
    """
    Change the activation status of areas in the geographical referential.

    Parameters
    ----------
    area_code : list of str
        List of area codes to activate or deactivate.
    area_name : list of str
        List of area names to activate or deactivate.
    area_type : list of str
        List of area types to activate or deactivate. The type codes are
        checked in the `bib_areas_types` table.
    in_polygon : str
        WKT polygon defined in WGS84 coordinate reference system. The
        areas inside the polygon will be activated or deactivated.
    enable : bool
        If True, the areas will be activated, otherwise they will be
        deactivated.
    """
    str_ = "activated" if enable else "deactivated"
    if area_code:
        click.echo("The following area codes will be {}: {}".format(str_, ", ".join(area_code)))
        q = sa.update(LAreas).where(LAreas.area_code.in_(area_code)).values(enable=enable)
        db.session.execute(q)
    if area_name:
        click.echo("The following area names will be {}: {}".format(str_, ", ".join(area_name)))
        q = sa.update(LAreas).where(LAreas.area_name.in_(area_name)).values(enable=enable)
        db.session.execute(q)
    if area_type:
        click.echo("The following area types will be {}: {}".format(str_, ", ".join(area_type)))
        area_type_ids = db.session.scalars(
            select(BibAreasTypes.id_type).where(BibAreasTypes.type_code.in_(area_type))
        ).all()
        q = sa.update(LAreas).where(LAreas.id_type.in_(area_type_ids)).values(enable=enable)
        db.session.execute(q)
    if in_polygon:
        click.echo(
            "The following areas will be {} in the following polygon: {}".format(str_, in_polygon)
        )
        in_polygon_cte = select(
            LAreas.id_area, func.ST_Intersects(LAreas.geom_4326, func.ST_GeomFromText(in_polygon))
        ).cte("in_polygon")
        q = (
            sa.update(LAreas)
            .where(in_polygon_cte.c.id_area == LAreas.id_area)
            .values(enable=enable)
        )
        db.session.execute(q)
    db.session.commit()


@ref_geo.command()
@click.option("--area-code", "-a", multiple=True, help="Areas' code to deactivate")
@click.option("--area-name", "-n", multiple=True, help="Areas' name to deactivate")
@click.option(
    "--area-type",
    "-t",
    multiple=True,
    help="Area type to deactivate (check `type_code` in `bib_areas_types` table)",
)
@click.option(
    "--in-polygon",
    "-p",
    help="Indicate a polygon in which areas will be deactivated. Must be in WKT format (SRID 4326)",
)
@with_appcontext
def deactivate(area_code, area_name, area_type, in_polygon):
    click.echo("RefGeo : deactivating areas...")
    change_area_activation_status(area_code, area_name, area_type, in_polygon, False)


@ref_geo.command()
@click.option("--area-code", "-a", multiple=True, help="Areas' code to activate")
@click.option("--area-name", "-n", multiple=True, help="Areas' name to activate")
@click.option(
    "--area-type",
    "-t",
    multiple=True,
    help="Area type to activate (check `type_code` in `bib_areas_types` table)",
)
@click.option(
    "--in-polygon",
    "-p",
    help="Indicate a polygon in which areas will be activated. Must be in WKT format (SRID 4326)",
)
@with_appcontext
def activate(area_code, area_name, area_type, in_polygon):
    click.echo("RefGeo : activating areas...")
    change_area_activation_status(area_code, area_name, area_type, in_polygon, True)
