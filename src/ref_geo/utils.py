'''

'''


def get_local_srid(db_engine):
    return (
        db_engine
        .execute("SELECT FIND_SRID('ref_geo', 'l_areas', 'geom')")
        .fetchone()[0]
    )
