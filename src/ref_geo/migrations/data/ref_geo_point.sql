-- tables pour gérer les référentiels géographiques points (PK/PR, ..)


-- table des type de points

CREATE TABLE ref_geo.bib_points_types (
    id_type SERIAL NOT NULL,
    type_name character varying(200) NOT NULL,
    type_code character varying(25) NOT NULL,
    type_desc text,
    ref_name character varying(200),
    ref_version integer,
    num_version character varying(50),
    meta_create_date timestamp without time zone,
    meta_update_date timestamp without time zone,
    CONSTRAINT pk_ref_geo_bib_points_types_id_type PRIMARY KEY (id_type),
    UNIQUE(type_code)
);


-- table des points (PK/PR, ...)

CREATE TABLE ref_geo.l_points (
    id_point SERIAL NOT NULL,
    id_type INTEGER NOT NULL,
    point_name character varying(250) NOT NULL,
    point_code character varying(25) NOT NULL,
    enable BOOLEAN NOT NULL DEFAULT (TRUE),
    geom GEOMETRY(GEOMETRY, :local_srid),
    geojson_4326 VARCHAR,
    source character varying(250),
    additional_data jsonb NULL,
    meta_create_date timestamp without time zone,
    meta_update_date timestamp without time zone,

    UNIQUE (id_type, point_code),

    CONSTRAINT pk_ref_geo_l_points_id_point PRIMARY KEY (id_point),
    CONSTRAINT fk_ref_geo_l_points_id_type FOREIGN KEY (id_type)
        REFERENCES ref_geo.bib_points_types(id_type)
        ON UPDATE CASCADE ON DELETE NO ACTION
);

