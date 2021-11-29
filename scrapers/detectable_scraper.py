import time
import random
import os

from bs4 import BeautifulSoup

from common import request_utils
from common import common_utils

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Some basic anti bot settings to mask
USER_AGENT_FILE = os.path.join(os.path.dirname(__file__), 'user-agents.txt')
REFERRER_LIST = ["http:www.google.com", "http:www.bing.com", "http:www.swisscows.com", "http:www.duckduckgo.com", "http:www.startpage.com"]
BASE_HEADERS = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9"}

# Proxy details
PROXY_USER = os.getenv("PROXY_USER", "sp70601931")
PROXY_PASS = os.getenv("PROXY_PASS", "Password123!")
# PROXY_USER = os.getenv("PROXY_USER", "")
# PROXY_PASS = os.getenv("PROXY_PASS", "")
if not PROXY_USER or not PROXY_PASS:
    print("Proxy credentials may be missing.  Ensure the PROXY_USER and PROXY_PASS environment variables are present on the Lambda configuration page.")

PROXY_ENDPOINT = f"http://user-{PROXY_USER}:{PROXY_PASS}@us.smartproxy.com:10000"
PROXIES = {"http": PROXY_ENDPOINT, "https": PROXY_ENDPOINT}


class DetectableScraper(object):
    def __init__(self):
        super(DetectableScraper, self).__init__()

        # Read the list of user agents from file
        try:
            with open(USER_AGENT_FILE, "r") as f:
                self.user_agent_pool = [line.strip() for line in f.readlines()]
        except Exception as e:
            print(f"Failed to open the user agent file: {USER_AGENT_FILE} with the error: {e}")

    def make_request(self,  url):
        """
        Creates a retry session and makes a request to the given url.

        If the initial request fails, an attempt is made to get the url
        through a proxy instead

        Args:
            url(str): The url to make a request to

        Returns:
            requests.Response or None: Returns a request object on a successful request else None
        """
        retry_session = request_utils.requests_retry_session(retries=1)

        headers = {"User-Agent": random.choice(self.user_agent_pool),
                    "Referer": random.choice(REFERRER_LIST)}
        headers.update(BASE_HEADERS)
        retry_session.headers.update(headers)

        try:
            print(f"Getting {url}")
            initial_get_start_time = time.time()
            r = retry_session.get(url, headers=headers, timeout=1, stream=True, verify=False)
            print(f"Initial GET request took {time.time() - initial_get_start_time}s to complete.")
        except Exception as e:
            print(f"Initial GET request took {time.time() - initial_get_start_time}s to complete.")
            print(f"Timed out getting the page, next attempt is with a proxy")
            try:
                proxy_get_start_time = time.time()
                r = retry_session.get(url, headers=headers, timeout=1, stream=True, verify=False, proxies=PROXIES)
                print(f"Proxy GET request took {time.time() - proxy_get_start_time}s to complete.")
            except Exception as e:
                print(f"Proxy GET request took {time.time() - proxy_get_start_time}s to complete.")
                print(f"Timed out getting the page with proxy, returning")
                return None

        return r

    def scrape_page(self, url):
        """
        Requests the page at the given url and tries to find the relavent data
        if the request is successful.

        Detects a possible IP Ban as well as when an anti cloudflare solution will be needed

        Args:
            url(str): The url to make a request to

        Returns:
            dict: If data was able to be found, a dict of this data is returned.  Else a dict
                    containing an error message to indicate the anti cloudflare scrape is needed.
        """
        response = self.make_request(url)

        # Couldn't make a response through a normal request?
        if not response:
            print(f"Response from {url} failed")
            print(f"Possible Bot Detection")
            return {"Error": "Needs anti-cloudflare request."}

        soup_parse_time = time.time()
        soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")
        print(f"Parsing page took {time.time() - soup_parse_time}s to complete.")

        # Connection was made, and data retrieved, but lets check if we have an anti-bot page
        if response.status_code != 200:
            # Check if we've been blocked
            if self.detect_block(soup):
                return {"Error": "Needs anti-cloudflare request."}
            return ""

        data_collection_time = time.time()
        # Check if we can find the OG properties first
        product_name = self.get_meta_tag_info(soup, "title")
        product_image = self.clean_url_string(self.get_meta_tag_info(soup, "image"))
        product_desc = self.get_meta_tag_info(soup, "description")

        # If we didn't have a title meta tag, check the title tag instead
        if not product_name:
            title_ele = soup.select("title")
            if title_ele:
                product_name = title_ele[0].contents[0]

        # Now look for all of the images likely to be the product
        image_set = self.get_all_images_filtered(soup)
        if product_image:
            image_set = [product_image] + image_set

        # Make sure all images are absolute
        final_image_set = set()
        for image_url in image_set:
            final_image_set.add(common_utils.relative_to_absolute_url(url, image_url))

        print(f"Data collection took {time.time() - data_collection_time}s to complete.")
        return {"product_name": product_name,
                "product_image_urls": list(final_image_set)[:20], # Take 20 images max
                "product_description": product_desc,
                "status_code": response.status_code}

    @staticmethod
    def contains_cloudflare_text(text):
        """
        Checks if a string contains known bot detection alert text

        Args:
            text(str): The text to check

        Returns:
            bool: True if known text is found else False
        """
        return any([x in text.lower() for x in ["cloudflare", "captcha"]])

    @staticmethod
    def detect_block(soup):
        """
        Looks through various elements on the page to try and determine whether
        or not we have been blocked by anti-bot

        Args:
            soup(BeautifulSoup.Soup): The soup object containing the parsed html

        Returns:
            bool: True if it was determined we were detected else False
        """
        # Check the title for cloudflare
        title_ele = soup.select("title")
        if title_ele:
            if title_ele[0].contents:
                title_string = title_ele[0].contents[0] or ""
                if DetectableScraper.contains_cloudflare_text(title_string):
                    return True

        body_ele = soup.select("body")
        if body_ele:
            if not body_ele[0].text:
                return True
            for i in body_ele[0].contents:
                if i:
                    if DetectableScraper.contains_cloudflare_text(i.text):
                        return True
        return False

    @staticmethod
    def get_meta_tag_info(soup, name):
        """
        Pulls the meta tag information from a parsed page

        Args:
            soup(BeautifulSoup.Soup): The soup object containing the parsed html
            name(str): The name of the element to search for

        Returns:
            str: The text from the tag if found
        """
        meta_tag_ele = soup.find("meta", property=f"og:{name}")
        if meta_tag_ele:
            return meta_tag_ele.get("content", "")
        return ""

    @staticmethod
    def clean_url_string(url):
        """
        Removes any newlines and spaces found at the start/end of a string

        Args:
            str(url): The url string to clean up

        Returns:
            str: The cleaned up text
        """
        return url.replace("\n", "").strip()

    @staticmethod
    def get_all_images_filtered(soup):
        """
        Searches a parsed html page for all img tags, pulls the src data, and then filters them down
        to the most likely images to be related to the product based.

        Args:
            soup(BeautifulSoup.Soup): The soup object containing the parsed html

        Returns:
            list(str): A list of found image urls.
        """
        image_set = set()
        for img_tag in soup.select("img"):
            img_url = ""

            # Check which attribute is being used to store the image data
            if img_tag.get("srcset", ""):
                img_url = DetectableScraper.clean_url_string(img_tag.get("srcset").split()[0])
            elif img_tag.get("src", ""):
                img_url = DetectableScraper.clean_url_string(img_tag.get("src"))

            # Only accept the image types likely to represent a product
            if any([x in img_url for x in ["image", "jpg", "png", "jpeg"]]):
                if ".svg" in img_url:
                    continue
                if img_url.startswith("data:"):
                    continue
                try:
                    getHeight = 126
                    for i in ["sh=", "hei=", "height="]:
                        tryingToFind = img_url.find(i)
                        if tryingToFind != -1:
                            s = img_url[tryingToFind+len(i):tryingToFind+(len(i)+4)]
                            getHeight = int(s.split('&')[0])
                            break
                    if getHeight < 125:
                        continue
                except:
                    print("Error parsing height")
                    
                image_set.add(img_url)

        return list(image_set)
