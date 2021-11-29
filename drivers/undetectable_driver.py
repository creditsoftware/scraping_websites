import os
import sys

import undetected_chromedriver.v2 as uc
from seleniumwire.undetected_chromedriver.v2 import Chrome as sw_Chrome
from seleniumwire.undetected_chromedriver.v2 import ChromeOptions as sw_ChromeOptions
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class UndetectableDriver(object):
	"""
	The base class for all scrapers that need to bypass cloudflare.

	This class also handles setting all of the arguments needed to be able
	to run on AWS Lambda
	"""
	def __init__(self):
		super(UndetectableDriver, self).__init__()

		self.driver = None
		self.within_docker = bool(int(os.getenv("WITHIN_DOCKER", 0)))
		self.driver_options = uc.ChromeOptions()

	def set_driver_args(self, args):
		"""
		Sets the driver arguments from a list of arguments

		Args:
			args(list(str)): A list of options to pass to the driver
		"""
		for opt in args:
			# Special case for headless drivers
			if opt == "--headless":
				self.driver_options.headless = True
				continue
			self.driver_options.add_argument(opt)

	def init_driver(self, with_proxies=False):
		"""
		Initialise the driver based on the environment we are currently running in (local/aws)
		and open the driver

		Modify these settings with care as certain parameter patterns will trigger bot detectors
		and burn the current session.  In some cases a new IP will be required if this happens.

		Args:
			with_proxies(bool): If True, the driver will be configured to use proxies.
		"""

		# Create the options we will pass to the driver
		# We need a different set of options if using proxies
		if with_proxies:
			self.driver_options = sw_ChromeOptions()
		else:
			self.driver_options = uc.ChromeOptions()

		# Used when run within a Docker container or once on AWS
		if self.within_docker:
			self.driver_options.binary_location = "/opt/chrome/95.0.4638.54/chrome"
		# MODIFY WITH CARE!
		self.set_driver_args(["--headless", "--no-sandbox", "--disable-dev-shm-usage", "--disable-dev-tools",
								"--no-zygote", "--single-process", "--window-size=1920x1080"])

		# Used to start parsing data as soon as the "document" is ready, rather than when the "page" is ready
		# desired_caps = DesiredCapabilities().CHROME
		# desired_caps["pageLoadStrategy"] = "eager"
		self.driver_options.page_load_strategy = "eager"

		# Try to create the driver with the chosen parameters
		try:
			if with_proxies:
				# Get the proxy details from the environment
				proxy_user = os.getenv("PROXY_USER", "sp70601931")
				proxy_pass = os.getenv("PROXY_PASS", "Password123!")
				if not proxy_user or not proxy_pass:
					print("Proxy credentials may be missing.  Ensure the PROXY_USER and PROXY_PASS environment variables are present on the Lambda configuration page.")

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

				if self.within_docker:
					self.driver = sw_Chrome(executable_path="/tmp/chromedriver/95.0.4638.54/chromedriver",
											options=self.driver_options, service_log_path='/tmp/chromedriver.log',
											seleniumwire_options=wire_options)
				else:
					self.driver = sw_Chrome(options=self.driver_options, seleniumwire_options=wire_options)
			else:
				if self.within_docker:
					self.driver = uc.Chrome(executable_path="/tmp/chromedriver/95.0.4638.54/chromedriver",
											options=self.driver_options, service_log_path='/tmp/chromedriver.log')
				else:
					self.driver = uc.Chrome(options=self.driver_options)
		except SessionNotCreatedException as e:
			print(f"Failed to create a driver session with the error: {e}")
			sys.exit(1)
		except Exception as e:
			print(f"Failed to create a driver at all with the error: {e}")
			sys.exit(1)

		self.driver.implicitly_wait(5)
