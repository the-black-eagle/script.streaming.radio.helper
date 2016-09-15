#!/usr/bin/python
# -*- coding: utf-8 -*-
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
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

import xbmc ,xbmcvfs, xbmcaddon
import xbmcgui
import urllib
import sys
from resources.lib.audiodb import audiodbinfo as settings

import pickle
import datetime
if sys.version_info >= (2, 7):
    import json as _json
else:
    import simplejson as _json
from threading import Timer

rusty_gate = settings.rusty_gate
addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
addonversion = addon.getAddonInfo('version')
addonpath = addon.getAddonInfo('path').decode('utf-8')
addonid = addon.getAddonInfo('id').decode('utf-8')

# variables 
BaseString = addon.getSetting('musicdirectory')     # Base directory for Music albums
logostring = xbmc.translatePath('special://profile/addon_data/' + addonid +'/').decode('utf-8') # Base directory to store downloaded logos
was_playing =""
dict1 = {}
dict2 = {}
dict3 = {}
time_diff = datetime.timedelta(days = 7) # date to next check
todays_date = datetime.datetime.combine(datetime.date.today(),datetime.datetime.min.time())
BaseString = xbmc.validatePath(BaseString)
onlinelookup = addon.getSetting('onlinelookup')
fanart = addon.getSetting('usefanarttv')
tadb = addon.getSetting('usetadb')
st1find = addon.getSetting('st1find').strip()
st1rep = addon.getSetting('st1rep').strip()
st2find = addon.getSetting('st2find').strip()
st2rep = addon.getSetting('st2rep').strip()
st3find = addon.getSetting('st3find').strip()
st3rep = addon.getSetting('st3rep').strip()
st4find = addon.getSetting('st4find').strip()
st4rep = addon.getSetting('st4rep').strip()
st5find = addon.getSetting('st5find').strip()
st5rep = addon.getSetting('st5rep').strip()
firstpass = 0

def log(txt, mylevel=xbmc.LOGNOTICE):
    """ Logs to Kodi's standard logfile """
    
    if isinstance(txt, str):
        txt = txt.decode('utf-8')
    message = u'%s : %s' % (addonname, txt)
    xbmc.log(msg=message.encode('utf-8'), level=mylevel)

def load_pickle():
    """Loads cache data from file in the addon_data directory of the script"""
    
    log("Loading data from pickle file")
    pfile = open(logostring + 'data.pickle',"r")
    d1 = pickle.load(pfile)
    d2 = pickle.load(pfile)
    d3 = pickle.load(pfile)
    pfile.close()
    return d1,d2,d3
    
def save_pickle(d1,d2,d3):
    """Saves local cache data to file in the addon_data directory of the script"""
    
    log("Saving data to pickle file")
    pfile = open(logostring + 'data.pickle',"wb")
    pickle.dump(d1,pfile)
    pickle.dump(d2,pfile)
    pickle.dump(d3,pfile)
    pfile.close()
    
def get_year(artist,track):
    """Look in local cache for album and year data corresponding to current track. 
    Return the local data if present, unless it is older than 7 days in which case re-lookup online.
    If data not present in cache, lookup online and add to cache"""
    
    if (artist == "") and (track == ""):
        return None,None
    log("Looking up album and year data for %s, %s" %(artist, track))
    if track in dict1:
        log("Track %s in local data cache" % track)
        albumname = dict1[track]
        if  track in dict2:
            year = dict2[track]
        else: 
            year = None
        datechecked = dict3[track]

        log("Data for %s : %s last checked %s" % (track, albumname, str(datechecked)))
        if datechecked < (todays_date - time_diff):
            log( "Data too old re-lookup!!")
            dict1[track], dict2[track] = tadb_trackdata(artist,track)
            dict3[track] = datetime.datetime.combine(datetime.date.today(),datetime.datetime.min.time())
            log( "Got new data!!")
            return dict1[track], dict2[track] # get new data else return these
            
        else:
            log( "Using old data" )
            return dict1[track],dict2[track]
    else:
        log("New track - get data ")
        dict1[track], dict2[track] = tadb_trackdata(artist,track)
        dict3[track] = datetime.datetime.combine(datetime.date.today(),datetime.datetime.min.time())
        log( "New data has been cached")
        return dict1[track], dict2[track]
     
def tadb_trackdata(artist,track):
    """ Searches theaudiodb for an album containing track.  If a album is found, attempts
    to get the year of the album.  Returns album name and year if both are found, just the album name if
    no year is found, or none if nothing is found."""
    
    artist = artist.replace(" ","+")
    track = track.replace(" ","+").replace("(radio edit)","").replace("(Radio Edit)","")
    track = track.rstrip("+")
    url = 'http://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
    searchurl = url + '/searchtrack.php?s=' + artist + '&t=' + track
    log("Search artist, track : %s,%s" %(artist,track))
    try:
        response = urllib.urlopen(searchurl).read()
        if "service" in response:                # theaudiodb not available
            log("No response from theaudiodb",xbmc.LOGWARNING)
            if track in dict1:
                log("Using data from cache and not refreshing",xbmc.LOGWARNING)
                return dict1[track], dict2[track]    # so return the data we already have
            else:
                return None,None
        index1 = response.find("strAlbum")
        if index1 != -1:
            index2 = response.find(',"strArtist')
            chop = response[index1+10:index2].strip('"')
            if (chop == "") or (chop == "null"):
                log("No album data found")
                return None,None
            album_title = chop
            album_title_search = album_title.replace(" ","+")
            searchurl = url + '/searchalbum.php?s=' + artist + '&a=' + album_title_search
            log("Search artist,album : %s,%s" %(artist,album_title_search))
            response = urllib.urlopen(searchurl).read()
            index1 = response.find("intYearReleased")
            if index1 != -1:
                index2 = response.find(',"strStyle')
                chop = response[index1+18:index2].strip('"')
    
                the_year = chop
                return album_title, the_year
            else:
                return album_title, None
        return None, None
    except Exception as e:
        log("Error searching theaudiodb for album and year data : %S" %e, xbmc.LOGERROR)
        if track in dict1:
            return dict1[track], dict2[track]
        else:
            return None, None
    
