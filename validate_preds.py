import spacy
from fuzzywuzzy import fuzz


def granular_corroborate(pred, sit_1, sit_2):
    '''
    Breaks each prediction into granular tuples. Sees if those
    specific tuples occur later.
    '''
    results = []
    predictions = []
    for sent in pred.sents:
        predictions.extend(get_data(sent, granular=True))
    #print('sit 1 is: ', sit_1)
    #print('type of sit1 is: ', type(sit_1))
    situations = []
    if sit_1:
        for sent in sit_1.sents:
            situations.extend(get_data(sent, granular=True))
        #situations = [get_data(sent, granular=True) for sent in sit_1.sents]
    #else:
        #situations = []
    if sit_2:
        for sent in sit_2.sents:
            situations.extend(get_data(sent, granular=True))
    #print('situations: ', situations)
    if predictions and not situations: # case where there is no situation report and pred is nothing significant will happen
        #print('no sits, pred is: ', predictions[0][2][0][0].text.lower())
        if predictions[0][0].text.lower() == 'no':
            return [True]
    for pred in predictions:
        print('pred: ', pred)
        results.append(compare_one_granular(pred, situations))
        print('result: ', compare_one_granular(pred, situations))
    return results


def compare_one_granular(pred, situations):
    '''
    compares one granular prediction tuple against all situations.
    '''
    for sit in situations:
        if not sit and pred:
            continue
        #print('situations: ', situations)
        #print('situation', sit)
        #print('pred: ', pred)
        if not (pred[1] and sit[1]) or fuzz.token_set_ratio(pred[1], sit[1]) == 100: # generalize to locations
            print('situation: ', sit)
            if pred[0]._.subject_decline: # matches locusts will decline to no locusts
                print('pred subject decline', pred[0]._.subject_decline)
                if sit[0]._.subject_decline or is_negated(sit[0]):
                    print('negated?', is_negated(sit[0]))
                    return True
            #if is_negated(pred[0]) != is_negated(sit[0]): # one is negated and one is not, not a match
                #continue
            if is_negated(pred[0]) and is_negated(sit[0]): # match no devs to no locusts
                return True
            if fuzz.token_set_ratio(pred[0], sit[0]) == 100: # matches mature as verb to mature locusts
                return True
            if pred[0].label_ == 'ACTION' and sit[0].label_ == 'ACTION':
                if fuzz.partial_ratio(pred[0].root.lemma_, sit[0].root.lemma_) == 100:
                    return True
            elif pred[0].label_ == 'LOC_TYPE' and sit[0].label_ == 'LOC_TYPE':
                if pred[0].root.lemma_ == sit[0].root.lemma_:
                    if pred[0]._.is_solitarious == sit[0]._.is_solitarious:
                        return True

    return False

def is_negated(ent):
    '''
    Returns whether an ent is negated (i.e., 'no locusts')
    '''
    #print(ent[0].text.lower())
    return ent[0].text.lower().startswith('no ')



def corroborate(pred, sit_1, sit_2):
    '''
    First pass at corroborating predictions.
    Simply checks if any locust groups/predictions/behaviors end up in forecasted locations.
    '''
    results = []
    predictions = [get_data(sent) for sent in pred.sents]
    print('sit 1 is: ', sit_1)
    print('type of sit1 is: ', type(sit_1))
    if sit_1:
        situations = [get_data(sent) for sent in sit_1.sents]
    else:
        situations = []
    if sit_2:
        situations.extend([get_data(sent) for sent in sit_2.sents if sit_2])
    if not situations:
        #print('no sits, pred is: ', predictions[0][2][0][0].text.lower())
        if predictions[0][2][0][0].text.lower() == 'no':
            return [True]
    for pred in predictions:
        results.append(check_one_pred(pred, situations))
        #print('pred: ', pred)
        #print('result: ', check_one_pred(pred, situations))
    return results



def check_one_pred(pred_list, sits):
    '''
    Validates a single sentence of a prediction against ALL situations.
    '''
    #for pred_list in preds:
    if sits:
        for sit_list in sits:
            #print('locs compared: ', compare_locs(pred_list, sit_list))
            if compare_locs(pred_list, sit_list) or not (pred_list[0] and sit_list[0]):
                if compare_groups(pred_list, sit_list) or compare_behaviors(pred_list, sit_list):
                    return True
    #else:
        #print('no sits')
    return False


def compare_behaviors(pred_list, sit_list, granular=False):
    if granular:
        return fuzz.partial_ratio(pred_bx.root.lemma_, sit_bx.root.lemma_) == 100
    # sentence level:
    for pred_bx in pred_list[1]:
        for sit_bx in sit_list[1]:
            if fuzz.partial_ratio(pred_bx.root.lemma_, sit_bx.root.lemma_) == 100:
                return True
    #elif 'no significant developments' in []
    
    return False

def compare_groups(pred_list, sit_list):
    '''
    Takes in two lists of locust groups.
    Compares them based on whether or not they're solitarious or gregarious 
    as well as life stage (based on ent.lemma_ for now).
    Checks if entities have the same lemma, then checks if they're solitarious.
    '''
    for group_1 in pred_list[2]:
        for group_2 in sit_list[2]:
            if group_1[0].text.lower() == 'no' or 'decline' in [word.text for word in sit_list[1]]: # match no significant devs to no locusts
                if group_2[0].text.lower() == 'no': # match 'decline' to 'no locusts'
                    return True
            elif group_1.root.lemma_ == group_2.root.lemma_:
                if group_1._.is_solitarious == group_2._.is_solitarious:
                    return True
    return False

def compare_locs(pred_list, sit_list, granular=False):
    '''
    Takes in two lists of locations. Returns true if the lists contain at least one matching location.
    ADD IN FUNCTIONALITY FOR COMPARING GENERAL TO SPECIFIC 
    '''
    #match = False
    if granular:
        return fuzz.token_set_ratio(loc_1, loc_2) == 100
    
    for loc_1 in pred_list[0]:
        for loc_2 in sit_list[0]:
            if fuzz.token_set_ratio(loc_1, loc_2) == 100:
                return True
    return False



def get_data(sent, granular=False):
    '''
    Pulls out locations, locust types, and behaviors from text.
    Inputs:
        sent: a sentence of an nlp object of text
        granular (bool): whether the data should be extracted at location-level rather than sentence-level
    '''
    #for sent in text.sents:
    locations = [ent for ent in sent.ents if ent.label_ in ('GEN_LOC', 'SPEC_LOC')]
    behaviors = [ent for ent in sent.ents if (ent.label_ == 'ACTION' and ent.text not in ('scattered', 'isolated', 'decline'))]
    locust_groups = [ent for ent in sent.ents if ent.label_=='LOC_TYPE']
    #granular version:
    if granular:
        tuples = []
        for group in locust_groups:
            if locations:
                for place in locations:
                    tuples.append((group, place))
            else:
                tuples.append((group, ''))
        for behavior in behaviors:
            if locations:
                for place in locations:
                    tuples.append((behavior, place))
                else:
                    tuples.append((behavior, ''))
        #print('tuples: ', tuples)
        return tuples
    # non granular version
    return (locations, behaviors, locust_groups)