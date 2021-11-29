import time
import boto3
import json
s3 = boto3.client('s3')
bucketName = 'url-request-type'

from scrapers import undetectable_scraper
from scrapers import detectable_scraper


urls = ["https://www.abercrombie.com/shop/us/p/90s-ultra-high-rise-straight-jeans-46531448?seq=17&cmp=PLA:EVG:20:A:D:USCA:X:GGL:X:SHOP:X:X:X:X:x:SC+Shopping+-+ANF+-+Zombie+SKUs+-+Smart+Shopping_Ad+group_PRODUCT_GROUP&gclid=CjwKCAjwiY6MBhBqEiwARFSCPhLdnASxOoSQvxzGYs8U3l7DpuX8zf2T3JkzT_c3OAFq1Z3JNl_LIxoCoUYQAvD_BwE&gclsrc=aw.ds",
			"https://www.untuckit.com/collections/wrinkle-free/products/veneto-wf-teal-2",
			"https://www.everlane.com/products/womens-day-boot-reknit-toffee",
			"https://shop.lululemon.com/p/womens-leggings/Swift-Speed-HighRise-Tight-28/_/prod9960839?color=48285",
			"https://www.zara.com/us/en/bodysuit-with-rings-p09288707.html?v1=137629564&v2=1609213",
			"https://thehalara.com/collections/leggings/products/everyday-leggings-high-rise-7-8-crossover-hem?pmui=10.1.collections.list.12.leggings&pmuih=leggings&variant=40906982097062",
			"https://www.forever21.com/us/2000430314.html?dwvar_2000430314_color=04",
			"https://www.urbanoutfitters.com/shop/smoko-potato-mochi-plushie?color=020&size=0000",
			"https://www.anthropologie.com/shop/sachin-babi-connie-jumpsuit",
			"https://www.bloomingdales.com/shop/product/adrianna-papell-beaded-halter-cocktail-dress?ID=3951778",
			"https://pin.it/652qlhp",
			"https://www.toryburch.com/en-us/shoes/flats/jessa-loafer/60801.html?color=006&size=5.5&utm_source=google&utm_medium=cpc&adpos=&scid=scplp192485344769&sc_intid=192485344769&journey=RT_Intent_PaidSearch_NoList_PLA&gclid=CjwKCAjwiY6MBhBqEiwARFSCPtfU191yWVTYLw_Nb4fATlVvbbrjXx7fvbcfzE0ThLhjz89JNgGdiBoCnXoQAvD_BwE&gclsrc=aw.ds",
			"https://www.bathandbodyworks.com/p/fall-farmhouse-3-wick-candle-026303365.html?gclid=CjwKCAjwiY6MBhBqEiwARFSCPj-7sCVr-VzqBXmOftdsFiKr2GCZX-9KRg89aSQOlyBS6Fj35lS0XBoCTr4QAvD_BwE&ef_id=CjwKCAjwiY6MBhBqEiwARFSCPj-7sCVr-VzqBXmOftdsFiKr2GCZX-9KRg89aSQOlyBS6Fj35lS0XBoCTr4QAvD_BwE:G:s&gclsrc=aw.ds&&ef_id=CjwKCAjwiY6MBhBqEiwARFSCPj-7sCVr-VzqBXmOftdsFiKr2GCZX-9KRg89aSQOlyBS6Fj35lS0XBoCTr4QAvD_BwE:G:s&cm_mmc=GooglePLA--Paid+Search--8569898802-_-87029087512",
			"https://www.urbanoutfitters.com/shop/for-love-and-lemons-tamara-corset-top?category=womens-going-out-tops&color=059&type=REGULAR&quantity=1",
			"https://www.nastygal.com/large-check-shacket-/AGG14991.html?color=130",
			"https://www.nordstrom.com/s/levis-high-pile-fleece-hooded-zip-jacket/5910275?color=IVORY%2F+PEACH+BLOSSOM&mrkgadid=3320091423&mrkgcl=760&mrkgen=gpla&mrkgbflag=1&mrkgcat=&utm_content=62223601895&utm_term=pla-322138638434&utm_channel=low_nd_shopping_standard&sp_source=google&sp_campaign=745687890&adpos=&creative=312319651107&device=m&matchtype=&network=g&acctid=21700000001689570&dskeywordid=92700049880928297&lid=92700049880928297&ds_s_kwgid=58700005468310335&ds_s_inventory_feed_id=97700000007631122&dsproductgroupid=322138638434&product_id=37869695&merchid=1243147&prodctry=US&prodlang=en&channel=online&storeid=&locationid=9067609&targetid=pla-322138638434&campaignid=745687890&adgroupid=62223601895&gclid=EAIaIQobChMIw8fRz4X98wIVwwWICR2jSwq0EAQYAiABEgKVnPD_BwE&gclsrc=aw.ds",
			"https://www.dollskill.com/azalea-wang-black-bryant-platform-boots.html",
			"https://bananarepublic.gap.com/browse/product.do?pid=668920012&vid=1&tid=brpl000045&kwid=1&ap=7&gclid=CjwKCAjwwsmLBhACEiwANq-tXGIubaFHmAWO2o5h35CGnPAuqKl2-UiB9l77KKDPpbdRvLM1OKmYERoCjlwQAvD_BwE&gclsrc=aw.ds#pdp-page-content",
			"https://thursdayboots.com/products/womens-legend-chelsea-boot-black-matte",
			"https://www.aritzia.com/us/en/product/classic-mini-skirt/77520.html",
			"https://www.jcrew.com/p/womens/categories/clothing/blazers/novelty/lady-blazer-in-stretch-crepe-checks/BA489"]


