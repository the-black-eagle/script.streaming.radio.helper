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
#  (C) Black_eagle 2016
#
#  WINDOW PROPERTIES SET BY THIS SCRIPT
#  artiststring - contains the name of the artist
#  trackstring - contains the track name
#  stationname - name of radio station playing
#  haslogo - true if script found a logo to display, else false
#  logopath - path to logo if found, else empty string
#  srh.Artist.Thumb - thumb of the current artist
#  srh.Artist.Banner - banner of the current artist
#  albumtitle - track the album is off if the addon can find a match (note that this may not be accurate as we just match the first album we find with that track on)
#  year the album 'albumtitle' is from if the addon can find a match
#  radio-streaming-helper-running - true when script running

import xbmc ,xbmcvfs, xbmcaddon
import xbmcgui
import urllib, urllib2
import sys
from resources.lib.audiodb import audiodbinfo as settings
from resources.lib.utils import *
import pickle
import datetime
if sys.version_info >= (2, 7):
    import json as _json
else:
    import simplejson as _json
from threading import Timer

def script_exit():
    """Clears all the window properties and stops the timer used for auto-saving the data"""

    WINDOW.clearProperty("radio-streaming-helper-running")
    WINDOW.clearProperty("artiststring")
    WINDOW.clearProperty("trackstring")
    WINDOW.clearProperty("haslogo")
    WINDOW.clearProperty("logopath")
    WINDOW.clearProperty("albumtitle")
    WINDOW.clearProperty("year")
    WINDOW.clearProperty("srh.Artist.Thumb")
    WINDOW.clearProperty("srh.Artist.Banner")
    log("Script Stopped")
#    logit.close()
    rt.stop()
    exit()

def check_station(file_playing):
    """Attempts to parse a URL to find the name of the station being played
    and performs substitutions to 'pretty up' the name if those options
    are set in the settings"""
    try:
        if 'icy-' in file_playing: # looking at an ICY stream
            x = file_playing.rfind('/')
            station_list = file_playing[x+1:]
            if ('.' in station_list) and ("http" not in station_list):
                station,ending = station_list.split('.')
    
        elif '|' in file_playing:
            y = file_playing.rfind('|')
            station_list = file_playing[:y]
            x = station_list.rfind('/')
            station = station_list[x+1:]
        else:
            station_list = file_playing.strip('http://')
            x = station_list.rfind(':')
            if x != -1:
                station = station_list[:x]
            else:
                station = station_list
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
        return station, station_list
    except Exception as e:
        log("Error trying to parse station name [ %s ]" %str(e))
        return 'Online Radio', file_playing

def slice_string(string1, string2, n):
    if string2 == "" or string2 == None : return -1
    start = string1.find(string2)
    while start >= 0 and n > 1:
        start = string1.find(string2, start+len(string2))
        n -= 1
    return start
    
def no_track():
    """Sets the appropriate window properties when we have no track to display"""

    WINDOW.setProperty("artiststring","")
    WINDOW.setProperty("trackstring","")
    WINDOW.setProperty("haslogo","false")
    WINDOW.setProperty("logopath","")
    WINDOW.setProperty("albumtitle","")
    WINDOW.setProperty("year","")
    WINDOW.setProperty("srh.Artist.Thumb","")
    WINDOW.setProperty("srh.Artist.Banner","")
