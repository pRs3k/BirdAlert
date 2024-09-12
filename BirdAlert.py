#!/usr/bin/env python3

import smtplib
import json
import time
import requests
from math import radians, cos, sin, asin, sqrt, atan2, degrees

#################################################################################

# Script behavior
update_rate = 5                                    # The frequency that this script runs checking for aircraft updates, in seconds
aircraft_json_path = "/run/readsb/aircraft.json"   # Change this if your aircraft.json is in a different location
range_miles = 20                                   # Change this to the radius of the notification zone (in miles)
min_alert_period = 600                             # Change this to the number of seconds to wait before alerting again for the same aircraft
include_military_check = True                      # Change to False if you don't want to alert based on the military flag being set or the hex falling within the military range  (True will alert regardless of other settings)
include_emergency_check = True                     # Change to False if you don't want to alert based on the emergency flag being set (True will alert regardless of other settings)
skip_commercial = True                             # Change to False to include alerts for commerical aircraft (doesn't effect notificaitons for emergency flag being set)
transponder_types = [                              # Comment in/out rows corresponding to transponder types you want to receive alerts for
    'adsb_icao',                                   # Mode S or ADS-B transponder
#    'adsb_icao_nt',                                # ADS-B equipped “non-transponder” emitter, such as a ground vehicle
    'adsr_icao',                                   # Rebroadcast of ADS-B messages originally sent via UAT transponder
    'tisb_icao',                                   # Non-ADS-B aircraft
    'adsc',                                        # Automatic Dependent Surveillance-Contract received by monitoring satellite downlinks
    'mlat',                                        # Multilateration position calculated using arrival time differences from multiple receivers
    'mode_s',                                      # Mode S transponder (no position transmitted)
    'adsb_other',                                  # ADS-B transponder using a non-ICAO address, such as an anonymized address
    'adsr_other',                                  # Rebroadcast of ADS-B messages originally sent via UAT transponder, using a non-ICAO address
    'tisb_other',                                  # Non-ADS-B target using a non-ICAO address
]

watch_list = [                                     # Add the hex codes of specific aircraft to always alert on
    'a2575b', #B-25J Mitchell "Yellow Rose"
    'a082d8' #C-130 firefighting
    'a69072' #DC-10 firefighting   
    'a1a640' #UH-1 firefighting
    'a4bf3d' #CH-47 firefighting
    'a1a640' #UH-1 firefighting
    'a270c6' #DC-3 firefighting
]

# Your location
your_lat = latitude_here  # change this to the latitude of the notification zone
your_lon = longitude_here  # change this to the longitude of the notification zone

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

#################################################################################

# Tracking last notification times
last_notified = {}


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
    dlon = lon2 - lon1
    y = sin(dlon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    initial_bearing = atan2(y, x)
    initial_bearing = degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    directions = ["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West"]
    idx = round(compass_bearing / 45) % 8
    return directions[idx]

# Function to send an email notification
def send_email_notification(aircraft_info, hex_code, distance, direction):
    subject = "Bird Alert!"
    military_status = "Yes" if aircraft_info.get('military', False) or is_military_aircraft(hex_code) else "Unknown"
    ground_speed = aircraft_info.get('gs', 'N/A')
    emergency_status = aircraft_info.get('emergency', 'none')

    message = f"Subject:{subject}\n\n" \
              f"Aircraft hex: {hex_code}\n Distance: {distance:.2f}mi\n Direction: {direction}\n" \
              f"Transponder: {aircraft_info.get('type', 'N/A')}\n Callsign: {aircraft_info.get('flight', 'N/A')}\n" \
              f"Military: {military_status}\n Ground Speed: {ground_speed} knots\n" \
              f"Emergency: {emergency_status}\n"

    try:
        with smtplib.SMTP(your_smtp_server, your_smtp_port) as server:
            server.starttls()
            server.login(your_email, your_email_app_password)
            server.sendmail(your_email, your_email, message)
            print(f"Sending Email: {message}\n")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}\n")
        return False

