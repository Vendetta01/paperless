#!/bin/bash
set -e


# Variables
source /usr/bin/environment.sh

# functions
function generate_ssl {
  mkdir -p $DEFAULT_SSL_BASE
  confout="${DEFAULT_SSL_BASE}/conf"
  keyout="${DEFAULT_SSL_KEY}"
  certout="${DEFAULT_SSL_CRT}"
  cakey="${DEFAULT_SSL_BASE}/ca.key"
  cacert="${DEFAULT_SSL_BASE}/ca.crt"
  serialfile="${DEFAULT_SSL_BASE}/serial"

  echo "Generating CA key"
  openssl genrsa -out $cakey 2048
  if [ $? -ne 0 ]; then exit 1 ; fi

  echo "Generating CA certificate"
  openssl req \
          -x509 \
          -new \
          -nodes \
          -subj "/CN=${SERVER_HOSTNAME}" \
          -key $cakey \
          -sha256 \
          -days 7300 \
          -out $cacert
  if [ $? -ne 0 ]; then exit 1 ; fi

  echo "Generating openssl configuration"

  cat <<EoCertConf>$confout
subjectAltName = DNS:${SERVER_HOSTNAME},IP:127.0.0.1
extendedKeyUsage = serverAuth
EoCertConf

  echo "Generating server key..."
  openssl genrsa -out $keyout 2048
  if [ $? -ne 0 ]; then exit 1 ; fi

  echo "Generating server signing request..."
  openssl req \
               -subj "/CN=${SERVER_HOSTNAME}" \
               -sha256 \
               -new \
               -key $keyout \
               -out /tmp/server.csr
  if [ $? -ne 0 ]; then exit 1 ; fi

  echo "Generating server cert..."
  openssl x509 \
                -req \
                -days 7300 \
                -sha256 \
                -in /tmp/server.csr \
                -CA $cacert \
                -CAkey $cakey \
                -CAcreateserial \
                -CAserial $serialfile \
                -out $certout \
                -extfile $confout
  if [ $? -ne 0 ]; then exit 1 ; fi
}


# Source: https://github.com/sameersbn/docker-gitlab/
map_uidgid() {
    USERMAP_ORIG_UID=$(id -u paperless)
    USERMAP_ORIG_GID=$(id -g paperless)
    USERMAP_NEW_UID=${USERMAP_UID:-$USERMAP_ORIG_UID}
    USERMAP_NEW_GID=${USERMAP_GID:-${USERMAP_ORIG_GID:-$USERMAP_NEW_UID}}
    if [[ ${USERMAP_NEW_UID} != "${USERMAP_ORIG_UID}" || ${USERMAP_NEW_GID} != "${USERMAP_ORIG_GID}" ]]; then
        echo "Mapping UID and GID for paperless:paperless to $USERMAP_NEW_UID:$USERMAP_NEW_GID"
        usermod -u "${USERMAP_NEW_UID}" paperless
        groupmod -g "${USERMAP_NEW_GID}" paperless
    fi
}

set_permissions() {
    # Set permissions for consumption and export directory
    for dir in PAPERLESS_CONSUMPTION_DIR PAPERLESS_EXPORT_DIR; do
      # Extract the name of the current directory from $dir for the error message
      cur_dir_name=$(echo "$dir" | awk -F'_' '{ print tolower($2); }')
      chgrp paperless "${!dir}" || {
          echo "Changing group of ${cur_dir_name} directory:"
          echo "  ${!dir}"
          echo "failed."
          echo ""
          echo "Either try to set it on your host-mounted directory"
          echo "directly, or make sure that the directory has \`g+wx\`"
          echo "permissions and the files in it at least \`o+r\`."
      } >&2
      chmod g+wx "${!dir}" || {
          echo "Changing group permissions of ${cur_dir_name} directory:"
          echo "  ${!dir}"
          echo "failed."
          echo ""
          echo "Either try to set it on your host-mounted directory"
          echo "directly, or make sure that the directory has \`g+wx\`"
          echo "permissions and the files in it at least \`o+r\`."
      } >&2
    done
    # Set permissions for application directory
    chown -Rh paperless:paperless /usr/src/paperless
}

migrations() {
    # A simple lock file in case other containers use this startup
    LOCKFILE="/usr/src/paperless/data/db.sqlite3.migration"

    # check for and create lock file in one command 
    if (set -o noclobber; echo "$$" > "${LOCKFILE}") 2> /dev/null
    then
        trap 'rm -f "${LOCKFILE}"; exit $?' INT TERM EXIT
        sudo -HEu paperless "/usr/src/paperless/src/manage.py" "migrate"
        rm ${LOCKFILE}
    fi
}

initialize() {
    map_uidgid
    set_permissions
    generate_ssl
    # first set up confd itself from env
    echo "INFO: Setting up confd"
    /usr/bin/confd -onetime -backend env -confdir /tmp/etc/confd
    # now set up all config files initially
    echo "INFO: Setting up config files"
    /usr/bin/confd -onetime -confdir /etc/confd \
	-config-file /etc/confd/confd.toml
    echo "INFO: Initialization done"
    migrations
    touch "$FIRST_START_FILE_URL"
}

install_languages() {
    local langs="$1"
    read -ra langs <<<"$langs"

    # Check that it is not empty
    if [ ${#langs[@]} -eq 0 ]; then
        return
    fi

    # Loop over languages to be installed
    for lang in "${langs[@]}"; do
        pkg="tesseract-ocr-data-$lang"

        # English is installed by default
        if [[ "$lang" ==  "eng" ]]; then
            continue
        fi

        if apk info -e "$pkg" > /dev/null 2>&1; then
            continue
        fi
        if ! apk --update --no-cache info "$pkg" > /dev/null 2>&1; then
            continue
        fi

        apk --no-cache --update add "$pkg"
    done
}



# main
if [[ ! -e "$FIRST_START_FILE_URL" ]]; then
	# Do stuff
	initialize
fi


# Start paperless
exec /usr/bin/supervisord -c /etc/supervisord.conf

