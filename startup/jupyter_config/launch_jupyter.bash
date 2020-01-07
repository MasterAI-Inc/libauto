#!/bin/bash

set -e

if ! [ $(id -u) = 0 ]
then
    echo "You must be root to use this script."
    exit 1
fi

cd "$(dirname "$0")"   # Change to this script's directory.

if [ -z "$LIBAUTO_UP_USER" ] || [ -z "$LIBAUTO_PRIV_USER" ]
then
    echo "Error: The LIBAUTO_UP_USER and LIBAUTO_PRIV_USER variable is not set."
    exit 1
fi

JUPYTER_CONFIG_DIR="/var/lib/jupyter_config"
JUPYTER_CONFIG_FILE="$JUPYTER_CONFIG_DIR/jupyter_notebook_config.py"

mkdir -p "$JUPYTER_CONFIG_DIR"
rm -f "$JUPYTER_CONFIG_FILE"
touch "$JUPYTER_CONFIG_FILE"
chown "$LIBAUTO_UP_USER":"$LIBAUTO_UP_USER" "$JUPYTER_CONFIG_FILE"
chmod 400 "$JUPYTER_CONFIG_FILE"

python3 write_jupyter_config.py jupyter_notebook_config_template.py > "$JUPYTER_CONFIG_FILE"

exec sudo -u "$LIBAUTO_UP_USER" -i jupyter notebook --ip=0.0.0.0 --no-browser --config="$JUPYTER_CONFIG_FILE"

