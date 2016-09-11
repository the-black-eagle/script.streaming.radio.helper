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
#  albumtitle - track the album is off if the addon can find a match
#  year the album 'albumtitle' is from if the addon can find a match
#  radio-streaming-helper-running - true when script running

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
    
# Addon Stuff
rusty_gate = settings.rusty_gate
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
    response = urllib.urlopen(searchurl).read()
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
        if response == '':
            return None
        index1 = response.find("artist id")
        index2 = response.find("type")
        mbid = response[index1+11:index2-2].strip()
        log('Got an MBID of : %s' % mbid, xbmc.LOGDEBUG) 
        return mbid
    except Exception as e:
        log ("ERROR !! : %s " %e, xbmc.LOGERROR)
        return None

def get_hdlogo(mbid, artist):
    """Get the first found HD clearlogo from fanart.tv if it exists.
    
    Args:
         The MBID of the artist and the artist name
    
    Returns :
        The fully qualified path to an existing logo or newly downloaded logo or 
        None if the logo is not found """
         
    url = "https://fanart.tv/artist/" + mbid
    logopath = logostring + mbid + "/logo.png"
    logopath = xbmc.validatePath(logopath)
    if not xbmcvfs.exists(logopath):
        log("Searching for HD logo on fanart.tv")
        response = urllib.urlopen(url).read()
        if response == '':
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
            log("Downloading logo from fanart.tv and cacheing")
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
        response = urllib.urlopen(searchurl).read()
        if response == '':
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
            logopath = logostring + '/'
            xbmcvfs.mkdir(logopath)
            log("Downloading logo from tadb and cacheing")
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
            log("Logo has already been downloaded and is in cache")
            return logopath
        else:
            return None

def script_exit():
    """Clears all the window properties and stops the timer used for auto-saving the data"""
    
    WINDOW.clearProperty("radio-streaming-helper-running")
    WINDOW.clearProperty("artiststring")
    WINDOW.clearProperty("trackstring")
    WINDOW.clearProperty("haslogo")
    WINDOW.clearProperty("logopath")
    WINDOW.clearProperty("albumtitle")
    WINDOW.clearProperty("year")
    log("Script Stopped")
    rt.stop()
def no_track():
    """Sets the appropriate window properties when we have no track to display"""
    
    WINDOW.setProperty("artiststring","")
    WINDOW.setProperty("trackstring","")
    WINDOW.setProperty("haslogo","false")
    WINDOW.setProperty("logopath","")
    WINDOW.setProperty("albumtitle","")
    WINDOW.setProperty("year","")
# Script starts here
try:      
    WINDOW = xbmcgui.Window(12006)
    if WINDOW.getProperty("radio-streaming-helper-running") == "true" :
        log("Script already running", xbmc.LOGWARNING)
        exit(0)
    if BaseString == "":
        addon.openSettings(addonname)
        
    WINDOW.setProperty("radio-streaming-helper-running","true")
    log("Version %s started" % addonversion)
    log("----------Settings----------")
    log("Use fanart.tv : %s" % fanart)
    log("use tadb : %s" % tadb)
    log("changing %s to %s" % (st1find, st1rep))
    log("changing %s to %s" % (st2find, st2rep))
    log("changing %s to %s" % (st3find, st3rep))
    log("changing %s to %s" % (st4find, st4rep))
    log("changing %s to %s" % (st5find, st5rep))

    log("----------Settings----------")
    log("Setting up addon")
    if xbmcvfs.exists(logostring + "data.pickle"):
        dict1,dict2,dict3 = load_pickle()
        cut_off_date = todays_date - time_diff
        log("Data before %s will be re-cached" % str(cut_off_date))
        rt = RepeatedTimer(900, save_pickle, dict1,dict2,dict3)
        log("Auto saving data every 15 minutes")
