#!/bin/bash

# Change to the `libauto` directory.
cd "$(dirname "$0")"/..

sync

for i in `seq 1 3`
do
    echo '=========================================================='
    echo '==========================================================' 1>&2
done

echo "Starting at $(date) in directory $(pwd) as user $(whoami)"

if ! diff -qN resources/scripts/profile_d_libauto.sh /etc/profile.d/libauto.sh
then
    cp resources/scripts/profile_d_libauto.sh /etc/profile.d/libauto.sh
    chmod 0755 /etc/profile.d/libauto.sh
    echo "Updated /etc/profile.d/libauto.sh, will now reboot!"
    reboot
else
    echo "The script at /etc/profile.d/libauto.sh is already up-to-date."
fi

if ! diff -qN resources/scripts/update_curriculum /usr/local/bin/update_curriculum
then
    cp resources/scripts/update_curriculum /usr/local/bin/update_curriculum
    chmod 0755 /usr/local/bin/update_curriculum
    echo "Updated the update_curriculum script."
else
    echo "The update_curriculum script is already up-to-date."
fi

if ! diff -qN resources/scripts/set_hostname /usr/local/bin/set_hostname
then
    cp resources/scripts/set_hostname /usr/local/bin/set_hostname
    chmod 0755 /usr/local/bin/set_hostname
    echo "Updated the set_hostname script."
else
    echo "The set_hostname script is already up-to-date."
fi

if ! diff -qN resources/scripts/update_libauto /usr/local/bin/update_libauto
then
    cp resources/scripts/update_libauto /usr/local/bin/update_libauto
    chmod 0755 /usr/local/bin/update_libauto
    echo "Updated the update_libauto script."
else
    echo "The update_libauto script is already up-to-date."
fi

if [ -z "$LIBAUTO_UP_USER" ] || [ -z "$LIBAUTO_PRIV_USER" ]
then
    echo "Error: The LIBAUTO_UP_USER and LIBAUTO_PRIV_USER variable is not set."
    exit 1
fi

if [ -z "$LIBAUTO_SERVICES_PYTHON" ] || [ -z "$LIBAUTO_CONSOLE_UI_PYTHON" ]
then
    echo "Error: The LIBAUTO_SERVICES_PYTHON and LIBAUTO_CONSOLE_UI_PYTHON variable is not set."
    exit 1
fi

if [ ! -f /var/lib/libauto/secure.db ]
then
    mkdir -p /var/lib/libauto
    chmod 755 /var/lib/libauto
    chown "$LIBAUTO_PRIV_USER":"$LIBAUTO_PRIV_USER" /var/lib/libauto

    touch /var/lib/libauto/settings.db
    chmod 644 /var/lib/libauto/settings.db
    chown "$LIBAUTO_PRIV_USER":"$LIBAUTO_PRIV_USER" /var/lib/libauto/settings.db

    touch /var/lib/libauto/secure.db
    chmod 600 /var/lib/libauto/secure.db
fi

if [ ! -f /var/lib/libauto/env_setup ]
then
    sudo -u "$LIBAUTO_UP_USER"   -i "$(pwd)/environment/install_environment.bash"
    sudo -u "$LIBAUTO_PRIV_USER" -i "$(pwd)/environment/install_environment.bash"
    touch /var/lib/libauto/env_setup
fi

"$LIBAUTO_SERVICES_PYTHON" startup/cio_rpc_server/cio_rpc_server.py &
CIO_RPC_SERVER_PID=$!

"$LIBAUTO_SERVICES_PYTHON" startup/camera_rpc_server/camera_rpc_server.py &
CAM_RPC_SERVER_PID=$!

while ! nc -z localhost 18861; do
    sleep 0.1
done

while ! nc -z localhost 18862; do
    sleep 0.1
done

"$LIBAUTO_SERVICES_PYTHON" resources/scripts/startup_demo_car.py &
DEMO_PID=$!

fbcp &
FBCP_PID=$!

omxplayer -b resources/videos/boot_up_video.mp4

kill $FBCP_PID
wait $FBCP_PID

wait $DEMO_PID

"$LIBAUTO_CONSOLE_UI_PYTHON" startup/console_ui/console_ui.py &
CUI_PID=$!

while ! nc -z localhost 18863; do
    sleep 0.1
done

"$LIBAUTO_SERVICES_PYTHON" startup/wifi_controller/wifi_controller.py "$LIBAUTO_PRIV_USER" &
WIFI_PID=$!

sudo -u "$LIBAUTO_UP_USER" -i tmux new-session -d -s cdp_dashboard

sudo -u "$LIBAUTO_UP_USER" -i tmux new-session -d -s bootup_session
sudo -u "$LIBAUTO_UP_USER" -i tmux send -t bootup_session python SPACE bootup_script.py ENTER

"$LIBAUTO_SERVICES_PYTHON" startup/cdp_connector/cdp_connector.py "$LIBAUTO_UP_USER" "$LIBAUTO_PRIV_USER" &
CDPC_PID=$!

while ! nc -z localhost 18864; do
    sleep 0.1
done

./startup/jupyter_config/launch_jupyter.bash &
JUPYTER_PID=$!

"$LIBAUTO_SERVICES_PYTHON" startup/battery_monitor/battery_monitor.py &
BATT_PID=$!

"$LIBAUTO_SERVICES_PYTHON" startup/menu_driver/menu_driver.py &
MENU_PID=$!

echo 'EVERYTHING LAUNCHED SUCCESSFULLY!'

wait $CUI_PID

kill -9 $MENU_PID
wait $MENU_PID

kill -9 $BATT_PID
wait $BATT_PID

kill -9 $JUPYTER_PID
wait $JUPYTER_PID

kill -9 $CDPC_PID
wait $CDPC_PID

kill -9 $WIFI_PID
wait $WIFI_PID

kill -9 $CAM_RPC_SERVER_PID
wait $CAM_RPC_SERVER_PID

kill -1 $CIO_RPC_SERVER_PID
wait $CIO_RPC_SERVER_PID

