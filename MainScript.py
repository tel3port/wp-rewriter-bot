from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from random import randint
import random
import traceback
import heroku3
import time
from http_request_randomizer.requests.proxy.requestProxy import RequestProxy
import globals as gls
import re
from collections import defaultdict
import requests
from urllib.request import urlparse, urljoin
from bs4 import BeautifulSoup
import colorama
import asyncio
import aiohttp
import os
import uuid
import csv

colorama.init()
GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET

total_urls_visited = 0

global parsed_links
parsed_links = []

# initialize the set of links (unique links)
internal_urls = set()
external_urls = set()

wp_bot_name = "wp-rewriterbot-1"


def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_website_links(url):
    try:
        """
        Returns all URLs that is found on `url` in which it belongs to the same website
        """
        # all URLs of `url`
        urls = set()
        # domain name of the URL without the protocol
        domain_name = urlparse(url).netloc
        soup = BeautifulSoup(requests.get(url).content, "html.parser")
        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None:
                # href empty tag
                continue
            # join the URL if it's relative (not absolute link)
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            # remove URL GET parameters, URL fragments, etc.
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            if not is_valid(href):
                # not a valid URL
                continue
            if href in internal_urls:
                # already in the set
                continue
            if domain_name not in href:
                # external link
                if href not in external_urls:
                    print(f"{GRAY}[!] External link: {href}{RESET}")
                    external_urls.add(href)

                continue
            print(f"{GREEN}[*] Internal link: {href}{RESET}")
            urls.add(href)
            internal_urls.add(href)
    except Exception as e:
        print(e)
        return False

    return urls


def crawl(url, max_urls=35):
    """
    Crawls a web page and extracts all links.
    You'll find all links in `external_urls` and `internal_urls` global set variables.
    params:
        max_urls (int): number of max urls to crawl, default is 30.
    """
    global total_urls_visited
    total_urls_visited += 1
    links = get_all_website_links(url)
    for link in links:
        print(f"total_urls_visited:{total_urls_visited} -- max_urls:{max_urls}")
        if total_urls_visited > max_urls:
            break
        crawl(link, max_urls=max_urls)


