#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

for service in robot.service robot-watcher.service robot-watcher.path ; do
    sudo ln -s $SCRIPT_DIR/$service /etc/systemd/system/
    sudo systemctl start $service
    sudo systemctl enable $service
done

sudo apt install bluetooth bluez libbluetooth-dev

pip install -r $SCRIPT_DIR/requirements.txt