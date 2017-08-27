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
#  srh.Artist - contains the name of the artist
#  srh.Track - contains the track name
#  srh.TrackInfo - track information as scraped from either TADB or last.fm (if any found)
#  srh.Stationname - name of radio station playing
#  srh.Haslogo - true if script found a logo to display, else false
#  srh.Logopath - path to logo if found, else empty string
#  srh.Artist.Thumb - thumb of the current artist
#  srh.Artist.Banner - banner of the current artist
#  srh.Album - track the album is off if the addon can find a match (note that this may not be accurate as we just match the first album we find with that track on)
#  srh.Year the album 'srh.Album' is from if the addon can find a match
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
    WINDOW.clearProperty("srh.Artist")
    WINDOW.clearProperty("srh.Track")
    WINDOW.clearProperty("srh.TrackInfo")
    WINDOW.clearProperty("srh.Haslogo")
    WINDOW.clearProperty("srh.Logopath")
    WINDOW.clearProperty("srh.Album")
    WINDOW.clearProperty("srh.Year")
    WINDOW.clearProperty("srh.Artist.Thumb")
    WINDOW.clearProperty("srh.Artist.Banner")
    WINDOW.clearProperty("srh.MBIDS")
    log("Script Stopped")
    rt.stop()
    exit()

def set_timer(delay):
    cs = datetime.datetime.now().time().second
    et = cs + delay
    if (et) >= 60 :
        et = et - 60
    return et

