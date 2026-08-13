-- various sql's in this sql file

-- create table hegewarrents with links to graphs, these graphs are generated on a daily basis
drop table if exists timeseries.hegewarrents;
create table timeseries.hegewarrents as
select l.geom, l.locationkey, l.name as locationname, 
       p.name as parametername, u.unit, 
	   l.altitude_msl as maaiveldhoogte, 
	   l.tubetop as bovenkant_peilbuis, 
	   l.tubebot as onderkant_peilbuis, 
	   '<a href="https://nl2120.openearth.nl/data/graphs/'||l.name||'_'||replace(p.name,' ','_')||'.html" target="_blank">click for current timeseries</a>' as tslink, 
	   count(*) from timeseries.location l
join timeseries.timeseries ts on ts.locationkey = l.locationkey
join timeseries.parameter p on p.parameterkey = ts.parameterkey
join timeseries.unit u on u.unitkey = p.unitkey
join timeseries.timeseriesvaluesandflags tsv on tsv.timeserieskey = ts.timeserieskey
group by l.locationkey, l.name, l.description, p.name, u.unit,l.tubetop,l.tubebot,tslink
order by l.name;

REASSIGN OWNED BY hendrik_gt to nl2120_owner

-- function to retrieve parameters
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
