#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pushbullet import Pushbullet
import requests
import json
import sys
import os

### Get the config data from "config.cfg" file in same folder ###
def get_config():
	if os.path.isfile("config.cfg"):
		config_data = json.load(open("config.cfg"))
		api_key = config_data["api_key"]
		client_id = config_data["client_id"]
		oauth = config_data["oauth"]
		return api_key, client_id, oauth
	else:
		cfg = {"api_key":"",
			   "client_id": "",
			   "oauth": ""}
		json.dump(cfg, open("config.cfg", "w"))

### Send a pushbullet notification with streamer and game ###
def send_notification(streamer, game):
	pb.push_note("Twitch Notify", "{0} is now playing {1}.".format(streamer, game))

### Access Twitch Api to check if the game has changed ###
def check_stream(streamer, client_id, url, oauth):
	headers = {
		"Accept": "application/vnd.twitchtv.v3+json",
		"client_id": client_id,
		"Authorization": "OAuth {0}".format(oauth)
	}
	new_url = url + streamer
	### Request json about the streamer ###
	data = requests.get(new_url, headers=headers)
	### Check the responses status code and act accordingly ###
	if data.status_code != 200:
		print "Bad response code: {0}".format(data.status_code)
		sys.exit()
	else:
		data = data.json()
	### Parse the json from the response ###
	if data["stream"] != None:
		now_playing = data["stream"]["game"]
		### If the game currently played is different than the one stored, send notification ###
		if now_playing != json.load(open("game.json"))["game"]:
			json.dump({"game": now_playing}, open("game.json", "w"), indent=4)
			send_notification(streamer, now_playing)

if __name__ == "__main__":
	### Url to Twitch API (see https://github.com/justintv/Twitch-API) ###
	url = "http://api.twitch.tv/kraken/streams/"
	api_key, client_id, oauth = get_config()
	pb = Pushbullet(api_key)
	check_stream("lirik", client_id, url, oauth)