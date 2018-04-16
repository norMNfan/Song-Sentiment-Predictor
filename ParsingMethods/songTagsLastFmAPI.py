#API call to Last.fm to obtain songs given a certain tag
import requests
import json

limit = 400
tagCats = ["hurt","anger","funny","happy","calm","inspirational","romantic"]
api_key = "Insert_API_Key_Here"

#Write Data - where we store data
wData = {}

for tag in tagCats:
    wData[tag] = []
    response = requests.get("http://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag="+str(tag)+"&api_key="+api_key+"&format=json&limit="+str(limit))
    data = response.json()
    for i in range(limit):
        song = data["tracks"]["track"][i]
        songName = song["name"]
        artist = song["artist"]["name"]

        #Write to wData
        wData[tag].append({
            'Title': songName,
            'Artist' : artist
            })
            
#Write to output file 'data.txt'
with open('data.txt', 'w') as outfile:
    json.dump(wData, outfile, indent=4)        
    
