import socket
import struct
import sys
import subprocess
import re
import urllib2
import backend.discovery.upnp_devices as upnp_devices
from video.models import LocalSource as LocalSource
import cv2

MCAST_GRP = '239.255.255.250'
MCAST_PORT = 1900
SERVICE_LOCS = {'id1': 'udap:rootservice', 'id2': '127.0.0.1:7766'}
 
DISCOVERY_MSG = ('M-SEARCH * HTTP/1.1\r\n' +
                 'HOST: 239.255.255.250:1900\r\n' +
                 'ST: ssdp:all\r\n' +
                 'MX: 3\r\n' +
                 'MAN: "ssdp:discover"\r\n\r\n\r\n')



# Linux-specific, gotta find a better alternative
def interface_addresses(family=socket.AF_INET):
    co = subprocess.Popen(['/sbin/ifconfig'], stdout = subprocess.PIPE)
    ifconfig = co.stdout.read()
    ip_regex = re.compile('addr\:((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-4]|2[0-5][0-9]|[01]?[0-9][0-9]?))')
    for a in [match[0] for match in ip_regex.findall(ifconfig, re.MULTILINE)]:
        yield a


# Helper
def find_between(s, start, end):
  return (s.split(start))[1].split(end)[0]



# Perform SSDP discovery
def discovery(timeout=1, retries=5):
    socket.setdefaulttimeout(timeout)

    locations = []
    for _ in xrange(retries):
        for addr in interface_addresses():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 5)
            try:
                sock.bind((addr, 0))
            except Exception:
                pass
 
            msg = DISCOVERY_MSG
            for _ in xrange(2):
                sock.sendto(msg, (MCAST_GRP, MCAST_PORT))
 
            bad = False
            while not bad:
                try:
                    data = sock.recv(1024)
                    lines = data.split('\r\n')
                    for line in lines:
                        split_lines = line.split(': ')
                        if len(split_lines)==2 and (split_lines[0]=='Location') or (split_lines[0]=='LOCATION'):
                            if split_lines[1] not in locations:
                                locations.append(split_lines[1])
                except socket.timeout:
                    bad = True
    return locations



# Get the list of devices
def get_devices(locations):

    devices = []
    socket.setdefaulttimeout(10)

    for location in locations:
        try:
            response = urllib2.urlopen(location)
            html = response.read()
            manufacturer = find_between(html,'<manufacturer>','</manufacturer>')
            modelname = find_between(html,'<modelName>','</modelName>')
            friendlyname = find_between(html,'<friendlyName>','</friendlyName>')
            presentationurl = find_between(html,'<presentationURL>','</presentationURL>')
            elem = { 'manufacturer' : manufacturer, 'modelname' : modelname, 'presentationurl': presentationurl, 'friendlyname': friendlyname }
            devices.append(elem)
        except Exception:
            pass

    return devices


def get_url(url,host):
    return url.replace("%URL%",host)




# Match a device against list
def match(device):
    devices_list = upnp_devices.get_list()

    found_dev = None
    for dev in devices_list:
        if (dev["manufacturer"] == device["manufacturer"]) and (dev["modelname"] == device["modelname"]):
            found_dev = device.copy()
            found_dev["is_setup"] = False
            found_dev["username"] = ""
            found_dev["password"] = ""
            found_dev["url"] = found_dev["presentationurl"]

            found_dev["videourl"] = get_url(dev["videourl"],found_dev["presentationurl"])
            found_dev["audiourl"] = get_url(dev["audiourl"],found_dev["presentationurl"])
            found_dev["zoomurl"] = get_url(dev["zoomurl"],found_dev["presentationurl"])
            found_dev["zoomcontrol"] = dev["zoomcontrol"]
            found_dev["zoomdata"] = dev["zoomdata"]
            found_dev["zoommin"] = dev["zoommin"]
            found_dev["zoommax"] = dev["zoommax"]

            found_dev["ptz_control"] = dev["ptz_control"]
            found_dev["ptz_type"] = dev["ptz_type"]
            found_dev["ptz_step_min"] = dev["ptz_step_min"]
            found_dev["ptz_step_max"] = dev["ptz_step_max"]
            found_dev["ptz_min"] = dev["ptz_min"]
            found_dev["ptz_max"] = dev["ptz_max"]

            found_dev["ptz_up"] = dev["ptz_up"]
            found_dev["ptz_up_right"] = dev["ptz_up_right"]
            found_dev["ptz_right"] = dev["ptz_right"]
            found_dev["ptz_bottom_right"] = dev["ptz_bottom_right"]
            found_dev["ptz_bottom"] = dev["ptz_bottom"]
            found_dev["ptz_bottom_left"] = dev["ptz_bottom_left"]
            found_dev["ptz_left"] = dev["ptz_left"]
            found_dev["ptz_up_left"] = dev["ptz_up_left"]

            found_dev["ptz_up_data"] = dev["ptz_up_data"]
            found_dev["ptz_up_right_data"] = dev["ptz_up_right_data"]
            found_dev["ptz_right_data"] = dev["ptz_right_data"]
            found_dev["ptz_bottom_right_data"] = dev["ptz_bottom_right_data"]
            found_dev["ptz_bottom_data"] = dev["ptz_bottom_data"]
            found_dev["ptz_bottom_left_data"] = dev["ptz_bottom_left_data"]
            found_dev["ptz_left_data"] = dev["ptz_left_data"]
            found_dev["ptz_up_left_data"] = dev["ptz_up_left_data"]


            found_dev["reseturl"] = get_url(dev["reseturl"],found_dev["presentationurl"])
            found_dev["resetcontrol"] = dev["resetcontrol"]
            found_dev["resetdata"] = dev["resetdata"]

            found_dev["nightmodeurl"] = get_url(dev["nightmodeurl"],found_dev["presentationurl"])
            found_dev["nightmodecontrol"] = dev["nightmodecontrol"]
            found_dev["nightmodedata"] = dev["nightmodedata"]

            found_dev["daymodeurl"] = get_url(dev["daymodeurl"],found_dev["presentationurl"])
            found_dev["daymodecontrol"] = dev["daymodecontrol"]
            found_dev["daymodedata"] = dev["daymodedata"]

            found_dev["automodeurl"] = get_url(dev["automodeurl"],found_dev["presentationurl"])
            found_dev["automodecontrol"] = dev["automodecontrol"]
            found_dev["automodedata"] = dev["automodedata"]

            found_dev["profileurl"] = get_url(dev["profileurl"],found_dev["presentationurl"])
            found_dev["profilecontrol"] = dev["profilecontrol"]
            found_dev["profiledata"] = dev["profiledata"]
            found_dev["profilemin"] = dev["profilemin"]
            found_dev["profilemax"] = dev["profilemax"]

    return found_dev



