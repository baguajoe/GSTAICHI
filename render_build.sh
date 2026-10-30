#!/usr/bin/env bash
# Render build for the API (gstaichi-api). The website itself is built separately and uploaded to HostGator,
# so there is no npm/webpack step here.
# exit on error
set -o errexit

# Install exactly the versions in Pipfile.lock into Render's Python, so gunicorn and flask run without pipenv
pip install --upgrade pip
pip install pipenv==2023.6.2
pipenv requirements > /tmp/requirements.lock.txt
pip install -r /tmp/requirements.lock.txt

# The database is brought up to date by preDeployCommand in render.yaml (the database isn't reachable during builds)
