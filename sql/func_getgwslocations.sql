CREATE OR REPLACE FUNCTION timeseries.get_location_observations(
  _location_name   text,
  _parameter_name  text,
  _date_start      timestamptz,
  _date_end        timestamptz
)
RETURNS jsonb
LANGUAGE sql
STABLE
AS $$
  SELECT jsonb_build_object(
    'locationproperties', jsonb_build_object(
      'locationid',   l.name,
      'xcoord',       l.x,
      'ycoord',       l.y,
      'crs',          'EPSG:' || l.epsgcode::text,
      'top_filter',   l.tubetop,
      'bot_filter',   l.tubebot,
      'cable_length', l.cablelength
    ),
    'parameterproperties', jsonb_build_object(
      'parameter', p.name,
      'unit',      u.unit
    ),
    'timeseries', COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'datetime', tsv.datetime,
          'head',     tsv.scalarvalue
        )
        ORDER BY tsv.datetime
      ),
      '[]'::jsonb
    )
  )
  FROM timeseries.location l
  JOIN timeseries.timeseries sk
    ON sk.locationkey = l.locationkey
  JOIN timeseries.parameter p
    ON p.parameterkey = sk.parameterkey
  JOIN timeseries.unit u
    ON u.unitkey = p.unitkey
  LEFT JOIN timeseries.timeseriesvaluesandflags tsv
    ON tsv.timeserieskey = sk.timeserieskey
    AND tsv.datetime >= _date_start
    AND tsv.datetime <= _date_end
  WHERE p.name = _parameter_name
    AND l.name = _location_name
  GROUP BY
    l.name, p.name, l.x, l.y, l.epsgcode, l.tubetop, l.tubebot, l.cablelength, u.unit
  LIMIT 1;
$$;

-- for testing
-- SELECT timeseries.get_location_parameter_data(
--   'HEG_01_W2404_01_SH',
--   'Grondwaterstand',
--   TIMESTAMPTZ '2024-01-01 00:00+01',
--   TIMESTAMPTZ '2025-12-31 23:59:59+01'
-- );