import pandas as pd
import extract_info
import validate_preds
import seaborn as sns

'''
Analyze results of predictions.
'''

df = pd.read_csv("report_text_2.csv")

def gen_merged_df(df):
    df = extract_info.get_snippets(df, 'SITUATION')
    df = extract_info.get_snippets(df, 'FORECAST')
    df = extract_info.prelim_cleaning(df)
    return validate_preds.make_merged_df(df)
     


def gen_results_df(df, loc_matching=False):
    
    #df['most_gran_data'] = df.apply(lambda x: validate_preds.granular_corroborate(x.FORECAST, x.SIT_1, x.SIT_2, match_type='exact'), axis=1)
    #print('col is', df['most_gran_data'])
    #df['most_gran_results'] = df['most_gran_data'].apply(lambda most_gran_data: most_gran_data[0])
    #df['most_gran_results_sig_preds'] = df['most_gran_data'].apply(lambda most_gran_data: most_gran_data[1])
    df['most_gran_results'] = df.apply(lambda x: validate_preds.granular_corroborate(x.FORECAST, x.SIT_1, x.SIT_2, match_type='exact')[0], axis=1)
    #print('col is: ', df['most_gran_results'])
    df['most_gran_results_sig_preds'] = df.apply(lambda x: validate_preds.granular_corroborate(x.FORECAST, x.SIT_1, x.SIT_2, match_type='exact')[1], axis=1)
    df['most_gran_results_pct'] = df.apply(lambda x: validate_preds.percent_true(x.most_gran_results), axis=1)
    
    #df['any_by_place_data'] = df.apply(lambda x: validate_preds.results_by_place(x.FORECAST, x.SIT_1, x.SIT_2), axis=1)
    df['any_by_place'] = df.apply(lambda x: validate_preds.results_by_place(x.FORECAST, x.SIT_1, x.SIT_2)[0], axis=1)
    df['any_by_place_sig_preds'] = df.apply(lambda x: validate_preds.results_by_place(x.FORECAST, x.SIT_1, x.SIT_2)[1], axis=1)

    #df['any_by_place'] = df['any_by_place_data'].apply(lambda any_by_place_data: any_by_place_data[0])
    #df['any_by_place_sig_preds'] = df['any_by_place_data'].apply(lambda any_by_place_data: any_by_place_data[1])
    df['any_by_place_pct'] = df.apply(lambda x: validate_preds.percent_true(x.any_by_place), axis=1)
    
    df['sentence_by_gen_stage_data'] = df.apply(lambda x: validate_preds.results_by_sentence(x.FORECAST, x.SIT_1, x.SIT_2), axis=1)
    df['sentence_by_gen_stage'] = df.apply(lambda x: validate_preds.results_by_sentence(x.FORECAST, x.SIT_1, x.SIT_2)[0], axis=1)
    df['sentence_by_gen_stage_sig_preds'] = df.apply(lambda x: validate_preds.results_by_sentence(x.FORECAST, x.SIT_1, x.SIT_2)[1], axis=1)

    #df['sentence_by_gen_stage'] = df['sentence_by_gen_stage_data'].apply(lambda sentence_by_gen_stage_data: sentence_by_gen_stage_data[0])
    #df['sentence_by_gen_stage_sig_preds'] = df['sentence_by_gen_stage_data'].apply(lambda sentence_by_gen_stage_data: sentence_by_gen_stage_data[1])
    #df['sentence_by_gen_stage'] = df.apply(lambda x: validate_preds.results_by_sentence(x.FORECAST, x.SIT_1, x.SIT_2)[1], axis=1)
    df['sent_by_gen_stage_pct'] = df.apply(lambda x: validate_preds.percent_true(x.sentence_by_gen_stage), axis=1)
    #df.drop(columns=['most_gran_data', 'any_by_place_data', 'any_by_gen_stage_data'], inplace=True)
    return df

def analyze_results(df, loc_matching=False):
    df['total_true_any'] = df.apply(lambda x: count_true(x.any_by_place), axis=1)
    df['total_no_match_any'] = df.apply(lambda x: count_false_no_match(x.any_by_place), axis=1)
    df['total_false_any'] = df.apply(lambda x: count_false(x.any_by_place), axis=1)

    df['total_true_gen'] = df.apply(lambda x: count_true(x.sentence_by_gen_stage), axis=1)
    df['total_no_match_gen'] = df.apply(lambda x: count_false_no_match(x.sentence_by_gen_stage), axis=1)
    df['total_false_gen'] = df.apply(lambda x: count_false(x.sentence_by_gen_stage), axis=1)

    df['total_true_exact'] = df.apply(lambda x: count_true(x.most_gran_results), axis=1)
    df['total_no_match_exact'] = df.apply(lambda x: count_false_no_match(x.most_gran_results), axis=1)
    df['total_false_exact'] = df.apply(lambda x: count_false(x.most_gran_results), axis=1)

    return df

def confusion_matrix(df):
    '''
    Analyzes false and true positives and negatives.
    '''
    pred_correct = np.concatenate(df['any_by_place'].reset_index(drop=True))
    pred_sig_pred = np.concatenate(df['any_by_place_sig_preds'].reset_index(drop=True)) 
    conf_matrix = pd.crosstab(pred_sig_pred, pred_correct, rownames=['sig. event predicted'], colnames=['pred result'])
    sns.heatmap(conf_matrix, annot=True)

def any_true(results_list):
    return any(result == True for result in results_list)


def count_true(results_list):
    '''
    Gives a raw count of true predictions.
    '''
    return sum([result for result in results_list if result == True])

def count_false_no_match(results_list):
    return len([result for result in results_list if result == "False - No match"])

def count_false(results_list):
    '''
    count all false, including no match
    '''
    return len([result for result in results_list if result != True])





