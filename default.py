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
#
#  srh.Artist -             contains the name of the artist
#  srh.Track -              contains the track name
#  srh.TrackInfo -          track information as scraped from either TADB or last.fm (if any found)
#  srh.Stationname -        name of radio station playing
#  srh.Logopath -           path to logo if found, else empty string
#  srh.Artist.Thumb -       thumb of the current artist
#  srh.Artist.Banner -      banner of the current artist
#  srh.Album -              track the album is off if the addon can find a match (note that this may not be accurate as we just match the first album we find with that track on)
#  srh.Year -               the year 'srh.Album' is from if the addon can find a match
#  srh.MBIDS -              Mbid(s) of the current artist(s)
#  srh.AlbumCover -         Path to local album cover if found, else empty string
#
#  streaming-radio-helper-running - true when script running
#
# ** All window properties are set for the MusicVisualisation window (12006) **

import xbmc

import xbmcvfs

import xbmcaddon

import xbmcgui

import urllib

import urllib2

import sys

import re

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

    WINDOW.clearProperty("streaming-radio-helper-running")
    WINDOW.clearProperty("srh.Artist")
    WINDOW.clearProperty("srh.Track")
    WINDOW.clearProperty("srh.TrackInfo")
    WINDOW.clearProperty("srh.Logopath")
    WINDOW.clearProperty("srh.Album")
    WINDOW.clearProperty("srh.Year")
    WINDOW.clearProperty("srh.Artist.Thumb")
    WINDOW.clearProperty("srh.Artist.Banner")
    WINDOW.clearProperty("srh.MBIDS")
    WINDOW.clearProperty("srh.AlbumCover")
    log("Script Stopped")
    # data_out.close()
    rt.stop()
    exit()

def no_track():
    """Sets the appropriate window properties when we have no track to display"""

    WINDOW.setProperty("srh.Artist", "")
    WINDOW.setProperty("srh.Track", "")
    WINDOW.setProperty("srh.TrackInfo", "")
    WINDOW.setProperty("srh.Logopath", "")
    WINDOW.setProperty("srh.Album", "")
    WINDOW.setProperty("srh.Year", "")
    WINDOW.setProperty("srh.Artist.Thumb", "")
    WINDOW.setProperty("srh.Artist.Banner", "")
    WINDOW.setProperty("srh.MBIDS", "")
    WINDOW.setProperty("srh.Musicpath", "")
    WINDOW.setProperty("srh.AlbumCover","")
    return False, False

def get_info(local_logo, tadb_json_data, testpath, searchartist, artist, multi_artist, already_checked, checked_all_artists):
    #    outstring = ""
    #    data_out_albumtitle = "null"
    #    data_out_trackinfo = "null"
    #    data_out_year = "null"
    local_logo = False
    albumtitle = None
    trackinfo = None
    theyear = None
    if multi_artist:
        orig_artist = artist
    log("Checked all artists is %s" %checked_all_artists)
    if xbmcvfs.exists(testpath):     # See if there is a logo in the music directory
        local_logo = True
    else:
        local_logo = False
        log("Logo in Music Directory : Path is %s" %
            testpath, xbmc.LOGDEBUG)

    if onlinelookup == "true":
        mbid = get_mbid(searchartist, dict6)
    else:
        mbid = None
    if tadb == "true":
        artist, logopath, ArtistThumb, ArtistBanner = search_tadb(tadb_json_data, local_logo, mbid, searchartist, dict4, dict5, checked_all_artists)
    else:
        logopath = ""
        ArtistThumb = ""
        ArtistBanner = ""
    log("artist thumb - %s" % ArtistThumb)
    log("artist banner - %s" % ArtistBanner)
    if local_logo:
        logopath = testpath
    if logopath:  # We have a logo to display
        WINDOW.setProperty("srh.Logopath", logopath)
    elif not logopath and not multi_artist:  # No logos to display
        WINDOW.setProperty("srh.Logopath", "")
        log("No logo in cache directory", xbmc.LOGDEBUG)
    if ArtistThumb:
        WINDOW.setProperty("srh.Artist.Thumb", ArtistThumb)
    if ArtistBanner:
        WINDOW.setProperty("srh.Artist.Banner", ArtistBanner)
    WINDOW.setProperty("srh.Musicpath", BaseString)


    if not already_checked:
        log("Not checked the album and year data yet for this artist")
        already_checked, albumtitle, theyear, trackinfo = get_year(
            artist, track, dict1, dict2, dict3, dict7, already_checked)

    if albumtitle and not multi_artist:
        # set if single artist and got album
        WINDOW.setProperty("srh.Album", albumtitle)
        log("Single artist - Window property srh.Album set")
