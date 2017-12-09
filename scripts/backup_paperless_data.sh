#!/bin/bash
set -e


PAPERLESS_BASE="/usr/src/paperless"


############################
# sqlite backup
sqlite3 ${PAPERLESS_BASE}/data/db.sqlite3 ".backup '${PAPERLESS_BASE}/backup/data/db.sqlite3'"


############################
# documents backup
rsync -a ${PAPERLESS_BASE}/media/ ${PAPERLESS_BASE}/backup/media


