#!/bin/bash -x

owd=`pwd`
bn=`basename $owd`
if [ -f /lib/systemd/system/ihab.service ]; then
   sudo systemctl stop ihab
fi

sudo cp util/ihab.service /lib/systemd/system/
sudo systemctl --system daemon-reload

cd ..
td=`pwd`
if [ ! -f config.yaml ]; then
    cp ISYHelperHABridge/config.example.yaml config.yaml
    echo "Created $td/config.yaml"
fi

if [ ! -d logs ]; then
    mkdir logs
fi

git clone https://github.com/jimboca/PyISY

sudo systemctl enable ihab

echo "Setup and run:
cd $nd
leafpad config.yaml
sudo systemctl start ihab
sudo systemctl status ihab
"
