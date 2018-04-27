#!/usr/bin/env python3
# See https://docs.python.org/3.2/library/socket.html
import socket, os, time, datetime, stat, sys, json, string, re

from threading import Thread
from argparse import ArgumentParser
from pathlib import Path
import lyricwikia
import nltk
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cross_validation import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn import metrics
import numpy as np

#nltk.download('punkt')
#nltk.download('stopwords')

BUFSIZE = 4096
DEBUG = False

CRLF = '\r\n'
OK = 'HTTP/1.1 200 OK' + CRLF
CREATED = 'HTTP/1.1 201 Created' + CRLF
NOT_FOUND = 'HTTP/1.1 404 NOT FOUND' + CRLF + 'Connection: close' + CRLF

"""
Class for starting server
Internals not important!
"""
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
    #print('talking to {}'.format(client_address))
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
    #if DEBUG: print("###### REQUEST BODY ######\n\n" + data + "###################\n")
    (method, content, resource, file_type, date_time) = self.parse_request(data)
    
    if(method == "GET"):
      return self.process_GET(content, resource, file_type, date_time)
      
    elif(method == "POST"):
      return self.process_POST(content, resource, file_type, date_time)
      
    else:
      return NOT_ALLOWED
      
  def process_GET(self, content, resource, file_type, date_time):
    #print("GET " + resource)
    response = u''
    if resource == "/" or resource == "/extractData.html":
      response += OK
      response += 'Content-Length: ' + str(len(read_file("client/extractData.html").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += read_file("client/extractData.html")
    
    elif file_type == "css":
      response += OK
      response += 'Content-Length: ' + str(len(read_file("client/css/style.css").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += read_file("client/css/style.css")
      
    elif file_type == "js":
      response += OK
      response += 'Content-Length: ' + str(len(read_file("client/js/script.js").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += read_file("client/js/script.js")
	
    return response
	
  def process_POST(self, content, resource, file_type, date_time):

    if resource == "/predictSong":

      artist = content.split('&')[0].split('=')[1].replace('+', ' ').replace('%20', ' ')
      song = content.split('&')[1].split('=')[1].replace('+', ' ').replace('%27', "'")
      print(artist + " " + song)
    
      # Add artist lyrics
      return predictSong(artist, song)
      
    if resource == "/classifyLyrics":
      classifyLyrics()
      
    if resource == '/gatherLyrics':
      gatherLyrics()
      
    else:
	  
      response = u''
      response += OK
      response += 'Content-Length: ' + str(len(read_file("client/extractData.html").encode('utf-8'))) + CRLF
      response += 'Content-Type: text/' + file_type + '\n' + CRLF
      response += read_file("client/extractData.html")
    
      return response
	
"""
Help function for reading files
"""
def read_file(resource):
  with open(resource, "r") as f:
    return f.read()
  
"""
Helper function for writing to files
"""   
def write_file(resource, content):
  with open(resource, "w") as f:
    f.write(content)
    os.chmod(resource, 646)
"""
Helper function to check if file exists
""" 
def file_exists(resource):
  my_file = Path(resource)
  return my_file.is_file()

"""
Read in data from known songs/sentiment
Only do this once!
"""
def gatherLyrics():
  with open("Data/ground.json") as g:
    ground_data = json.load(g)
  
  for tagName in ground_data:
    print(tagName)
    for song in ground_data[tagName]:
      #print(song['Artist'] + " " + song['Title'])
      addArtistLyrics(song['Artist'], song['Title'], tagName)

"""
Classify song lyrics based on Naive Bayes(NB) and Support Vector Model(SVM)
print the recall, precision and f1-score of each model
Iterate 100 times and find the average accuracy between the two models
"""
def classifyLyrics():
  with open("Data/lyrics.json") as f:
    json_data = json.load(f)
  
  all_data = []
  all_labels = []
  
  train_data = []
  train_labels = []
  
  test_data = []
  test_labels = []
  
  # Read all lyrics int memory
  for track in json_data["songs"]:
    all_data.append(track["lyrics"])
    all_labels.append(getTagNumber(track["tag"]))
    
  iterations = 100
  avg_pred_NB = avg_pred_SVM = 0
    
  for x in range(0,iterations):
	  
    # Split data into train and test data
    train_data, test_data, train_labels, test_labels = train_test_split(all_data, all_labels, test_size = 0.2)
  
    print("*************************************************")
    print("********************* NB ************************")
    print("*************************************************")
  
    # Create pipeline: data => tokens => tfidf model => NB classifer
    text_clf_NB = Pipeline([('vect', CountVectorizer()),
                         ('tfidf', TfidfTransformer()),
                         ('clf', MultinomialNB())
    ])
  
    # Create Naive Bayes (NB) classifier for training data
    text_clf_NB.fit(train_data, train_labels)
    
    # Predict test data
    predicted = text_clf_NB.predict(test_data)
    
    # Calculate how much of the test data we predicted correctly
    predictions_NB = np.mean(predicted == test_labels)
    
    avg_pred_NB += predictions_NB
    print(predictions_NB)
    print(metrics.classification_report(test_labels, predicted))
  
    print("*************************************************")
    print("******************** SVM ************************")
    print("*************************************************")
  
    # Create pipeline: data => tokens => tfidf model => SVM classifier
    text_clf_SVM = Pipeline([('vect', CountVectorizer()),
                         ('tfidf', TfidfTransformer()),
                         ('clf', SGDClassifier(loss='hinge',
                                               alpha=1e-3, random_state=42)),
    ])
  
    # Create Support Vector Machine (SVM) classifier for training data
    text_clf_SVM.fit(train_data, train_labels)
    
    # Predict test data
    predicted = text_clf_SVM.predict(test_data)
    
    # Calculate how much of the test data we predicted correctly
    predictions_SVM = np.mean(predicted == test_labels)
    
    avg_pred_SVM += predictions_SVM
    print(predictions_SVM)
    print(metrics.classification_report(test_labels, predicted))
    
  avg_pred_NB = avg_pred_NB * 100 / iterations
  avg_pred_SVM = avg_pred_SVM * 100 / iterations
    
  print("NB " + str(avg_pred_NB) + " % correct")
  print("SVM " + str(avg_pred_SVM) + " % correct")

"""
Predicts the sentiment of a song based on its lyrics
Creates an SVM and then classifies the song
Returns the accutacy % along with the classification
"""
def predictSong(artist, song):
  with open("Data/lyrics.json") as f:
    json_data = json.load(f)
    
  # Try to extract lyrics from lyricwikia (the API can be finicky)
  try:
    lyrics = lyricwikia.get_lyrics(artist,song)
    lyrics = " ".join(tokenize(lyrics))
        
    all_data = []
    all_labels = []
  
    train_data = []
    train_labels = []
    test_data = []
    test_labels = []
  
    # Read all lyrics into memory
    for track in json_data["songs"]:
      all_data.append(track["lyrics"])
      all_labels.append(getTagNumber(track["tag"]))
    
    # Split data into train and test data
    train_data, test_data, train_labels, test_labels = train_test_split(all_data, all_labels, test_size = 0.2)
  
    # Create pipeline: data => tokens => tfidf model => SVM classifier
    # We use SVM instead of NB because on average
    # NB accuracy: 35.5 %
    # SVM accuracy: 41.5 %
    text_clf_SVM = Pipeline([('vect', CountVectorizer()),
                         ('tfidf', TfidfTransformer()),
                         ('clf', SGDClassifier(loss='hinge',
                                               alpha=1e-3, random_state=42)),
    ])
  
    # Create Support Vector Machine (SVM) classifier for training data
    text_clf_SVM.fit(train_data, train_labels)
    
    # Predict test data
    predicted = text_clf_SVM.predict(test_data)
    
    # Calculate how much of the test data we predicted correctly
    predictions_SVM = np.mean(predicted == test_labels)
         
    # Predict song
    new_song = []
    new_song.append(lyrics)
    new_song_prediction = text_clf_SVM.predict(new_song)
    
    # Print output
    print(getTagName(new_song_prediction))
    print("Accuracy of: " + str(predictions_SVM) + " %")
    
    # Form return message
    message = "sentiment: " + getTagName(new_song_prediction)
    message += " Accuracy of: " + str(predictions_SVM) + " %\n"
      
    response = ''
    response += OK
    response += 'Content-Length: ' + str(len(message)) + CRLF
    response += 'Content-Type: text/html'  + '\n' + CRLF
    response += message
    return response
     
  # If we weren't able to extract the lyrics from lyricwikia API
  except:
    response = ''
    response += OK
    response += 'Content-Length: ' + str(len("Could not find song")) + CRLF
    response += 'Content-Type: text/html'  + '\n' + CRLF
    response += "Could not find song"
    return response

# map tag # to tag name
def getTagNumber(tagName):
  return {
    'happy': 0,
    'anger': 1,
    'funny': 2,
    'hurt': 3,
    'calm': 4,
    'romantic': 5,
    'inspirational': 6,
  }[tagName]
  
# map tag name to tag #
def getTagName(tagNumber):
  if tagNumber == 0:
    return 'happy'
  elif tagNumber == 1:
    return 'anger'
  elif tagNumber == 2:
    return 'funny'
  elif tagNumber == 3:
    return 'hurt'
  elif tagNumber == 4:
    return 'calm'
  elif tagNumber == 5:
    return 'romantic'
  elif tagNumber == 6:
    return 'inspirational'

"""
Used for collecting data
Adds an artist, song, and tag into lyrics.json
"""
# Add artists lyrics to lyrics.json
def addArtistLyrics(artist, song, tag):
	
  # check if file exists
  my_file = Path("Data/lyrics.json")
  if not my_file.is_file():
    open("Data/lyrics.json", 'a').close()
  
  # check if file is empty
  if os.stat("Data/lyrics.json").st_size == 0:
    data = '{ "songs": [] }'
    with open("Data/lyrics.json", "w+") as f:
      f.write(data)

  # read current json file
  with open("Data/lyrics.json", "r") as f:
    json_data = json.load(f)
    
  for song in json_data["songs"]:
    if song["track"] == song and song["artist"] == artist:
      print("song already saved!")
      return
    
  try:
    lyrics = lyricwikia.get_lyrics(artist,song)
    if lyrics != "instrument":
      lyrics = " ".join(tokenize(lyrics))
      #print(lyrics)
      print("*** ADDED TRACK ***")
      json_data["songs"].append({
        "artist": artist,
        "track": song,
        "lyrics": lyrics,
        "tag": tag
      })
  except:
    print("could not find song")
      
  # open file to write to
  with open("Data/lyrics.json", "w+") as f:
    json.dump(json_data, f, indent=4)

"""
Tokenize lyrics
Not actually used in our algorithm...
"""
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

