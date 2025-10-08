create or replace function timeseries.gwsfiltertimeseries (loc_id text,parameter text) 
returns TABLE
    dt datetime,
    values float)
as $$
BEGIN
    SELECT tsv.datetime,tsv.scalarvalue FROM timeseries.timeseriesvaluesandflags tsv
    join timeseries.timeseries ts on ts.timeserieskey = tsv.timeserieskey
    join timeseries."location" l on l.locationkey = ts.locationkey
    join timeseries.parameter p on p.parameterkey = ts.parameterkey
    where p.name = parameter and l.locationkey = loc_id
END
$$ 
language plpgsql