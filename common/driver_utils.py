import os
import sys

import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import SessionNotCreatedException
import selenium.common.exceptions
from selenium.webdriver.common.by import By


def wait_for_element(driver, expr_type, expr, wait_time=60):
	"""
	Waits for an element to load before trying to return it.

	Args:
		driver(WebDriver or WebElement): A driver or webelement to start from for a search.
		expr_type(By): The type of search query to use.
		expr(str): The query itself.
		wait_time(int): The time in seconds to wait before giving up on finding the element.

	Returns:
		WebElement or None: Returns the found web element on success else None.
	"""
	try:
		ele = WebDriverWait(driver, wait_time).until(EC.visibility_of_element_located((expr_type, expr)))
		return ele
	except selenium.common.exceptions.TimeoutException:
		return


def find_child_image_source(ele):
	"""
	Looks for img tags present in the child nodes and returns the src url

	Args:
		ele(WebElement): The element to start the search from

	Returns:
		str: The url of the img if found
	"""
	try:
		img_ele = ele.find_element(By.XPATH, ".//img")
		if img_ele:
			return get_image_url_from_element(img_ele, recursive=False)
	except selenium.common.exceptions.NoSuchElementException as e:
		pass

	return ""

def get_image_url_from_element(ele, recursive=True):
	"""
	Finds the url for the img element.
	Searches children in recursive is True

	Args:
		ele(WebElement): The element to start the search from
		recursive(bool): If True, child nodes will be searched

	Returns:
		str: The url of the img if found
	"""
	if ele.get_attribute("srcset"):
		return ele.get_attribute("srcset").split()[0].strip()
	elif ele.get_attribute("src"):
		return ele.get_attribute("src").strip()

	# Possible that the element on top isn't an image, dive deeper
	if recursive:
		return find_child_image_source(ele)


def find_sibling_images(ele, depth=2):
	"""
	Looks for possible sibling img tags

	Args:
		ele(WebElement): The element to start the search from
		depth(int): How deep to search the DOM

	Returns:
		str: The url of the img if found
	"""
	found_images = set()
	img_tags = []

	depth_expr = "../../../..//img"
	for d in range(depth):
		try:
			img_tags = ele.find_elements(By.XPATH, depth_expr)
		except Exception as e:
			continue

		# If we find more than 1 image, filter and get the urls from the tags and break out of the loop
		if len(img_tags) > 2:
			for img_tag in img_tags:
				image_url = get_image_url_from_element(img_tag)
				if image_url:
					if ".svg" in image_url.strip():
						continue
					found_images.add(image_url.strip())
			break
		# Set up the next depth expression
		depth_expr = "../../../" + depth_expr

	# If we didn't find any new images, just grab the original if present
	if not found_images:
		if img_tags:
			for img_tag in img_tags:
				try:
					found_images.add(get_image_url_from_element(img_tag).strip())
				except Exception as e:
					continue

	return [x for x in list(found_images) if x]


def get_center_of_window(driver):
	"""
	Returns the center points of the simmed display

	Args
		driver(WebDriver): The driver to query

	Returns:
		list(int): A pair of ints representing the center of the simmed window
	"""
	win_size = driver.get_window_size()
	return [win_size["width"] / 2, win_size["height"] / 2]


def find_element_at_point(driver, x, y):
	"""
	Returns an element under a coordinate through JS

	Args
		driver(WebDriver): The driver to query

	Returns:
		WebElement: The element found at the given coordinates
	"""
	return driver.execute_script("""return document.elementFromPoint(arguments[0], arguments[1]);""", x, y)


def best_guess_image_position(driver):
	"""
	Returns an element at the most likely product position

	Args
		driver(WebDriver): The driver to query

	Returns:
		WebElement: The resulting element
	"""
	center_of_page = get_center_of_window(driver)
	center_of_page[0] = center_of_page[0] - 200
	product_image_ele = find_element_at_point(driver, center_of_page[0], center_of_page[1])
	return product_image_ele


def best_guess_image_element(driver):
	"""
	Find the most likely image to be the product.
	From there, it search it's parent and children for other images
	in order to find the entire range of images used for the product

	Args
		driver(WebDriver): The driver to query

	Returns:
		WebElement, str: The resulting element, and image url
	"""
	product_image_url = ""
	product_image_ele = None
	for i in range(3):
		product_image_ele = best_guess_image_position(driver)

		try:
			product_image_url = get_image_url_from_element(product_image_ele)
			break
		except selenium.common.exceptions.StaleElementReferenceException:
			continue

	return (product_image_ele, product_image_url)


