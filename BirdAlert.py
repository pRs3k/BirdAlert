#!/usr/bin/env python3

import os
import smtplib
import json
import time
import requests
from math import radians, cos, sin, asin, sqrt, atan2, degrees

#############################################################

# Script behavior
update_rate = 5                                  # The frequency that this script runs checking for aircraft updates, in seconds
aircraft_json_path = "/run/readsb/aircraft.json" # Change this if your aircraft.json is in a different location
aircrafts_json_path = "~/aircrafts.json"         # This is referring to the Mictronics aircraft database. Leave this alone unless you have already downloaded it and would like to store it elsewhere.
range_miles = 20                                 # Change this to the radius of the notification zone (in miles)
min_alert_period = 600                           # Change this to the number of seconds to wait before alerting again for the same aircraft
include_military_check = True                    # Change to False if you don't want to alert based on the military flag being set or the hex falling within the military range  (True will alert regardless of other settings)
include_emergency_check = True                   # Change to False if you don't want to alert based on the emergency flag being set (True will alert regardless of other settings)
skip_commercial = True                           # Change to False to include alerts for commerical aircraft (doesn't effect notificaitons for emergency flag being set)
transponder_types = [                            # Comment in/out rows corresponding to transponder types you want to receive alerts for
    'adsb_icao',     # Mode S or ADS-B transponder (I usually comment this out to prevent too many notifications of non-interesting aircraft)
 #   'adsb_icao_nt',  # ADS-B equipped “non-transponder” emitter, such as a ground vehicle (this is an example of a transponder commented out)
    'adsr_icao',     # Rebroadcast of ADS-B messages originally sent via UAT transponder
    'tisb_icao',     # Non-ADS-B aircraft
    'adsc',          # Automatic Dependent Surveillance-Contract received by monitoring satellite downlinks
    'mlat',          # Multilateration position calculated using arrival time differences from multiple receivers
    'mode_s',        # Mode S transponder (no position transmitted)
    'adsb_other',    # ADS-B transponder using a non-ICAO address, such as an anonymized address
    'adsr_other',    # Rebroadcast of ADS-B messages originally sent via UAT transponder, using a non-ICAO address
    'tisb_other',    # Non-ADS-B target using a non-ICAO address
]

