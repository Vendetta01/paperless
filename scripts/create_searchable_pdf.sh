#!/usr/bin/env bash
sudo chmod 777 ${1} && \
/usr/bin/create_searchable_pdf.py -i ${1}

