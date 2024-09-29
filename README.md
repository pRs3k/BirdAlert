# BirdAlert
BirdAlert is an aircraft reporting tool for ADS-B receivers that sends notifications whenever an aircraft of a certain type enters a certain radius of airspace. The alert includes the aircraft hex, callsign, type, owner, distance, direction, ground speed, transponder type, military flag and emergy flag information.

## Features
- Supports notifications via email, email-to-sms (untested), Twilio (untested), Telegram, Signal (untested), IFTTT (untested), and Pushover (untested)
- Option to set the periodicity that the script parses aircraft.json for new data (default is 5 seconds)
- Sends an alert based on user defined transponders, callsigns, hex codes, military flag, or emergency flag values
- Option to set the minimum amount of time between notifications for a given aircraft (default is 10 minutes)
- Option to ignore commercial airlines (default is "True")
- Includes a list of celebrity aircraft hexes to monitor by default
- Monitors for Civil Air Patrol (CAP) aircraft callsigns by default

## Setup

To get notifications using Telegram (my personal preference), search "how to set up botfather, get token and chatid", or follow the steps here https://www.cytron.io/tutorial/how-to-create-a-telegram-bot-get-the-api-key-and-chat-id<br><br>

If you can figure out how to get Signal (signal-cli) working on Raspberry Pi, please send me the instructions and I'll add support in this script. I tried for a long time and failed.<br><br>

Install the required Python modules:<br>
`   pip3 install -r requirements.txt`<br>
Copy BirdAlert.py to your ADS-B receiver and modify it to set the variables:<br>
`cd ~`<br>
`wget https://raw.githubusercontent.com/pRs3k/BirdAlert/refs/heads/main/BirdAlert.py`<br>
`nano BirdAlert.py`<br><br>
If using an operating system that supports crontab, enable the script to run on boot (do not execute as sudo or the script won't work right):<br>
`crontab -e`<br><br>
Add the following line to the bottom of your crontab file:<br>
`@reboot /usr/bin/python3 <path to BirdAlert.py>`<br><br>
Save, and then reboot the device<br>
`sudo reboot now`<br><br>
If you need to stop BirdAlert or modify the configuration variables:<br>
`ps aux | grep -i birdalert`<br>
`kill <pid of BirdAlert.py, there will be 2 processes to kill>`<br>
`nano BirdAlert.py`<br>
`sudo reboot now`

## Future Enhancements
- [ ] Switch to using the new Mictronics aircraft database that receives regular updates https://github.com/Mictronics/readsb-protobuf/blob/dev/webapp/src/db/aircrafts.json by parsing the Mictronics types database https://github.com/Mictronics/readsb-protobuf/blob/dev/webapp/src/db/types.json 
- [ ] Use the Mictronics operator database to include more comprehensive filtering https://github.com/Mictronics/readsb-protobuf/blob/dev/webapp/src/db/operators.json
- [x] ~~Allow for notifications using email-to-SMS~~
- [ ] Figure out where the "interesting" aircraft database comes from on adsbx and incorporate it here
- [x] ~~Add the ability to schedule the script to run only at certain times of day~~
- [x] ~~Make it easier to customize/select custom alert rules~~
- [ ] Account for aircraft using TIS-B that may rapidly change their hex code (which begin with "~") leading to a flood of notifications
- [x] ~~Add error handling for notification failures~~
- [x] ~~Allow for hex code specific notifications~~
- [x] ~~Allow for callsign specific notifications~~
- [ ] Clean up terminal output to be more compact
- [x] ~~Add more commercial airline callsigns to the ignore list~~
- [ ] Investigate if data could also be taken from https://globe.adsbexchange.com/ as a separate option, ex. using a browser plugin
- [ ] Incorporate category codes into alerts
- [ ] Allow for category specific notifications
- [x] ~~Use the database of known aircraft information to give more details in notifications~~

## Comments
- Email-to-SMS is increasingly more difficult due to email providers implementing spam restrictions/rate limiting
- I'm not sure if the military and emergency flags are actually being set in the aircraft.json
- Currently the default path for aicraft.json is `/run/readsb/aircraft.json` which contains the raw flight data. This data is gets refined into `/run/adsbexchange-feed/aircraft.json`, which is sent to ADSBx for feeding.
- Some military aircraft set their hexes outside of the designated hex range for military use only. For these cases, a database of known military hexes is useful.
- Alas, some military aircraft will not broadcast at all and can only be seen with the naked eye.