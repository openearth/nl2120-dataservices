create or replace function timeseries.gwslocations () returns setof json as 
$$
SELECT json_build_object(
    'type', 'FeatureCollection', 
    'features', json_agg(
        json_build_object(
            'type',       'Feature',
            'geometry', ST_AsGeoJSON(geom)::json,
            'properties', json_build_object(
                -- list of fields
                'filterid', filterid,
				'filterdepth',filterdepth,
				'name', name,
				'shortname', shortname,
				'description',description,
                'x', x,
                'y', y,
				'z', z,
				'epsgcode',epsgcode,
				'altitude_msl',altitude_msl,
				'tubetop', tubetop,
				'tubebot', tubebot,
				'cablelength',cablelength
            )
        )
    )
)
FROM timeseries.location
$$ language sql

--select * from timeseries.gwslocations();