import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def requests_retry_session(retries=3, backoff_factor=0.3, status_force_list=(500, 502, 504), session=None):
	"""
	Creates and returns a session with an adapter set up for retrying http(s) requests.

	Args:
		retries (int): The number of time to retry a requests.
		backoff_factor (float): The factor used to determine how long to wait between retries.
		status_force_list (set): A set of status codes in which to force a retry on.
		session (requests.Session): A pre existing session to attach the retry adapter to.

	Returns:
		session (requests.Session): A session with the retry adapter attached.
	"""
	session = session or requests.Session()
	retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor, status_forcelist=status_force_list)
	adapter = HTTPAdapter(max_retries=retry)
	session.mount("http://", adapter)
	session.mount("https://", adapter)
	return session
