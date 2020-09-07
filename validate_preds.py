import spacy
import pandas as pd
from fuzzywuzzy import fuzz
from location_matching import match_places
from dateutil.relativedelta import relativedelta


def make_merged_df(df):
    '''
    Creates a dataframe with forecast and situations aligned.
    Inputs:
        df: a Pandas dataframe where each row represents one country at one month
    Returns:
        a merged dataframe lining up forecasts to corresponding situation reports
    '''

    df.loc[:, 'DATE'] = pd.to_datetime(df['DATE'], format='%b_%Y')
    df['ONE_MONTH_OUT'] = df['DATE'].apply(lambda x: x + relativedelta(months=+1))
    df['TWO_MONTHS_OUT'] = df['DATE'].apply(lambda x: x + relativedelta(months=+2))
    one_month = df[['COUNTRY', 'SITUATION', 'ONE_MONTH_OUT']].copy()
    one_month.rename(columns={'SITUATION': 'SIT_1'}, inplace=True)
    two_months = df[['COUNTRY', 'SITUATION', 'TWO_MONTHS_OUT']].copy()
    two_months.rename(columns={'SITUATION': 'SIT_2'}, inplace=True)
    df.drop(columns=['ONE_MONTH_OUT', 'TWO_MONTHS_OUT'], inplace=True)
    df = df.merge(one_month,
                left_on = ['COUNTRY', 'DATE'],
                right_on = ['COUNTRY', 'ONE_MONTH_OUT'],
                 how='left')
    df = df.merge(two_months,
                     left_on=['COUNTRY', 'DATE'],
                     right_on = ['COUNTRY', 'TWO_MONTHS_OUT'],
                     how='left')
    return df

def results_by_sentence(pred, sit_1, sit_2, match_type='general_type', loc_matching=False, country_tree=None):
    '''
    If anything in the prediction sentence is correct, returns True.
    Inputs:
        pred: an NLP object of the forecast text
        sit_1: an NLP object of the situation report text one month out
        sit_2: an NLP object of the situation report text two months out
        match_type (string):
            'any_locusts': matches based on being able to predict any locusts
            'general_type': matches on adult vs. hopper, solitarious vs. gregarious,
                            and immature vs. mature
            'exact': matches on exact wording (e.g., 'few small groups' will only 
                                                match to 'few small groups')
        loc_matching (bool): whether to use a location matching tree
        country_tree: if loc_matching is True, must supply a location matching tree
    Returns:
        results: a list of booleans corresponding to the veracity of each prediction
        pos_preds: a list of booleans representing whether the corresponding prediction
            was for a significant event (i.e., anything but "no significant events")
    '''
    results = []
    situations = []
    for sit in [sit_1, sit_2]:
        if type(sit) == spacy.tokens.doc.Doc:
            for sent in sit.sents:
                situations.extend(get_data(sent, granular=True))
    pos_preds = []
    for sent in pred.sents:
        predictions = get_data(sent, granular=True)
        no_sig = False
        for pred in predictions:
            if pred[0].text.lower().startswith('no sign'):
                no_sig = True
        pos_preds.append(not no_sig)
        if predictions and not situations: # case where there is no situation report and pred is nothing significant will happen
            if no_sig:
                results.append(True)
            else:
                results.append(False)
        else:
            if all((compare_one_granular(prediction, situations, match_type=match_type, 
            loc_matching=loc_matching, country_tree=country_tree) not in [True, False]) for prediction in predictions):
                        results.append('Unknown')
            else:
                results.append(any((compare_one_granular(prediction, situations, match_type=match_type, 
                            loc_matching=loc_matching, country_tree=country_tree) == True) for prediction in predictions))

    return results, pos_preds

