FROM npodewitz/confd:latest


ENV PAPERLESS_CONSUMPTION_DIR /consume
ENV PAPERLESS_EXPORT_DIR /export
ENV GHOSTSCRIPT_APK ghostscript-9.26-r2.apk


##############################
# Install dependencies
COPY requirements.txt /usr/src/paperless/
#COPY aports/main/ghostscript/$GHOSTSCRIPT_APK /tmp/
RUN cd /usr/src/paperless/ && \
    apk add --update --no-cache python3 sudo imagemagick \
      gnupg bash curl poppler unpaper optipng libmagic libpq tiff zlib \
      shadow tesseract-ocr poppler-utils nginx supervisor openssl \
      ghostscript && \
#    apk add --no-cache --allow-untrusted /tmp/$GHOSTSCRIPT_APK && \
#    rm /tmp/$GHOSTSCRIPT_APK /etc/nginx/conf.d/default.conf && \
    rm /etc/nginx/conf.d/default.conf && \
    apk add --update --no-cache --virtual .build-deps python3-dev poppler-dev \
      postgresql-dev build-base musl-dev zlib-dev jpeg-dev openldap-dev && \
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
    mkdir -p /usr/src/paperless/backup/media && \
    mkdir -p /var/www/ && \
    ln -s /usr/src/paperless/src /var/www/paperless && \
    ln -s /usr/src/paperless/static /var/www/paperless/static && \
    ln -s /usr/src/paperless/media /var/www/paperless/media

COPY src/ /usr/src/paperless/src/
COPY data/ /usr/src/paperless/data/
COPY media/ /usr/src/paperless/media/

##############################
# Create consumption and export directory
RUN mkdir -p $PAPERLESS_CONSUMPTION_DIR \
    && mkdir -p $PAPERLESS_EXPORT_DIR


##############################
# Migrate database and collect static files
RUN cd /usr/src/paperless/src && \
      ./manage.py migrate && \
      ./manage.py collectstatic


##############################
# Create user
RUN groupadd -g 1000 paperless && \
    useradd -u 1000 -g paperless -d /usr/src/paperless paperless && \
    chown -Rh paperless:paperless /usr/src/paperless && \
    echo "paperless ALL=(ALL) NOPASSWD: /bin/chmod" >> /etc/sudoers


##############################
# Copy entrypoint, scripts and config
COPY scripts/* /usr/bin/
COPY etc/ /etc/



WORKDIR /usr/src/paperless/src

EXPOSE 80 443

##############################
# Mount volumes
VOLUME ["/usr/src/paperless/data", "/usr/src/paperless/media", "/consume", "/export"]
ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]

