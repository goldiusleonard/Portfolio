import PySimpleGUI as sg
import os
import re
from random import randint
import pandas as pd
from googletrans import Translator
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC

# Import news
news = []
for dirname, _, filenames in os.walk('./data/'):
    for filename in filenames:
        df = pd.read_csv(os.path.join(dirname, filename), index_col = None, header = 0)
        row, cols = df.shape
        news.append(df)
        
data_set = pd.concat(news, axis=0, ignore_index=True)
data_set = data_set.drop('Unnamed: 0', axis = 1)
del news

txt = open("corpus.txt", "r")
corpus = []
for line in txt:
    sentence = line.rstrip("\n")
    corpus.append(sentence)

vectorizer = TfidfVectorizer()
x = vectorizer.fit_transform(corpus)
y = data_set.iloc[:, -1].values

svc = SVC(kernel = 'rbf')
svc.fit(x, y)

# Define the window"s contents
layout = [[sg.Text("News Sample:")],
          [sg.Text(size=(100, 3), key="-INPUT-")],
          [sg.Text("News Translation (Indonesian):")],
          [sg.Text(size=(100, 3), key="-OUTPUT-")],
          [sg.Text("Category:")],
          [sg.Text(size=(100, 1), key="-OUTPUT2-")],
          [sg.Button("Try"), sg.Button("Quit")]]

# Create the window
window = sg.Window("News Classification and Translation", layout)
translator = Translator()
ps = PorterStemmer()
vectorizer2 = TfidfVectorizer()
size = len(data_set)

# Display and interact with the Window using an Event Loop
while True:
    event, values = window.read()
    
    if event == sg.WINDOW_CLOSED or event == "Quit":
        break
    
    index = randint(0, size - 1)
    inp = data_set["news_article"][index]
    values["-INPUT-"] = inp

    window["-INPUT-"].update(inp)
    translated = translator.translate(values["-INPUT-"], src="en", dest="id")
    
    classification = svc.predict(x[index])
    # sampe sini
    
    window["-OUTPUT-"].update(translated.text)
    window["-OUTPUT2-"].update(*classification)

# Finish up by removing from the screen
window.close()
txt.close()