hex_watch_list = {   # Add the hex codes of specific aircraft to always alert on
    'a35e6b': "Elton John's Bombardier Global Express (M-EDZE)",
    'a35e89': "Oprah Winfrey's Gulfstream G650 (N540W)",
    'a3a8a7': "Elon Musk's Gulfstream V (N272BG)",
    'a3a8c2': "George Lucas's Gulfstream V (N138GL)",
    'a3b23a': "Michael Bloomberg's Dassault Falcon 900 (N8AG)",
    'a3b29b': "Jim Carrey's Gulfstream V (N162JC)",
    'a3b78d': "Judge Judy's Cessna Citation 750 (N555QB)",
    'a3d53f': "Nike Corporation's Gulfstream G650 (N6453)",
    'a3e31a': "Michael Bloomberg's Dassault Falcon 900 (N5MV)",
    'a3e3d2': "Caesars Palace Casino's Gulfstream V (N898CE)",
    'a4b69f': "Matt Damon's Bombardier Global 7500 (N444WT)",
    'a4b7df': "Larry Ellison's Gulfstream G650 (N817GS)",
    'a4bd79': "Mark Wahlberg's Bombardier Global Express (N143MW)",
    'a44e47': "Michael Jordan's Gulfstream V (N236MJ)",
    'a44e85': "Mark Zuckerberg's Gulfstream G650 (N68885)",
    'a53afc': "Ronald Perelman's Gulfstream G650 (N838MF)",
    'a54e98': "Travis Scott's Embraer E-190 (N713TS)",
    'a59bfa': "Kid Rock's Bombardier Challenger 600 (N71KR)",
    'a59f1b': "Tom Cruise's Bombardier Challenger 350 (N350XX)",
    'a59525': "Dan Bilzerian's Gulfstream IV (N701DB)",
    'a5958b': "Bill Gates' Cessna 208 Amphibian Caravan",
    'a60e73': "Bill Gates's Gulfstream G650 (N887WM)",
    'a60e84': "Bill Gates's Gulfstream G650 (N194WM)",
    'a62742': "Eric Schmidt's Gulfstream G650 (N652WE)",
    'a6758d': "Tyler Perry's Embraer E-190 (N378TP)",
    'a68258': "Elon Musk's Gulfstream G650 (N628TS)",
    'a96f69': "John Travolta's Boeing 707-136B",
    'a98bfa': "Kid Rock's Bombardier Challenger 600 (N71KR)",
    'a1e4f2': "Phil Knight's Gulfstream G650 (N1KE)",
    'a1b8ab': "Luke Bryan's Learjet 60 (N506AB)",
    'a1f680': "Steve Ballmer's Gulfstream G650 (N709DS)",
    'a2c818': "Sergey Brin's Gulfstream G650 (N232G)",
    'a2cb4d': "Kylie Jenner's Bombardier Global 7500 (N810KJ)",
    'a2e4cd': "Kim Kardashian's Gulfstream G650 (N1980K)",
    'a2e77d': "David Geffen's Gulfstream G650 (N221DG)",
    'a4b7df': "Larry Ellison's Gulfstream G650 (N817GS)",
    'a47bf4': "Donald Trump's Boeing 757 (N757AF)",
    'a48d23': "Lady Gaga's Gulfstream V (N474D)",
    'a4bdb3': "Steve Wynn's Gulfstream V (N88WR)",
    'a5e41b': "Bill Gates's Gulfstream G650 (N887WM)",
    'a4bdb3': "Steve Wynn's Gulfstream V (N88WR)",
    'a2cb4d': "Kylie Jenner's Bombardier Global 7500 (N810KJ)",
    'a0b70e': "Google's Gulfstream V (N10XG)",
    'a1e4f2': "Phil Knight's Gulfstream G650 (N1KE)",
    'a53afc': "Ronald Perelman's Gulfstream G650 (N838MF)",
    'a4bdb3': "Steve Wynn's Gulfstream V (N88WR)",
    'a59bfa': "Kid Rock's Bombardier Challenger 600 (N71KR)",
    'a4b69f': "Matt Damon's Bombardier Global 7500 (N444WT)",
    'a3a8a7': "Elon Musk's Gulfstream V (N272BG)",
    'a2cb4d': "Kylie Jenner's Bombardier Global 7500 (N810KJ)",
    'ac39d6': "Bill Gates' Gulfstream G650ER",
    'a17907': "Bill Gates' Gulfstream G650ER",
    'a5958b': "Bill Gates' Cessna 208 Amphibian Caravan",
    'ac64c6': "Taylor Swift's Dassault Falcon 900",
    'a0f9e7': "Jim Carrey's Gulfstream V",
    'a96f69': "John Travolta's Boeing 707-136B"
}

# List of callsigns to watch for
callsign_watch_list = [
    "CAP",                                         # Civil Air Patrol
]

# Your location
your_lat = latitude_here  # change this to the latitude of the notification zone (ex. 40.12345)
your_lon = longitude_here  # change this to the longitude of the notification zone (ex -104.12345)

# Choose as many of the following notification methods as you like (it's not necessary to comment them out if you don't use them).
# The script will try them in order and stop after the first successful notification is sent.

# Email configuration
your_email = ''  # change this to your email
your_email_app_password = ''  # change this to your email app password
your_smtp_server = ''  # change this to your email SMTP domain
your_smtp_port = 587

# Telegram configuration
telegram_bot_token = ''  # change this to your Telegram bot token
telegram_chat_id = ''  # change this to your Telegram chat ID

# Pushover configuration
pushover_user_key = ''  # change this to your Pushover user key
pushover_app_token = ''  # change this to your Pushover app token

# IFTTT configuration
ifttt_webhook_event = ''  # change this to your IFTTT webhook event name
ifttt_webhook_key = ''  # change this to your IFTTT webhook key

# Signal configuration
signal_phone_number = ''  # change this to your Signal phone number
signal_recipients = []  # change this to a list of recipients

#############################################################

# Tracking last notification times
last_notified = {}

# Handle file path if it uses a tilda
home_dir_check = os.path.expanduser(aircrafts_json_path)