def results_by_place(pred, sit_1, sit_2, match_type='any_locusts', loc_matching=False, country_tree=None):
    '''
    Most lenient pass at accuracy. For each location in which locusts were predicted,
    did locusts appear?
    All predictions for a single place are combined, and if any are true, returns true.
    Inputs:
        pred: an NLP object of the forecast text
        sit_1: an NLP object of the situation report text one month out
        sit_2: an NLP object of the situation report text two months out
        match_type (string):
            'any_locusts': matches based on being able to predict any locusts
            'general_type': matches on adult vs. hopper, solitarious vs. gregarious,
                            and immature vs. mature
            'exact': matches on exact wording (e.g., 'few small groups' will only 
                                                match to 'few small groups')
        loc_matching (bool): whether to use a location matching tree
        country_tree: if loc_matching is True, must supply a location matching tree
    '''
    predictions, situations = get_tuple_list(pred, sit_1, sit_2)
    if predictions and not situations:
        if predictions[0][0].text.lower().startswith('no sign') or (predictions[0][0].text.lower() == 'no' and predictions[0][1].text.lower.startswith('sign')):
            return ([True], [False])
        else:
            return ([False], [True])
    pred_locs = generate_by_place_dict(predictions)
    sit_locs = generate_by_place_dict(situations)
    results = []
    pos_preds = []
    for pred_loc, pred_list in pred_locs.items():
        matching_locs = [sit_loc for sit_loc in sit_locs.keys() if match_places(pred_loc, sit_loc, loc_matching, country_tree)]
        if matching_locs:
            results.append(any(compare_preds_by_place(pred_list, sit_group, match_type) for sit_group in sit_locs.values()))
        else:
            results.append('Unknown - no match')
        has_sig = True
        for pred in pred_list:
            if pred.text.lower().startswith('no sign'):
                has_sig = False
        pos_preds.append(has_sig)

    return results, pos_preds


def generate_by_place_dict(tuple_list):
    '''
    Takes in list of tuples and generates a dictionary clustering predictions/reports of locust 
    groups or activity into associated locations.
    Inputs:
        tuple_list: list of tuples containing locust groups/behaviors 
        in the first position and associated locations in the second position
    Returns:
        by_locs: a dictionary with locations as keys and a list of associated 
            locust groups/behaviors as values
    '''
    by_locs = {}
    for group, place in tuple_list:
        if not place:
            place_name = ''
        else:
            place_name = place.text
        if place_name in by_locs:
            by_locs[place_name].append(group)
        else:
            by_locs[place_name] = [group]

    return by_locs


def get_tuple_list(pred, sit_1, sit_2):
    '''
    Creates list of tuples from predictions and situations.
    Inputs:
        pred: an NLP object of the forecast text
        sit_1: an NLP object of the situation report text one month out
        sit_2: an NLP object of the situation report text two months out
    Returns:
        predictions: list of tuples with groups/behaviors and lcoation pairs
        situations: list of tuples with groups/behaviors and lcoation pairs
    '''
    predictions = []
    situations = []
    for sent in pred.sents:
        predictions.extend(get_data(sent, granular=True))
    for sit in [sit_1, sit_2]:
        if type(sit) == spacy.tokens.doc.Doc:
            for sent in sit.sents:
                situations.extend(get_data(sent, granular=True))

    return (predictions, situations)


def percent_result_type(results_list, result_type, distinguish_false=False):
    '''
    Given a results list of true and false, returns percent of true predictions.
    Inputs:
        results_list: a list of results
        result_type: the type of result (either True, False, or 'False - No match')
        distinguish_false: if True, will exclude falses labeled "no match" or 
            "no report received" from the calculation of the final score
    Returns:
        float representing share of total results held by specified type
    '''
    if not results_list:
        return 0
    if distinguish_false:
        valid_results = [result for result in results_list if result in [True, False]]
        if not valid_results:
            return 0
    else:
        valid_results = results_list
    if type(result_type) == str:
        return len([result for result in results_list if (type(result) == str and result.startswith(result_type))])/len(valid_results)

    return len([result for result in results_list if result==result_type])/len(valid_results)


