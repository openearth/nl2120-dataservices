#  Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2025 Deltares for Project A27.
#   Main contributors: 
#   Ioanna Micha (ioanna.micha@deltares.nl)
#   Gerrit Hendriksen (Gerrit Hendriksen@deltares.nl)
#
#   This library is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this library.  If not, see <http://www.gnu.org/licenses/>.
#   --------------------------------------------------------------------
#
# This tool is part of <a href="http://www.OpenEarth.eu">OpenEarthTools</a>.
# OpenEarthTools is an online collaboration to share and manage data and
# programming tools in an open source, version controlled environment.
# Sign up to recieve regular updates of this function, and to contribute
# your own tools.

import configparser
import time
from datetime import datetime
from functools import lru_cache
import json
import re
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy import create_engine
service_path = Path(__file__).resolve().parents[1]
import logging
logger = logging.getLogger("PYWPS")

def read_config(file_name="configuration.txt"):
    """Reads the configuration file
    Returns:
        configuration object
    """
    cf_file = service_path / file_name
    cf = configparser.RawConfigParser()
    cf.read(cf_file)
    logger.info("TESTING CONFIGURATION") 
    
    return cf

@lru_cache(maxsize=1)
def create_connection_db():
    """Creates a connection to the database
    Returns:
        connection object
    """
    cf = read_config()
    print(cf)
    user = cf.get("PostGIS", "USER")
    password = cf.get("PostGIS", "PASSWORD")
    host = cf.get("PostGIS", "HOST")
    port = cf.get("PostGIS", "PORT")
    database = cf.get("PostGIS", "DATABASE")
    try:
        engine = create_engine(
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
            pool_size=1,
            max_overflow=0,
            pool_pre_ping=True,
        )
        result = 'connection to database setup succesful'
    except Exception as e:
        engine = None
        result = 'connection not succesful due to '+e
    finally:
        logger.info('connection message', result)
    return engine

def get_parameters():
    """Retrieves the locations from the database
    Returns:
        json of locations
    """
    engine = create_connection_db()
    with engine.connect() as connection:
        #query = select(func.gws.get_locations_geojson())
        query = select(func.timeseries.get_parameters())  # this yields list of locatie_id and peilfilter_id
        result = connection.execute(query).fetchone()[0]
        logger.info('result of the function',result)
    return result

def get_locations(local=False):
    """Retrieves the locations from the database
    Returns:
        json of locations
    """
    engine = create_connection_db()
    with engine.connect() as connection:
        #query = select(func.gws.get_locations_geojson())
        query = select(func.timeseries.gwslocations())  # this yields list of locatie_id and peilfilter_id
        result = connection.execute(query).fetchone()[0]
        logger.info('result of the function',result)
    if local:
        return result
    return json.dumps(result)

def get_data(peilfilterid,start_date,end_date,parameter='Grondwaterstand',graph=False):
    """Retrieves the data for specific peilfilter id
    Inputs:
        peilfilterid: Integer
        start_date  : startdate (text will be formatted to timestamp), can be empty string
        end_date  : enddate (text will be formatted to timestamp), can be empty string
    Returns:
        json with datetime and stages
    """

    strformat = '%Y-%m-%d' 
    if start_date == '':
        start_date = None
    else:
        sd = start_date
    if not start_date:
        start_date = '2025-01-01' # considered as start of the project
        sd = datetime.strptime(start_date, strformat)

    if end_date == '':
        end_date = None
    else:
        ed = end_date
    if not end_date:
        end_date = datetime.now().strftime(strformat)
        ed = datetime.strptime(end_date, strformat)

    

    logger.info('startdate: ', start_date)
    engine = create_connection_db()
    with engine.connect() as connection:
        #query = select(func.gws.get_locations_geojson())
        query = select(func.timeseries.get_location_observations(peilfilterid,parameter,sd,ed))  # this yields list of locatie_id and peilfilter_id
        try:
            result = connection.execute(query).fetchone()[0]
        except Exception:
            result = 'no data found for specified period' 
        finally:
            logger.info('result of the function',result)
    if graph:
        #return json with datetime and stages for graphing
        return result
    return json.dumps(result)