# Main Loop
    while (not xbmc.abortRequested):
        try:
            if xbmc.getCondVisibility("Player.IsInternetStream"):
                current_track = xbmc.getInfoLabel("MusicPlayer.Title")
                player_details = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.GetActivePlayers","id":1}' )
                player_id_temp = _json.loads(player_details)
                player_id = player_id_temp['result'][0]['playerid']
                json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": [ "file"], "playerid":%d  }, "id": "AudioGetItem"}' % player_id)
                file_playing = _json.loads(json_query).get('result',{}).get('item',{}).get('file',[])
                if firstpass == 0:
                    firstpass = 1
                    log("File playing is %s" % file_playing, xbmc.LOGDEBUG)
                    x = file_playing.rfind('/')
                    station_check = file_playing[x+1:]
                    if station_check == "":  # we only have an http address
                        station_list = file_playing
                    else:
                        station_list = station_check
                    station = station_list
                    if ('.' in station_list) and ("http" not in station_list):
                        station,ending = station_list.split('.')
                    if st5find in station_list:
                        station = st5rep
                    if st4find in station_list:
                        station = st4rep
                    if st3find in station_list:
                        station = st3rep
                    if st2find in station_list:
                        station = st2rep
                    if st1find in station_list:
                        station = st1rep
                    log("Station name was : %s - changed to %s" % ( station_list, station))
                if "T - Rex" in current_track:
                    current_track = current_track.replace("T - Rex","T-Rex")
                if " - " in current_track:
                    artist,track = current_track.split(" - ")
                    artist = artist.strip()
                    track = track.strip()
                    if artist == "Pink":
                        artist = "P!nk"
                    if was_playing != track:
                        log("Checking station is the same" , xbmc.LOGDEBUG)
                        x = file_playing.rfind('/')
                        station_check = file_playing[x+1:]
                        if station_check == "":  # we only have an http address
                            station_list = file_playing
                        else:
                            station_list = station_check
                        station = station_list
                        if ('.' in station_list) and ("http" not in station_list):
                            station,ending = station_list.split('.')
                        if st5find in station_list:
                            station = st5rep
                        if st4find in station_list:
                            station = st4rep
                        if st3find in station_list:
                            station = st3rep
                        if st2find in station_list:
                            station = st2rep
                        if st1find in station_list:
                            station = st1rep
                        WINDOW.setProperty("stationname",station)
                        log("Track changed to %s by %s" % (track, artist), xbmc.LOGDEBUG)
                        log("Playing station : %s" % station, xbmc.LOGDEBUG)
                        logopath =''
                        testpath = BaseString + artist + "/logo.png"
                        testpath = xbmc.validatePath(testpath)
                        if xbmcvfs.exists(testpath):     # See if there is a logo in the music directory
                            WINDOW.setProperty("haslogo", "true") 
                            WINDOW.setProperty("logopath", testpath)
                            log("Logo in Music Directory : Path is %s" % testpath)
                        else:
                            WINDOW.setProperty("haslogo", "false")
                            log("No logo in music directory", xbmc.LOGDEBUG)
                            searchartist = artist.replace('feat ','~').replace('ft ','~').strip('.')
                            
                            x = searchartist.find('~')
                            if x != -1:
                                searchartist = artist[: x-1]
                            if onlinelookup == "true":
                                mbid = get_mbid(searchartist)     # No logo in music directory - get artist MBID
                            else:
                                mbid = None
                            if mbid:
                                if fanart == "true":
                                    logopath = get_hdlogo(mbid, searchartist)     # Try and get a logo from cache directory or fanart.tv
                                if not logopath:
                                    if tadb == "true":
                                        logopath = search_tadb(mbid,searchartist)
                            if logopath:     #     We have a logo to display
                                WINDOW.setProperty("logopath",logopath)
                                log("Logo in script cache directory : Path is %s" % logopath, xbmc.LOGDEBUG)
                                WINDOW.setProperty("haslogo","true")
                            else:     #     No logos to display
                                WINDOW.setProperty("logopath","")
                                log("No logo in cache directory", xbmc.LOGDEBUG)
                                WINDOW.setProperty("haslogo","false")
                        albumtitle, theyear = get_year(artist,track)
                        if albumtitle:
                            WINDOW.setProperty("albumtitle",albumtitle)
                        else:
                            WINDOW.setProperty("albumtitle","")
                        if theyear:
                            WINDOW.setProperty("year",theyear)
                        else:
                            WINDOW.setProperty("year","")
                        if (albumtitle) and (theyear):
                            log("Album & year details found : %s, %s" %( albumtitle, theyear), xbmc.LOGDEBUG)
                        elif (albumtitle) and not (theyear):
                            log("Found album %s but no year" % albumtitle, xbmc.LOGDEBUG)
                        else:
                            log("No album or year details found", xbmc.LOGDEBUG)
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
                save_pickle(dict1,dict2,dict3)
                script_exit()
                exit()
        except Exception as e:
            log("OOPS - ERROR - %s" % e, xbmc.LOGERROR)
            script_exit()
except Exception as e:
    log("There was an error : %s" %e, xbmc.LOGERROR)
    script_exit()