def granular_corroborate(pred, sit_1, sit_2, match_type='general_type', loc_matching=False, country_tree=None):
    '''
    Breaks each prediction into granular tuples. Sees if those
    specific tuples occur later.
    Inputs:
        pred: an NLP object of the forecast text
        sit_1: an NLP object of the situation report text one month out
        sit_2: an NLP object of the situation report text two months out
        match_type: how sensitive a match should be. One of 'general_type,' 'any_locusts,' or 'exact'
        loc_matching (bool): whether to use a location matching tree
        country_tree: if loc_matching is True, must supply a location matching tree
    Returns:
        results: a list of booleans corresponding to the veracity of each prediction
        pos_preds: a list of booleans representing whether the corresponding prediction
            was for a significant event (i.e., anything but "no significant events")
    '''
    results = []
    predictions = []
    if all((type(item) != spacy.tokens.doc.Doc) for item in [pred, sit_1, sit_2]):
        return []
    for sent in pred.sents:
        predictions.extend(get_data(sent, granular=True))
    situations = []
    for sit in [sit_1, sit_2]:
        if type(sit) == spacy.tokens.doc.Doc:
            for sent in sit.sents:
                situations.extend(get_data(sent, granular=True))
    if predictions and not situations: # case where there is no situation report and pred is nothing significant will happen
        if predictions[0][0].text.lower().startswith('no signi'):
            return ([True], [False])
    for pred in predictions:
        results.append(compare_one_granular(pred, situations, match_type=match_type))
    pos_preds = positive_prediction(predictions)

    return (results, pos_preds)


def compare_preds_by_place(pred_groups, sit_groups, match_type='general_type'):
    '''
    Compares a list of predictions to a list of situations. If any of them are in common, 
    returns True.
    Inputs:
        pred_groups: list of nlp objects of prediction text
        sit_groups: list of nlp objects of situation text
        match_type (string):
            'any_locusts': matches based on being able to predict any locusts
            'general_type': matches on adult vs. hopper, solitarious vs. gregarious,
                            and immature vs. mature
            'exact': matches on exact wording (e.g., 'few small groups' will only 
                                                match to 'few small groups')
    '''
    for pred in pred_groups:
        for sit in sit_groups:
            if (compare_predictions(pred, sit, match_type) == True):
                return True

    return False


def compare_predictions(pred_group, sit_group, match_type='general_type'):
    '''
    Compares two locust groups or actions and returns whether or not they're a match.
    Inputs:
        pred_group (nlp object): a locust group or behavior
        sit_group (nlp object): a locust group or behavior
        match_type (string):
            'any_locusts': matches based on being able to predict any locusts
            'general_type': matches on adult vs. hopper, solitarious vs. gregarious,
                            and immature vs. mature
            'exact': matches on exact wording (e.g., 'few small groups' will only 
                                                match to 'few small groups')
    Returns:
        whether the two groups match: one of True, False, or Unknown (if no reports were received)
    '''

    if sit_group.text.startswith('no reports'):
        return "Unknown - no reports"
    if pred_group._.subject_decline: # matches locusts will decline to no locusts
        if sit_group._.subject_decline or is_negated(sit_group):
            return True
        else:
            return False
    if is_negated(pred_group) and is_negated(sit_group): # match no developmentss to no locusts
        return True
    if is_negated(pred_group) != is_negated(sit_group): # make sure 'no locusts' won't match to 'locusts'
        return False
    if fuzz.token_set_ratio(pred_group, sit_group) == 100: # matches mature as verb to mature locusts
        return True
    if pred_group.label_ == 'ACTION' and sit_group.label_ == 'ACTION':
        if fuzz.token_set_ratio(pred_group.lemma_, sit_group.lemma_) == 100 or set([pred_group, sit_group]) == set(['laying', 'lay']):
            return True
    elif pred_group.label_ == 'LOC_TYPE' and sit_group.label_ == 'LOC_TYPE': # already filtered out negations
        if match_type == 'any_locusts':
            return True
        if pred_group.text.lower() == 'locusts' or pred_group.text.lower() == 'populations': # if just locusts is predicted, will match to anything
            return True
        elif match_type == 'general_type':
            if pred_group._.contains_adults == sit_group._.contains_adults:
                if pred_group._.ent_solitarious == sit_group._.ent_solitarious:
                    return True
        elif match_type == 'exact':
            return fuzz.partial_ratio(pred_group, sit_group) == 100


