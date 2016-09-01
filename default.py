#!/usr/bin/python
# -*- coding: utf-8 -*-
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

#
#  WINDOW PROPERTIES SET BY THIS SCRIPT
#  artiststring - contains the name of the artist
#  trackstring - contains the track name
#  stationname - name of radio station playing
#  haslogo - true if script found a logo to display, else false
#  logopath - path to logo if found, else empty string
#  radio-streaming-helper-running - true when script running

import xbmc ,xbmcvfs, xbmcaddon
import xbmcgui
import urllib
import sys
if sys.version_info >= (2, 7):
    import json as _json
else:
    import simplejson as _json
# Addon Stuff

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
addonversion = addon.getAddonInfo('version')
addonpath = addon.getAddonInfo('path').decode('utf-8')
addonid = addon.getAddonInfo('id').decode('utf-8')
#
# variables 
BaseString = addon.getSetting('musicdirectory')     # Base directory for Music albums
logostring = xbmc.translatePath('special://profile/addon_data/' + addonid +'/').decode('utf-8') # Base directory to store downloaded logos
was_playing =""
API_KEY = '64526564694f534d656544'
BaseString = xbmc.validatePath(BaseString)
fanart = addon.getSetting('usefanarttv')
tadb = addon.getSetting('usetadb')
st1find = addon.getSetting('st1find')
st1rep = addon.getSetting('st1rep')
st2find = addon.getSetting('st2find')
st2rep = addon.getSetting('st2rep')
st3find = addon.getSetting('st3find')
st3rep = addon.getSetting('st3rep')
st4find = addon.getSetting('st4find')
st4rep = addon.getSetting('st4rep')
st5find = addon.getSetting('st5find')
st5rep = addon.getSetting('st5rep')

def log(txt, mylevel=xbmc.LOGNOTICE):
    """ Logs to Kodi's standard logfile """
    
    if isinstance(txt, str):
        txt = txt.decode('utf-8')
    message = u'%s : %s' % (addonname, txt)
    xbmc.log(msg=message.encode('utf-8'), level=mylevel)
    
def get_mbid(artist):
    """ Gets the MBID for a given artist name.
    Note that radio stations often omit 'The' from band names so this may return the wrong MBID """
    log("Getting mbid for artist %s " % artist)
    try:
        url = "http://musicbrainz.org/ws/2/artist/?query=artist:" + artist
        response = urllib.urlopen(url).read()
        index1 = response.find("artist id")
        index2 = response.find("type")
        mbid = response[index1+11:index2-2].strip()
        log('Got an MBID of : %s' % mbid)
        return mbid
    except Exception as e:
        log ("ERROR !! : %s " %e)
        return None

def get_hdlogo(mbid, artist):
    """Get the first found HD clearlogo from fanart.tv if it exists.
    
    Args:
         The MBID of the artist and the artist name
    
    Returns :
        The fully qualified path to an existing logo or newly downloaded logo or 
        None if the logo is not found """
         
    url = "https://fanart.tv/artist/" + mbid
    log("Looking up artist on fanart.tv")
    response = urllib.urlopen(url).read()
    index1 = response.find("<h2>HD ClearLOGO<div")
    if index1 != -1:
        index2 = response.find('<div class="image_options">',index1)
        anylogos = response[index1:index2]
        if "currently no images" in anylogos:
            log("No HD logos found for %s" % artist)
            return None
        index3= response.find('<a href="/api/download.php?type=download')
        index4 = response.find('class="btn btn-inverse download"')
        chop = response[index3+9:index4-2]
        url = "https://fanart.tv" + chop
        logopath = logostring + mbid + "/"
        logopath = xbmc.validatePath(logopath)
        if not xbmcvfs.exists(logopath):
            log("Downloading HD logo from fanart.tv")
            xbmcvfs.mkdir(logopath)
            logopath = logopath + "logo.png"
            imagedata = urllib.urlopen(url).read()
            f = open(logopath,'wb')
            f.write(imagedata)
            f.close()
            return logopath
        else:
            logopath = logostring + mbid + '/logo.png'
            logopath = xbmc.validatePath(logopath)
            log("Logo downloaded previously")
            return logopath
    else:
        return None
def search_tadb(mbid,artist):
    artist = artist.replace(" ","+")
    url = "http://www.theaudiodb.com/api/v1/json/"+API_KEY+"/search.php?s="+artist
    log("Looking up %s on tadb.com" % artist)
    response = urllib.urlopen(url).read()
    index1 = response.find("strArtistLogo")
    if index1 != -1:
        index2 = response.find(',"strArtistFanart')
        chop = response[index1+15:index2].strip('"')
        if chop == "":
            log("No logo found for %s, trying The %s" % (artist, artist))
            artist = 'The+' + artist
            url = "http://www.theaudiodb.com/api/v1/json/"+API_KEY+"/search.php?s="+artist
            log("Looking up %s on tadb.com" % artist)
            response = urllib.urlopen(url).read()
            index1 = response.find("strArtistLogo")
            if index1 != -1:
                index2 = response.find(',"strArtistFanart')
                chop = response[index1+15:index2].strip('"')
                if chop == "":
                    return None
        url = chop
        logopath = logostring + mbid + "/"
        logopath = xbmc.validatePath(logopath)
        if not xbmcvfs.exists(logopath):
            log("Downloading logo from tadb")
            xbmcvfs.mkdir(logopath)
            logopath = logopath + "logo.png"
            imagedata = urllib.urlopen(url).read()
            f = open(logopath,'wb')
            f.write(imagedata)
            f.close()
            return logopath
        else:
            logopath = logostring + mbid + '/logo.png'
            logopath = xbmc.validatePath(logopath)
            log("Logo downloaded previously")
            return logopath
    else:
        return None
