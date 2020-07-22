import spacy
from spacy.matcher import Matcher
import re

nlp = spacy.load("en_core_web_sm")
#matcher = Matcher(nlp.vocab)
LOCUST_VERBS = ['form', 'mature', 'lay', 'fledge', 'breed', 'hatch', 'copulate'] # can look for lemma of verb
LOCUST_GERUNDS = ['breeding', 'hatching', 'laying']
LOCUST_TYPES = ["locust", "fledgling", "hopper", "adult", "group", "swarm", 'band', 'swarmlet']
#LOCUST_ADJ = ["immature", 'mature', 'solitarious', 'gregarious', 'isolated']

def prep_text(text):
    '''
    Prepares text for processing.
    '''
    text = re.sub(r'\n', "", text)
    text = re.sub(r'J ask', r'Jask', text)
    text = re.sub(r'[B-Z] [a-z]+', r'[B-Z][a-z]+', text) # should handle the above case
    text = re.sub(r'no reports of [a-z]+', r'no [a-z]+', text)

    return text

def get_specific_locations():
    '''
    Extracts locations with lat/long specified
    '''
    pattern = {}
    #re.findall(r'[A-Z][a-z]+ \(.+?\)', text)
    re.findall(r'(([A-Z][a-z]+ ?)+ \(.+?\))', text) # take just first entry of each tuple

def get_snippets(text):
    snippets = []
    nlp = spacy.load("en_core_web_sm")
    text = prep_text(text)
    for sent in text.split('.'):
        sent = nlp(sent)
        keywords = sent_matches(sent)
        if keywords:
            snippets.append(keywords)
    return snippets

def sent_matches(sent):
    '''
    Note: this function works on a single sentence
    '''
    rv = []
    ranges = []
    matcher = make_matcher()
    matches = matcher(sent)
    for i in range(0, len(matches)):
        start, end = matches[i][1], matches[i][2]
        span = str(sent[start:end])
        #print("SPAN IS: ", span)
        #if ranges:
            #print(ranges[-1], (start, end))
        if ranges and set(range(start, end)).issubset((ranges[-1])):
            # if longer match is already in there, skip it
            continue
        if ranges and set(ranges[-1]).issubset(range(start, end)):
            # if shorter match was added, replace the shorter match with a longer one
            rv[-1] = span
            ranges[-1] = range(start, end)
        else:
            rv.append(span)
            ranges.append(range(start, end))
    return rv

def make_matcher():
    '''
    creates the matcher object with specified patterns
    '''
    # maybe move relevant global vars into this function
    matcher = Matcher(nlp.vocab)
    actions = [[{'LEMMA': {'IN': LOCUST_VERBS}}]]
    locust_groups = [[{'POS': 'ADJ', 'OP': '?'},
    {'LOWER': 'and', 'OP': '?'},
    {'POS': 'ADJ', 'OP': '*'},
    {'LEMMA': {'IN': LOCUST_TYPES}},
                 {'LOWER': 'AND', 'OP': '?'},
                 {'LEMMA': {'IN': LOCUST_TYPES}, 'OP': '?'}],
                 [{'LOWER': 'no'}, {'LOWER': 'desert', 'OP': '?'}, {'LOWER': 'locusts'}]]
    locust_gerunds = [[{'LOWER': {'IN': LOCUST_GERUNDS}, 'POS': {'NOT IN': 'VERB'}}]]
    matcher.add("actions", actions)
    matcher.add("loc_group", locust_groups)
    matcher.add("gerunds", locust_gerunds)
    return matcher

def parse_info(text):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', "November", "December"]
    d = {'locs': [],
        #'spec_locs': [],
        'stage': [],
        'action': []}
    for i, chunk in enumerate(text.noun_chunks):
        if chunk.root.dep_.startswith('nsubj'):
            #print(chunk)
            #who = []
            #what = []
            # subject and verb pair
            #who.append(chunk.text)
            #what.append(chunk.root.head.text)
            d['stage'].append((chunk.text, chunk.root.head.text))
            #d['action'].append(chunk.root.head.text)
        #if chunk.root.dep_ in ['pobj', 'conj', 'dobj']:
            if chunk.root.head.text == 'form': # form and mature and the like
                #print("we got a form")
                #print("here's the thing")
                #print([word.text for word in chunk.root.head.subtree if word.dep_ == 'conj' and word.pos_ == 'VERB'])
                d['action'].extend([word.text for word in chunk.root.head.subtree if word.dep_ == 'conj' and word.pos_ == 'VERB'])
                #verb = [child for child in chunk.root.head.children if child.dep_ == 'conj' and child.text in LOCUST_VERBS]
                #print(verb)
                #if verb:
                    #d['stage'].append(('previous', str(verb)))
                #what.extend([child for child in chunk.root.head.children if child.dep_ == 'conj' and child in LOCUST_VERBS])
            #d['stage'].append((who, what))
        #elif chunk.root.head.text == 'groups' and chunk.root.dep_ == 'conj':
            #d['stage'].append((chunk.text, 'previous'))
        # handle hopper groups and bands, etc. as one chunk
        elif chunk.root.text == 'groups':
            #print("here's the other thing" ,list(chunk.root.subtree))
            d['stage'].append((' '.join([word.text for word in chunk.root.subtree]), None))
            #d['stage'].extend(' '.join(list(chunk.root.subtree)))
            # also want to skip the next noun chunk
        elif set(LOCUST_TYPES).intersection(chunk.text.split()):
            d['stage'].append((chunk.text, None))
        else:
            #print(chunk)
            if not set(months).intersection(chunk.text.split()) and not re.search(r'\d', chunk.text): # doesn't have a month in it
                d['locs'].append(chunk.text)
        #for word in text:
            #if word.pos_ == 'VERB' and word.text in LOCUST_VERBS:
                #d['action'].append(word)
    return d