try:
    WINDOW = xbmcgui.Window(12006)
    if WINDOW.getProperty("radio-streaming-helper-running") == "true" :
       log("Script already running - Not starting a new instance")
       exit(0)
    if BaseString == "":
        addon.openSettings(addonname)
    
    WINDOW.setProperty("radio-streaming-helper-running","true")
    log("Version %s started" % addonversion, xbmc.LOGNOTICE)
    log("----------Settings-------------------------", xbmc.LOGNOTICE)
    log("Use fanart.tv : %s" % fanart, xbmc.LOGNOTICE)
    log("use tadb : %s" % tadb, xbmc.LOGNOTICE)
    log("changing %s to %s" % (st1find, st1rep), xbmc.LOGNOTICE)
    log("changing %s to %s" % (st2find, st2rep), xbmc.LOGNOTICE)
    log("changing %s to %s" % (st3find, st3rep), xbmc.LOGNOTICE)
    log("changing %s to %s" % (st4find, st4rep), xbmc.LOGNOTICE)
    log("changing %s to %s" % (st5find, st5rep), xbmc.LOGNOTICE)
    
    log("----------Settings-------------------------", xbmc.LOGNOTICE)
    log("Setting up addon", xbmc.LOGNOTICE)
    if xbmcvfs.exists(logostring + "data.pickle"):
        dict1,dict2,dict3, dict4, dict5, dict6 = load_pickle()
    my_size = len(dict1)
    if xbmcvfs.exists(logfile):
        xbmcvfs.delete(logfile)
#    logit = xbmcvfs.File(logfile,'w')
    log("Cache contains %d tracks" % my_size, xbmc.LOGDEBUG)
    cut_off_date = todays_date - time_diff
    log("Cached data obtained before before %s will be refreshed if details are missing" % (cut_off_date.strftime("%d-%m-%Y")), xbmc.LOGDEBUG)
    rt = RepeatedTimer(900, save_pickle, dict1,dict2,dict3, dict4, dict5, dict6)
    
    # Main Loop
    while (not xbmc.abortRequested):
        if xbmc.getCondVisibility("Player.IsInternetStream"):
            current_track = xbmc.getInfoLabel("MusicPlayer.Title")
