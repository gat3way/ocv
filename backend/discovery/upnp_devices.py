#!/usr/bin/env python


supported_devices = [
{
    "manufacturer" : "D-Link",
    "modelname" : "DCS-5020L",
    "requireadmincredentials" : True,
    "friendlyname" : "", # ALWAYS leave that empty
    "presentationurl" : "", # ALWAYS leave that empty
    "is_setup" : False, # ALWAYS leave that False

    "videourl" : "%URL%/video/mjpg.cgi?test.mjpg",
    "audiourl" : "%URL%/dgaudio.cgi",

    "zoomurl" : "",
    "zoomcontrol" : "none",
    "zoomdata" : "",
    "zoommin" : 0,
    "zoommax" : 0,

    "ptz_type" : "rel",
    "ptz_control" : "get",
    "ptz_step_min" : 1,
    "ptz_step_max" : 30,
    "ptz_min" : 0,
    "ptz_max" : 0,

    "ptz_up" : "%URL%/pantiltcontrol.cgi?PanSingleMoveDegree=%VAL%&TiltSingleMoveDegree=%VAL%&PanTiltSingleMove=1",
    "ptz_up_data" : "",
    "ptz_up_right" : "%URL%/pantiltcontrol.cgi?PanSingleMoveDegree=%VAL%&TiltSingleMoveDegree=%VAL%&PanTiltSingleMove=2",
    "ptz_up_right_data" : "",
    "ptz_right" : "%URL%/pantiltcontrol.cgi?PanSingleMoveDegree=%VAL%&TiltSingleMoveDegree=%VAL%&PanTiltSingleMove=5",
    "ptz_right_data" : "",
    "ptz_bottom_right" : "%URL%/pantiltcontrol.cgi?PanSingleMoveDegree=%VAL%&TiltSingleMoveDegree=%VAL%&PanTiltSingleMove=8",
    "ptz_bottom_right_data" : "",
    "ptz_bottom" : "%URL%/pantiltcontrol.cgi?PanSingleMoveDegree=%VAL%&TiltSingleMoveDegree=%VAL%&PanTiltSingleMove=7",
    "ptz_bottom_data" : "",
    "ptz_bottom_left" : "%URL%/pantiltcontrol.cgi?PanSingleMoveDegree=%VAL%&TiltSingleMoveDegree=%VAL%&PanTiltSingleMove=6",
    "ptz_bottom_left_data" : "",
    "ptz_left" : "%URL%/pantiltcontrol.cgi?PanSingleMoveDegree=%VAL%&TiltSingleMoveDegree=%VAL%&PanTiltSingleMove=3",
    "ptz_left_data" : "",
    "ptz_up_left" : "%URL%/pantiltcontrol.cgi?PanSingleMoveDegree=%VAL%&TiltSingleMoveDegree=%VAL%&PanTiltSingleMove=0",
    "ptz_up_left_data" : "",

    "reseturl" : "%URL%/pantiltcontrol.cgi",
    "resetcontrol" : "post",
    "resetdata" : "PanTiltSingleMove: 4\n",

    "nightmodeurl" : "%URL%/setDayNightMode",
    "nightmodecontrol" : "post",
    "nightmodedata" : "ReplySuccessPage=night.htm&ReplyErrorPage=errrnght.htm&DayNightMode=3&ConfigDayNightMode=Save",

    "daymodeurl" : "%URL%/setDayNightMode",
    "daymodecontrol" : "post",
    "daymodedata" : "ReplySuccessPage=night.htm&ReplyErrorPage=errrnght.htm&DayNightMode=2&ConfigDayNightMode=Save",

    "automodeurl" : "%URL%/setDayNightMode",
    "automodecontrol" : "post",
    "automodedata" : "ReplySuccessPage=night.htm&ReplyErrorPage=errrnght.htm&DayNightMode=0&ConfigDayNightMode=Save",

    "profileurl" : "",
    "profiledata" : "",
    "profilecontrol" : "none",
    "profilemin" : 0,
    "profilemax" : 0,
}

]




def get_list():
    return supported_devices


