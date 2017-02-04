# ISYHelperHABridge
Python interface between the UDI ISY and HABridge

# Reason

Why would I use this to control ISY devices with Alexa or Google Home instead
of just using the Portal?

Harmony Hub's support Hue, so using this emulator allows controlling with
Alexa, Google Home, and Harmony.  Controlling lights with a Harmony Elite
home control buttons is awesome, even when we can do it with voice control
sometimes it's better to just to push a button.

Control scenes as groups, so light levels can be set for a scene together!

# Why not the original ISYHelper

ISYHelper was created before there was a Polyglot, then idea was to allow
an easy way to add modules to support any functions.  It worked great to
create a Hue Emulator, WeMo Emulator, Harmony Hub Interface, IP Camera
control, IFTTT/Maker ...  But with the Portal supporting Maker, and Polyglot
allowing control of cameras, it's not a as necessary.

The other big reason is that ISYHelper does not store a persistant database
so after each restart, the Hue device numbers may change, which is a problem
for other hubs, like Harmony, which use these device ID's for linking.  To
fix this in ISYHelper would have required a lot of work, and I decided to try
ha-bridge instead.

# Why use ha-bridge

The original ha-bridge has matured a lot and now has a nice REST interface
for adding/removing devices and controlling the state.  This allows ISY
devices to be added on the fly, and allows tracking the current state and
brightness of ISY device levels back to the ha-bridge.

The interfaces needed to to communicate with the Alexa, Google Home,
Harmony Hubs keep changing which required updates to the PyHue and PyHarmony
recently and ha-bridge author is good at keeping up with those changes.

The ha-bridge supports creating command sequences on the Harmony and linking
those to a device in the Hue Emulator.  This allows you to add a Hue device
called "ESPN" so you can tell Google Home "Turn on ESPN".   These could be done
also by creating an ESPN activity on the Harmony, but I don't want to create
an activity for every channel I watch.

# ISY Spoken Property

For an ISY device or scene to be enabled and sent to the ha-bridge you select
the object in the ISY Admin Console, right click and select 'Notes'.  In the
notes there is a line to enter the Spoken property.

If you set the spoken property to just 1, this tells ihab to always use
the devices name as the spoken name, if you want to use a different name
then just enter that name.

## Devies or Scenes

If you set the spoken on a controller of a scene, this tells ihab that you want
the abiity to control direct brightness levels of all responders in the scene
at the same time.  So you can say 'set yourname to 30 percent' which will change
ALL responders in that scene that are dimmable, to 30 percent.  You can also dim
or brighten the scene, which will set all devices to the new brightness sent by
Google Home or Alexa.  Note that when it is turned on or off, the ISY scene is
controlled, so if you have other responders like KPL buttons, they will still turn
on.  This could be enhanced further to dim/brighten each responder based on their
current level, but I don't really have a need for that, so it hasn't been done yet.
The current brightness of the controller is pushed to ha-bridge so any brigthen or
dim commands are based on it's brightness level.

If you set the spoken on a scene, then that scene will be controlled directly.
so you can not dim, brighten, or set the scene to a percentage.

These two methods work very well for my enviornment, and makes my wife happy
because things just work as one would expect.  But, if you have different requirments
then please let me know.

### Renameing

If you rename a device on the ISY then you must restart IHAB.  This is an issue
with PyISY that needs to be fixed...

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