def test_scrape():
	results = []
	urls = ["https://www.everlane.com/products/womens-day-boot-reknit-toffee"]
	for url in urls:
		# Try without the anticloudflare request first
		# Defaults for failed requests
		res = {"product_name": "",
		       "product_image_urls": [],
		       "product_description": "",
		       "status_code": 000}

		# Try without the anticloudflare request first
		try:
			print("Using DetectableScraper")
			scraper = detectable_scraper.DetectableScraper()
			res = scraper.scrape_page(url)
			print(res)
			if "Error" in res:
				raise
			#return res
			continue
		except Exception as e:
			print(e)
			print("Normal request failed, trying anti bot")

		try:
			print("Using Anti-Bot Scraper")
			scraper = undetectable_scraper.UndetectableScraper()
			res = scraper.scrape_page(url)
			print(res)
			if scraper.driver:
				scraper.driver.quit()

			#return res
			continue
		except Exception as e:
			print(e)
			print("Both detectable and undetectable requests failed to find the data.")

		#return res


# The handler that AWS Lambda will call.
def handler(event, context):
	url = event.get("url")
	if not url:
		return {"msg": "No url provided"}

	# Defaults for failed requests
	res = {"product_name": "",
			"product_image_urls": [],
			"product_description": "",
			"status_code": 000}
	
	# Get URL Site and see if it needs cloudfare avoidance
	try:
		urlSite = url.split('/')[2]
		print("URL SITE")
		print(urlSite)
		cloudfareCheck = s3.get_object(Bucket = bucketName, Key = urlSite.lower())
		jsonObject = cloudfareCheck['Body'].read()
		needsAntiBot = json.loads(jsonObject)
		if not needsAntiBot == True:
			needsAntiBot = False
	except:
		needsAntiBot = False
	
	print(needsAntiBot)
	if needsAntiBot == True:
		try:
			print("Using Anti-Bot Scraper First")
			scraper = undetectable_scraper.UndetectableScraper()
			res = scraper.scrape_page(url)
			print(res)
			if scraper.driver:
				scraper.driver.quit()

			return res
		except Exception as e:
			print(e)
			print("Both detectable and undetectable requests failed to find the data.")
	else:
		# Try without the anticloudflare request first
		try:
			print("Using DetectableScraper")
			scraper = detectable_scraper.DetectableScraper()
			res = scraper.scrape_page(url)
			print(res)
			if "Error" in res:
				raise
			return res
		except Exception as e:
			print(e)
			print("Normal request failed, trying anti bot")

		try:
			print("Using Anti-Bot Scraper Second")
			scraper = undetectable_scraper.UndetectableScraper()
			res = scraper.scrape_page(url)
			print(res)
			s3.put_object(Bucket = bucketName, Key = urlSite.lower(), Body = json.dumps(True))
			if scraper.driver:
				scraper.driver.quit()

			return res
		except Exception as e:
			print(e)
			print("Both detectable and undetectable requests failed to find the data.")

	return res


if __name__ == "__main__":
	test_scrape()