def get_info(testpath, searchartist, artist, multi_artist, already_checked, checked_all_artists):
    if multi_artist:
        orig_artist = artist
    if xbmcvfs.exists(testpath):     # See if there is a logo in the music directory
        WINDOW.setProperty("srh.Haslogo", "true")
        WINDOW.setProperty("srh.Logopath", testpath)
        log("Logo in Music Directory : Path is %s" % testpath, xbmc.LOGDEBUG)

        if onlinelookup == "true":
            mbid = get_mbid(searchartist, dict6)
        else:
            mbid = None
        if tadb == "true":
            artist, logopath, ArtistThumb, ArtistBanner = search_tadb(mbid,searchartist, dict4, dict5, checked_all_artists)
        else:
            logopath=""
            ArtistThumb =""
            ArtistBanner=""
    else:
        WINDOW.setProperty("srh.Haslogo", "false")
        log("No logo in music directory", xbmc.LOGDEBUG)
        if onlinelookup == "true":
            mbid = get_mbid(searchartist, dict6)     # No logo in music directory - get artist MBID
        else:
            mbid = None
        if mbid:
            if fanart == "true":
                logopath = get_hdlogo(mbid, searchartist)     # Try and get a logo from cache directory or fanart.tv
            if tadb == "true":
                artist, logopath, ArtistThumb, ArtistBanner = search_tadb(mbid,searchartist, dict4, dict5, checked_all_artists)
            else:
                logopath=""
                ArtistThumb =""
                ArtistBanner=""
        if logopath:     #     We have a logo to display
            log("Logo found in path %s " % logopath)
            WINDOW.setProperty("srh.Logopath",logopath)
            WINDOW.setProperty("srh.Haslogo","true")
        elif not logopath and not multi_artist:     #     No logos to display
            WINDOW.setProperty("srh.Logopath","")
            log("No logo in cache directory", xbmc.LOGDEBUG)
            WINDOW.setProperty("srh.Haslogo","false")
    if  ArtistThumb :
        WINDOW.setProperty("srh.Artist.Thumb", ArtistThumb)
    if ArtistBanner :
        WINDOW.setProperty("srh.Artist.Banner", ArtistBanner)
    if not already_checked:
        log("Not checked the album and year data yet for this artist")
        already_checked, albumtitle, theyear, trackinfo = get_year(artist,track,dict1,dict2,dict3,dict7, already_checked)

        if albumtitle and not multi_artist:
            WINDOW.setProperty("srh.Album",albumtitle.encode('utf-8')) # set if single artist and got album
            log("Single artist - Window property srh.Album set")
        elif albumtitle and multi_artist and (WINDOW.getProperty("srh.Album") == ""):
            WINDOW.setProperty("srh.Album",albumtitle.encode('utf-8'))

            log("Multi artist - srh.Album was empty - now set to %s" %albumtitle)
        elif not albumtitle and (not multi_artist):
            WINDOW.setProperty("srh.Album","") # clear if no title and not multi artist
            log("No album title for single artist")
        log("Album set to [%s]" % albumtitle)
        if trackinfo:
            trackinfo = trackinfo +'\n'
            WINDOW.setProperty("srh.TrackInfo", trackinfo.encode('utf-8'))
        else:
            WINDOW.setProperty("srh.TrackInfo","")
        if theyear and theyear != '0' and (not multi_artist):
            WINDOW.setProperty("srh.Year",theyear)
        elif theyear and multi_artist and(WINDOW.getProperty("srh.Year") == ""):
            WINDOW.setProperty("srh.Year",theyear)
        elif (not theyear or (theyear == 0 )) and (not multi_artist):
            WINDOW.setProperty("srh.Year","")
        if (albumtitle) and (theyear):
            log("Album & year details found : %s, %s" %( albumtitle, theyear), xbmc.LOGDEBUG)
        elif (albumtitle) and not (theyear):
            log("Found album %s but no year" % albumtitle, xbmc.LOGDEBUG)
        else:
            log("No album or year details found", xbmc.LOGDEBUG)
    if multi_artist:
        WINDOW.setProperty("srh.Artist",orig_artist.encode('utf-8'))
    else:
        WINDOW.setProperty("srh.Artist",artist.encode('utf-8'))
    WINDOW.setProperty("srh.Track", track.encode('utf-8'))
    return already_checked

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
        log(station, station_list)
        station =  next(v for k,v in replacelist.items() if k in (station_list))
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

    WINDOW.setProperty("srh.Artist","")
    WINDOW.setProperty("srh.Track","")
    WINDOW.setProperty("srh.TrackInfo","")
    WINDOW.setProperty("srh.Haslogo","false")
    WINDOW.setProperty("srh.Logopath","")
    WINDOW.setProperty("srh.Album","")
    WINDOW.setProperty("srh.Year","")
    WINDOW.setProperty("srh.Artist.Thumb","")
    WINDOW.setProperty("srh.Artist.Banner","")
    WINDOW.setProperty("srh.MBIDS","")
    return False, False
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
    for key in replacelist:
        log("Changing %s to %s" % (key, replacelist[key]))
    if luma:
        log("Lookup details for featured artists", xbmc.LOGNOTICE)
    else:
        log("Not looking up details for featured artists", xbmc.LOGNOTICE)

    log("----------Settings-------------------------", xbmc.LOGNOTICE)
    log("Setting up addon", xbmc.LOGNOTICE)
    already_checked = False
    log("aready_checked is set to [%s] " %str(already_checked))
    if xbmcvfs.exists(logostring + "data.pickle"):
        dict1,dict2,dict3, dict4, dict5, dict6,dict7 = load_pickle()
    my_size = len(dict1)
    log("Cache contains %d tracks" % my_size, xbmc.LOGDEBUG)
    cut_off_date = todays_date - time_diff
    log("Cached data obtained before before %s will be refreshed if details are missing" % (cut_off_date.strftime("%d-%m-%Y")), xbmc.LOGDEBUG)
    rt = RepeatedTimer(900, save_pickle, dict1,dict2,dict3, dict4, dict5, dict6,dict7)

    # Main Loop
    while (not xbmc.abortRequested):
        if xbmc.getCondVisibility("Player.IsInternetStream"):
            current_track = xbmc.getInfoLabel("MusicPlayer.Title")
