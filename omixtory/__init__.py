# -*- coding: utf-8 -*-

from . import controllers
from . import models


def post_init_hook(cr, registry):
    cr.execute("""
        CREATE OR REPLACE FUNCTION delete_config() RETURNS trigger AS $$
                DECLARE vmodel text;
                        vid integer;
                        vtabl text;
                BEGIN
                        vmodel = split_part(OLD.config, ',', 1);
                        vid = split_part(OLD.config, ',', 2);
                        IF vmodel NOT LIKE 'omixtory.config.%' THEN
                            RAISE EXCEPTION 'Wrong config reference!';
                        END IF;
                        select tabl into vtabl from omixtory_host_template where model = vmodel;
                        IF vtabl IS NOT NULL THEN
                            EXECUTE format('DELETE FROM %I WHERE id = %L', vtabl, vid);
                        END IF;
                        RETURN OLD;
                END;
        $$ LANGUAGE plpgsql;
        DROP TRIGGER IF EXISTS delete_config on omixtory_host;
        CREATE TRIGGER delete_config
            BEFORE DELETE ON omixtory_host
            FOR EACH ROW
            WHEN (OLD.config IS NOT NULL)
            EXECUTE PROCEDURE delete_config();
    """)


def uninstall_hook(cr, registry):
    cr.execute("""
        DROP TRIGGER IF EXISTS delete_config on omixtory_host;
        DROP FUNCTION delete_config();
    """)