# Function to support downloading updated Mictronics aircraft database
def download_file(url, path):
    try:
        file_response = requests.get(url)
        if file_response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(file_response.content)
            print(f"{path} has been downloaded.\n")
        else:
            print(f"Failed to download the file. HTTP Status: {file_response.status_code}\n")
    except Exception as e:
        print(f"Error downloading file: {e}\n")

# Function to check if there is a newer version of the Mictronics aircraft database and then download it
def aircrafts_age_check():
    url = 'https://raw.githubusercontent.com/Mictronics/readsb-protobuf/refs/heads/dev/webapp/src/db/aircrafts.json'
    global home_dir_check
    time_check_file = '.time_check'

    # Check if .time_check exists
    is_new_time_check = False
    if not os.path.exists(time_check_file):
        is_new_time_check = True
        open(time_check_file, 'a').close()  # Create the .time_check file

    # Check if aircrafts.json exists
    is_new_aircrafts_json = not os.path.exists(home_dir_check)

    # Check the last modified time of the .time_check file
    last_check_time = os.path.getmtime(time_check_file)
    current_time = time.time()

    # If .time_check is new or it's been more than an hour since the last check
    if is_new_time_check or (current_time - last_check_time) > 3600:
        if is_new_aircrafts_json:
            print(f"{home_dir_check} not found. Downloading for the first time...\n")
        else:
            print("More than 1 hour since last check for updated Micronics database. Checking for updates...\n")
        
        # Download the latest aircrafts.json
        download_file(url, home_dir_check)
        # Update the .time_check file to the current time
        os.utime(time_check_file, (current_time, current_time))
    else:
        print("Less than 1 hour since last check for updated Micronics database. Skipping...\n")

def is_military_aircraft(hex_code):
    # Remove the '~' character if it exists
    hex_code = hex_code.lstrip('~')
    
    # Convert the hex code to an integer
    hex_int = int(hex_code, 16)

    military_ranges = [
        ("adf7c8", "afffff"),
        ("010070", "01008f"),
        ("0a4000", "0a4fff"),
        ("33ff00", "33ffff"),
        ("350000", "37ffff"),
        ("3aa000", "3affff"),
        ("3b7000", "3bffff"),
        ("3ea000", "3ebfff"),
        ("3f4000", "3fbfff"),
        ("400000", "40003f"),
        ("43c000", "43cfff"),
        ("444000", "446fff"),
        ("44f000", "44ffff"),
        ("457000", "457fff"),
        ("45f400", "45f4ff"),
        ("468000", "4683ff"),
        ("473c00", "473c0f"),
        ("478100", "4781ff"),
        ("480000", "480fff"),
        ("48d800", "48d87f"),
        ("497c00", "497cff"),
        ("498420", "49842f"),
        ("4b7000", "4b7fff"),
        ("4b8200", "4b82ff"),
        ("70c070", "70c07f"),
        ("710258", "71028f"),
        ("710380", "71039f"),
        ("738a00", "738aff"),
        ("7cf800", "7cfaff"),
        ("800200", "8002ff"),
        ("c20000", "c3ffff"),
        ("e40000", "e41fff")
    ]

    # Check if the hex code is within any of the military ranges
    for start, end in military_ranges:
        start_int = int(start, 16)
        end_int = int(end, 16)
        if start_int <= hex_int <= end_int:
            return True
    return False

# Function to calculate the distance between two lat/lon pairs using the Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 3956
    return c * r

# Function to calculate the direction from your location to the aircraft
def calculate_direction(lat1, lon1, lat2, lon2):
    # Convert latitudes and longitudes to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    y = sin(dlon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    
    # Calculate the initial bearing in radians and convert to degrees
    initial_bearing = atan2(y, x)
    initial_bearing = degrees(initial_bearing)
    
    # Normalize the compass bearing to a range of 0 to 360 degrees
    compass_bearing = (initial_bearing + 360) % 360

    # Determine the closest direction based on 45-degree intervals
    directions = ["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West"]
    idx = round(compass_bearing / 45) % 8
    return directions[idx]