async def if_comment_box_exists(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                html_text = await resp.read()

        if "comment-form-field" in str(html_text) \
                or "comments-area" in str(html_text) \
                or "comment-form" in str(html_text) \
                or "jetpack_remote_comment" in str(html_text) \
                or "reply-title" in str(html_text) \
                or "captcha" not in str(html_text) \
                or "comment-respond" in str(html_text):
            with open("EXTRACTOR/extracted/FINAL_URL_LIST.txt", "a") as new_urls_file:
                print(url.strip(), file=new_urls_file)
            return True
        else:
            pass
            # with open("extracted/x.txt", "a") as new_urls_file:
            #     print(url.strip(), file=new_urls_file)

    except Exception as e:
        print(e)
        return False


async def parse_tasks(url):
    await if_comment_box_exists(url)


def int_checker(url):
    char_list = url.split('/')
    last_element = char_list[len(char_list) - 2]

    if len(last_element) > 4:
        return False

    return True


async def main():
    tasks = []
    for url in (open("EXTRACTOR/extracted/internal_links.txt").readlines()):
        t = loop.create_task(parse_tasks(url))
        tasks.append(t)

    await asyncio.wait(tasks)


def create_append_text_file(extd_links, my_uuid):
    if not os.path.exists(f'./EXTRACTOR/urls/static_url_list_{my_uuid}.txt'):
        with open(f'./EXTRACTOR/urls/static_url_list_{my_uuid}.txt', 'a') as final_urls_list_file:
            for single_lk in extd_links:
                print(single_lk.strip(), file=final_urls_list_file)


def soft_file_cleanup():
    open('EXTRACTOR/extracted/internal_links.txt', 'w').close()
    open('EXTRACTOR/extracted/external_links.txt', 'w').close()


def hard_file_cleanup():
    open('EXTRACTOR/extracted/internal_links.txt', 'w').close()
    open('EXTRACTOR/extracted/external_links.txt', 'w').close()
    open('EXTRACTOR/extracted/blog_link_file.txt', 'w').close()
    open('EXTRACTOR/extracted/FINAL_URL_LIST.txt', 'w').close()
    open('GENERATED/titles_headings.csv', 'w').close()


def static_url_path_list():
    static_url_list_paths = os.listdir('./EXTRACTOR/urls')

    return static_url_list_paths
    # return f'EXTRACTOR/urls/static_url_list_26f8faa8c60b4542aed6d89847441296.txt'


class SpinBot:
    def __init__(self, bot_name, my_proxy):
        self.my_proxy = my_proxy
        self.bot_name = bot_name
        chrome_options = webdriver.ChromeOptions()
        chrome_options.set_capability('unhandledPromptBehavior', 'accept')
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--disable-dev-sgm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        my_proxy_address = self.my_proxy.get_address()
        webdriver.DesiredCapabilities.CHROME['proxy'] = {
            "httpProxy": my_proxy_address,
            "ftpProxy": my_proxy_address,
            "sslProxy": my_proxy_address,

            "proxyType": "MANUAL",

        }
        # self.driver = webdriver.Chrome(executable_path='./chromedriver', options=chrome_options)
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)
        print("my ip address", my_proxy_address)

    def blog_extractor(self):
        with open("EXTRACTOR/extracted/search_terms.txt") as search_terms_file:
            search_terms = [line.strip() for line in search_terms_file]
            random_search_term = search_terms[randint(0, len(search_terms) - 2)]
            print(f"searching for blogs on: {random_search_term}")

        self.driver.get(f'https://en.wordpress.com/tag/{random_search_term}/')

        data = self.driver.page_source

        soup = BeautifulSoup(data, "html.parser")

        links_list = soup.find_all('a', class_="blog-url")

        for single_link in links_list:
            link = single_link['href']
            with open("EXTRACTOR/extracted/blog_link_file.txt", "a") as new_blogs_file:
                print(link.strip(), file=new_blogs_file)

    def restart_application(self):
        heroku_conn = heroku3.from_key('b477d2e0-d1ba-48b1-a2df-88d87db973e7')
        app = heroku_conn.apps()[self.bot_name]
        app.restart()

    def clean_up(self):
        t = randint(50, 100)
        print(f"clean up sleep for {t} seconds")
        time.sleep(t)

        self.driver.delete_all_cookies()
        self.restart_application()

    @staticmethod
    def article_counter():
        articles = os.listdir('./GENERATED')

        return len(articles)

    def wp_post_getter(self, post_url):
        self.driver.get(post_url)
        time.sleep(5)

        data = self.driver.page_source

        soup = BeautifulSoup(data, "html.parser")

        title = soup.title.text  # extracts the title of the page
        content = soup.find('div', class_="entry-content")

        full_article = ""
        count = 0
        advert = f'\n We are making a random film about this. Book for free HERE! https://my7.travel.blog/awesome/\n'
        for single_paragraph in content.find_all_next('p'):
            if len(full_article.split(" ")) <= 500:

                full_article += single_paragraph.text
                if count % 3 == 0:
                    full_article += advert

                count += 1

        print(full_article)

        title_article = [title, full_article]
        return title_article

    @staticmethod
    def create_append_article_file(extracted):

        csv_file = open(f'./GENERATED/titles_headings.csv', 'a', newline='')
        obj = csv.writer(csv_file)
        obj.writerow(extracted)

    def post_getter_saver(self, post_url):
        try:

            extracted = self.wp_post_getter(post_url)
            self.create_append_article_file(extracted)

        except Exception as em:
            print(f'comment Error occurred with url: {post_url} ' + str(em))
            print(traceback.format_exc())

            if 'invalid session id' in str(em):
                self.clean_up()

        finally:
            print("post_getter_saver() done")

    @staticmethod
    def wp_post_extractor():
        titles = []
        posts = []
        csv_file = open(f'./GENERATED/titles_headings.csv', 'r', newline='')
        obj = csv.reader(csv_file)

        for single_row in obj:
            titles.append(single_row[0])
            posts.append(single_row[1])

        return titles, posts

    def wp_login(self):
        wp_login_url = 'https://wordpress.com/wp-login.php?checkemail=confirm'
        wp_email_xpath = '//*[@id="user_login"]'
        wp_password_xpath = '//*[@id="user_pass"]'
        wp_login_xpath = '//*[@id="wp-submit"]'
        wp_email = "johnsong201812@protonmail.com"
        wp_password = 'ap7fktQ43BZD&ZjqjwT^ak7GAD'

        try:
            self.driver.delete_all_cookies()
            self.driver.get(wp_login_url)
            gls.sleep_time()
            self.driver.find_element_by_xpath(wp_email_xpath).send_keys(wp_email)
            gls.sleep_time()
            self.driver.find_element_by_xpath(wp_password_xpath).send_keys(wp_password)
            gls.sleep_time()
            continue_btn = self.driver.find_element_by_xpath(wp_login_xpath)
            gls.sleep_time()
            continue_btn.click()

        except Exception as ex:
            print("wp login error at ", ex)
            print(traceback.format_exc())

    def wp_post(self, title, post):
        wp_post_url = 'https://hobbie370330789.wordpress.com/wp-admin/post-new.php'
        wp_title_xpath = '//*[@id="post-title-0"]'
        wp_post_xpath = '//*[@aria-label="Empty block; start writing or type forward slash to choose a block"]'
        wp_publish_1_xpath = '//button[text()="Publish"]'
        prepub_checkbox_xpath = '//*[@id="inspector-checkbox-control-2"]'
        close_panel_xpath = '//*[@aria-label="Close panel"]'

        self.driver.get(wp_post_url)

        try:
            gls.sleep_time()
            time.sleep(20)
            self.driver.find_element_by_xpath(wp_title_xpath).send_keys(title)
            gls.sleep_time()
            self.driver.find_element_by_class_name('block-editor-writing-flow__click-redirect').click()
            gls.sleep_time()
            self.driver.find_element_by_xpath(wp_post_xpath).send_keys(post)
            gls.sleep_time()
            pub1_btn = self.driver.find_element_by_xpath(wp_publish_1_xpath)
            gls.sleep_time()
            pub1_btn.click()
            gls.sleep_time()
            prepub_checkbox = self.driver.find_element_by_xpath(prepub_checkbox_xpath)
            if prepub_checkbox.is_selected():
                prepub_checkbox.click()
            gls.sleep_time()
            close_btn = self.driver.find_element_by_xpath(close_panel_xpath)
            gls.sleep_time()
            close_btn.click()
            gls.sleep_time()
            pub1_btn.click()
            time.sleep(15)

        except Exception as ex:
            print("wp post error at ", ex)
            print(traceback.format_exc())

        try:
            WebDriverWait(self.driver, 3).until(EC.alert_is_present(), 'Timed out waiting for PA creation ' +'confirmation popup to appear.')
            alert = self.driver.switch_to.alert()
            alert.accept()
            print("alert accepted")
        except TimeoutException:
            print("no alert")

    def clear_stuff(self):
        self.driver.delete_all_cookies()

    def handle_alert(self):
        self.driver.switch_to.alert.accept()


