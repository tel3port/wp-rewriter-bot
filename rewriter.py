import time
from bs4 import BeautifulSoup
from selenium import webdriver
import traceback
import os
import uuid
import globals as gls
import csv

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--disable-dev-sgm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
driver = webdriver.Chrome(executable_path='./chromedriver', options=chrome_options)


def wp_post_getter(post_url):
    driver.get(post_url)
    time.sleep(5)

    data = driver.page_source

    soup = BeautifulSoup(data, "html.parser")

    article = soup.find('div', class_="entry-content")
    title = soup.title.text  # extracts the title of the page

    return title, article.text


def create_append_article_file(extracted, a_uuid):
    if not os.path.exists(f'./GENERATED/article_{a_uuid}.txt'):
        with open(f'./GENERATED/article_{a_uuid}.txt', 'a') as final_urls_list_file:
            print(extracted, file=final_urls_list_file)


def post_getter_saver(post_url, single_uuid):
    try:
        extracted = wp_post_getter(post_url)
        create_append_article_file(extracted, single_uuid)

    except Exception as em:
        print(f'comment Error occurred with url: {post_url} ' + str(em))
        print(traceback.format_exc())

    finally:
        print("post_spinner() done")


def wp_login():
    wp_login_url = 'https://wordpress.com/wp-login.php?checkemail=confirm'
    wp_email_xpath = '//*[@id="user_login"]'
    wp_password_xpath = '//*[@id="user_pass"]'
    wp_login_xpath = '//*[@id="wp-submit"]'
    wp_email = "johnsong201812@protonmail.com"
    wp_password = 'ap7fktQ43BZD&ZjqjwT^ak7GAD'

    try:
        driver.get(wp_login_url)
        gls.sleep_time()
        driver.find_element_by_xpath(wp_email_xpath).send_keys(wp_email)
        gls.sleep_time()
        driver.find_element_by_xpath(wp_password_xpath).send_keys(wp_password)
        gls.sleep_time()
        continue_btn = driver.find_element_by_xpath(wp_login_xpath)
        gls.sleep_time()
        continue_btn.click()

    except Exception as ex:
        print("wp login error at ", ex)
        print(traceback.format_exc())


def wp_post(title, post):
    wp_post_url = 'https://hobbie370330789.wordpress.com/wp-admin/post-new.php'
    wp_title_xpath = '//*[@id="post-title-0"]'
    wp_post_xpath = '//*[@aria-label="Empty block; start writing or type forward slash to choose a block"]'
    wp_publish_1_xpath = '//button[text()="Publish"]'
    prepub_checkbox_xpath = '//*[@id="inspector-checkbox-control-2"]'
    close_panel_xpath = '//*[@aria-label="Close panel"]'
    try:
        driver.get(wp_post_url)
        gls.sleep_time()
        time.sleep(20)

        driver.find_element_by_xpath(wp_title_xpath).send_keys(title)
        gls.sleep_time()
        driver.find_element_by_xpath('//*[@id="editor"]/div/div/div[1]/div/div[2]/div[1]/div[4]/div[2]/div/div/div[2]/div[2]/div/div[2]/div').click()
        gls.sleep_time()
        driver.find_element_by_xpath(wp_post_xpath).send_keys(post)
        gls.sleep_time()
        pub1_btn = driver.find_element_by_xpath(wp_publish_1_xpath)
        gls.sleep_time()
        pub1_btn.click()
        gls.sleep_time()
        prepub_checkbox = driver.find_element_by_xpath(prepub_checkbox_xpath)
        if prepub_checkbox.is_selected():
            prepub_checkbox.click()
        gls.sleep_time()
        close_btn = driver.find_element_by_xpath(close_panel_xpath)
        gls.sleep_time()
        close_btn.click()
        gls.sleep_time()
        pub1_btn.click()

    except Exception as ex:
        print("wp post error at ", ex)
        print(traceback.format_exc())

# post_getter_saver('https://morealtitude.wordpress.com/2009/09/09/snowkiting-as-dumb-as-it-sounds/', uuid.uuid4().hex)


def wp_post_extractor():
    csv_file = open(f'./GENERATED/titles_headings.csv', 'r', newline='')
    obj = csv.reader(csv_file)

    for single_row in obj:
        print(single_row[0])
        print(single_row[1])
        print('--------------------')

    title = ''
    post = ''
    return title, post

wp_post_extractor()