# Function to send an email notification
def send_email_notification(message_body):
    subject = "Bird Alert!"

    try:
        with smtplib.SMTP(your_smtp_server, your_smtp_port) as server:
            server.starttls()
            server.login(your_email, your_email_app_password)
            server.sendmail(your_email, your_email, message_body)
            print(f"Sending Email: {message_body}\n")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}\n")
        return False

# Function to send a Telegram notification
def send_telegram_notification(message_body):
    if not telegram_bot_token or not telegram_chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": message_body
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram message sent\n")
        return True
    except Exception as e:
        print(f"Failed to send Telegram message: {e}\n")
        return False

# Function to send a Pushover notification
def send_pushover_notification(message_body):
    if not pushover_user_key or not pushover_app_token:
        return False

    url = "https://api.pushover.net/1/messages.json"
    payload = {
        "token": pushover_app_token,
        "user": pushover_user_key,
        "message": message_body
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("Pushover message sent\n")
        return True
    except Exception as e:
        print(f"Failed to send Pushover message: {e}\n")
        return False

# Function to send a notification via IFTTT
def send_ifttt_notification(message_body):
    if not ifttt_webhook_event or not ifttt_webhook_key:
        return False

    url = f"https://maker.ifttt.com/trigger/{ifttt_webhook_event}/with/key/{ifttt_webhook_key}"
    payload = {"value1": message_body}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("IFTTT notification sent\n")
        return True
    except Exception as e:
        print(f"Failed to send IFTTT notification: {e}\n")
        return False

# Function to send a Signal notification
def send_signal_notification(message_body):
    if not signal_phone_number or not signal_recipients:
        return False

    try:
        for recipient in signal_recipients:
            # Replace with actual Signal command or API call to send a message
            print(f"Sending Signal message to {recipient}: {message_body}\n")
        return True
    except Exception as e:
        print(f"Failed to send Signal message: {e}\n")
        return False

# Function to send notifications through all available methods
def send_notification(aircraft_info, hex_code, distance, direction, aircraft_owner):
    global home_dir_check
    hex_code = hex_code.upper()  # Convert to uppercase to match structure of aircrafts.json
    message_body = f"Bird Alert!\n" \
              f"Aircraft hex: {hex_code}\n" \
              f"Callsign: {aircraft_info.get('flight', 'N/A')}\n" \
              
    try:
        with open(home_dir_check, 'r') as f:
            aircrafts_data = json.load(f)
            # Find the entry with the matching hex_code (ICAO24)
            aircraft_entry = aircrafts_data.get(hex_code)
            if aircraft_entry:
                type_info = aircraft_entry['d'] if aircraft_entry['d'] else aircraft_entry['t']
                print(f"Description: {aircraft_entry['d']}\n Type: {aircraft_entry['t']}")
                message_body += f"Type: {type_info}\n"
            else:
                message_body += "Type: Unknown\n"  # Handle case where hex is not found
    except FileNotFoundError:
        print(f"File not found: {home_dir_check}")
        message_body += "Type: Unknown\n"  # Handle file not found
    except json.JSONDecodeError:
        print("Error decoding JSON response")
        message_body += "Type: Unknown\n"  # Handle JSON decode error


    message_body += f"Owner: {aircraft_owner}\n" \
                    f"Distance: {distance:.2f}mi\n" \
                    f"Direction: {direction}\n" \
                    f"Ground Speed: {aircraft_info.get('gs', 'N/A')} knots\n" \
                    f"Transponder: {aircraft_info.get('type', 'N/A')}\n" \
                    f"Military: {'Yes' if aircraft_info.get('military', False) or is_military_aircraft(hex_code) else 'Unknown'}\n" \
                    f"Emergency: {aircraft_info.get('emergency', 'none')}\n"

    if send_email_notification(message_body):
        return
    if send_telegram_notification(message_body):
        return
    if send_pushover_notification(message_body):
        return
    if send_ifttt_notification(message_body):
        return
    if send_signal_notification(message_body):
        return
    print("All notification methods failed")
    exit()

# Function to check if aircraft is within the defined range and/or flagged for special attention
def check_aircraft(aircraft):
    hex_code = aircraft.get('hex')
    lat = aircraft.get('lat')
    lon = aircraft.get('lon')
    transponder_type = aircraft.get('type', 'N/A')
    military_flag = "Yes" if aircraft.get('military', False) or is_military_aircraft(hex_code) else "Unknown"
    emergency_flag = aircraft.get('emergency', 'none')
    flight = aircraft.get('flight', 'N/A')
    global skip_commercial
    global transponder_types
    global min_alert_period
    global hex_watch_list
    aircraft_owner = "Unknown"

    # Calculate distance and direction only if lat and lon are available
    if lat is not None and lon is not None:
        dist = haversine(your_lat, your_lon, lat, lon)
        direction = calculate_direction(your_lat, your_lon, lat, lon)
        current_time = time.time()
        
        print(f"Checking aircraft: Hex={hex_code}, Distance={dist:.2f}mi, "
              f"Transponder Type={transponder_type}, Callsign={flight}, "
              f"Military={military_flag}, Emergency={emergency_flag}.")

        # 1. Check if aircraft is within the defined range
        if dist > range_miles:
            print(f"Skipping aircraft hex {hex_code}: Distance={dist:.2f}mi is outside of notification range.\n\n")
            return

        # 2. Check if the hex code matches the watch list
        if hex_code in hex_watch_list:
            aircraft_owner = hex_watch_list[hex_code]
            if hex_code not in last_notified or (current_time - last_notified[hex_code]) > min_alert_period:
                send_notification(aircraft, hex_code, dist, direction, aircraft_owner)
                last_notified[hex_code] = current_time
            else:
                print(f"Skipping aircraft hex {hex_code}: Last alert sent {int((current_time - last_notified[hex_code]) / 60)} minutes ago.\n\n")
            return
        
        # 3. Check if the callsign matches the watch list
        for callsign in callsign_watch_list:
            if flight.startswith(callsign):
                if hex_code not in last_notified or (current_time - last_notified[hex_code]) > min_alert_period:
                    send_notification(aircraft, hex_code, dist, direction, aircraft_owner)
                    last_notified[hex_code] = current_time
                else:
                    print(f"Skipping aircraft hex {hex_code}: Last alert sent {int((current_time - last_notified[hex_code]) / 60)} minutes ago.\n\n")
                return

        # 4. Check if the emergency flag is set
        if (include_emergency_check and emergency_flag != 'none'):
            if hex_code not in last_notified or (current_time - last_notified[hex_code]) > min_alert_period:
                send_notification(aircraft, hex_code, dist, direction, aircraft_owner)
                last_notified[hex_code] = current_time
            else:
                print(f"Skipping aircraft hex {hex_code}: Last alert sent {int((current_time - last_notified[hex_code]) / 60)} minutes ago.\n\n")
            return

        # 5. Check if the callsign belongs to a commercial airline
        if skip_commercial == False:
            pass
        else:
            if flight.startswith((
                'AAL',  # American Airlines
                'AAY',  # Allegiant Air
                'ACA',  # Air Canada
                'AFR',  # Air France
                'AIC',  # Air India
                'AMX',  # Aeromexico
                'ANA',  # All Nippon Airways
                'ASA',  # Alaska Airlines
                'ASH',  # Mesa Airlines
                'ATN',  # Air Transport International (Cargo)
                'AWI',  # Air Wisconsin
                'BAW',  # British Airways
                'BTA',  # Envoy Air (formerly American Eagle)
                'CFG',  # Condor
                'CHQ',  # Chautauqua Airlines
                'CPA',  # Cathay Pacific
                'CRE',  # Corporate Air (Cargo)
                'CXK',  # Kalitta Charters (Cargo)
                'DAL',  # Delta Air Lines
                'DLH',  # Lufthansa
                'EIN',  # Aer Lingus
                'EJA',  # NetJets (Charter)
                'EJM',  # Executive Jet Management (Charter)
                'ENY',  # Envoy Air
                'ETD',  # Etihad Airways
                'EZY',  # easyJet
                'FDX',  # FedEx (Cargo)
                'FDY',  # Southern Airways Express
                'FFT',  # Frontier Airlines
                'GES',  # Gestair (Charter)
                'GJS',  # GoJet Airlines
                'ICE',  # Icelandair
                'JAL',  # Japan Airlines
                'JBU',  # JetBlue Airways
                'JIA',  # PSA Airlines
                'JRE',  # flyExclusive (Charter)
                'JSX',  # JetSuiteX (Charter)
                'JTL',  # Jet Linx Aviation (Charter)
                'JTZ',  # Nicholas Air (Charter)
                'KAL',  # Korean Air
                'KLM',  # KLM Royal Dutch Airlines
                'LOF',  # Trans States Airlines
                'LXJ',  # Flexjet (Charter)
                'LYM',  # Key Lime Air (Cargo/Regional)
                'MVJ',  # Marvel Air Services (Charter)
                'MXY',  # Breeze Airways
                'NKS',  # Spirit Airlines
                'PDT',  # Piedmont Airlines
                'QFA',  # Qantas
                'QXE',  # Horizon Air
                'RPA',  # Republic Airways
                'RYR',  # Ryanair
                'SAS',  # Scandinavian Airlines
                'SCX',  # Sun Country Airlines (Charter)
                'SIA',  # Singapore Airlines
                'SKW',  # SkyWest Airlines
                'SWA',  # Southwest Airlines
                'SWQ',  # Swift Air (Charter)
                'THA',  # Thai Airways
                'TSC',  # Air Transat
                'TWY',  # Solairus Aviation (Charter)
                'UAL',  # United Airlines
                'UAE',  # Emirates
                'UJC',  # Ultimate Jetcharters (Charter)
                'UPS',  # United Parcel Service (Cargo)
                'VIR',  # Virgin Atlantic
                'VJA',  # Vista America (Charter)
                'VOI',  # Volaris
                'VRD',  # Virgin America (now merged with Alaska Airlines)
                'WJA',  # WestJet
                'XSR'   # Executive AirShare (Charter)
            )):
                print(f"Skipping aircraft hex {hex_code}: Commercial airline.\n\n")
                return

        # 6. Check if the hex code or flag indicates military
        if (include_military_check and (aircraft.get('military', False) or is_military_aircraft(hex_code))):
            if hex_code not in last_notified or (current_time - last_notified[hex_code]) > min_alert_period:
                send_notification(aircraft, hex_code, dist, direction, aircraft_owner)
                last_notified[hex_code] = current_time
            else:
                print(f"Skipping aircraft hex {hex_code}: Last alert sent {int((current_time - last_notified[hex_code]) / 60)} minutes ago.\n\n")
            return
        
        # 7. Check the transponder type
        if transponder_type in transponder_types:
            if hex_code not in last_notified or (current_time - last_notified[hex_code]) > min_alert_period:
                send_notification(aircraft, hex_code, dist, direction, aircraft_owner)
                last_notified[hex_code] = current_time
            else:
                print(f"Skipping aircraft hex {hex_code}: Last alert sent {int((current_time - last_notified[hex_code]) / 60)} minutes ago.\n\n")
        else:
            print(f"Skipping aircraft hex {hex_code}: Does not match required transponder type.\n\n")
    else:
        print(f"Checking aircraft: Hex={hex_code}\n Skipping aircraft hex {hex_code}: Missing lat/lon data.\n\n")

# Fetch data from your local ADSBExchange server aircraft.json 
def fetch_aircraft_data():
    global aircraft_json_path
    global home_dir_check
    try:
        file_path = aircraft_json_path
        with open(file_path, 'r') as f:
            aircraft_data = json.load(f)
            for aircraft in aircraft_data.get('aircraft', []):
                check_aircraft(aircraft)

        # Check for aircrafts.json using the home_dir_check variable
        with open(home_dir_check, 'r') as f:
            aircrafts_data = json.load(f)
            # Process aircrafts_data as needed, if it will be used elsewhere
    except FileNotFoundError:
        print(f"File not found: {file_path} or {aircrafts_file_path}")
    except json.JSONDecodeError:
        print("Error decoding JSON response")


# Function to run the script based on user defined update rate
def run_script():
    while True:
        global update_rate
        start_time = time.time()
        aircrafts_age_check()
        fetch_aircraft_data()
        elapsed_time = time.time() - start_time
        time.sleep(max(update_rate - elapsed_time, 0))

if __name__ == "__main__":
    run_script()
