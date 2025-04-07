from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import numpy as np
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# all specifications

preferred_location = "North Coast" #input X if no location

preferred_date = '2025-04-10' #YEAR-MONTH-DAY format. Include leading zeros in months/days.

preferred_people = 2

permit_number = '4098362' #the permit number found on recreation.gov

#example locations below, they need to match the listing exactly. Any number of permits requested will work here, as long as you list them all.
# IF IT IS ONLY ONE PERMIT, MUST INCLUDE A COMMA AFTER
permit_names = (
                'Seafield Creek',
                )

# Path to the GeckoDriver executable | this is if you want to run it locally, so unnecessary if on colab
os_system = os.name
if os.name == 'nt':
    driver_path = 'geckodriver.exe'
elif os.name == 'posix':
    driver_path = os.path.join(os.getcwd(), 'geckodriver')


###SMTP info for the email automation

smtp_server = 'smtp.gmail.com'
smtp_port = 587
smtp_username = 'quinn.mackay@gmail.com'
smtp_password = 'qnud ykgz ujxb quus' #this is an app password, different from normal google password

from_email = 'quinn.mackay@gmail.com' #typically same as smtp_username
to_email = 'quinn.mackay@gmail.com' #can be same as sending email
subject = 'Recreation Gov Scraper Update' #it will only send an update if a site is available

def recgov():
        
    ######### startup the browser

    #configuration
    headOption = webdriver.FirefoxOptions()
    headOption.add_argument("--headless")


    # Initialize the WebDriver | code below is for locally run firefox
    service = Service(driver_path)
    driver = webdriver.Firefox(service=service, options=headOption)

    #change this to the permit you want
    url = "https://www.recreation.gov/permits/{}/registration/detailed-availability?date={}".format(permit_number, preferred_date)
    driver.get(url)

    ######### click location button & wait for it to be present

    if preferred_location != "X":
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//button[span/span[contains(text(), '{}')]]".format(preferred_location)))
        )

        location_button = driver.find_element(By.XPATH, "//button[span/span[contains(text(), '{}')]]".format(preferred_location))

        location_button.click()

    ######### open dropdown and add people

    for x in range(preferred_people):
        people_button = driver.find_element(By.ID, 'guest-counter')
        people_button.click()
        time.sleep(0.1)
        add_people_button = driver.find_element(By.XPATH, "//button[@aria-label='Add Peoples']")
        add_people_button.click()
        time.sleep(0.1)
        people_button.click()
        time.sleep(0.2)


    ######### remedy the date to correct format

    date_object = datetime.strptime(preferred_date, '%Y-%m-%d')

    lengthy_date = date_object.strftime('%B %d, %Y')
    lengthy_date = lengthy_date.replace(' 0', ' ')  # This removes the leading zero

    ######### scroll down to load everything

    def scroll_incrementally(driver, scroll_pause_time=2, max_scrolls=10):
        for _ in range(max_scrolls):
            driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
            time.sleep(scroll_pause_time)  # Wait for content to load
            # Check if the end of the page is reached
            if driver.execute_script("return window.innerHeight + window.scrollY >= document.body.scrollHeight"):
                break

    # Perform incremental scrolling
    scroll_incrementally(driver)

    # Wait for elements to be present
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.sarsa-button-content'))
    )

    ######### do checks for availability

    page_source = driver.page_source

    time.sleep(1)
    succ_storage = ["Blank"] * len(permit_names)

    for i in range(len(permit_names)):

        search_phrase_success = '{} on {} - Available'.format(permit_names[i], lengthy_date)
        search_phrase_fail = '{} on {} - Unavailable'.format(permit_names[i], lengthy_date)
        search_phrase_walkup = '{} on {} - Walk-Up'.format(permit_names[i], lengthy_date)

        if search_phrase_success in page_source:
            print(permit_names[i], 'is Available on', lengthy_date)
            succ_storage[i] = '{} is now available on {}'.format(permit_names[i], lengthy_date)
        elif search_phrase_walkup in page_source:
            print(permit_names[i], 'is Walk-Up on', lengthy_date)
        elif search_phrase_fail in page_source:
            print(permit_names[i], 'is Unavailable on', lengthy_date)
        else:
            print(permit_names[i], 'has not been found. Is it spelled correctly?')
            succ_storage[i] = '{} is not found on the list of permits. Is it spelled correctly?'.format(permit_names[i])

    driver.quit()
    return succ_storage

def email_protocol():

    non_blank_succ_storage = [entry for entry in succ_storage if entry != "Blank"]
    body = "\n".join(non_blank_succ_storage)

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        server.quit()

def email_send():
    if any(item != "Blank" for item in succ_storage):
        email_protocol()
        sys.exit()

# running the loop

while True: 
    succ_storage = recgov()
    email_send()
    time.sleep(60)