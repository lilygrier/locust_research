from bs4 import BeautifulSoup as bs
import requests
from requests import get
import os


def wrapper():
    starting_url = "http://www.fao.org/ag/locusts/en/archives/archive/index.html"
    domain = "http://www.fao.org/ag/locusts/en/archives"
    to_visit = get_urls_to_visit(starting_url, domain)
    get_pdfs(to_visit)
    return None


def get_urls_to_visit(starting_url, domain):
    '''
    Creates dictionary of years and URLs to visit.
    '''
    to_visit = {}

    req = requests.get(starting_url)
    soup = bs(req.text, 'html.parser')
    potential_page = soup.find_all('a')
    for page in potential_page:
        link = page.get('href')
        year = page.text
        print("Link: ", link)
        print("text: ", year)
        if '/archives/archive/' in link and len(year) == 4:
            to_visit[year] = domain + link[14:]
            print("added to dict: ", year, ": ", domain + link[14:])
    return to_visit


def get_pdfs(to_visit):
    domain = "http://www.fao.org/ag/locusts"

    # account for accidental duplicates on the site

    for year, url in to_visit.items():
        #downloaded = []
        filetype = ".pdf"
        #URL = "http://www.fao.org/ag/locusts/en/archives/archive/1366/1669/index.html" # 2009 page
        req = requests.get(url)
        soup = bs(req.text, 'html.parser')
        links = soup.find_all('a')

        #YEAR = "2009"
        # make url and year local vars, make this a function

        parent_dir = os.getcwd()
        new_dir = os.path.join(parent_dir, year)
        if not os.path.exists(new_dir):
            os.mkdir(new_dir)

        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUNE", "JULY", "AUG", "SEPT", "OCT", "NOV", "DEC"]
        month_tracker = 0 # start at JAN, but traverse list of links backward
        if year == "1978": # 1978 data starts in September
            month_tracker = 8

        for link in reversed(links):
            file_link = link.get('href')
            if filetype in file_link and link.text == "english":
                file_name = file_link[33:]
                print("og file_name is: ", file_name)
                if "PR" not in file_name:
                    if year == "1987" and month_tracker == 0: # JAN AND FEB combine for 1987
                        file_name = "/JAN_FEB_" + year
                        month_tracker = month_tracker + 2
                    else:
                        if year == "1988" and month_tracker == 4: # 1988 is missing May, skip to June
                            month_tracker = month_tracker + 1
                        #print("month tracker is: ", month_tracker)
                        file_name = "/" + months[month_tracker] + "_" + year
                        print("file_name changed to: ", file_name)
                        month_tracker = month_tracker + 1 # iterate forward through months
                with open(new_dir + file_name, 'wb') as file:
                    file_path = domain + file_link[14:]
                    #print("link.text is: ", link.text)
                    #print("file_name is: ", file_name)
                    response = requests.get(file_path)
                    #print("response is: ", file_path)
                    file.write(response.content)
                #downloaded.append(file_link)
            else:
                continue
    return None