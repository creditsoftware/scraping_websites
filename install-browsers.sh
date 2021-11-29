#!/bin/bash

declare -A chrome_versions

chrome_versions='95.0.4638.54'
chrome_drivers="95.0.4638.54"

# Download Chrome
echo "Downloading Chrome version $chrome_versions"
mkdir -p "/opt/chrome/$chrome_versions"
curl -Lo "/opt/chrome/$chrome_versions/chrome-linux.zip" "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F920005%2Fchrome-linux.zip?generation=1631232582939202&alt=media"
unzip -q "/opt/chrome/$chrome_versions/chrome-linux.zip" -d "/opt/chrome/$chrome_versions/"
mv /opt/chrome/$chrome_versions/chrome-linux/* /opt/chrome/$chrome_versions/
rm -rf /opt/chrome/$chrome_versions/chrome-linux "/opt/chrome/$chrome_versions/chrome-linux.zip"


# Download Chromedriver for patching

echo "Downloading Chromedriver version $chrome_drivers"
mkdir -p "/opt/chromedriver/$chrome_drivers"
curl -Lo "/opt/chromedriver/$chrome_drivers/chromedriver_linux64.zip" "https://chromedriver.storage.googleapis.com/95.0.4638.54/chromedriver_linux64.zip"
unzip -q "/opt/chromedriver/$chrome_drivers/chromedriver_linux64.zip" -d "/opt/chromedriver/$chrome_drivers/"
chmod +x "/opt/chromedriver/$chrome_drivers/chromedriver"
rm -rf "/opt/chromedriver/$chrome_drivers/chromedriver_linux64.zip"
