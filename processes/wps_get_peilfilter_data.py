# -*- coding: utf-8 -*-
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
 
# test and production requests
# http://localhost:5000/wps?service=WPS&request=Execute&version=2.0.0&identifier=wps_get_peilfilter_data&datainputs=peilfilterid=HEG_02_W2404_01_GW;parameter=Grondwaterstand;start_date=2025-01-01T00%3A00%3A00Z;end_date=2026-01-01T00%3A00%3A00Z
# https://nl2120.openearth.nl/wps?service=wps&request=Execute&version=2.0.0&identifier=wps_get_peilfilter_data&datainputs=peilfilterid=HEG_02_W2404_01_GW;parameter=Grondwaterstand;start_date=2025-01-01T00%3A00%3A00Z;end_date=2026-01-01T00%3A00%3A00Z
 

from pywps import Process, LiteralInput, ComplexOutput, Format
from .utils import get_data
import logging
logger = logging.getLogger("PYWPS")

class WpsGetPeilfilterData(Process):
    def __init__(self):
        inputs = [
            LiteralInput(
                identifier='peilfilterid',
                title='Peilfilter ID',
                abstract='String or number identifying the peilfilter. Can repeat.',
                data_type='string',
                keywords=['peilfilter', 'groundwater', 'timeseries']
            ),
            LiteralInput(
                identifier='start_date',
                title='Start date (ISO 8601 or empty)',
                abstract='ISO 8601 (e.g., 2025-01-01 or 2025-01-01T00:00:00). Empty string means open start.',
                data_type='string',
            ),
            LiteralInput(
                identifier='end_date',
                title='End date (ISO 8601 or empty)',
                abstract='ISO 8601 (e.g., 2026-01-01 or 2026-01-01T00:00:00). Empty string means open end.',
                data_type='string',
            ),
            LiteralInput(
                identifier='parameter',
                title='Parameter',
                abstract='Groundwater parameter (e.g., "Grondwaterstand").',
                data_type='string',
                keywords=['parameter', 'groundwater']
            )
        ]

        outputs = [
            ComplexOutput(
                identifier='peilfilter_data',
                title='Result JSON',
                supported_formats=[Format('application/json')]
            )
        ]

        super(WpsGetPeilfilterData, self).__init__(
            self._handler,
            identifier='wps_get_peilfilter_data',
            version='1.0.0',
            title='Groundwater timeseries',
            abstract='Returns raw timeseries for peilfilters within a date range',
            inputs=inputs,
            outputs=outputs
        )

    def _handler(self, request, response):
        try:
            # Collect possibly multiple peilfilter IDs
            peilfilterids = [item.data for item in request.inputs.get('peilfilterid', [])]

            # Dates as strings (may be empty)
            start_date_str = request.inputs.get('start_date', [None])[0].data if 'start_date' in request.inputs else ''
            end_date_str   = request.inputs.get('end_date',   [None])[0].data if 'end_date'   in request.inputs else ''
            parameter      = request.inputs.get('parameter',  [None])[0].data

            # You can parse/validate ISO-8601 here if you want
            # and turn empty strings into None.
            start_date = parse_iso8601_or_none(start_date_str)
            end_date   = parse_iso8601_or_none(end_date_str)

            # ... call your database function/query using start_dt/end_dt (or None)
            response.outputs["peilfilter_data"].data = get_data(peilfilterids[0],start_date,end_date,parameter)
        except Exception as e:
            res = { 'errMsg' : 'ERROR: {}'.format(e)}
            logger.info(res)
            response.outputs["peilfilter_data"].data = "Something went very wrong, please check logfile"
        return response


# Helpers
from datetime import datetime, timezone

def parse_iso8601_or_none(val: str):
    if not val:
        return None
    # Handle common ISO-8601 formats; tolerate trailing 'Z'
    s = val.strip().replace('Z', '+00:00')
    try:
        dt = datetime.fromisoformat(s)
        # If naive, assume local or set UTC depending on your policy:
        if dt.tzinfo is None:
            # Option: treat as UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        # You may raise a ProcessError here to fail fast with a nice message
        return None