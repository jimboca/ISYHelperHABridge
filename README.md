# ISYHelperHABridge
Python interface between the UDI ISY and HABridge

# Reason

Why would I use this to control ISY devices with Alexa or Google Home instead
of just using the Portal?

Harmony Hub's support Hue, so using this emulator allows controlling with
Alexa, Google Home, and Harmony.  Controlling lights with a Harmony Elite
remote with the home control buttons is awesome, even when Google can do it
sometimes it's easier just to push a button.

Control scenes as groups, so light levels can be set for a scene together.

# ISY Spoken Property

For an ISY device or scene to be enabled sent to the ha-bridge you select
the object in the ISY Admin Console, right click and select 'Notes'.  In
the notes there is a line to enter the Spoken property.

If you set the spoken property to just 1, this tells ihab to always use
the devices name as the spoken name, if you want to use a different name
then just enter that name.

## Devies or Scenes

If you set the spoken on a scene, then that scene will be controlled directly.
So you can not say 'set yourname to 30 percent', but you can say 'dim yourname'
or 'brighten yourname' and the levels will dim/brighten together based on their
current levels as set in the scene properties.  The advantage of this method
is that ihab is not involved in the control, the direct control goes from ha-bridge
to the ISY.

(I'm going to look into allowing dim/bright and direct percent commands to see
how they work, so might be able to do both?)

If you set the spoken on a controller of a scene, this tells ihab that you want
the abiity to control direct brightness levels of all responders in the scene
at the same time.  So you can say 'set yourname to 30 percent' this will change
ALL responders in that scene that are dimmable, to 30 percent.  But, with direct
on/off commands it will still turn on the scene, so if you have other responders
like KPL buttons, they will still turn on.

These two methods work very well for my enviornment, and makes my wife happy
because things just work as one would expect.  But, if you have different requirments
then please let me know.

# Installation

cd /home/pi
mkdir ihb
cd ibh
git clone https://github.com/jimboca/ISYHelperHABridge

cd ISYHelperHABridge
./install_habridge.sh

Configure the habridge by going to add a Harmony Hub
http://your_pi_ip_address

./install_ihb.sh



2016-12-27 18:30:55,228:IHAB:INFO: bridge:set_device_state '64'={'on': 'true', 'bri': '255'} 
2016-12-27 18:31:08,131:IHAB:INFO: bridge:set_device_state '64'={'on': 'true', 'bri': '102'} 
2016-12-27 18:31:36,735:IHAB:INFO: bridge:set_device_state '64'={'on': 'true', 'bri': '41'} 
2016-12-27 18:32:14,337:IHAB:INFO: bridge:set_device_state '64'={'on': 'true', 'bri': '16'} 
2016-12-27 18:32:38,718:IHAB:INFO: bridge:set_device_state '64'={'on': 'true', 'bri': '6'} 
2016-12-27 18:33:00,595:IHAB:INFO: bridge:set_device_state '64'={'on': 'true', 'bri': '2'} 
2016-12-27 18:33:22,287:IHAB:INFO: bridge:set_device_state '64'={'on': 'true', 'bri': '1'} 
