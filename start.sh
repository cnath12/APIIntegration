#!/bin/bash
export FLASK_ENV=production
export FLASK_APP=wsgi.py
gunicorn --config gunicorn.conf.py wsgi:application