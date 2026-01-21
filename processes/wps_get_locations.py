# -*- coding: utf-8 -*-
#  Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2026 Deltares for Project NL2120.
#   Main contributors: 
#   Gerrit Hendriksen (Gerrit Hendriksen@deltares.nl)
#   Ioanna Micha (ioanna.micha@deltares.nl)
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



from pywps import Format
from pywps.app import Process
from pywps.inout.outputs import LiteralOutput
from pywps.app.Common import Metadata
from pywps.inout.outputs import ComplexOutput
from .utils import get_locations
import json

# Process to retrieve A27 locations from the database

#http://localhost:5000/wps?service=WPS&request=Execute&version=1.0.0&identifier=wps_get_locations
#https://nl2120.openearth.nl/wps?service=wps&request=Execute&version=1.0.0&identifier=wps_get_locations
class WpsGetLocations(Process):
    def __init__(self):
        inputs = []
        outputs = [
            ComplexOutput(identifier="locations", title="A27 locations", supported_formats=[Format('application/json')])
        ]

        super(WpsGetLocations, self).__init__(
            self._handler,
            identifier="wps_get_locations",
            version="1.0.0",
            title="Retrieve A27 locations",
            abstract="The process retrieves the A27 locations from the database",
            profile="",
            metadata=[
                Metadata("GetLocations"),
                Metadata("get_locations"),
            ],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False,
        )

    def _handler(self, request, response):
        try:
            response.outputs["locations"].data = get_locations()
        except Exception as e:
            res = { 'errMsg' : 'ERROR: {}'.format(e)}
            response.outputs['output_json'].data = json.dumps(res)	
        return response
