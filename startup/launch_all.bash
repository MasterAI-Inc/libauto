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

if [ -z "$LIBAUTO_UP_USER" ] || [ -z "$LIBAUTO_PRIV_USER" ]
then
    echo "Error: The LIBAUTO_UP_USER and LIBAUTO_PRIV_USER variable is not set."
    exit 1
fi

if [ -z "$PYTHON_EXE" ]
then
    echo "Error: The PYTHON_EXE variable is not set."
    exit 1
fi

exit

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