#            data_out_albumtitle =  albumtitle.encode('utf-8')
    elif albumtitle and multi_artist and (WINDOW.getProperty("srh.Album") == ""):
        WINDOW.setProperty("srh.Album", albumtitle)

        log("Multi artist - srh.Album was empty - now set to %s" %
            albumtitle)
    elif not albumtitle and (not multi_artist):
        # clear if no title and not multi artist
        WINDOW.setProperty("srh.Album", "")
        log("No album title for single artist")
    log("Album set to [%s]" % albumtitle)
    if trackinfo:
        trackinfo = trackinfo + '\n'
        WINDOW.setProperty(
            "srh.TrackInfo",
            trackinfo.encode('utf-8'))
#            data_out_trackinfo = trackinfo.encode('utf-8')
    else:
        WINDOW.setProperty("srh.TrackInfo", "")
    if theyear and theyear != '0' and (not multi_artist):
        WINDOW.setProperty("srh.Year", theyear)
#            data_out_year = theyear
    elif theyear and multi_artist and(WINDOW.getProperty("srh.Year") == ""):
        WINDOW.setProperty("srh.Year", theyear)
    elif (not theyear or (theyear == 0)) and (not multi_artist):
        WINDOW.setProperty("srh.Year", "")
    if (albumtitle) and (theyear):
        log("Album & year details found : %s, %s" %
            (albumtitle, theyear), xbmc.LOGDEBUG)
    elif (albumtitle) and not (theyear):
        log("Found album %s but no year" %
            albumtitle, xbmc.LOGDEBUG)
    else:
        log("No album or year details found", xbmc.LOGDEBUG)

    WINDOW.setProperty("srh.AlbumCover", get_local_cover(BaseString, artist, track, albumtitle))


    if multi_artist:
        WINDOW.setProperty("srh.Artist", orig_artist.encode('utf-8'))
    else:
        WINDOW.setProperty("srh.Artist", artist.encode('utf-8'))
    if track:
        WINDOW.setProperty("srh.Track", track.encode('utf-8'))
    else:
        WINDOW.setProperty("srh.Track", "No track info available")
    return already_checked