def compare_one_granular(pred, situations, match_type='general_type', loc_matching=False, country_tree=None):
    '''
    Compares one granular prediction tuple against all situations.
    Inputs:
        pred: an nlp object of a single prediction
        situations: a list of nlp object of situation statements
        match_type (string):
            'any_locusts': matches based on being able to predict any locusts
            'general_type': matches on adult vs. hopper, solitarious vs. gregarious,
                            and immature vs. mature
            'exact': matches on exact wording (e.g., 'few small groups' will only 
                                                match to 'few small groups')
    '''
    for sit in situations:
        if not sit and pred:
            continue
        if pred[1] and not sit[1]:
            continue
        if loc_matching:
            locs_match = not(pred[1] and sit[1]) or match_places(pred[1], sit[1], country_tree)
        else:
            locs_match = not (pred[1] and sit[1]) or fuzz.token_set_ratio(pred[1], sit[1]) == 100 # deal with not sit[1] separately
        if locs_match:
            if sit[0].text.lower().startswith('no reports'): # account for no reports received
                return "Unknown - no reports"
            if pred[0]._.subject_decline: # matches locusts will decline to no locusts
                if sit[0]._.subject_decline or is_negated(sit[0]):
                    return True
                else:
                    continue
            if is_negated(pred[0]) and is_negated(sit[0]): # match no devs to no locusts
                return True
            if is_negated(pred[0]) != is_negated(sit[0]): # make sure 'no locusts' won't match to 'locusts'
                continue
            if fuzz.token_set_ratio(pred[0], sit[0]) == 100: # matches mature as verb to mature locusts
                return True
            if pred[0].label_ == 'ACTION' and sit[0].label_ == 'ACTION':
                if fuzz.token_set_ratio(pred[0].lemma_, sit[0].lemma_) == 100 or set([pred[0], sit[0]]) == set(['laying', 'lay']): # NEED TO ADDRESS LAYING VS LAY
                    return True
            elif pred[0].label_ == 'LOC_TYPE' and sit[0].label_ == 'LOC_TYPE':
                if match_type == 'any_locusts':
                    return True
                if pred[0].text.lower() == 'locusts' or pred[0].text.lower() == 'populations': # if just locusts is predicted, will match to anything
                    return True
                elif match_type == 'general_type':
                    if pred[0]._.contains_adults == sit[0]._.contains_adults:
                        if pred[0]._.ent_solitarious == sit[0]._.ent_solitarious:
                            return True
                elif match_type == 'exact':
                    return fuzz.partial_ratio(pred[0], sit[0]) == 100
        else:
            return "Unknown - no match"

    return False


def is_negated(ent):
    '''
    Returns whether an ent is negated (i.e., 'no locusts')
    '''
    return ent[0].text.lower().startswith('no ')

def get_data(sent, granular=False):
    '''
    Pulls out locations, locust types, and behaviors from text.
    Inputs:
        sent: a sentence of an nlp object of text
        granular (bool): whether the data should be extracted at location-level rather than sentence-level
    '''
    locations = [ent for ent in sent.ents if ent.label_ in ('GEN_LOC', 'SPEC_LOC')]
    behaviors = [ent for ent in sent.ents if (ent.label_ == 'ACTION' and ent.text not in ('scattered', 'isolated', 'decline', 'decrease'))]
    locust_groups = [ent for ent in sent.ents if ent.label_=='LOC_TYPE']
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
        return tuples
    return (locations, behaviors, locust_groups)

def positive_prediction(preds_list):
    '''
    Creates a list of booleans indicating whether a prediction indicates something other than
    "no significant developments."
    Inputs:
        preds_list: a list of tuples containing predictions
    Returns:
        list of booleans indicating whether predictions contain a significant development
    '''
    rv = []
    for pred in preds_list:
        no_sig = pred[0].text.lower().startswith('no sign') or (pred[0].text.lower() == 'no' and pred[1].text.lower.startswith('sign'))
        rv.append(not no_sig)
    return rv