# Function to send a Telegram notification
def send_telegram_notification(message):
    if not telegram_bot_token or not telegram_chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": message
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
def send_pushover_notification(message):
    if not pushover_user_key or not pushover_app_token:
        return False

    url = "https://api.pushover.net/1/messages.json"
    payload = {
        "token": pushover_app_token,
        "user": pushover_user_key,
        "message": message
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
def send_ifttt_notification(message):
    if not ifttt_webhook_event or not ifttt_webhook_key:
        return False

    url = f"https://maker.ifttt.com/trigger/{ifttt_webhook_event}/with/key/{ifttt_webhook_key}"
    payload = {"value1": message}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("IFTTT notification sent\n")
        return True
    except Exception as e:
        print(f"Failed to send IFTTT notification: {e}\n")
        return False

# Function to send a Signal notification
def send_signal_notification(message):
    if not signal_phone_number or not signal_recipients:
        return False

    try:
        for recipient in signal_recipients:
            # Replace with actual Signal command or API call to send a message
            print(f"Sending Signal message to {recipient}: {message}\n")
        return True
    except Exception as e:
        print(f"Failed to send Signal message: {e}\n")
        return False

# Function to send notifications through all available methods
def send_notification(aircraft_info, hex_code, distance, direction):
    message = f"Bird Alert!\n" \
              f"Aircraft hex: {hex_code}\n Distance: {distance:.2f}mi\n Direction: {direction}\n" \
              f"Transponder: {aircraft_info.get('type', 'N/A')}\n Callsign: {aircraft_info.get('flight', 'N/A')}\n" \
              f"Military: {'Yes' if aircraft_info.get('military', False) or is_military_aircraft(hex_code) else 'Unknown'}\n" \
              f"Ground Speed: {aircraft_info.get('gs', 'N/A')} knots\n" \
              f"Emergency: {aircraft_info.get('emergency', 'none')}\n"

    if send_email_notification(aircraft_info, hex_code, distance, direction):
        return
    if send_telegram_notification(message):
        return
    if send_pushover_notification(message):
        return
    if send_ifttt_notification(message):
        return
    if send_signal_notification(message):
        return
    print("All notification methods failed")

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
    global watch_list

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
        if hex_code in watch_list:
            if hex_code not in last_notified or (current_time - last_notified[hex_code]) > min_alert_period:
                send_notification(aircraft, hex_code, dist, direction)
                last_notified[hex_code] = current_time
            else:
                print(f"Skipping aircraft hex {hex_code}: Last alert sent {int((current_time - last_notified[hex_code]) / 60)} minutes ago.\n\n")
            return

        # 3. Check if the emergency flag is set
        if (include_emergency_check and emergency_flag != 'none'):
            if hex_code not in last_notified or (current_time - last_notified[hex_code]) > min_alert_period:
                send_notification(aircraft, hex_code, dist, direction)
                last_notified[hex_code] = current_time
            else:
                print(f"Skipping aircraft hex {hex_code}: Last alert sent {int((current_time - last_notified[hex_code]) / 60)} minutes ago.\n\n")
            return

        # 4. Check if the callsign belongs to a commercial airline
        if skip_commercial == False:
            pass
        else:
            if flight.startswith((
                'AAL',  # American Airlines
                'AAY',  # Allegiant Air
                'ACA',  # Air Canada
                'AFR',  # Air France
                'AIC',  # Air India
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
                'JAL',  # Japan Airlines
                'JBU',  # JetBlue Airways
                'JIA',  # PSA Airlines
                'JSX',  # JetSuiteX (Charter)
                'JTL',  # Jet Linx Aviation (Charter)
                'KAL',  # Korean Air
                'KLM',  # KLM Royal Dutch Airlines
                'LOF',  # Trans States Airlines
                'LXJ',  # Flexjet (Charter)
                'LYM',  # Key Lime Air (Cargo/Regional)
                'MVJ',  # Marvel Air Services (Charter)
                'MXY',  # Breeze Airways
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
                'UAL',  # United Airlines
                'UAE',  # Emirates
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

        # 5. Check if the hex code or flag indicates military
        if (include_military_check and (aircraft.get('military', False) or is_military_aircraft(hex_code))):
            if hex_code not in last_notified or (current_time - last_notified[hex_code]) > min_alert_period:
                send_notification(aircraft, hex_code, dist, direction)
                last_notified[hex_code] = current_time
            else:
                print(f"Skipping aircraft hex {hex_code}: Last alert sent {int((current_time - last_notified[hex_code]) / 60)} minutes ago.\n\n")
            return
        
        # 6. Check the transponder type
        if transponder_type in transponder_types:
            if hex_code not in last_notified or (current_time - last_notified[hex_code]) > min_alert_period:
                send_notification(aircraft, hex_code, dist, direction)
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
    try:
        file_path = aircraft_json_path
        with open(file_path, 'r') as f:
            aircraft_data = json.load(f)
            for aircraft in aircraft_data.get('aircraft', []):
                check_aircraft(aircraft)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print("Error decoding JSON response")

# Function to run the script based on user defined update rate
def run_script():
    while True:
        global update_rate
        start_time = time.time()
        fetch_aircraft_data()
        elapsed_time = time.time() - start_time
        time.sleep(max(update_rate - elapsed_time, 0))

if __name__ == "__main__":
    run_script()