def get_all_imgs_filtered(driver):
	"""
	Finds all of the img tags on the page, and then filters them down
	to try and find the most likely product images

	Args
		driver(WebDriver): The driver to query

	Returns:
		list(str): A list of found image urls
	"""
	image_set = []
	# Loop the tags
	img_tags = driver.find_elements(By.XPATH, "//*[self::image or self::img]")
	for img_tag in img_tags:
		# Check which attribute is being used to store the image data
		img_url = get_image_url_from_element(img_tag, recursive=False)

		# Only accept the image types likely to represent a product
		if img_url and any([x in img_url for x in ["image", "jpg", "png", "jpeg"]]):
			if ".svg" in img_url:
				continue
			if img_url.startswith("data:"):
				continue
			image_set.append(img_url)

	return image_set


def create_driver(options, within_docker=False, with_proxy=False):
	"""
	MODIFY WITH CARE!
	Create a driver with the specified options.

	Args:
		uc.ChromeOptions: A set of options to pass to the driver.

	Returns:
		uc.Chrome: A configured Chrome driver based on the options.
	"""

	from seleniumwire.undetected_chromedriver.v2 import Chrome as sw_Chrome
	from seleniumwire.undetected_chromedriver.v2 import ChromeOptions as sw_ChromeOptions
	# Create the options we will pass to the driver
	# We need a different set of options if using proxies
	if with_proxy:
		options = sw_ChromeOptions()
		for opt in ["--headless", "--no-sandbox", "--disable-dev-shm-usage", "--disable-dev-tools", "--no-zygote", "--single-process", "--window-size=1920x1080"]:
			# Special case for headless drivers
			if opt == "--headless":
				options.headless = True
				continue
			options.add_argument(opt)

	# Used when run within a Docker container or once on AWS
	if within_docker:
		options.binary_location = "/opt/chrome/95.0.4638.54/chrome"

	# Used to start parsing data as soon as the "document" is ready, rather than when the "page" is ready
	# desired_caps = DesiredCapabilities().CHROME
	# desired_caps["pageLoadStrategy"] = "eager"
	options.page_load_strategy = "eager"

	# Try to create the driver with the chosen parameters
	try:
		if with_proxy:
			# Get the proxy details from the environment
			proxy_user = os.getenv("PROXY_USER", "sp70601931")
			proxy_pass = os.getenv("PROXY_PASS", "Password123!")
			if not proxy_user or not proxy_pass:
				print(
					"Proxy credentials may be missing.  Ensure the PROXY_USER and PROXY_PASS environment variables are present on the Lambda configuration page.")

			# Modify these settings with care, adding/removing/modifying incorrectly can trigger bot detection,
			# Proxy details
			wire_options = {"proxy":
				                {"http": f"http://user-{proxy_user}:{proxy_pass}@us.smartproxy.com:10000",
				                 "https": f"http://user-{proxy_user}:{proxy_pass}@us.smartproxy.com:10000",
				                 "no_proxy": "localhost,127.0.0.1"},
			                "connection_keep_alive": True,
			                "disable_capture": True,
			                "verify_ssl": False,
			                "ignore_http_methods": ["GET", "POST", "OPTIONS"],
			                "request_storage_base_dir": "/tmp"  # Use /tmp to store captured data
			                }

			if within_docker:
				driver = sw_Chrome(executable_path="/tmp/chromedriver/95.0.4638.54/chromedriver",
				                        options=options, service_log_path='/tmp/chromedriver.log',
				                        seleniumwire_options=wire_options)
			else:
				driver = sw_Chrome(options=options, seleniumwire_options=wire_options)
		else:
			if within_docker:
				driver = uc.Chrome(executable_path="/tmp/chromedriver/95.0.4638.54/chromedriver",
				                        options=options, service_log_path='/tmp/chromedriver.log')
			else:
				driver = uc.Chrome(options=options)
	except SessionNotCreatedException as e:
		print(f"Failed to create a driver session with the error: {e}")
		sys.exit(1)
	except Exception as e:
		print(f"Failed to create a driver at all with the error: {e}")
		sys.exit(1)

	driver.implicitly_wait(5)
	return driver
