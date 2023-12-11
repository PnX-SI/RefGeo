import click
from flask.cli import with_appcontext
from sqlalchemy import func, select

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
