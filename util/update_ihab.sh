#!/bin/bash -x

owd=`pwd`

if [ -f /lib/systemd/system/ihab.service ]; then
   sudo systemctl stop ihab
fi

git pull

sudo cp util/ihab.service /lib/systemd/system/
sudo systemctl --system daemon-reload
sudo systemctl enable ihab

cd ../PyISY
git pull

if [ -f /lib/systemd/system/ihab.service ]; then
  sudo systemctl start ihab
  sudo systemctl status ihab
fi