def script_exit():
    WINDOW.clearProperty("radio-streaming-helper-running")
    WINDOW.clearProperty("artiststring")
    WINDOW.clearProperty("trackstring")
    WINDOW.clearProperty("haslogo")
    WINDOW.clearProperty("logopath")
    log("Script Stopped")
def no_track():
    WINDOW.setProperty("artiststring","")
    WINDOW.setProperty("trackstring","")
    WINDOW.setProperty("haslogo","false")
    WINDOW.setProperty("logopath","")
try:      
    WINDOW = xbmcgui.Window(12006)
    if WINDOW.getProperty("radio-streaming-helper-running") == "true" :
        log("Script already running")
        exit(0)
    if BaseString == "":
        Addon.OpenSettings(addonname)
    WINDOW.setProperty("radio-streaming-helper-running","true")
    log("Version %s started" % addonversion)
    log("----------Settings----------")
    log("Use fanart.tv : %s" % fanart)
    log("use tadb : %s" % tadb)
    log("----------Settings----------")

    while (not xbmc.abortRequested):
        try:
            if xbmc.getCondVisibility("Player.IsInternetStream"):
                current_track = xbmc.getInfoLabel("MusicPlayer.Title")
                player_details = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.GetActivePlayers","id":1}' )
                player_id_temp = _json.loads(player_details)
                player_id = player_id_temp['result'][0]['playerid']
                json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": [ "file"], "playerid":%d  }, "id": "AudioGetItem"}' % player_id)
                station_list = _json.loads(json_query).get('result',{}).get('item',{}).get('file',[])
                x = station_list.rfind('/')
                station_list = station_list[x+1:]
                station=""
                if '.' in station_list:
                    station,ending = station_list.split('.')
                if st1find in station_list:
                    station = st1rep
                if st2find in station_list:
                    station = st2rep
                if st3find in station_list:
                    station = st3rep
                if st4find in station_list:
                    station = st4rep
                if st5find in station_list:
                    station = st5rep
                WINDOW.setProperty("stationname",station)
                if "T - Rex" in current_track:
                    current_track = current_track.replace("T - Rex","T-Rex")
                if " - " in current_track:
                    artist,track = current_track.split(" - ")
                    artist = artist.strip()
                    track = track.strip()
                    if was_playing != track:
                        log("Track changed to %s" % track)
                        log("Playing station : %s" % station)
                        logopath =''
                        testpath = BaseString + artist + "/logo.png"
                        testpath = xbmc.validatePath(testpath)
                        if xbmcvfs.exists(testpath):     # See if there is a logo in the music directory
                            WINDOW.setProperty("haslogo", "true") 
                            WINDOW.setProperty("logopath", testpath)
                            log("Logo in Music Directory : Path is %s" % testpath)
                        else:
                            WINDOW.setProperty("haslogo", "false")
                            log("No logo in music directory")
                            searchartist = artist.replace('feat','~').replace('ft','~').strip('.')
                            
                            x = searchartist.find('~')
                            if x != -1:
                                searchartist = artist[: x-1]
                            mbid = get_mbid(searchartist)     # No logo in music directory - get artist MBID
                            if mbid:
                                if fanart == "true":
                                    logopath = get_hdlogo(mbid, searchartist)     # Try and get a logo from cache directory or fanart.tv
                                if not logopath:
                                    if tadb == "true":
                                        logopath = search_tadb(mbid,searchartist)
                            if logopath:     #     We have a logo to display
                                WINDOW.setProperty("logopath",logopath)
                                log("Logo in script cache directory : Path is %s" % logopath)
                                WINDOW.setProperty("haslogo","true")
                            else:     #     No logos to display
                                WINDOW.setProperty("logopath","")
                                log("No logo in cache directory")
                                WINDOW.setProperty("haslogo","false")
                        WINDOW.setProperty("artiststring",artist)
                        WINDOW.setProperty("trackstring", track)
                        was_playing = track
                else:
                    no_track()
                xbmc.sleep(500)
            else:
                no_track()
            if xbmc.Player().isPlayingAudio() == False:
                log("Not playing audio")
                script_exit()
                exit()
        except Exception as e:
            log("OOPS - ERROR - %s" % e)
            script_exit()
    
except Exception as e:
    log("There was an error : %s" %e)
    script_exit()
