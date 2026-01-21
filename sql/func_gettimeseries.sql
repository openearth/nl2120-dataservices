
CREATE OR REPLACE FUNCTION timeseries.get_location_observations(
  _location_name   text,
  _parameter_desc  text,
  _date_start      timestamp,
  _date_end        timestamp
)
RETURNS jsonb
LANGUAGE sql
STABLE
AS $$
  SELECT jsonb_build_object(
    'locationproperties', jsonb_build_object(
        'locationid', l.name,
        'xcoord',      l.x,
        'ycoord',      l.y,
        'crs',         'EPSG' || l.epsgcode::text,
        'top_filter',  l.tubetop,
        'bot_filter',  l.tubebot,
        'cable_length',l.cablelength
    ),
    'parameterproperties', jsonb_build_object(
        'parameter', p.name,
        'unit',      u.unit
    ),
    'timeseries', (
       SELECT COALESCE(
         jsonb_agg(
           jsonb_build_object(
             'datetime', tsv.datetime,
             'head',     tsv.scalarvalue
           )
           ORDER BY tsv.datetime
         ),
         '[]'::jsonb
       )
       FROM timeseries.timeseriesvaluesandflags AS tsv
       WHERE tsv.timeserieskey = sk.timeserieskey
         AND tsv.datetime >= _date_start
         AND tsv.datetime <  _date_end
    )
  )
  FROM timeseries.location   AS l
  JOIN timeseries.timeseries AS sk ON sk.locationkey   = l.locationkey
  JOIN timeseries.parameter  AS p  ON p.parameterkey   = sk.parameterkey
  JOIN timeseries.unit       AS u  ON u.unitkey        = p.unitkey
  WHERE l.name = _location_name
    AND p.description = _parameter_desc
  LIMIT 1;
$$;

-- # usage
-- SELECT timeseries.get_location_observations(
--   'HEG_01_W2404_01_SH',
--   'Grondwaterstand',
--   TIMESTAMP '2025-01-01',
--   TIMESTAMP '2026-01-01'
-- );
