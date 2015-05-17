#!/usr/bin/env python
import urllib2
import socket
import base64
import sys

from video.models import Source
from video.models import Sink
from video.models import LocalSource

def make_url(camurl,url,val):
    return camurl.replace("%URL%",url).replace("%VAL%",val)


def request_get_url(camurl,url,val,username,password):
    request_url = make_url(camurl,url,val)

    request = urllib2.Request(request_url)
    if username and password and (username!="" or password!=""):
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request)
    #DEBUG
    result = request_url
    return result


def request_post_url(camurl,url,val,username,password,data):
    request_url = make_url(camurl,url,val)

    if username and password and (username!="" or password!=""):
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)

    request = urllib2.Request(request_url, data)

    result = urllib2.urlopen(request)
    return result



def get_stream_url(url,username,password):
    if not "@" in url and (len(username)>0 or len(password)>0):
        videourls = url.split("http://")
        if len(videourls)==1:
            videourls = url.split("https://")
            if len(videourls)==1:
                videourls = url.split("rtsp://")
                if len(videourls)==1:
                    raise Exception("Malformed URL")
                else:
                    proto="rtsp://"
            else:
                proto = "https://"
        else:
            proto = "http://"
        address = videourls[1]
        newvideourl = proto + username + ":" + password + "@" +address
        return newvideourl

    if "@" in url and (len(username)>0 or len(password)>0):
        videourls = url.split("http://")
        if len(videourls)==1:
            videourls = url.split("https://")
            if len(videourls)==1:
                videourls = url.split("rtsp://")
                if len(videourls)==1:
                    raise Exception("Malformed URL")
                else:
                    proto="rtsp://"
            else:
                proto = "https://"
        else:
            proto = "http://"
        address = videourls[1]
        adresses = address.split("@")
        if len(addresses)==1:
            raise Exception("Malformed URL")
        address = addresses[1]

        newvideourl = proto + username + ":" + password + "@" +address
        return newvideourl


def get_localsource(src,srctype):
    if srctype and src:
        if srctype=="sink":
            try:
                sink = Sink.objects.get(name=src)
                try:
                    source = Source.objects.get(raw_sink=sink.id)
                except Exception:
                    source = Source.objects.get(overlay_sink=sink.id)
                localsource = Source.device
            except Exception:
                return None
            return  source.device
        elif srctype=="source":
            try:
                source = Source.objects.get(name=src)
            except Exception:
                return None

            return source.device

        else:
            return None
