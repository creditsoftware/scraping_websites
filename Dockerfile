# Use the AWS lambda base
FROM public.ecr.aws/lambda/python:3.8

ENV WITHIN_DOCKER=1

# Copy the requirements for python
COPY requirements.txt .

# Copy the script used to install the driver
COPY install-browsers.sh .
# Copy the script used to install the driver
COPY copy_driver_to_tmp.sh .
COPY copy_driver.sh .


# Install OS dependencies needed for the driver
RUN yum install xz atk cups-libs gtk3 libXcomposite alsa-lib tar \
    libXcursor libXdamage libXext libXi libXrandr \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel unzip bzip2 -y -q


# Install Browsers
RUN /usr/bin/bash install-browsers.sh

# Upgrade pip and install the python requirements
RUN /var/lang/bin/python3.8 -m pip install --upgrade pip
RUN pip install -r requirements.txt


# Remove the temp packages
RUN yum remove xz tar unzip bzip2 -y

# Copy the project in
COPY . .

ENTRYPOINT ["./copy_driver_to_tmp.sh"]

# Specify the handler to use.
CMD [ "main.handler"]
