FROM alpine:edge
#FROM npodewitz/docker-tesseract:4.0b


ENV PAPERLESS_CONSUMPTION_DIR /consume
ENV PAPERLESS_EXPORT_DIR /export


##############################
# Install dependencies
COPY requirements.txt /usr/src/paperless/
RUN cd /usr/src/paperless/ && \
    apk add --no-cache python3 sudo imagemagick ghostscript gnupg bash curl \
      poppler unpaper optipng libmagic libpq tiff zlib shadow tesseract-ocr && \
    apk add --no-cache --virtual .build-deps python3-dev poppler-dev \
      postgresql-dev build-base musl-dev zlib-dev jpeg-dev && \
    pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apk del .build-deps


##############################
# Create directories and copy application
RUN mkdir -p /usr/src/paperless/src && \
    mkdir -p /usr/src/paperless/data && \
    mkdir -p /usr/src/paperless/media && \
    mkdir -p /usr/src/paperless/scripts && \
    mkdir -p /usr/src/paperless/backup/data && \
    mkdir -p /usr/src/paperless/backup/media
COPY src/ /usr/src/paperless/src/
COPY data/ /usr/src/paperless/data/
COPY media/ /usr/src/paperless/media/
COPY scripts/ /usr/src/paperless/scripts/


##############################
# Create consumption and export directory
RUN mkdir -p $PAPERLESS_CONSUMPTION_DIR \
    && mkdir -p $PAPERLESS_EXPORT_DIR


##############################
# Migrate database
RUN (cd /usr/src/paperless/src && \
  ./manage.py migrate)



##############################
# Create user
RUN groupadd -g 1000 paperless
RUN useradd -u 1000 -g paperless -d /usr/src/paperless paperless
RUN chown -Rh paperless:paperless /usr/src/paperless


##############################
# Setup entrypoint
RUN cp /usr/src/paperless/scripts/docker-entrypoint.sh /sbin/docker-entrypoint.sh && \
    chmod 755 /sbin/docker-entrypoint.sh &&\
    cp /usr/src/paperless/scripts/create_searchable_pdf.py /usr/bin/ && \
    chmod 755 /usr/bin/create_searchable_pdf.py

WORKDIR /usr/src/paperless/src


##############################
# Mount volumes
VOLUME ["/usr/src/paperless/data", "/usr/src/paperless/media", "/consume", "/export"]
ENTRYPOINT ["/sbin/docker-entrypoint.sh"]
CMD ["--help"]

