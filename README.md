# BirdAlert
BirdAlert is an aircraft reporting tool for ADSBx receivers that sends notifications whenever an aircraft of a certain type enters a certain radius of airspace. The alert includes the aircraft hex, callsign, type, owner, distance, direction, ground speed, transponder type, military flag and emergy flag information.

## Features
- Option to set the periodicity that the script parses aircraft.json for new data (default is 5 seconds)
- Sends an alert based on user defined transponders, callsigns, hex codes, military flag, or emergency flag values
- Option to set the minimum amount of time between notifications for a given aircraft (default is 10 minutes)
- Option to ignore commercial airlines (default is true)
- Includes a list of celebrity aircraft hexes to mointor by default
- Monitors for Civil Air Patrol (CAP) aircraft callsigns by default

## Setup
Copy BirdAlert.py to your ADSBx receiver and modify it to set the variables.<br><br>
If using an operating system that supports crontab, enable the script to run on boot:<br>
`sudo crontab -e`<br><br>
Add the following line to the bottom of your crontab: <br>
`@reboot /usr/bin/python3 <path to BirdAlert.py>`<br><br>
Reboot the device

## Future Enhancements
- [ ] Allow for notifications using email-to-SMS
- [x] ~~Make it easier to customize/select custom alert rules~~
- [ ] Account for aircraft using TIS-B that may rapidly change their hex code (which begin with "~") leading to a flood of notifications
- [ ] Add error handling for notification failures
- [x] Allow for hex code specific notifications
- [x] Allow for callsign specific notifications
- [ ] Clean up terminal output to be more compact
- [x] ~~Add more commercial airline callsigns to the ignore list~~
- [ ] Investigate if data could also be taken from https://globe.adsbexchange.com/ as a separate option, ex. using a browser plugin
- [ ] Incorporate category codes into alerts
- [ ] Allow for category specific notifications
- [x] Use the database of known aircraft information to give more details in notifications

## Comments
- Email-to-SMS is increasingly more difficult due to email providers implementing spam restrictions/rate limiting
- I'm not sure if the military and emergency flags are actually being set in the aircraft.json
- Currently the default path for aicraft.json is `/run/readsb/aircraft.json` which contains the raw flight data. This data is then refined into `/run/adsbexchange-feed/aircraft.json` which is sent to ADSBx for feeding.
- https://globe.adsbexchange.com/ is also able to provide other details like aircraft type, which would be nice to have in the notifications. Maybe if I figure out what they're using to pull that data, this tool could do the same.
- Some military aircraft set their hexes outside of the designated hex range for military use only. For these cases, a database of known military hexes is useful.
- Alas, some military aircraft will not broadcast at all and can only be seen with the naked eye.