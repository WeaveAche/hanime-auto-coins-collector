# Hanime auto coin collector
Hanime mobile app gives some coins as reward on clicking an ad. This has a timeout of 3 hours. It gets really annoying to open the app every 3 hours to click on an ad. 

This script when run, will forge a request to the server claiming that you have clicked on the ad. The server then adds the coins to your account. It still checks the last clicked time, so you can only run this once every 3 hours. But this makes it easier to automate getting coins, just set a cronjob that'll execute the script periodically every 3 hours.

Tested on current version 3.7.1

## Usage
1. Clone this repository 
2. Install all the requirements:
`pip install -r requirements.txt`
3. Open `.env` file and enter your hanime email and password
4. Run the script.

If you get any errors or need any help, feel free to open an issue.

## How does it work?
When we observe the requests made by the app to it's server, we'll see that, to get coins the app makes a request containing a reward token. The server then validates the reward token and gives us the coins. The token is generated on the client side somewhere when you click on an ad.

What we'd like to do is directly send this request through a script without ever clicking on an ad. So we want to reverse engineer the app a bit to understand how this token is generated.

Hanime app is based on react native framework. So the main logic of the program is mostly written in javascript. Decompiling the apk we get the minified javascript. We quickly find the token generation mechanism. The token is just a SHA-256 hash of a dynamically generated string concatenated with the current time. The server verifies if the hash matches and checks whether if 3 hours have passed since last click on ad.

We can generate random tokens now, but when we try sending this request we get an 
```
{"errors":["Unauthorized"]}
```
in response. On inspection of actual requests made by the app, we see that it includes headers called `X-Claim, X-Signature`. These are probably used to verify whether if the request comes from the actual app or a script like this one. `X-Claim` is just the current time in epoch time standard. But some reversing is required to know how is `X-Signature` generated. 

This time the signature wasn't generated in the javascript code, but inside the react native modules in java. Again the signature turned out to be SHA-256 hash of a dynamically generated string based on current time. 

After this we can include these headers in our request each time to make fake requests.