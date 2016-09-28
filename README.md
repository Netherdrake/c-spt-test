## Install Anaconda with Python 3.5 64bit
https://www.continuum.io/downloads

## Clone the repo
git clone https://github.com/cshrem/SteemPowerTrail
cd SteemPowerTrail

## Install requirements
pip install -r requirements.txt

## Add private posting keys to Piston wallet
piston addkey 5.....

## Edit config.json.
Example:
```
{
	"author_subscriptions": ["curie"],
	"voter_subscriptions": ["curie"],
	"reserve_voting_power": 90,
	"sim_mode": false
}
```

Notes:  
If `sim_mode` is true, the bot won't actually vote. It will just run as a simulation.

## Run the script
UNLOCK=piston_wallet_password
python autovote.py