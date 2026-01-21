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
import datetime
import json
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

def create_connection_db():
    """Creates a connection to the database
    Returns:
        connection object
    """
    cf = read_config()
    user = cf.get("PostGIS", "USER")
    password = cf.get("PostGIS", "PASSWORD")
    host = cf.get("PostGIS", "HOST")
    port = cf.get("PostGIS", "PORT")
    database = cf.get("PostGIS", "DATABASE")
    try:
        engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")
        result = 'connection to database setup succesful'
    except Exception as e:
        engine = None
        result = 'connection not succesful due to '+e
    finally:
        logger.info('connection message', result)
    return engine

def get_locations():
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
    return json.dumps(result)


def get_data(peilfilterid,start_date,end_date):
    """Retrieves the data for specific peilfilter id
    Inputs:
        peilfilterid: Integer
        start_date  : startdate (text will be formatted to timestamp), can be empty string
        end_date  : enddate (text will be formatted to timestamp), can be empty string
    Returns:
        json with datetime and stages
    """
    if start_date == '':
        start_date = None
    if end_date == '':
        end_date = None

    logger.info('startdate: ', start_date)
    engine = create_connection_db()
    with engine.connect() as connection:
        #query = select(func.gws.get_locations_geojson())
        query = select(func.gws.get_peilfilter_data_json(peilfilterid,start_date,end_date))  # this yields list of locatie_id and peilfilter_id
        try:
            result = connection.execute(query).fetchone()[0]
        except Exception:
            result = 'no data found for specified period' 
        finally:
            logger.info('result of the function',result)
    return json.dumps(result)


def test_get_data():
    dcttest={}
    dcttest["t1"] = [530,None,None]
    dcttest["t2"] = [530,'2016-09-12T08:00:00','2016-12-12T08:00:00']
    dcttest["t3"] = [530,'2016-09-12T08:00:00',None]
    dcttest["t4"] = [530,None,'2016-12-12T08:00:00']

    for t in dcttest.keys():
        peilfilterid = dcttest[t][0]
        start_date = dcttest[t][1]
        end_date = dcttest[t][2]
        try:
            result = get_data(peilfilterid,start_date,end_date)
        except Exception:
            result = 'no data found'
        finally:
            print(t,result)
