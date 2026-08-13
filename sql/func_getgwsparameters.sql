CREATE OR REPLACE FUNCTION timeseries.get_parameters()
RETURNS jsonb
LANGUAGE sql
STABLE
AS $$
  SELECT jsonb_build_object(
    'parameterproperties',
    jsonb_agg(
      jsonb_build_object(
        'parameter', p.name,
        'unit', u.unit
      )
    )
  )
  FROM timeseries.parameter p
  JOIN timeseries.unit u ON u.unitkey = p.unitkey;
$$;


-- for testing
-- SELECT timeseries.get_location_parameter_data(
--   'HEG_01_W2404_01_SH',
--   'Grondwaterstand',
--   TIMESTAMPTZ '2024-01-01 00:00+01',
--   TIMESTAMPTZ '2025-12-31 23:59:59+01'
-- );