#imports
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import re

#starting_url, results are all companies on glassdoor site
start_url = "https://www.glassdoor.com/Reviews/us-reviews-SRCH_IL.0,2_IN1.htm"

#Firefox session
driver = webdriver.Firefox()
driver.get(start_url)
driver.implicitly_wait(10, TimeUnit.SECONDS)

#get soup
soup = BeautifulSoup(driver.page_source, 'html.parser')

#page count limitation for companies pages
mainPageLimit = 2
mainPageCount = 1
mainHasNext = True

#list that holds the links to the company review pages
reviewPageList = []

#review page links on starting page entered into list
reviewLinkSoup = soup.find_all('a', {'class':'eiCell cell reviews'})
for link in reviewLinkSoup:
    reviewPageList.append("https://glassdoor.com" + link['href'])

#moves to next page if page limit is not reached
while mainHasNext:
    nextMainPage = soup.find('li', {'class':'next'})
    link = "https://glassdoor.com" + nextMainPage.find('a')['href']
    driver.get(link)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    #adds all company review page links on the current page to the list
    reviewLinkSoup = soup.find_all('a', {'class':'eiCell cell reviews'})
    for link in reviewLinkSoup:
        reviewPageList.append("https://glassdoor.com" + link['href'])
    #increments companies page limiter and checks if limit is reached
    mainPageCount += 1
    if mainPageCount >= mainPageLimit:
        mainHasNext = False

#list of all data entries for loading into the csv file
listOfLists = []

#gets review score and reviewer's position in company, then creates a list with that information and company name and adds it to the export csv
def getRatings(soup):
    ratingSpans = soup.find_all('span', {'class':'value-title'})
    positionSpans = soup.find_all('span', {'class':'authorJobTitle middle reviewer'})
    resultCount = 0
    for rspan, pspan in zip(ratingSpans[1:], positionSpans):
        postext = pspan.text
        if postext[0] == 'C':
            cleanpostext = postext[19:]
        else:
            cleanpostext = postext[18:]
        #add data entry list to list of data entry lists
        reviewEntry = [companyName, rspan['title'], cleanpostext]
        listOfLists.append(reviewEntry)
        resultCount += 1
    #checks to see if there are any more reviews (10 is max per page)
    if resultCount < 10:
        return False
    else:
        return True

#loop through list of review pages and access each one
for page in reviewPageList:
    driver.get(page)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    #gets the company name
    companyNameSoup = soup.find('p', {'class':'h1 strong tightAll'})
    companyName = companyNameSoup['data-company']
    #grabs the review information on the current page
    getRatings(soup)
    #page count limitation for review pages
    hasMorePages = True
    pageLimit = 2
    pageCount = 1
    #moves to next review page if page limit is not reached and reviews have not run out
    while hasMorePages:
        nextPage = soup.find('a', {'class':'pagination__ArrowStyle__nextArrow'})
        reviewlink = "https://glassdoor.com" + nextPage['href']
        driver.get(reviewlink)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        #get data and add to csv list, and check if reviews have run out
        hasMorePages = getRatings(soup)
        #increments page counter and checks if limit is reached
        pageCount += 1
        if pageCount >= pageLimit:
            hasMorePages = False

#creates csv file where data will be stored and exported
with open('scrape_test.csv', 'w') as f:
    scrape_writer = csv.writer(f)
    scrape_writer.writerows(listOfLists)

print('done')
