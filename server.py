#!/usr/bin/env python3
# See https://docs.python.org/3.2/library/socket.html
import socket, os, time, datetime, stat, sys, json, string, re

from threading import Thread
from argparse import ArgumentParser
from pathlib import Path
from PyLyrics import *
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

nltk.download('punkt')
nltk.download('stopwords')

BUFSIZE = 4096
DEBUG = False

CRLF = '\r\n'
OK = 'HTTP/1.1 200 OK' + CRLF
CREATED = 'HTTP/1.1 201 Created' + CRLF
NOT_FOUND = 'HTTP/1.1 404 NOT FOUND' + CRLF + 'Connection: close' + CRLF

class HTTPServer:
  def __init__(self, host, port):
    print('listening on port {}'.format(port))
    self.host = host
    self.port = port

    self.setup_socket()

    self.accept()

    self.sock.shutdown()
    self.sock.close()

  def setup_socket(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.bind((self.host, self.port))
    self.sock.listen(128)

  def accept(self):
    while True:
      (client, address) = self.sock.accept()
      th = Thread(target=self.accept_request, args=(client, address))
      th.start()
      
  def accept_request(self, client_sock, client_address):
    print('talking to {}'.format(client_address))
    data = client_sock.recv(BUFSIZE)
    request = data.decode('utf-8')
    response = self.process_request(request)
    client_sock.send(bytes(response, 'utf8'))
    client_sock.shutdown(1)
    client_sock.close()
    
  def parse_request(self, data):
    method = data.split()[0].split(" ")[0]
    content = data.split()[-1]
    try:
      resource = data.split("\n")[0].split(" ")[1]
      try:
        file_type = resource.split(".")[1]
      except:
        file_type = u'html'
    except:
      resource = u''
    date_time = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S.%f")
    
    return method, content, resource, file_type, date_time
    
  def process_request(self, data):
    # parse request
    if DEBUG: print("###### REQUEST BODY ######\n\n" + data + "###################\n")
    (method, content, resource, file_type, date_time) = self.parse_request(data)
    
    if(method == "GET"):
      return self.process_GET(content, resource, file_type, date_time)
      
    elif(method == "POST"):
      return self.process_POST(content, resource, file_type, date_time)
      
    else:
      return NOT_ALLOWED
      
  def process_GET(self, content, resource, file_type, date_time):
    print("GET " + resource)
    response = u''
    if resource == "/" or resource == "/extractData.html":
      response += OK
      response += 'Content-Length: ' + str(len(self.read_file("client/extractData.html").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += self.read_file("client/extractData.html")
      
    elif resource == "/displayData.html":
      response += OK
      response += 'Content-Length: ' + str(len(self.read_file("client/displayData.html").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += self.read_file("client/displayData.html")
    
    elif file_type == "css":
      response += OK
      response += 'Content-Length: ' + str(len(self.read_file("client/css/style.css").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += self.read_file("client/css/style.css")
      
    elif file_type == "js":
      response += OK
      response += 'Content-Length: ' + str(len(self.read_file("client/js/script.js").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += self.read_file("client/js/script.js")
	
    return response
	
  def process_POST(self, content, resource, file_type, date_time):

    if resource == "/getArtistInfo":
		
      artist = content.split('&')[0].split('=')[1].replace('+', ' ').replace('%20', ' ')
      track_name = content.split('&')[1].split('=')[1].replace('+', ' ').replace('%27', "'")
      tag = content.split('&')[2].split('=')[1].replace('+', ' ')
      print(artist + " " + track_name + " " + tag)
    
      # Add artist lyrics
      addArtistLyrics(artist, track_name, tag)
      
    if resource == "/clusterLyrics":
      clusterLyrics()
	  
    response = u''
    
    response += OK
    response += 'Content-Length: ' + str(len(self.read_file("client/extractData.html").encode('utf-8'))) + CRLF
    response += 'Content-Type: text/' + file_type + '\n' + CRLF
    response += self.read_file("client/extractData.html")
    
    return response
	
  def read_file(self, resource):
    with open(resource, "r") as f:
      return f.read()
      
  def write_file(self, resource, content):
    with open(resource, "w") as f:
      f.write(content)
      os.chmod(resource, 646)
    
  def file_exists(self, resource):
    my_file = Path(resource)
    return my_file.is_file()
  
def clusterLyrics():
  with open("Data/lyrics.json") as f:
    json_data = json.load(f)
    
  track_dict = {}
  
  num_clusters = 0
  all_stems = []
  
  for artist in json_data["artists"]:
    num_clusters = num_clusters + 1
    for track in artist["tracks"]:
      track_dict[track["track"]] = track["lyrics"]
      stems = tokenize(track["lyrics"])
      for stem in stems:
        if stem not in all_stems:
          all_stems.append(stem)
      
  print(all_stems) 
      
  tfidf = TfidfVectorizer(tokenizer=tokenize, stop_words='english')
  tfs = tfidf.fit_transform(track_dict.values())
  print(tfs.shape)
  
  kmeans = KMeans(n_clusters=num_clusters, random_state=0).fit(tfs)
  clusters = kmeans.labels_.tolist()
  print(clusters)
  
  centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
  print(centroids)
  for i in range(num_clusters):
    print("Cluster %d words:" % i, end='')
    
    for ind in centroids[i, :6]: #replace 6 with n words per cluster
        print(' %s' % vocab_frame.ix[terms[ind].split(' ')].values.tolist()[0][0].encode('utf-8', 'ignore'), end=',')

# Add artists lyrics to lyrics.json
def addArtistLyrics(artist, track_name, tag):
	
  # check if file exists
  my_file = Path("Data/lyrics.json")
  if not my_file.is_file():
    open("Data/lyrics.json", 'a').close()
  
  # check if file is empty
  if os.stat("Data/lyrics.json").st_size == 0:
    data = '{ "artists": [] }'
    with open("Data/lyrics.json", "w+") as f:
      f.write(data)

  # read current json file
  with open("Data/lyrics.json", "r") as f:
    json_data = json.load(f)
	
  artist_exists = False
  track_exists = False
	
  # check if artist already exists
  for x in json_data["artists"]:
    if x["name"] == artist:
      artist_exists = True
      for track in x["tracks"]:
        if track["track"] == track_name:
          track_exists = True

  if track_exists:
    print("track already exists")
    return
	  
  # Add artist if it doesn't exist
  if not artist_exists:
    json_data["artists"].append({
      "name": artist,
      "tracks": []
    })
    
  artist_index = 0
  counter = 0
	
  # find index of artist in json_data
  for x in json_data["artists"]:
    if x["name"] == artist:
      artist_index = counter
    counter = counter + 1
    
  # get all albums
  albums = PyLyrics.getAlbums(singer=artist)
  album_index = 0
  
  found_track = False
  
  # iterate through albums
  for album in albums:
	  
    # get all tracks for album
    album_tracks = album.tracks()
    
    #iterate through tracks
    for track in album_tracks:
      if(track_name.lower() == track.name.lower()):
        found_track = True
        lyrics = track.getLyrics()
        lyrics = ' '.join(tokenize(lyrics))
        
  if found_track: 
    json_data["artists"][artist_index]["tracks"].append({
      "track": track_name,
      "lyrics": lyrics,
      "tag": tag
    })  
    print("*** ADDED TRACK ***")
  else:
    print("could not find track")
	
  # open file to write to
  with open("Data/lyrics.json", "w+") as f:
    json.dump(json_data, f, indent=4)

def tokenize(text):
  if not text:
    return ""
  text = text.lower()
  for i in set(string.punctuation+'\n'+'\t'):
    text = text.replace(i, ' ')
  for i in range(0,10):
    text = text.replace('  ', ' ')
  text = text.translate(string.punctuation)
  word_tokens = nltk.word_tokenize(text)
  stop_words = set(nltk.corpus.stopwords.words("english"))
  tokens = [w for w in word_tokens if not w in stop_words]
  tokens = (token for token in tokens if re.match('[0-9]+', token) is None)
    
  stemmer = nltk.stem.PorterStemmer()
  stems = []
  for i in tokens:
    stems.append(stemmer.stem(i))
  return stems

def parse_args():
  parser = ArgumentParser()
  parser.add_argument('--host', type=str, default='localhost',
                      help='specify a host to operate on (default: localhost)')
  parser.add_argument('-p', '--port', type=int, default=9001,
                      help='specify a port to operate on (default: 9001)')
  args = parser.parse_args()
  return (args.host, args.port)

if __name__ == '__main__':
  (host, port) = parse_args()
  HTTPServer(host, port)

