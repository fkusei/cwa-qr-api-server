import logging
import re
from datetime import datetime, timedelta, timezone
from io import BytesIO
from os import getpid
from os.path import abspath, dirname
from uuid import uuid4

from flask import Flask, request, Response

import cwa


PROJECT_ROOT = dirname(dirname(abspath(__file__)))
FLASK_ROOT = dirname(abspath(__file__))

app = Flask(__name__)
app.secret_key = str(uuid4())

if not app.debug:
    log = logging.StreamHandler()
    log.setLevel(logging.INFO)
    app.logger.addHandler(log)


@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width,initial-scale=1.0">
        <title>Corona-Warn-App QR-Code-Generator</title>
    </head>
    <body>
        <form action="/generate" method="post">
            <fieldset>
                <legend>QR Code</legend>

                <label for="description">Location Description</label>
                <input type="text" name="description" id="description" required><br>

                <label for="address">Location Address</label>
                <input type="text" name="address" id="address" required><br>

                <label for="checkin_length_minutes">Default Check-In-Length (in Minutes)</label>
                <input type="number" name="checkin_length_minutes" id="checkin_length_minutes" value="240"><br>

                <label for="location_type">Location Type</label>
                <select name="location_type" id="location_type">
                    <option value="0" selected>UNSPECIFIED</option>
                    <option value="1">PERMANENT_OTHER</option>
                    <option value="2">TEMPORARY_OTHER</option>
                    <option value="3">RETAIL</option>
                    <option value="4">FOOD_SERVICE</option>
                    <option value="5">CRAFT</option>
                    <option value="6">WORKPLACE</option>
                    <option value="7">EDUCATIONAL_INSTITUTION</option>
                    <option value="8">PUBLIC_BUILDING</option>
                    <option value="9">CULTURAL_EVENT</option>
                    <option value="10">CLUB_ACTIVITY</option>
                    <option value="11">PRIVATE_EVENT</option>
                    <option value="12">WORSHIP_SERVICE</option>
                </select><br>

                <input type="submit" value="generate a qr code">
            </fieldset>
        </form>
        <p>Or use JSON:</p>
        <pre>
{
    "description": "Your Location", # required
    'address": "Somewhere", # required
    "start_utc": 2342, # Timestamp (UTC), start of event, default now
    "end_utc": 4223, # Timestamp (UTC), end of event, default now+1day
    "location_type": 0, # Location Type, default unspecified
    "checkin_length_minutes": 180 # Default Check-In Length, default 4h
}
        </pre>
        <p>For help about valid location Types, consult <a href="https://github.com/corona-warn-app/cwa-documentation/blob/c0e2829/event_registration.md#qr-code-structure">the Documentation about QR Codes on Github</a></p>
    </body>
</html>'''


@app.route('/generate', methods=['POST'])
def generate_qr_code():
    if request.is_json:
        req_data = request.json
    else:
        req_data = request.form.to_dict()

    start_utc = int(req_data.get('start_utc', datetime.now(timezone.utc).timestamp()))
    end_utc = int(req_data.get('end_utc', (datetime.now(timezone.utc) + timedelta(days=1))).timestamp())

    eventDescription = cwa.CwaEventDescription()
    eventDescription.locationDescription = str(req_data['description'])
    eventDescription.locationAddress = str(req_data['address'])
    eventDescription.startDateTime = datetime.fromtimestamp(start_utc)
    eventDescription.endDateTime = datetime.fromtimestamp(end_utc)
    eventDescription.locationType = int(req_data.get('location_type', cwa.lowlevel.LOCATION_TYPE_UNSPECIFIED))
    eventDescription.defaultCheckInLengthInMinutes = int(req_data.get('checkin_length_minutes', 4*60))

    if not eventDescription.locationDescription or not eventDescription.locationAddress:
        return 'missing required data', 400

    qr = cwa.generateQrCode(eventDescription)
    img = qr.make_image(fill_color='black', back_color='white')

    output = BytesIO()
    target_size = req_data.get('qr_size', 1000)
    if target_size:
        scaled = img.resize((int(target_size), int(target_size)))
        scaled.save(output, format='png')
    else:
        img.save(output, format='png')

    return Response(output.getvalue(), mimetype='image/png')
