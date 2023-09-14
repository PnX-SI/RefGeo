-- cor_areas
-- - table de correspondance entre un groupe de zonage et ses éléments
--     par exemple une régions et ses départements ou ses communes.

CREATE TABLE ref_geo.cor_areas (
    id_area_group integer,
    id_area integer
);

COMMENT ON TABLE ref_geo.cor_areas IS 'Table de correspondance des intersections des zonages. Non remplie par défaut.';

ALTER TABLE ref_geo.cor_areas
    ADD CONSTRAINT fk_ref_geo_cor_areas_id_area_group FOREIGN KEY (id_area_group)
    REFERENCES ref_geo.l_areas(id_area)
    ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ref_geo.cor_areas
    ADD CONSTRAINT fk_ref_geo_cor_areas_id_area FOREIGN KEY (id_area)
    REFERENCES ref_geo.l_areas(id_area)
    ON UPDATE CASCADE ON DELETE CASCADE;

CREATE INDEX ref_geo_cor_areas_id_area ON ref_geo.cor_areas USING btree(id_area);
CREATE INDEX ref_geo_cor_areas_id_area_group ON ref_geo.cor_areas USING btree(id_area_group);


-- cor_linear_area
-- - Table de correspondance entre les éléments lineaires et les éléments de zonage
--     par exemple pour trouver rapidement les routes d'une communes
--     ou inversement les communes traversée par un linéaire


CREATE TABLE ref_geo.cor_linear_area (
    id_linear integer,
    id_area integer
);

COMMENT ON TABLE ref_geo.cor_areas IS 'Table de correspondance entre les éléments lineaires et les éléments de zonage. Non remplie par défaut';


ALTER TABLE ref_geo.cor_linear_area
    ADD CONSTRAINT fk_ref_geo_cor_linear_id_area_group FOREIGN KEY (id_area)
    REFERENCES ref_geo.l_areas(id_area)
    ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ref_geo.cor_linear_area
    ADD CONSTRAINT fk_ref_geo_cor_linear_id_lineair_group FOREIGN KEY (id_linear)
    REFERENCES ref_geo.l_linears(id_linear)
    ON UPDATE CASCADE ON DELETE CASCADE;

CREATE INDEX ref_geo_cor_linear_area_id_area ON ref_geo.cor_linear_area USING btree(id_area);
CREATE INDEX ref_geo_cor_linear_area_id_linear ON ref_geo.cor_linear_area USING btree(id_linear);
