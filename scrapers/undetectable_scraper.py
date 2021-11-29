import random
import time

from common import common_utils
from common import driver_utils
from drivers import undetectable_driver

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import selenium.common.exceptions


class UndetectableScraper(undetectable_driver.UndetectableDriver):
	"""
	An undetectable scraper class that can bypass cloudflare security
	"""
	def __init__(self):
		"""
		Initialise the scraper by passing the options we'll need to use
		to our base class in order to configure the driver.
		"""
		super(UndetectableScraper, self).__init__()

		self.set_driver_args(["--headless", "--no-sandbox", "--disable-dev-shm-usage", "--disable-dev-tools",
		                      "--no-zygote", "--single-process", "--window-size=1920x1080"])

	def make_request(self, url, with_proxy=False, retry_count=2):
		"""
		Makes a request to the chosen url and retries once on failure.

		Args:
			url(str): The url to request
			with_proxy(bool): Whether or not to make the request through a proxy
			retry_count(int): How many time to retry the request

		"""
		start_init_time = time.time()
		#self.init_driver(with_proxies=with_proxy)
		self.driver = driver_utils.create_driver(self.driver_options, with_proxy=with_proxy, within_docker=self.within_docker)
		print(f"Driver initialisation Took {time.time() - start_init_time}s to finish")

		for i in range(retry_count):
			if i > 0:
				print("Retrying request...")
			if with_proxy:
				print(f"Getting {url} with proxy - Attempt {i+1}")
			else:
				print(f"Getting {url} - Attempt {i+1}")
			get_start_time = time.time()
			try:
				self.driver.get(url)
				print(f"Get request and parsing Took {time.time() - get_start_time}s to finish")
				return True
			except Exception as e:
				print(f"Get request and parsing Took {time.time() - get_start_time}s to finish")
				print(f"Failed to get {url} with the error: {e}")
				continue

		return False

	def scrape_page(self, url):
		"""
		Scrape a product page.  Determines which function is needed to pull the data
		by the domain of the url

		Args:
			url(str): The url to scrape

		Returns:
			dict: A dictionary of the data found on the page
		"""
		product_name = ""
		image_set = []
		product_image_url = ""
		product_desc = ""

		success = self.make_request(url)

		# Lets first check for OG tags
		if success:
			product_name, product_image, product_desc = self.get_base_properties()

		# If we couldn't find the tags, are we ip banned?
		# If we are, make a request with a proxy
		if self.check_for_ip_ban() or not success:
			self.driver.quit()
			success = self.make_request(url, with_proxy=True)
			time.sleep(random.uniform(0.2, 0.7))

			# Now a proxy request has been made, lets make sure this one isn't IP Banned
			if self.check_for_ip_ban() or not success:
				print("IP Banned")
				# We only try 1 new proxy on a failed request so return here
				return {"product_name": "", "product_image_urls": [""],
						"product_description": "", "status_code": 000}

			# If it's not banned, let check for the OG tags again first
			else:
				product_name, product_image, product_desc = self.get_base_properties()

		# Fallback to searching for elements on best guess
		if not product_name:
			product_name = self.driver.title
			product_name = product_name.split("|")[0].split(" - ")[0]

		# Check for a delayed ban - Rare, but annoying
		if self.check_for_ip_ban(delay=False):
			print("IP Banned")
			return {"product_name": "",
			        "product_image_urls": [""],
			        "product_description": "",
			        "status_code": 000}

		data_collection_time_start = time.time()
		
		
		image_set = driver_utils.get_all_imgs_filtered(self.driver)
		# If we still only have 0/1 images, just pull all of the images, and grab a filtered selection
		if len(image_set) < 2:
			product_image_ele, product_image_url = driver_utils.best_guess_image_element(self.driver)
			if product_image_url:
				image_set = driver_utils.find_sibling_images(product_image_ele, depth=0)

		# If we couldn't find the images, make sure no elements in the dom are interfering with the
		# renderer
		if not image_set:
			self.remove_accept_dialogs()
			self.remove_location_dialogs()
			self.sim_close_dialog()

			# Find the element most likely to be the product image
			product_image_ele, product_image_url = driver_utils.best_guess_image_element(self.driver)
			if product_image_url:
				print("Found items after first DOM removal")
				image_set = driver_utils.find_sibling_images(product_image_ele)

		# Still no images, search deeper
		if not image_set:
			self.remove_modals()
			self.remove_iframes()
			self.sim_close_dialog()

			# Find the element most likely to be the product image
			product_image_ele, product_image_url = driver_utils.best_guess_image_element(self.driver)
			if product_image_url:
				print("Found items after second DOM removal")
				image_set = driver_utils.find_sibling_images(product_image_ele)

		# Make sure all images are absolute
		final_image_set = set()
		for image_url in image_set:
			final_image_set.add(common_utils.relative_to_absolute_url(url, image_url))

		ret = {"product_name": product_name.strip(),
		       "product_image_urls": list(final_image_set)[:20], # Take only 20 images max
		       "product_description": product_desc}

		if product_name and image_set:
			ret["status_code"] = 200
		else:
			ret["status_code"] = 000

		print(f"Data collection took {time.time() - data_collection_time_start}s to complete.")
		return ret

	def remove_modals(self):
		"""
		Removes any modal dialogs from the DOM
		"""
		for i in self.driver.find_elements(By.XPATH, "//*[attribute::*[contains(., 'modal')]]"):
			try:
				self.driver.execute_script("""var element = arguments[0];element.parentNode.removeChild(element);""", i)
			except selenium.common.exceptions.StaleElementReferenceException:
				continue

	def remove_iframes(self):
		"""
		Removes any iframes from the DOM
		"""
		try:
			for i in self.driver.find_elements(By.XPATH, "//iframe"):
				try:
					self.driver.execute_script("""var element = arguments[0];element.parentNode.removeChild(element);""", i)
				except selenium.common.exceptions.StaleElementReferenceException as e:
					pass
		except Exception:
			pass

	def get_og_property_value(self, name):
		"""
		Get a value from a meta tag based on the name

		Args:
			name(str): The name of the meta tag to find

		Returns:
			str: The meta tags content or an empty string if the tag doesn't exist
		"""
		try:
			return self.driver.find_element(By.XPATH, f"//meta[@property='og:{name}']").get_attribute("content")
		except Exception:
			return ""

	def get_base_properties(self):
		"""
		Get the base properties of the product from meta tags if they exist.

		Returns:
			tuple(str): A tuple of strings holding the information found, if any.
		"""
		product_name = self.get_og_property_value("title")
		product_image = self.get_og_property_value("image")
		product_desc = self.get_og_property_value("description")

		return product_name, product_image, product_desc

	def sim_click(self, ele):
		"""
		Simulate a click an element

		Args:
			ele(WebElement): The web element to simulate a click on

		Returns:
			bool: True on a success else False
		"""
		exceptions_to_catch = (selenium.common.exceptions.ElementNotInteractableException, selenium.common.exceptions.ElementClickInterceptedException,
								selenium.common.exceptions.MoveTargetOutOfBoundsException, selenium.common.exceptions.StaleElementReferenceException)
		try:
			ele.click()
			return True
		except exceptions_to_catch:
			pass
		try:
			ActionChains(self.driver).move_to_element(ele).click(ele).perform()
			return True
		except exceptions_to_catch:
			pass
		return False

	def remove_accept_dialogs(self):
		"""
		Remove cookie dialogs from the DOM
		"""
		try:
			eles = self.driver.find_elements(By.XPATH, f"//button[contains(text(),'Accept All Cookies') or "
														f"contains(text(),'ACCEPT ALL COOKIES') or "
														f"contains(text(),'Accept') or "
														f"contains(text(),'ACCEPT')]")
		except selenium.common.exceptions.NoSuchElementException as e:
			return

		if eles:
			for ele in eles:
				self.sim_click(ele)

	def remove_location_dialogs(self):
		"""
		Remove any location specific dialogs
		"""
		for ele in self.driver.find_elements(By.XPATH, f"//button[contains(text(),'United States') or "
														f"attribute::*[contains(.,'United States')] or "
														f"contains(text(),'stay here') or "
														f"attribute::*[contains(.,'stay here')] or "
														f"contains(text(),'Shop now') or "
														f"attribute::*[contains(.,'Shop now')] or "
														f"contains(text(),'States') or "
														f"attribute::*[contains(.,'States')] or "
														f"contains(text(),'Start Shopping') or "
														f"attribute::*[contains(.,'Start Shopping')]]"):
			# Try various means to click the ele
			if ele:
				self.sim_click(ele)

	def sim_close_dialog(self):
		"""
		Sim a click to close any dialogs
		"""
		for ele in self.driver.find_elements(By.XPATH, "//button[attribute::*[contains(., 'close')] or "
		                                               "attribute::*[contains(., 'Close')]]"):
			# Try various means to click the ele
			if ele:
				self.sim_click(ele)
			break
		ActionChains(self.driver).send_keys(Keys.HOME).perform()

	def check_for_ip_ban(self, delay=False):
		"""
		Checks the page for common elements to indicate an IP ban.

		Returns
		"""
		title = self.driver.title or ""
		# If theres no reference to being blocker in the title, check the body
		if any([x in title.lower() for x in ["denied", "blocked", "unusual", "forbidden"]]):
			return True
		else:
			try:
				if delay:
					time.sleep(1)
				body_ele = self.driver.find_element(By.XPATH, "//body")
				if body_ele:
					if "unusual activity" in body_ele.text.lower():
						return True
			except Exception as e:
				return False