#            current_track = "Gromee feat. Ma-Britt Scheffer - Fearless w Hot 100 - Gorąca Setka Hitów"
            player_details = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.GetActivePlayers","id":1}' )
            player_id_temp = _json.loads(player_details)
            player_id = player_id_temp['result'][0]['playerid']
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": [ "file"], "playerid":%d  }, "id": "AudioGetItem"}' % player_id)
            file_playing = _json.loads(json_query).get('result',{}).get('item',{}).get('file',[])
            current_track = current_track.decode('utf-8')
            if firstpass == 0:
                firstpass = 1
                log("File playing is %s" % file_playing, xbmc.LOGDEBUG)
                station, station_list = check_station(file_playing)
                log("Station name was : %s - changed to %s" % ( station_list, station), xbmc.LOGDEBUG)
                WINDOW.setProperty("stationname",station)
            if "T - Rex" in current_track:
                current_track = current_track.replace("T - Rex","T-Rex")
            if " - " in current_track:
                try:
                    x = slice_string(current_track, ' - ',1)
                    artist = current_track[:x]
                    track = current_track[x+3:]
                    artist = artist.strip()
                    artist = " ".join(artist.split())  # Make sure there are no extra spaces in the artist name as this causes issues
                    pos = slice_string(track,replace1,1)
                    if pos != -1:
                        track = track[:pos]
                    else:
                        pos = slice_string(track,replace2,1)
                        if pos != -1:
                            track = track[:pos]
                        else:
                            pos = slice_string(track,replace3,1)
                            if pos != -1:
                                track = track[:pos]
                    track = track.strip()
                except Exception as e:
                    log("[Exception %s] while trying to slice current_track %s" %(str(e), current_track))
                if artist == "Pink":
                    artist = "P!nk"
                if (artist == "ELO") or (artist == "E.L.O"):
                    artist = "E.L.O."
                if artist == "Florence & The Machine":
                    artist = "Florence + The Machine"
                if was_playing != track:
                    log("Checking station is the same" , xbmc.LOGDEBUG)
                    station, station_list = check_station(file_playing)
                    WINDOW.setProperty("stationname",station)
                    log("Track changed to %s by %s" % (track, artist), xbmc.LOGDEBUG)
                    log("Playing station : %s" % station, xbmc.LOGDEBUG)
                    logopath =''
                    testpath = BaseString + artist + "/logo.png"
                    testpath = xbmc.validatePath(testpath)
                    searchartist = artist.replace(' feat. ',' ~ ').replace(' ft. ',' ~ ').replace(' feat ', ' ~ ').replace(' ft ',' ~ ')
                    log("Searchartist is %s" % searchartist)
                    x = searchartist.find('~')
                    log("searchartist.find('~') result was %s" % str(x))
                    if x != -1:
                        searchartist = artist[: x-1]
                    if xbmcvfs.exists(testpath):     # See if there is a logo in the music directory
                        WINDOW.setProperty("haslogo", "true")
                        WINDOW.setProperty("logopath", testpath)
                        log("Logo in Music Directory : Path is %s" % testpath, xbmc.LOGDEBUG)
                        
                        if onlinelookup == "true":
                            mbid = get_mbid(searchartist)   
                        else:
                            mbid = None
                        if tadb == "true":
                            artist, logopath, ArtistThumb, ArtistBanner = search_tadb(mbid,searchartist, dict4, dict5)
                        else:
                            logopath=""
                            ArtistThumb =""
                            ArtistBanner=""
                    else:
                        WINDOW.setProperty("haslogo", "false")
                        log("No logo in music directory", xbmc.LOGDEBUG)
                        if onlinelookup == "true":
                            mbid = get_mbid(searchartist)     # No logo in music directory - get artist MBID
                        else:
                            mbid = None
                        if mbid:
                            if fanart == "true":
                                logopath = get_hdlogo(mbid, searchartist)     # Try and get a logo from cache directory or fanart.tv
                            if tadb == "true":
                                artist, logopath, ArtistThumb, ArtistBanner = search_tadb(mbid,searchartist, dict4, dict5)
                            else:
                                logopath=""
                                ArtistThumb =""
                                ArtistBanner=""
                        if logopath:     #     We have a logo to display
                            log("Logo found in path %s " % logopath)
                            WINDOW.setProperty("logopath",logopath)
                            WINDOW.setProperty("haslogo","true")
                        else:     #     No logos to display
                            WINDOW.setProperty("logopath","")
                            log("No logo in cache directory", xbmc.LOGDEBUG)
                            WINDOW.setProperty("haslogo","false")
                    WINDOW.setProperty("srh.Artist.Thumb", ArtistThumb)
                    WINDOW.setProperty("srh.Artist.Banner", ArtistBanner)
                    albumtitle, theyear = get_year(artist,track,dict1,dict2,dict3)
                    if albumtitle:
                        WINDOW.setProperty("albumtitle",albumtitle.encode('utf-8'))
                    else:
                        WINDOW.setProperty("albumtitle","")
                    if theyear and theyear != '0':
                        WINDOW.setProperty("year",theyear)
                    else:
                        WINDOW.setProperty("year","")
                    if (albumtitle) and (theyear):
                        log("Album & year details found : %s, %s" %( albumtitle, theyear), xbmc.LOGDEBUG)
                    elif (albumtitle) and not (theyear):
                        log("Found album %s but no year" % albumtitle, xbmc.LOGDEBUG)
                    else:
                        log("No album or year details found", xbmc.LOGDEBUG)
                    WINDOW.setProperty("artiststring",artist.encode('utf-8'))
                    WINDOW.setProperty("trackstring", track.encode('utf-8'))
                    was_playing = track
            else:
                no_track()
            xbmc.sleep(500)
        else:
            no_track()
        if xbmc.Player().isPlayingAudio() == False:
            log("Not playing audio")
            save_pickle(dict1,dict2,dict3,dict4, dict5,dict6)
            script_exit()

except Exception as e:
    log("Radio Streaming Helper has encountered an error and needs to close - %s" % str(e))
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
    save_pickle(dict1,dict2,dict3,dict4, dict5, dict6)
    script_exit()
