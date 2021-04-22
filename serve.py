#!/usr/bin/env python3

from os import environ
from os.path import abspath, dirname, join

venv = join(dirname(abspath(__file__)), 'venv', 'bin', 'activate_this.py')
exec(open(venv).read(), {
    '__file__': venv
})

from cwa_qr_api import app
app.run(debug=True, host='0.0.0.0')
