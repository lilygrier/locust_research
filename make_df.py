'''
Takes in a string of text and makes a pandas dataframe
'''
from get_text import clean_page
import pandas as pd
import re

def parse_text(text):
    # find all situation and forecast
    cols = ["YEAR", 'MONTH', 'COUNTRY', 'SITUATION', 'FORECAST']
    df = pd.DataFrame(columns=cols)
    rel_text = get_relevant_text(text)
    
def get_countries(text):
    countries = re.split(r'(?:• )?SITUATION', text)
    country_name = countries[0]
    for country in countries[1:]:
        re.findall(r'(.+)\n• FORECAST\n(.+\.)(.+)', country, re.DOTALL)
    re.findall(r'(.+)\n• SITUATION\n(.+)\n• FORECAST\n(.+\.)', rv)
    

    # WE GOT IT OMGGGGG
    countries = re.findall(r'(.+?)\n• SITUATION ?\n(.+?)\n• FORECAST\n(.+?)(?=$|[^.]+\n• SITUATION ?\n)', text, re.DOTALL|re.IGNORECASE)


def get_relevant_text(text):
    result = re.findall(r'(?:Situation and Forecast)(.+?)(?:Announcements?|Other Locusts|Glossary of Terms|Other Species)', 
                        text, flags = re.DOTALL|re.IGNORECASE)[0]
    print(result)
    print("type of result: ", type(result))
    # get rid of headers and footers
    to_keep = []
    for line in result.split('\n'):
        if line and not re.match(r'D E S E R T  L O C U S T  B U L L E T I N|No. \d+|\( see also the summary', line, re.IGNORECASE):
            to_keep.append(line)
    return '\n'.join(to_keep)
    #return re.sub(r'(.+)D E S E R T  L O C U S T  B U L L E T I N|No. \d+(.+)', r'\1\2', result, re.IGNORECASE|re.DOTALL)

    #return re.sub(r'(.+)D E S E R T  L O C U S T  B U L L E T I N|No. \d+(.+)', r'\1\2', result, re.IGNORECASE|re.DOTALL)
