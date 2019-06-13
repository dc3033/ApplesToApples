#imports
import boto3
from bs4 import BeautifulSoup
import requests
import json

#glassdoor all company reviews page 1
start_url = "https://www.glassdoor.com/Reviews/us-reviews-SRCH_IL.0,2_IN1.htm"

#chrome agent, need this to avoid 403 error when using requests
headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'}

page = requests.get(start_url, headers=headers)
print(page.status_code)

#get soup
soup = BeautifulSoup(page.content, 'html.parser')

#page count limitation for companies pages
mainPageLimit = 3
mainPageCount = 1
mainHasNext = True

#list that holds the links to the company review pages
reviewPageList = []

#review page links on starting page entered into list
reviewLinkSoup = soup.find_all('a', {'class':'eiCell cell reviews'})
for link in reviewLinkSoup:
    print(link['href'])
    reviewPageList.append("https://glassdoor.com" + link['href'])

#text for modifying the URL so it goes to the next page
pageNumber = 2
URLaddon = "_IP" + str(pageNumber) + ".htm"

#moves to next page if page limit is not reached
while mainHasNext:
    nextMainPage = start_url[:-4] + URLaddon
    link = requests.get(nextMainPage, headers=headers)
    pageNumber += 1
    URLaddon = "_IP" + str(pageNumber) + ".htm"
    soup = BeautifulSoup(link.content, 'html.parser')
    #adds all company review page links on the current page to the list
    reviewLinkSoup = soup.find_all('a', {'class':'eiCell cell reviews'})
    for link in reviewLinkSoup:
        print(link['href'])
        reviewPageList.append("https://glassdoor.com" + link['href'])
    #increments companies page limiter and checks if limit is reached
    mainPageCount += 1
    if mainPageCount >= mainPageLimit:
        mainHasNext = False

lambda_client = boto3.client('lambda')

#invoke lambda function that scrapes the link's webpage
for link in reviewPageList:

    test_event = dict(site_url=link)
    lambda_client.invoke(
        FunctionName='scraperLambdaFunction',
        InvocationType='Event',
        Payload=json.dumps(test_event)
    )
