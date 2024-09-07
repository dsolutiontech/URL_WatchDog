![UptimeMonitor](https://github.com/user-attachments/assets/8c9fbfd7-c37f-479f-aa4b-503ea61ab96a)
### URL WatchDog Script
This script is a monitoring script that checks the status of multiple websites and sends notifications to WhatsApp when a website's status changes. Here's a breakdown of what the script does:

1. It loads environment variables from a `.env` file and sets up logging using Python's built-in `logging` module.
2. It defines a function to send a message to WhatsApp using the WhatsApp `GREEN API`.
3. It reads the configuration for the websites to monitor from a JSON file (`websites_config.json`).
4. It defines several helper functions to:
	* Ping a host using the `IMCP ping` command
	* Check if a website is up by checking its `response code` and `keyword` presence in the response text
	* Perform a `TCP ping` (connect to a host and port)
5. The main loop of the script iterates over the list of websites to monitor. For each website:
	* It checks if the website is up or down using one of the helper functions (`ping`, `TCP ping`, or `keyword check`)
	* It logs the result to a log file
	* If the website's status has changed, it sends a notification to WhatsApp using the WhatsApp API
6. The script also sets up signal handlers for SIGTERM and SIGINT signals, which will send a notification to WhatsApp when the script is terminated or interrupted.

The script runs indefinitely, sleeping for 30 seconds between iterations.

### Installing `python3` and `dotenv`

`sudo apt update`

`sudo apt install python3`

`sudo apt install python3-pip`

`pip3 install requests python-dotenv`

### Starting script at boot
`sudo crontab -e`

**Add this line to the bottom of the file**

`@reboot /usr/bin/python3 path/to/your/script/url_watchdog.py`

### How to terminate the script?
`sudo kill $(pgrep -f "path/to/your/script/url_watchdog.py")`

**Example:**

`sudo kill $(pgrep -f "home/dsolutiontech/URL_WatchDog/url_watchdog.py")`
