import spacy
from spacy.matcher import Matcher
import re

matcher = Matcher(nlp.vocab)
LOCUST_TYPES = ["no locusts", "locusts", "fledglings", "hoppers", "adults", "groups", "swarms", 'bands']
LOCUST_VERBS = ['form', 'mature']
LOCUST_ADJ = ["mature", "immature", "solitarious", "isolated", "gregarious", "scattered"]

def prep_text(text):
    '''
    Prepares text for processing.
    '''
    text = re.sub(r'\n', "", text)
    text = re.sub(r'J ask', r'Jask', text)
    text = re.sub(r'[B-Z] [a-z]+', r'[B-Z][a-z]+', text) # should handle the above case

    return text

def get_specific_locations():
    '''
    Extracts locations with lat/long specified
    '''
    pattern = {}
    #re.findall(r'[A-Z][a-z]+ \(.+?\)', text)
    re.findall(r'(([A-Z][a-z]+ ?)+ \(.+?\))', text) # take just first entry of each tuple

def parse_info(text):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', "November", "December"]
    d = {'locs': [],
        #'spec_locs': [],
        'stage': [],
        'action': []}
    for i, chunk in enumerate(text.noun_chunks):
        if chunk.root.dep_.startswith('nsubj'):
            #print(chunk)
            # subject and verb pair
            d['stage'].append((chunk.text, chunk.root.head.text))
            #d['action'].append(chunk.root.head.text)
        #if chunk.root.dep_ in ['pobj', 'conj', 'dobj']:
            if chunk.root.head.text == 'form': # form and mature and the like
                print("we got a form")
                d['action'].extend([child for child in chunk.root.head.children if child.dep_ == 'conj'])
        elif set(locust_types).intersection(chunk.text.split()):

            # sort further if time
            #if set(locust_types).intersection(chunk.text.split()):
            #if chunk.text in ["late instar hoppers", "fledglings", "immature adults", "adult groups", "swarms"]: # generalize this to any locust word
            d['stage'].append((chunk.text, None))
        else:
            #print(chunk)
            if not set(months).intersection(chunk.text.split()) and not re.search(r'\d', chunk.text): # doesn't have a month in it
                d['locs'].append(chunk.text)
    return d