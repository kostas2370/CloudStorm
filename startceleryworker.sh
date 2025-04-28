#!/bin/bash

set -o errexit
set -o nounset

rm -f './celerybeat.pid'

celery -A CloudStorm worker -l INFO --pool=solo