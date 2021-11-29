#!/bin/bash

declare -A chrome_versions

chrome_versions='95.0.4638.54'
chrome_drivers="95.0.4638.54"

# Copy the drivers to tmp, as this is the only place we have write access on AWS Lambda

mkdir -p "/tmp/chromedriver/$chrome_drivers"
cp -r /opt/chromedriver/$chrome_versions/. "/tmp/chromedriver/$chrome_versions"
chmod +x "/tmp/chromedriver/$chrome_drivers/chromedriver"
