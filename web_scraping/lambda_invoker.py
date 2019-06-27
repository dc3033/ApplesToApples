#imports
import boto3
from bs4 import BeautifulSoup
import requests
import json
import time

#get starting time
start_time = time.time()

#glassdoor all company reviews page 1
start_url = "https://www.glassdoor.com/Reviews/us-reviews-SRCH_IL.0,2_IN1.htm"

#chrome agent, need this to avoid 403 error when using requests
headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'}

page = requests.get(start_url, headers=headers)
print(page.status_code)

#get soup
soup = BeautifulSoup(page.content, 'html.parser')

#page count limitation for companies pages
mainPageLimit = 1000
mainPageCount = 1
mainHasNext = True

#list that holds the links to the company review pages on the first page
reviewPageList = []

#review page links on starting page entered into list
print('page 1')
reviewLinkSoup = soup.find_all('a', {'class':'eiCell cell reviews'})
for link in reviewLinkSoup:
    print(link['href'])
    reviewPageList.append("https://glassdoor.com" + link['href'])

#text for modifying the URL so it goes to the next page
pageNumber = 2
URLaddon = "_IP" + str(pageNumber) + ".htm"

lambda_client = boto3.client('lambda')

#invoke web scraper lambda function for all the links on the first page
print('outputting to lambda function...')
for link in reviewPageList:
    test_event = dict(site_url=link)
    lambda_client.invoke(
        FunctionName='scraperLambdaFunction',
        InvocationType='Event',
        Payload=json.dumps(test_event)
    )

#List for holding links that failed to load
failedLinkList = []

#moves to next page if page limit is not reached
while mainHasNext:
    #create a list of links on this page to send to lambda function as soon as the page is done
    pageLinkList = []
    #get next page and increment page number
    nextMainPage = start_url[:-4] + URLaddon
    try:
        link = requests.get(nextMainPage, headers=headers)
    except requests.exceptions.ConnectionError:
        #invoke lambda function that sets off CloudWatch alarm, then make changes for next loop and continue
        print('Connection error on ' + nextMainPage)
        lambda_client.invoke(
            FunctionName='LambdaInvokerAlarm',
            InvocationType='Event',
            Payload=json.dumps(nextMainPage)
        )
        failedLinkList.append(nextMainPage)
        print('page ' + str(pageNumber))
        pageNumber += 1
        URLaddon = "_IP" + str(pageNumber) + ".htm"
        mainPageCount += 1
        if mainPageCount >= mainPageLimit:
            mainHasNext = False
        continue

    print('page ' + str(pageNumber))
    pageNumber += 1
    URLaddon = "_IP" + str(pageNumber) + ".htm"
    soup = BeautifulSoup(link.content, 'html.parser')
    #adds all company review page links on the current page to the list
    reviewLinkSoup = soup.find_all('a', {'class':'eiCell cell reviews'})
    for link in reviewLinkSoup:
        print(link['href'])
        #reviewPageList.append("https://glassdoor.com" + link['href'])
        pageLinkList.append("https://glassdoor.com" + link['href'])
    #invoke web scraper lambda function for all the links on this page
    print('outputting to lambda function...')
    for link in pageLinkList:
        test_event = dict(site_url=link)
        lambda_client.invoke(
            FunctionName='scraperLambdaFunction',
            InvocationType='Event',
            Payload=json.dumps(test_event)
        )
    #increments companies page limiter and checks if limit is reached
    mainPageCount += 1
    if mainPageCount >= mainPageLimit:
        mainHasNext = False

#retry links that failed
print('Retrying links with connection errors...')
for failedLink in failedLinkList:
    try:
        link = requests.get(failedLink, headers=headers)
    except requests.exceptions.ConnectionError:
        #invoke lambda function that sets off CloudWatch alarm, then make changes for next loop and continue
        print('Connection error on ' + failedLink)
        lambda_client.invoke(
            FunctionName='LambdaInvokerAlarm',
            InvocationType='Event',
            Payload=json.dumps(failedLink)
        )
        continue

    soup = BeautifulSoup(link.content, 'html.parser')
    #adds all company review page links on the current page to the list
    reviewLinkSoup = soup.find_all('a', {'class':'eiCell cell reviews'})
    for link in reviewLinkSoup:
        print(link['href'])
        #reviewPageList.append("https://glassdoor.com" + link['href'])
        pageLinkList.append("https://glassdoor.com" + link['href'])
    #invoke web scraper lambda function for all the links on this page
    print('outputting to lambda function...')
    for link in pageLinkList:
        test_event = dict(site_url=link)
        lambda_client.invoke(
            FunctionName='scraperLambdaFunction',
            InvocationType='Event',
            Payload=json.dumps(test_event)
        )

#print time elapsed
print("%s seconds elapsed" % (time.time() - start_time))