if __name__ == "__main__":

    while 1:
        time.sleep(5)
        count = 0
        random_cycle_nums = randint(300, 700)

        req_proxy = RequestProxy()  # you may get different number of proxy when  you run this at each time
        proxies = req_proxy.get_proxy_list()  # this will create proxy list
        random_proxy = proxies[randint(0, len(proxies) - 1)]

        bot = SpinBot(wp_bot_name, random_proxy)

        # for _ in range(10):
        #     bot.blog_extractor()

        # ===============LOOPS THRU EACH BLOG AND EXTRACTS ALL INTERNAL AND EXTERNAL URLS========================

        # try:
        #     with open(f"EXTRACTOR/extracted/blog_link_file.txt", "r") as blog_list_file:
        #         main_blog_list = [line.strip() for line in blog_list_file]
        #         blog_list_set = set(main_blog_list)
        #
        #     for single_blog in blog_list_set:
        #         # initialize the set of links (unique links)
        #         internal_urls = set()
        #         external_urls = set()
        #         internal_urls.clear()
        #         external_urls.clear()
        #
        #         print(f"WORKING ON: {single_blog}")
        #         try:
        #             crawl(single_blog, max_urls=35)
        #         except Exception as e:
        #             print(e)
        #         print("[+] Total Internal links:", len(internal_urls))
        #         print("[+] Total External links:", len(external_urls))
        #         print("[+] Total URLs:", len(external_urls) + len(internal_urls))
        #
        #         # todo find out why do i need this urlparse
        #         # domain_name = urlparse(single_blog).netloc
        #
        #         # save the internal links to a file ====> {domain_name}_internal_links.txt"
        #         with open(f"EXTRACTOR/extracted/internal_links.txt", "a") as f:
        #             for internal_link in internal_urls:
        #                 if not ('/tag/' in internal_link or "/categor" in internal_link
        #                         or "faq" in internal_link or "events" in internal_link
        #                         or "policy" in internal_link or "terms" in internal_link
        #                         or "photos" in internal_link or "author" in internal_link
        #                         or "label" in internal_link or "video" in internal_link
        #                         or "search" in internal_link or "png" in internal_link
        #                         or "pdf" in internal_link or "jpg" in internal_link
        #                         or "facebook" in internal_link or "twitter" in internal_link
        #                         or "nytimes" in internal_link or "wsj" in internal_link
        #                         or "reddit" in internal_link or "bbc" in internal_link
        #                         or "wikipedia" in internal_link or "guardian" in internal_link
        #                         or "flickr" in internal_link or "cnn" in internal_link
        #                         or "ttps://wordpre" in internal_link or "google" in internal_link
        #                         or "cookies" in internal_link or "instagram" in internal_link
        #                         or "youtube" in internal_link or "spotify" in internal_link
        #                         or "mail" in internal_link or "pinterest" in internal_link
        #                         or "tumblr" in internal_link or "label" in internal_link
        #                         or "dribble" in internal_link or "unsplash" in internal_link
        #                         or "automattic" in internal_link or "facebook" in internal_link
        #                         or "amazon" in internal_link or "amzn" in internal_link
        #                         or "doc" in internal_link or "amzn" in internal_link
        #                         or int_checker(internal_link)) or "jsp" in internal_link:
        #                     print(internal_link.strip(), file=f)
        #                 else:
        #                     pass
        #         #
        #         loop = asyncio.get_event_loop()
        #         loop.run_until_complete(main())
        #
        #         soft_file_cleanup()
        #
        # except Exception as e:
        #     print(e)
        #
        # with open("EXTRACTOR/extracted/FINAL_URL_LIST.txt") as extracted_links_file:
        #     global extracted_links
        #     extracted_links = [line.strip() for line in extracted_links_file]
        #
        # create_append_text_file(extracted_links, uuid.uuid4().hex)

        for single_static_path in static_url_path_list():
            with open(f"EXTRACTOR/urls/{single_static_path}", "r") as internal_link_file:
                parsed_links = [line.strip() for line in internal_link_file]

                # to remove duplicates
                parsed_links_set = set()
                parsed_links_set.update(parsed_links)

            # extracts the posts and headings for the links and saves them into csv
            print("extracting posts and headings and saving to csv")
            if len(parsed_links_set) > 0:
                for link in list(parsed_links_set):
                    bot.post_getter_saver(link)
            print("extraction of posts and headings DONE")

        try:
            titles_posts = bot.wp_post_extractor()

            my_titles = titles_posts[0]
            my_posts = titles_posts[1]

            loop_nums = len(my_posts)
            print("number of times bot should post: ", loop_nums)
            for i in range(loop_nums):
                if i % 6 == 0:
                    bot.wp_login()

                bot.wp_post(my_titles[i], my_posts[i])
                print(f"single posting number {i} DONE")

        except Exception as e:
            print("posting error at ", e)
            print(traceback.format_exc())

        hard_file_cleanup()
        break

print("TESTING DONE!")
