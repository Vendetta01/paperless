FROM ubuntu:17.10


##############################
# Install necessary software
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential python3.6 \
      python3.6-dev python3-pip python3-venv python3-setuptools git wget sudo \
      imagemagick ghostscript poppler-utils software-properties-common unpaper \
      libmagic-dev libleptonica-dev g++ autoconf automake libtool pkg-config \
      autoconf-archive libpng-dev libjpeg8-dev libtiff5-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*


##############################
# Install tessetact4 from git
ENV TESSERACT_GIT_COMMIT eba0ae3b88a46a93e981770caa0b148d65cc4468
RUN cd /tmp/ && \
    git clone https://github.com/tesseract-ocr/tesseract.git tesseract-ocr && \
    cd tesseract-ocr && \
    git checkout $TESSERACT_GIT_COMMIT && \
    ./autogen.sh && \
    ./configure --prefix=/usr/ && \
    make && \
    make install && \
    ldconfig && \
    cd /usr/share/tessdata/ && \
    wget https://github.com/tesseract-ocr/tessdata_fast/raw/master/eng.traineddata && \
    wget https://github.com/tesseract-ocr/tessdata_fast/raw/master/osd.traineddata && \
    cp -r * ../ && \
    rm -rf /tmp/tesseract-ocr/


ENV PAPERLESS_CONSUMPTION_DIR /consume
ENV PAPERLESS_EXPORT_DIR /export


##############################
# Install python depedencies
WORKDIR /usr/src/paperless
COPY requirements.txt /usr/src/paperless/
RUN pip3 install --no-cache-dir -r requirements.txt


##############################
# Create directories and copy application
RUN mkdir -p /usr/src/paperless/src && \
    mkdir -p /usr/src/paperless/data && \
    mkdir -p /usr/src/paperless/media && \
    mkdir -p /usr/src/paperless/scripts
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
RUN groupadd -g 1000 paperless \
    && useradd -u 1000 -g 1000 -d /usr/src/paperless paperless \
    && chown -Rh paperless:paperless /usr/src/paperless


##############################
# Setup entrypoint
RUN cp /usr/src/paperless/scripts/docker-entrypoint.sh /sbin/docker-entrypoint.sh \
    && chmod 755 /sbin/docker-entrypoint.sh

WORKDIR /usr/src/paperless/src


##############################
# Mount volumes
VOLUME ["/usr/src/paperless/data", "/usr/src/paperless/media", "/consume", "/export"]

ENTRYPOINT ["/sbin/docker-entrypoint.sh"]
CMD ["--help"]