def get_graph(peilfilterid,start_date,end_date,parameter='Grondwaterstand',local=False):
    """Retrieves and stores an interactive graph for a specific peilfilter.
    Inputs:
        peilfilterid: Integer
        start_date  : startdate (text will be formatted to timestamp), can be empty string
        end_date    : enddate (text will be formatted to timestamp), can be empty string
    Returns:
        JSON string containing graph metadata and URL
    """
    # Call function get_data with graph=True to retrieve data for graphing.
    result = get_data(peilfilterid, start_date, end_date, parameter, graph=True)

    if not isinstance(result, dict):
        return json.dumps(
            {
                "status": "error",
                "message": "No data returned for graph generation.",
                "detail": result,
            }
        )

    timeseries = result.get("timeseries", [])
    if not isinstance(timeseries, list):
        timeseries = []

    x_values = []
    y_values = []
    for item in timeseries:
        if not isinstance(item, dict):
            continue
        x_values.append(item.get("datetime"))
        y_values.append(item.get("head"))

    location_props = result.get("locationproperties", {}) or {}
    parameter_props = result.get("parameterproperties", {}) or {}

    graph_dir = service_path / "data" / "graphs"
    graph_dir.mkdir(parents=True, exist_ok=True)

    safe_location = re.sub(r"[^A-Za-z0-9_-]", "_", str(peilfilterid))
    safe_parameter = re.sub(r"[^A-Za-z0-9_-]", "_", str(parameter))
    if local:
        filename = f"{safe_location}_{safe_parameter}.html"
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"{safe_location}_{timestamp}.html"
    filepath = graph_dir / filename

    title = f"Groundwater timeseries - {peilfilterid}"
    unit_description = parameter_props.get("unitdescription") or parameter_props.get("unit") or "-"
    ylabel = f"{parameter_props.get('parameter', parameter)} ({unit_description})"
    x_json = json.dumps(x_values, ensure_ascii=False)
    y_json = json.dumps(y_values, ensure_ascii=False)
    title_json = json.dumps(title, ensure_ascii=False)
    y_label_json = json.dumps(ylabel, ensure_ascii=False)
    unit_description_json = json.dumps(unit_description, ensure_ascii=False)
    location_json = json.dumps(location_props, ensure_ascii=False)
    parameter_json = json.dumps(parameter_props, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{title}</title>
    <script src=\"https://cdn.plot.ly/plotly-2.35.2.min.js\"></script>
    <style>
        :root {{
            --bg: #f4f6f8;
            --card: #ffffff;
            --ink: #0e2a3a;
            --line: #0077b6;
            --grid: rgba(14, 42, 58, 0.12);
        }}
        body {{
            margin: 0;
            padding: 24px;
            background: radial-gradient(circle at 20% 20%, #ffffff 0%, var(--bg) 75%);
            color: var(--ink);
            font-family: \"Segoe UI\", Tahoma, sans-serif;
        }}
        .wrap {{
            max-width: 1100px;
            margin: 0 auto;
            background: var(--card);
            border-radius: 14px;
            box-shadow: 0 8px 30px rgba(14, 42, 58, 0.12);
            padding: 20px;
        }}
        h1 {{
            margin: 0 0 8px 0;
            font-size: 24px;
        }}
        .meta {{
            margin-bottom: 16px;
            color: rgba(14, 42, 58, 0.8);
            font-size: 14px;
        }}
        #chart {{
            width: 100%;
            height: 620px;
        }}
        .note {{
            margin-top: 10px;
            font-size: 13px;
            color: rgba(14, 42, 58, 0.7);
        }}
    </style>
