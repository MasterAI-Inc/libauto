#!/bin/bash

set -e

if [ -z "$1" ]
then
    RUN_AS_USER="$USER"
else
    RUN_AS_USER="$1"
fi

cd "$(dirname "$0")"   # Change to this script's directory.

echo 'Jupyter launching as user' "$RUN_AS_USER"

JUPYTER_CONFIG_FILE="/tmp/jupyter_notebook_config.py"

python3 write_jupyter_config.py jupyter_notebook_config_template.py "$JUPYTER_CONFIG_FILE"

exec sudo -u "$RUN_AS_USER" -i jupyter notebook --config="$JUPYTER_CONFIG_FILE"

