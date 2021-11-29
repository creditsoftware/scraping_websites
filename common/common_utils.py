from urllib.parse import urlparse


def relative_to_absolute_url(domain, url):
	"""
	Convert a relative url to an absolute url.
	If the passed in url isn't actually relative, it's just returned

	Args:
		domain(str): The domain to which the relative url belongs.
		url(str): The url to make absolute

	Returns:
		str: An absolute url
	"""
	if url.startswith("/") and not url.startswith("//"):
		parsed_domain = urlparse(domain)
		return f"{parsed_domain.scheme}://{parsed_domain.netloc}{url}"
	elif url.startswith("//"):
		parsed_domain = urlparse(domain)
		return f"{parsed_domain.scheme}:{url}"
	return url