</head>
<body>
    <div class=\"wrap\">
        <h1 id=\"title\"></h1>
        <div class=\"meta\" id=\"meta\"></div>
        <div id=\"chart\"></div>
        <div class=\"note\">Tip: use mouse wheel/drag to zoom and pan, double click to reset.</div>
    </div>

    <script>
        const xValues = {x_json};
        const yValues = {y_json};
        const plotTitle = {title_json};
        const yLabel = {y_label_json};
        const unitDescription = {unit_description_json};
        const locationProps = {location_json};
        const parameterProps = {parameter_json};

        document.getElementById('title').textContent = plotTitle;
        document.getElementById('meta').textContent =
            `Location: ${'{'}locationProps.locationid || '-'{'}'} | Parameter: ${'{'}parameterProps.parameter || '-'{'}'} (${'{'}unitDescription{'}'})`;

        const trace = {{
            x: xValues,
            y: yValues,
            mode: 'lines+markers',
            name: parameterProps.parameter || 'Groundwaterstand',
            line: {{ color: '#0077b6', width: 2 }},
            marker: {{ size: 5, color: '#00a6fb' }},
            hovertemplate: '%{{x}}<br>Head: %{{y:.3f}}<extra></extra>'
        }};

        const layout = {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            margin: {{ l: 70, r: 20, t: 20, b: 60 }},
            xaxis: {{
                title: 'Datetime',
                gridcolor: 'rgba(14, 42, 58, 0.12)',
                zeroline: false
            }},
            yaxis: {{
                title: yLabel,
                gridcolor: 'rgba(14, 42, 58, 0.12)',
                zeroline: false
            }}
        }};

        const config = {{
            responsive: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['select2d', 'lasso2d']
        }};

        Plotly.newPlot('chart', [trace], layout, config);
    </script>
</body>
</html>
"""

    filepath.write_text(html_content, encoding="utf-8")
    graph_url = f"/data/graphs/{filename}"
    return json.dumps(
        {
            "status": "ok",
            "graph_url": graph_url,
            "graph_file": str(filepath),
            "points": len(x_values),
            "locationid": location_props.get("locationid", peilfilterid),
            "parameter": parameter_props.get("parameter", parameter),
            "unit": parameter_props.get("unit", None),
        }
    )

def createstaticgraph():
    """
    Function to create static (daily) graphs that are store under the name
    of the location and can be called from tslink column in the data from the viewer
    Calls get_locations and for each location calles get_graph
    """
    locations = get_locations(local=True) or {}
    features = locations.get("features", []) if isinstance(locations, dict) else []
    paramresult = get_parameters() or {}
    parameters = (
        paramresult.get("parameterproperties", [])
        if isinstance(paramresult, dict)
        else []
    )
    if isinstance(parameters, dict):
        parameters = [parameters]
    elif not isinstance(parameters, list):
        parameters = []

    generated = 0
    failed = 0
    skipped = 0
    for location in features:
        properties = location.get("properties", {}) if isinstance(location, dict) else {}
        location_name = properties.get("name") if isinstance(properties, dict) else None
        if not location_name:
            skipped += 1
            continue

        for parameter_info in parameters:
            parameter_name = (
                parameter_info.get("parameter")
                if isinstance(parameter_info, dict)
                else None
            )
            if not parameter_name:
                skipped += 1
                continue

            try:
                result = get_graph(
                    location_name,
                    start_date="",
                    end_date="",
                    parameter=parameter_name,
                    local=True,
                )
                result_data = json.loads(result) if isinstance(result, str) else result
                if not isinstance(result_data, dict) or result_data.get("status") != "ok":
                    failed += 1
                    logger.error(
                        "Static graph generation failed for %s (%s): %s",
                        location_name,
                        parameter_name,
                        result_data,
                    )
                    continue
                generated += 1
            except Exception:
                failed += 1
                logger.exception(
                    "Static graph generation raised an exception for %s (%s)",
                    location_name,
                    parameter_name,
                )

    return {"generated": generated, "failed": failed, "skipped": skipped}

def test_get_data():
    parameter='Grondwaterstand'
    dcttest={}
    dcttest["t1"] = ['HEG_01_W2404_01_SH',None,None]
    dcttest["t2"] = ['HEG_01_W2404_01_SH','2025-09-12','2025-12-12']
    dcttest["t3"] = ['HEG_01_W2404_01_SH','2026-01-01',None]
    dcttest["t4"] = ['HEG_01_W2404_01_SH',None,'2025-12-12']

    for t in dcttest.keys():
        peilfilterid = dcttest[t][0]
        start_date = dcttest[t][1]
        end_date = dcttest[t][2]
        try:
            result = get_data(peilfilterid,start_date,end_date,parameter)
        except Exception:
            result = 'no data found'
        finally:
            print(t,result)
