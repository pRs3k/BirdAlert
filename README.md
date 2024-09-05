# BirdAlert
BirdAlert is an aircraft reporting tool for ADSBx receivers that sends notifications whenever an aircraft of a certain transponder type enters a certain radius of airspace.

## Features
- Option to set the periodicity that the script parses aircraft.json for new data (default is 5 seconds)
- Sends an alert based on user defined transponders, military flag, or emergency flag values
- Option to set the minimum amount of time between notifications for a given aircraft (default is 20 minutes)
- Option to ignore commercial airlines, unless the emergency flag is set (enabled by default)

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
- [ ] Allow for hex code specific notifications
- [ ] Allow for callsign specific notifications
- [ ] Clean up terminal output to be more compact
- [x] ~~Add more commercial airline callsigns to the ignore list~~
- [ ] Investigate if data could also be taken from https://globe.adsbexchange.com/ as a separate option, ex. using a browser plugin
- [ ] Incorporate category codes into alerts
- [ ] Allow for category specific notifications
- [ ] Use the database of known aircraft information to give more details in notifications

## Comments
- Email-to-SMS is increasingly more difficult due to email providers implementing spam restrictions/rate limiting
- I'm not sure if the military and emergency flags are actually being set in the aircraft.json. A lot of military aircraft are just broadcasting ADS-B which are not currently caught by the tool. I need a way to notify on those instances without spamming all of the other non-military ADS-B aircraft. https://globe.adsbexchange.com/ provides this capability if the tool is ever able to use that directly. 
- Currently the default path for aicraft.json is `/run/readsb/aircraft.json` which contains the raw flight data. This data is then refined into `/run/adsbexchange-feed/aircraft.json` which is sent to ADSBx for feeding. It initially seems like the former is the better source of data for this script, but further investigation may be useful.
- https://globe.adsbexchange.com/ is also able to provide other details like aircraft type, which would be nice to have in the notifications. Maybe if I figure out what they're using to pull that data, this tool could do the same.
