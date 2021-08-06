# Hanime auto coin collector
Hanime mobile app gives some coins as reward on clicking an ad. This has a timeout of 3 hours. It gets really annoying to open the app every 3 hours to click on an ad. 

This script when run, will forge a request to the server claiming that you have clicked on the ad. The server then adds the coins to your account. It still checks the last clicked time, so you can only run this once every 3 hours. But this makes it easier to automate getting coins, just set a cronjob that'll execute the script periodically every 3 hours.

Tested on current version 3.6.7

## Usage
* Clone this repository 
* Open credentials.txt and enter your hanime email and password
* Run the script.

If you get any errors or need any help, feel free to open an issue.

## How does it work?
(will be added soon)
