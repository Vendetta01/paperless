FROM alpine:edge



ENV TESSERACT_GIT_COMMIT eba0ae3b88a46a93e981770caa0b148d65cc4468

##############################
# Install necessary software
COPY requirements.txt /usr/src/paperless/

RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories && \
    apk add --no-cache --virtual .build-deps python3-dev build-base git sudo \
      libmagic leptonica-dev libpng-dev libjpeg tiff-dev zlib-dev \
      autoconf autoconf-archive automake libtool pkgconf gnupg file && \
    cd /tmp/ && \
    git clone https://github.com/tesseract-ocr/tesseract.git tesseract-ocr && \
    cd tesseract-ocr && \
    git checkout $TESSERACT_GIT_COMMIT && \
    ./autogen.sh && \
    ./configure --prefix=/usr/ --datadir=/usr/share/tessdata/ && \
    make && \
    make install && \
    cd /usr/share/tessdata/ && \
    mv tessdata/* ./ && \
    rm -rf tessdata && \
    wget https://github.com/tesseract-ocr/tessdata_fast/raw/master/eng.traineddata && \
    wget https://github.com/tesseract-ocr/tessdata_fast/raw/master/osd.traineddata && \
    rm -rf /tmp/tesseract-ocr/ && \
    cd /usr/src/paperless && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apk del .build-deps && \
    apk add --no-cache python3 sudo imagemagick ghostscript gnupg bash rsync sqlite \
      poppler-utils unpaper libmagic leptonica libpng libjpeg tiff zlib



ENV PAPERLESS_CONSUMPTION_DIR /consume
ENV PAPERLESS_EXPORT_DIR /export


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
RUN (cd /usr/src/paperless/src && ./manage.py migrate)


##############################
# Create user
RUN addgroup -g 1000 paperless
RUN adduser -u 1000 -G paperless -h /usr/src/paperless -D paperless
RUN chown -Rh paperless:paperless /usr/src/paperless


##############################
# Setup entrypoint
RUN cp /usr/src/paperless/scripts/docker-entrypoint.sh /sbin/docker-entrypoint.sh && \
    chmod 755 /sbin/docker-entrypoint.sh &&\
    cp /usr/src/paperless/scripts/backup_paperless_data.sh /usr/bin/backup_paperless_data.sh && \
    chmod 755 /usr/bin/backup_paperless_data.sh

WORKDIR /usr/src/paperless/src


##############################
# Mount volumes
VOLUME ["/usr/src/paperless/data", "/usr/src/paperless/media", "/consume", "/export"]

ENTRYPOINT ["/sbin/docker-entrypoint.sh"]
CMD ["--help"]