#            current_track = "Gromee feat. Ma-Britt Scheffer - Fearless w Hot 100 - Gorąca Setka Hitów"
#            current_track = ""
            player_details = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Player.GetActivePlayers","id":1}' )
            player_id_temp = _json.loads(player_details)
            player_id = player_id_temp['result'][0]['playerid']
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": [ "file"], "playerid":%d  }, "id": "AudioGetItem"}' % player_id)
            file_playing = _json.loads(json_query).get('result',{}).get('item',{}).get('file',[])
            current_track = current_track.decode('utf-8')
            if firstpass == 0:
                firstpass = 1
                log("File playing is %s" % file_playing, xbmc.LOGDEBUG)
                log("Track playing is [%s]" % current_track, xbmc.LOGDEBUG)
                station, station_list = check_station(file_playing)
                log("Station name was : %s - changed to %s" % ( station_list, station), xbmc.LOGDEBUG)
                WINDOW.setProperty("srh.Stationname",station)
            if "T - Rex" in current_track:
                current_track = current_track.replace("T - Rex","T. Rex")
            if " - " in current_track:
                try:
                    x = slice_string(current_track, ' - ',1)
                    artist = current_track[x+3:]
                    track = current_track[:x]
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
                    if swaplist.get(station) == "true":
                        temp1 = track
                        track = artist
                        artist = temp1
                except Exception as e:
                    log("[Exception %s] while trying to slice current_track %s" %(str(e), current_track))
                if artist == "Pink":
                    artist = "P!nk"
                if (artist.upper() == "ELO") or (artist.upper() == "E.L.O") or (artist.upper() == "E.L.O."):
                    artist = "Electric Light Orchestra"
                if artist == "Florence & The Machine":
                    artist = "Florence + The Machine"
                if artist == "Cult":
                    artist = "The Cult"
                if was_playing != track:
                    checked_all_artists, already_checked = no_track()          # clear all window properties on track change
                    searchartists = []
                    station, station_list = check_station(file_playing)
                    WINDOW.setProperty("srh.Stationname",station)

                    log("Track changed to %s by %s" % (track, artist), xbmc.LOGDEBUG)
                    log("Playing station : %s" % station, xbmc.LOGDEBUG)
                    logopath =''
                    testpath = BaseString + artist + "/logo.png"
                    testpath = xbmc.validatePath(testpath)
                    searchartist = artist.replace(' feat. ',' ~ ').replace(' ft. ',' ~ ').replace(' feat ', ' ~ ').replace(' ft ',' ~ ')
                    searchartist = searchartist.replace(' & ', ' ~ ').replace(' and ', ' ~ ').replace( ' And ', ' ~ ').replace(' ~ the ', ' and the ').replace(' ~ The ' , ' and The ')
                    searchartist = searchartist.replace(' vs ',' ~ ').replace(', ',' ~ ')
                    log("Searchartist is %s" % searchartist)
                    x = searchartist.find('~')
                    log("searchartist.find('~') result was %s" % str(x))
                    if x != -1:
                        searchartists = searchartist.split('~')
                    else:
                        searchartists.append(searchartist)
                    num_artists = len(searchartists)
                    if num_artists > 1 and luma:
                        multi_artist = True
                    else:
                        multi_artist = False
                    mbids = ""
                    first_time = True

                    artist_index = 0
                    already_checked = get_info(testpath,searchartists[artist_index].strip(), artist, multi_artist, already_checked,checked_all_artists)
                    for z in range(0, len(searchartists)):
                        if searchartists[z] in dict6:
                            log("Setting mbid for artist %s to %s" % (searchartists[z], dict6[searchartists[z]]))
                            if first_time:
                                mbids = mbids + dict6[searchartists[z]]
                                first_time = False
                            else:
                                mbids = mbids +","+dict6[searchartists[z]]
                    if mbids:
                        WINDOW.setProperty('srh.MBIDS', mbids)
                    was_playing = track
                    et = set_timer(delay)
                    if multi_artist:
                        log("et is [%d]" %(et))
                if multi_artist:
                     cs = datetime.datetime.now().time().second
                     if cs == et:
                        log("Lookup next artist")
                        artist_index += 1
                        if artist_index == num_artists:
                            artist_index = 0
                            checked_all_artists = True
                        already_checked = get_info(testpath, searchartists[artist_index].strip(), artist, multi_artist, already_checked, checked_all_artists)
                        et = set_timer(delay)
                        log("et is now [%d]" %et)
            else:
                checked_all_artists, already_checked = no_track()
            xbmc.sleep(500)
        else:
            checked_all_artists, already_checked = no_track()
        if xbmc.Player().isPlayingAudio() == False:
            log("Not playing audio")
            save_pickle(dict1,dict2,dict3,dict4, dict5,dict6, dict7)
            script_exit()

except Exception as e:
    log("Radio Streaming Helper has encountered an error in the main loop and needs to close - %s" % str(e))
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
    save_pickle(dict1,dict2,dict3,dict4, dict5, dict6, dict7)
    script_exit()