def get_url(url,host):
    return url.replace("%URL%",host)


def create_device(device):

    target = get_url(device["videourl"],device["presentationurl"])
    found = True
    fps = 0
    height = width = 0


    try:
        capture = cv2.VideoCapture(target)
    except Exception:
        found = False

    if capture:
        try:
            ret, frame_first = capture.read()
        except Exception:
            ret = False
        if not ret:
            found = False

    if not found:
        device["is_setup"] = False
    else:
        capture.release()
        device["is_setup"] = True
        try:
            height = int(capture.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
            width = int(capture.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
        except Exception:
            height = width = 0
            done = True

        try:
            fps = int(capture.get(cv2.cv.CV_CAP_PROP_FPS))
        except Exception:
            fps = 0

    try:
        videourl = target
        camname = device["friendlyname"]
        url=videourl

        # Sqlite3 is buggy, so we try again on failure
        try:
            dev,created = LocalSource.objects.get_or_create(name=camname,videourl=videourl)
        except Exception:
            try:
                dev,created = LocalSource.objects.get_or_create(name=camname,videourl=videourl)
            except Exception:
                print "Database IO Error. That is not weird with SQLite3, please consider switching to postgresql"
                return

        if created:
            dev.username = ""
            dev.password = ""
            dev.url = device["url"]
            dev.requireadmincredentials = found
            dev.videourl = videourl
            dev.audiourl = device["audiourl"]
            dev.zoomurl = device["zoomurl"]
            dev.zoomcontrol = device["zoomcontrol"]
            dev.zoomdata = device["zoomdata"]
            dev.zoommin = device["zoommin"]
            dev.zoommax = device["zoommax"]

            dev.ptz_type = device["ptz_type"]
            dev.ptz_control = device["ptz_control"]
            dev.ptz_step_min = device["ptz_step_min"]
            dev.ptz_step_max = device["ptz_step_max"]
            dev.ptz_min = device["ptz_step_min"]
            dev.ptz_max = device["ptz_step_max"]

            dev.ptz_up = device["ptz_up"]
            dev.ptz_up_data = device["ptz_up_data"]
            dev.ptz_up_right = device["ptz_up_right"]
            dev.ptz_up_right_data = device["ptz_up_right_data"]
            dev.ptz_right = device["ptz_right"]
            dev.ptz_right_data = device["ptz_right_data"]
            dev.ptz_bottom_right = device["ptz_bottom_right"]
            dev.ptz_bottom_right_data = device["ptz_bottom_right_data"]
            dev.ptz_bottom = device["ptz_bottom"]
            dev.ptz_bottom_data = device["ptz_bottom_data"]
            dev.ptz_bottom_left = device["ptz_bottom_left"]
            dev.ptz_bottom_left_data = device["ptz_bottom_left_data"]
            dev.ptz_left = device["ptz_left"]
            dev.ptz_left_data = device["ptz_left_data"]
            dev.ptz_up_left = device["ptz_up_left"]
            dev.ptz_up_left_data = device["ptz_up_left_data"]

            dev.reseturl = device["reseturl"]
            dev.resetcontrol = device["resetcontrol"]
            dev.resetdata = device["resetdata"]

            dev.nightmodeurl = device["nightmodeurl"]
            dev.nightmodecontrol = device["nightmodecontrol"]
            dev.nightmodedata = device["nightmodedata"]

            dev.daymodeurl = device["daymodeurl"]
            dev.daymodecontrol = device["daymodecontrol"]
            dev.daymodedata = device["daymodedata"]

            dev.automodeurl = device["automodeurl"]
            dev.automodecontrol = device["automodecontrol"]
            dev.automodedata = device["automodedata"]

            dev.profileurl = device["profileurl"]
            dev.profilecontrol = device["profilecontrol"]
            dev.profiledata = device["profiledata"]
            dev.profilemin = device["profilemin"]
            dev.profilemax = device["profilemax"]
            dev.height = height
            dev.width = width
            dev.is_setup = device["is_setup"]
            print "SAVE"
            dev.save()

    except Exception:
        import traceback
        print traceback.format_exc()
        pass
