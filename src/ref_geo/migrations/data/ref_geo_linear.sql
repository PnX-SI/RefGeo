-- tables pour gérer les référentiels géographiques linéaires (routes, etc..)
-- - ref_geo.bib_linears_types
-- - ref_geo.l_linear


CREATE TABLE ref_geo.bib_linears_types (
    id_type SERIAL NOT NULL,
    type_code VARCHAR NOT NULL,
    type_name VARCHAR NOT NULL,
    type_desc VARCHAR,
    ref_name VARCHAR,
    ref_version VARCHAR,
    num_version VARCHAR,
    meta_create_date timestamp without time zone,
    meta_update_date timestamp without time zone,

    CONSTRAINT pk_ref_geo_bib_linears_types_id_type PRIMARY KEY (id_type),

    UNIQUE(type_code)
);


CREATE TABLE ref_geo.l_linears (
    id_linear SERIAL NOT NULL,
    id_type INTEGER NOT NULL,
    linear_name VARCHAR NOT NULL,
    linear_code VARCHAR NOT NULL,
    enable BOOLEAN,
    geom GEOMETRY(GEOMETRY, :local_srid),
    geojson_4326 VARCHAR,
    source character varying(250),
    additional_data jsonb NULL,
    meta_create_date timestamp without time zone,
    meta_update_date timestamp without time zone,

    UNIQUE (id_type, linear_code),

    CONSTRAINT pk_ref_geo_l_linears_id_linear PRIMARY KEY (id_linear),
    CONSTRAINT fk_ref_geo_l_linears_id_type FOREIGN KEY (id_type)
        REFERENCES ref_geo.bib_linears_types(id_type)
        ON UPDATE CASCADE ON DELETE NO ACTION
);

-- index geom

CREATE INDEX ref_geo_l_linears_geom_idx ON ref_geo.l_linears USING GIST(geom);


-- trigger geom_geojson

DROP TRIGGER IF EXISTS tri_calculate_geojson ON ref_geo.l_areas;
CREATE TRIGGER tri_calculate_geojson
    BEFORE INSERT OR UPDATE OF geom ON ref_geo.l_linears
    FOR EACH ROW
    EXECUTE PROCEDURE ref_geo.fct_tri_calculate_geojson();


-- linear groups

CREATE TABLE ref_geo.t_linear_groups (
    id_group SERIAL NOT NULL,
    id_type INTEGER NOT NULL,
    group_name VARCHAR,
    group_code VARCHAR,
    UNIQUE (group_code),
    CONSTRAINT pk_ref_geo_linear_group_id_group PRIMARY KEY (id_group),
    CONSTRAINT fk_ref_geo_t_linear_groups_id_type FOREIGN KEY (id_type)
        REFERENCES ref_geo.bib_linears_types(id_type)
        ON UPDATE CASCADE ON DELETE NO ACTION
);

-- correlation groupes - linear

CREATE TABLE ref_geo.cor_linear_group (
    id_group INTEGER NOT NULL,
    id_linear INTEGER NOT NULL,
    CONSTRAINT fk_ref_geo_cor_linear_group_id_group FOREIGN KEY (id_group)
        REFERENCES ref_geo.t_linear_groups(id_group)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_ref_geo_cor_linear_group_id_linear FOREIGN KEY (id_linear)
        REFERENCES ref_geo.l_linears(id_linear)
        ON UPDATE CASCADE ON DELETE CASCADE
);