def get_mbid(artist):
    """ Gets the MBID for a given artist name.
    Note that radio stations often omit 'The' from band names so this may return the wrong MBID """
    log("Getting mbid for artist %s " % artist)
    try:
        url = "http://musicbrainz.org/ws/2/artist/?query=artist:" + artist
        response = urllib.urlopen(url).read()
        if response == '':
            log("Unable to contact Musicbrainz to get an MBID", xbmc.LOGWARNING)
            return None
        index1 = response.find("artist id")
        index2 = response.find("type")
        mbid = response[index1+11:index2-2].strip()
        log('Got an MBID of : %s' % mbid, xbmc.LOGDEBUG)
        if mbid == '':
            log("Didn't get an MBID for artist : %s", xbmc.LOGWARNING)
            return None 
        return mbid
    except Exception as e:
        log ("Error getting Musicbrainz ID" %e, xbmc.LOGERROR)
        return None

def get_hdlogo(mbid, artist):
    """Get the first found HD clearlogo from fanart.tv if it exists.
    
    Args:
         The MBID of the artist and the artist name
    
    Returns :
        The fully qualified path to an existing logo or newly downloaded logo or 
        None if the logo is not found """
    try:     
        url = "https://fanart.tv/artist/" + mbid
        logopath = logostring + mbid + "/logo.png"
        logopath = xbmc.validatePath(logopath)
        if not xbmcvfs.exists(logopath):
            log("Searching for HD logo on fanart.tv")
            response = urllib.urlopen(url).read()
            if response == '':
                log("No response from fanart.tv",xbmc.LOGWARNING)
                return None
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
                logopath = logostring + mbid + '/'
                xbmcvfs.mkdir(logopath)
                log("Downloading logo from fanart.tv and cacheing in %s" % logopath)
                logopath = logopath + "logo.png"
                imagedata = urllib.urlopen(url).read()
                f = open(logopath,'wb')
                f.write(imagedata)
                f.close()
                return logopath
        else:
            logopath = logostring + mbid + '/logo.png'
            logopath = xbmc.validatePath(logopath)
            if xbmcvfs.exists(logopath):
                log("Logo downloaded previously")
                return logopath
            else:
                return None
    except Exception as e:
        log("Error searching fanart.tv for a logo : %S" %e, xbmc.LOGERROR)
        return None
    
def search_tadb(mbid,artist):
    """Checks to see if there is an existing logo locally in the scripts addon_data directory.
    If not, attempts to find a logo on theaudiodb and download it into the cache. As radio stations often
    drop 'The' from band names (eg 'Who' for 'The Who', 'Kinks' for 'The Kinks') if we fail to find a match
    for the artist we try again with 'The ' in front of the artist name"""
    
    logopath = logostring + mbid + "/logo.png"
    logopath = xbmc.validatePath(logopath)
    if not xbmcvfs.exists(logopath):
        log("Looking up %s on tadb.com" % artist)
        searchartist = artist.replace(" ","+")
        url = 'http://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
        searchurl = url + '/search.php?s=' + searchartist
        try:
            response = urllib.urlopen(searchurl).read()
            if response == '':
                log("No response from theaudiodb",xbmc.LOGWARNING)
                return None
            if response != '{"artists":null}':
                index1 = response.find("strArtistLogo")
                if index1 != -1:
                    index2 = response.find(',"strArtistFanart')
                    chop = response[index1+15:index2].strip('"')
                    if chop == "":
                        log("No logo found for %s" % artist)
                        return None
            else:
                searchartist = 'The+' + searchartist
                searchurl = url + '/search.php?s=' + searchartist
                log("Looking up %s on tadb.com" % searchartist)
                response = urllib.urlopen(url).read()
                if response == '':
                    return None
                if response == '{"artists":null}':
                    return None
                else:
                    index1 = response.find("strArtistLogo")
                    if index1 != -1:
                        index2 = response.find(',"strArtistFanart')
                        chop = response[index1+15:index2].strip('"')
                        if chop == "":
                            log("No logo found on tadb")
                            return None
                    else:
                        return None
            url = chop
            logopath = logostring + mbid + '/'
            logopath = xbmc.validatePath(logopath)
            xbmcvfs.mkdir(logopath)
            log("Downloading logo from tadb and cacheing in %s" % logopath)
            logopath = logopath + "logo.png"
            imagedata = urllib.urlopen(url).read()
            f = open(logopath,'wb')
            f.write(imagedata)
            f.close()
            return logopath
        except Exception as e:
            log("Error searching theaudiodb for a logo : %s" %e, xbmc.LOGERROR)
            return None        
            
    else:
        logopath = logostring + mbid + '/logo.png'
        logopath = xbmc.validatePath(logopath)
        if xbmcvfs.exists(logopath):
            log("Logo has already been downloaded and is in cache. Path is %s" % logopath)
            return logopath
        else:
            return None

class RepeatedTimer(object):
    """Auto-starting threaded timer.  Used for auto-saving the dictionary data
    to file every 15 minutes while the addon is running.
    
    Call as follows :-
    
    rt = RepeatingTimer(interval in secs, function name to call, params for function called)
    """
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
    