try:
    WINDOW = xbmcgui.Window(12006)
    if WINDOW.getProperty("streaming-radio-helper-running") == "true":
        log("Script already running - Not starting a new instance")
        exit(0)
    if not xbmc.getCondVisibility("Player.IsInternetStream"):
        log("Not playing an internet stream - quitting")
        exit(0)
    if BaseString == "":
        addon.openSettings(addonname)
    WINDOW.setProperty("streaming-radio-helper-running", "true")
    language = xbmc.getLanguage(xbmc.ISO_639_1).upper()
    log("Version %s started" % addonversion, xbmc.LOGNOTICE)
    log("----------Settings-------------------------", xbmc.LOGNOTICE)
    log("Use fanart.tv : %s" % fanart, xbmc.LOGNOTICE)
    log("use tadb : %s" % tadb, xbmc.LOGNOTICE)
    for key in replacelist:
        log("Changing %s to %s" %
            (key, replacelist[key]), xbmc.LOGNOTICE)
    if luma:
        log("Lookup details for featured artists", xbmc.LOGNOTICE)
    else:
        log("Not looking up details for featured artists", xbmc.LOGNOTICE)
    log("Language is set to %s" % language, xbmc.LOGNOTICE)
    log("----------Settings-------------------------", xbmc.LOGNOTICE)
    log("Setting up addon", xbmc.LOGNOTICE)
    artistlist = load_artist_subs()
    already_checked = False
    log("aready_checked is set to [%s] " % str(already_checked))
    if xbmcvfs.exists(logostring + "data.pickle"):
        dict1, dict2, dict3, dict4, dict5, dict6, dict7 = load_pickle()
    my_size = len(dict1)
    log("Cache contains %d tracks" % my_size, xbmc.LOGNOTICE)
    cut_off_date = todays_date - time_diff
    log("Cached data obtained before before %s will be refreshed if details are missing" %
        (cut_off_date.strftime("%d-%m-%Y")), xbmc.LOGNOTICE)
    rt = RepeatedTimer(900, save_pickle, dict1, dict2,
                       dict3, dict4, dict5, dict6, dict7)


    # Main Loop
    while (not xbmc.abortRequested):
        if xbmc.getCondVisibility("Player.IsInternetStream"):
            if bbc_first_time == 1:
                ct = datetime.datetime.now().time().second
                if bbc_delay == ct:
                    current_track = get_bbc_radio_info(bbc_channel)
                    bbc_delay = set_timer(5)
            else:
                current_track = xbmc.getInfoLabel("Player.Title")
                json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "xbmc.GetInfoLabels", "params":{"labels": ["player.Filename"]}, "id": 1}' )
                file_playing = _json.loads(json_query).get(
                    'result').get('player.Filename')
            try:
                current_track = current_track.decode('utf-8')
            except BaseException:  # can't decode track
                pass  # continue with track as is
            if not file_playing:
                file_playing = current_track
            if firstpass == 0:
                firstpass = 1
                log("File playing is %s" % file_playing, xbmc.LOGDEBUG)
                log("Track playing is [%s]" %
                    current_track, xbmc.LOGDEBUG)
                station, station_list = check_station(file_playing)
                log("Station name was : %s - changed to %s" %
                    (station_list, station), xbmc.LOGDEBUG)
                WINDOW.setProperty("srh.Stationname", station)
            if "BBC Radio" in station:
                if "Two" in station:
                    bbc_channel = 2
                else:
                    bbc_channel = 1
                if bbc_first_time == 0:
                    bbc_delay = set_timer(5)
                    bbc_first_time = 1
                    current_track = get_bbc_radio_info(bbc_channel)
            if "T - Rex" in current_track:
                current_track = current_track.replace(
                    "T - Rex", "T. Rex") # fix artist name for tadb (even though 'T - Rex' is technically correct)
            if " - " in current_track:
                try:
                    x = slice_string(current_track, ' - ', 1)
                    artist = current_track[x + 3:]
                    track = current_track[:x]
                    artist = artist.strip()
                    # Make sure there are no extra spaces in the artist name as
                    # this causes issues
                    artist = " ".join(artist.split())

                    pos = slice_string(track, replace1, 1)
                    if pos != -1:
                        track = track[:pos]
                    else:
                        pos = slice_string(track, replace2, 1)
                        if pos != -1:
                            track = track[:pos]
                        else:
                            pos = slice_string(track, replace3, 1)
                            if pos != -1:
                                track = track[:pos]
                    track = track.strip()
                    if swaplist.get(station) == "true":
                        temp1 = track
                        track = artist
                        artist = temp1
                except Exception as e:
                    log("[Exception %s] while trying to slice current_track %s" % (
                        str(e), current_track), xbmc.LOGDEBUG)
                if (artist.upper() == "ELO") or (artist.upper() ==
                                                 "E.L.O") or (artist.upper() == "E.L.O."):
                    artist = "Electric Light Orchestra"
                try:
                    artist = next(v for k, v in artistlist.items()
                                  if k == (artist))
                except StopIteration:
                    pass
                if was_playing != track:
                    # clear all window properties on track change
                    checked_all_artists, already_checked = no_track()
                    searchartists = []
                    station, station_list = check_station(file_playing)
                    WINDOW.setProperty("srh.Stationname", station)
                    log("Track changed to %s by %s" %
                        (track, artist), xbmc.LOGDEBUG)
                    log("Playing station : %s" % station, xbmc.LOGDEBUG)
                    logopath = ''
                    testpath = BaseString + artist + "/logo.png"
                    testpath = xbmc.validatePath(testpath)

                    tadb_json_data = {}
                    try:

                        _url = 'https://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
                        url = _url + '/search.php?s=' + artist.replace( ' ', '+' ).encode('utf-8')
                        log( "Initial lookup on tadb for artist [%s]" % artist)
                        response = load_url(url)  # see if this is a valid artist before we try splitting the string
                        tadb_json_data = _json.loads(response)
                        if tadb_json_data['artists'] is None:
                            searchartist = artist.replace(' feat. ', ' ~ ').replace(' ft. ', ' ~ ').replace(' feat ', ' ~ ').replace(' ft ', ' ~ ')
                            searchartist = searchartist.replace(' & ', ' ~ ').replace(' and ', ' ~ ').replace(' And ', ' ~ ').replace(' ~ the ', ' and the ').replace(' ~ The ',
                                ' and The ')
                            searchartist = searchartist.replace(' vs ', ' ~ ').replace(', ', ' ~ ')
                        else:
                            searchartist = artist
                    except:
                        searchartist = artist.replace(' feat. ', ' ~ ').replace(' ft. ', ' ~ ').replace(' feat ', ' ~ ').replace(' ft ', ' ~ ')
                        searchartist = searchartist.replace(' & ', ' ~ ').replace(' and ', ' ~ ').replace(' And ', ' ~ ').replace(' ~ the ', ' and the ').replace(' ~ The ',
                                ' and The ')
                        searchartist = searchartist.replace(' vs ', ' ~ ').replace(', ', ' ~ ')

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
                    already_checked = get_info(local_logo, tadb_json_data,
                        testpath,
                        searchartists[artist_index].strip(),
                        artist,
                        multi_artist,
                        already_checked,
                        checked_all_artists)
                    for z in range(0, len(searchartists)):
                        if searchartists[z] in dict6:
                            log("Setting mbid for artist %s to %s" %
                                (searchartists[z], dict6[searchartists[z]]))
                            if first_time:
                                mbids = mbids + dict6[searchartists[z]]
                                first_time = False
                            else:
                                mbids = mbids + "," + \
                                    dict6[searchartists[z]]
                    if mbids:
                        WINDOW.setProperty('srh.MBIDS', mbids)
                    was_playing = track
                    log("Was playing is set to [%s]" % was_playing)
                    et = set_timer(delay)
                    if multi_artist:
                        log("et is [%d]" % (et))
                if multi_artist:
                    cs = datetime.datetime.now().time().second
                    if cs == et:
                        log("Lookup next artist")
                        artist_index += 1
                        if artist_index == num_artists:
                            artist_index = 0
                            checked_all_artists = True
                        already_checked = get_info(local_logo, tadb_json_data,
                            testpath,
                            searchartists[artist_index].strip(),
                            artist,
                            multi_artist,
                            already_checked,
                            checked_all_artists)
                        et = set_timer(delay)
                        log("et is now [%d]" % et)
            else:
                checked_all_artists, already_checked = no_track()
            xbmc.sleep(1000)
        else:
            log("Not an internet stream", xbmc.LOGDEBUG)
        if (xbmc.Player().isPlayingAudio() == False) or (not xbmc.getCondVisibility("Player.IsInternetStream")):
            log("Not playing audio or not an internet stream")
            save_pickle(dict1, dict2, dict3, dict4, dict5, dict6, dict7)
            script_exit()

except Exception as e:
    log("Radio Streaming Helper has encountered an error in the main loop and needs to close - %s" %
        str(e), xbmc.LOGERROR)
    xbmcgui.Dialog().notification(
        "Radio Streaming Helper",
        'A fatal error has occured. Please check the Kodi Log',
        xbmcgui.NOTIFICATION_INFO,
        5000)
    exc_type, exc_value, exc_traceback = sys.exc_info()
    log(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)), xbmc.LOGERROR)
    save_pickle(dict1, dict2, dict3, dict4, dict5, dict6, dict7)

    script_exit()
