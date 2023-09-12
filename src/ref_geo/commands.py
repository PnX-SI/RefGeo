import click
from flask.cli import with_appcontext
from sqlalchemy import func, column

from ref_geo.env import db
from ref_geo.models import BibAreasTypes, LAreas


@click.group(help="Manage geographical referential.")
def ref_geo():
    pass


@ref_geo.command()
@with_appcontext
def info():
    click.echo("[RefGeo]")
    click.echo("Nombre de zones par type :")
    q = (
        db.session.query(BibAreasTypes, func.count(LAreas.id_area).label("count"))
        .join(LAreas)
        .group_by(BibAreasTypes.id_type)
        .order_by(BibAreasTypes.id_type)
    )
    for area_type, count in q.all():
        click.echo("\t{}: {}".format(area_type.type_name, count))
    click.echo("Modèle numérique de terrain :")
    dem_count = db.session.execute("SELECT count(*) FROM ref_geo.dem").scalar()
    click.echo(f"\tRaster : {dem_count} entrées")
    dem_count = db.session.execute("SELECT count(*) FROM ref_geo.dem_vector").scalar()
    click.echo(f"\tVectoriel : {dem_count} entrées")
