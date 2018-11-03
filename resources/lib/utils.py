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
# (C) Black_eagle 2016
#

import xbmc, xbmcvfs, xbmcaddon
import xbmcgui
import urllib, urllib2, re
import uuid
import sys, traceback
from resources.lib.audiodb import audiodbinfo as settings
from resources.lib.audiodb import lastfminfo as lfmsettings

import pickle
import datetime
if sys.version_info >= (2, 7):
    import json as _json
else:
    import simplejson as _json
from threading import Timer

rusty_gate = settings.rusty_gate
happy_hippo = lfmsettings.happy_hippo
addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
addonversion = addon.getAddonInfo('version')
addonpath = addon.getAddonInfo('path').decode('utf-8')
addonid = addon.getAddonInfo('id').decode('utf-8')
language = addon.getLocalizedString

# variables
BaseString = addon.getSetting('musicdirectory')     # Base directory for Music albums
logostring = xbmc.translatePath('special://profile/addon_data/' + addonid + '/').decode('utf-8')  # Base directory to store downloaded logos
logfile = xbmc.translatePath('special://temp/srh.log').decode('utf-8')
pathToAlbumCover = None
albumtitle = ""
was_playing = ""
local_logo = False
got_info = 0
bbc_first_time = 0
bbc_delay = 5
bbc_channel = 2
dict1 = {}  # Key = artistname+trackname, value = Album name
dict2 = {}  # Key = artistname+trackname, value = Album year
dict3 = {}  # Key = artistname+trackname, value = date last looked up
dict4 = {}  # Key = Artist Name, Value = URL to artist thumb
dict5 = {}  # Key = Artist Name, Value = URL to artist banner
dict6 = {}  # Key = artist Name, value = MBID
dict7 = {}  # Key = Artistname+trackname, value = Track details
time_diff = datetime.timedelta(days=7)  # date to next check
todays_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
BaseString = xbmc.validatePath(BaseString)
onlinelookup = addon.getSetting('onlinelookup')
fanart = addon.getSetting('usefanarttv')
tadb = addon.getSetting('usetadb')
replacelist={addon.getSetting('st1find').strip(): addon.getSetting('st1rep').strip(), \
addon.getSetting('st2find').strip(): addon.getSetting('st2rep').strip(), \
addon.getSetting('st3find').strip(): addon.getSetting('st3rep').strip(), \
addon.getSetting('st4find').strip(): addon.getSetting('st4rep').strip(), \
addon.getSetting('st5find').strip(): addon.getSetting('st5rep').strip(), \
addon.getSetting('st6find').strip(): addon.getSetting('st6rep').strip(), \
addon.getSetting('st7find').strip(): addon.getSetting('st7rep').strip(), \
addon.getSetting('st8find').strip(): addon.getSetting('st8rep').strip(), \
addon.getSetting('st9find').strip(): addon.getSetting('st9rep').strip(), \
addon.getSetting('st10find').strip(): addon.getSetting('st10rep').strip()}

artistlist={addon.getSetting('artist1').strip(): addon.getSetting('artistrep1').strip(), \
addon.getSetting('artist2').strip(): addon.getSetting('artistrep2').strip(), \
addon.getSetting('artist3').strip(): addon.getSetting('artistrep3').strip(), \
addon.getSetting('artist4').strip(): addon.getSetting('artistrep4').strip(), \
addon.getSetting('artist5').strip(): addon.getSetting('artistrep5').strip()}

swaplist = {addon.getSetting('st1rep').strip(): addon.getSetting('rev1'), \
addon.getSetting('st2rep').strip(): addon.getSetting('rev2'), \
addon.getSetting('st3rep').strip(): addon.getSetting('rev3'), \
addon.getSetting('st4rep').strip(): addon.getSetting('rev4'), \
addon.getSetting('st5rep').strip(): addon.getSetting('rev5'), \
addon.getSetting('st6rep').strip(): addon.getSetting('rev6'), \
addon.getSetting('st7rep').strip(): addon.getSetting('rev7'), \
addon.getSetting('st8rep').strip(): addon.getSetting('rev8'), \
addon.getSetting('st9rep').strip(): addon.getSetting('rev9'), \
addon.getSetting('st10rep').strip(): addon.getSetting('rev10')}

replace1 = addon.getSetting('remove1').decode('utf-8')
replace2 = addon.getSetting('remove2').decode('utf-8')
replace3 = addon.getSetting('remove3').decode('utf-8')
if addon.getSetting('luma') == 'true':
    luma = True
else:
    luma = False
firstpass = 0
delay = int(addon.getSetting('delay'))
previous_track = None
already_checked = False
checked_all_artists = False
mbid = None
WINDOW = xbmcgui.Window(12006)
debugging = addon.getSetting('debug')
if debugging == 'true' :
    debugging = True
else:
    debugging = False
exportfile = "/home/xbmc/data_out.txt"

data_out= None


def log(txt, mylevel=xbmc.LOGDEBUG):
    """
    Logs to Kodi's standard logfile
    """

    if debugging:
        mylevel = xbmc.LOGNOTICE

    if isinstance(txt, str):
        txt = txt.decode('utf-8')
    message = u'%s : %s' % (addonname, txt)
    xbmc.log(msg=message.encode('utf-8'), level=mylevel)


def download_logo(path,url,origin="Fanart.tv"):

    logopath = path + "logo.png"
    log ("Download logo [%s] " % logopath)
    imagedata = urllib.urlopen(url).read()
    f = open(logopath, 'wb')
    f.write(imagedata)
    f.close()
    log("Downloaded logo from %s" % origin, xbmc.LOGDEBUG)
    return logopath


def clean_string(text):
    text = re.sub('<a [^>]*>|</a>|<span[^>]*>|</span>', '', text)
    text = re.sub('&quot;', '"', text)
    text = re.sub('&amp;', '&', text)
    text = re.sub('&gt;', '>', text)
    text = re.sub('&lt;', '<', text)
    text = re.sub('User-contributed text is available under the Creative Commons By-SA License; additional terms may apply.', '', text)
    text = re.sub('Read more about .* on Last.fm.', '', text)
    text = re.sub('Read more on Last.fm.', '', text)
    return text


def load_pickle():
    """
    Loads cache data from file in the addon_data directory of the script
    """
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    log("            Entered routine 'load_pickle'           ", xbmc.LOGDEBUG)
    log("----------------------------------------------------", xbmc.LOGDEBUG)

    log("Loading data from pickle file")
    pfile = open(logostring + 'data.pickle',"rb")
    d1 = pickle.load(pfile)
    d2 = pickle.load(pfile)
    d3 = pickle.load(pfile)
    try:
        d4 = pickle.load(pfile)
        d5 = pickle.load(pfile)
    except:
        d4 = {}
        d5 = {}
        log("Pickle data for thumb and banner art didn't exist. Creating new dictionaries")
    try:
        d6 = pickle.load(pfile)
    except:
        d6 = {}
        log("created new pickle data for MBID storage")
    try:
        d7 = pickle.load(pfile)
    except:
        d7 = {}
        log("Created new pickle data for track information")
    pfile.close()
    return d1, d2, d3, d4, d5, d6, d7


def save_pickle(d1, d2, d3, d4, d5, d6, d7):
    """
    Saves local cache data to file in the addon_data directory of the script
    """
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    log("            Entered routine 'save_pickle'           ", xbmc.LOGDEBUG)
    log("----------------------------------------------------", xbmc.LOGDEBUG)

    log("Saving data to pickle file")

    pfile = open(logostring + 'data.pickle',"wb")
    pickle.dump(d1, pfile)
    pickle.dump(d2, pfile)
    pickle.dump(d3, pfile)
    pickle.dump(d4, pfile)
    pickle.dump(d5, pfile)
    pickle.dump(d6, pfile)
    pickle.dump(d7, pfile)
    pfile.close()

def load_url(url):

    try:
        response = urllib2.urlopen(url).read().decode('utf-8')
        if 'service' in response:
            return None
        else : return response
    except IOError as e:
        if hasattr(e,'reason'):
            log("Failed to reach server with url [%s]" % url, xbmc.LOGERROR)
            log("Error returned was [%s]" %e.reason, xbmc.LOGERROR)
        elif hasattr(e,'code'):
           log("Error getting url [%s]  Error code was [%s]" % ( url, e.code ) , xbmc.LOGERROR)

def get_local_cover(BaseString, artist, track, albumtitle):

    try:
        if albumtitle:
            pathToAlbumCover = xbmc.validatePath(BaseString + artist + "/" + albumtitle + "/cover.png")
            log("Looking for an album cover in %s" % pathToAlbumCover, xbmc.LOGDEBUG)
            if xbmcvfs.exists(pathToAlbumCover):
                log("Found a local 'cover.png' and set AlbumCover to [%s]" % pathToAlbumCover, xbmc.LOGDEBUG)
                return pathToAlbumCover
            pathToAlbumCover = xbmc.validatePath(BaseString + artist + "/" + albumtitle + "/folder.jpg")
            log("Looking for an album cover in %s" % pathToAlbumCover, xbmc.LOGDEBUG)
            if xbmcvfs.exists(pathToAlbumCover):
                log("Found a local 'folder.jpg' and set AlbumCover to [%s]" % pathToAlbumCover, xbmc.LOGDEBUG)
                return pathToAlbumCover
        pathToAlbumCover = xbmc.validatePath(BaseString + artist + "/" + track + "/folder.jpg")
        if xbmcvfs.exists(pathToAlbumCover):
            log("Found a local 'folder.jpg' and set AlbumCover to [%s]" % pathToAlbumCover, xbmc.LOGDEBUG)
            return pathToAlbumCover
        pathToAlbumCover = xbmc.validatePath(BaseString + artist + "/" + track + "/cover.png")
        log("Looking for an album cover in %s (last attempt before using thumbnail)" % pathToAlbumCover, xbmc.LOGDEBUG)
        if xbmcvfs.exists(pathToAlbumCover):
            log("Found a local 'cover.png' and set AlbumCover to [%s]" % pathToAlbumCover, xbmc.LOGDEBUG)
            return pathToAlbumCover
        return None

    except Exception as e:
        log("Got an error trying to look for a cover!! [%s]" % str(e), xbmc.LOGDEBUG)
        pass
        return None

def check_station(file_playing):
    """Attempts to parse a URL to find the name of the station being played
    and performs substitutions to 'pretty up' the name if those options
    are set in the settings"""
    station_list = ''
    if 'BBC Radio 2' in file_playing:
        return "BBC Radio Two", file_playing
    if '1Xtra' in file_playing:
        return 'BBC Radio 1xtra', file_playing
    if 'BBC Radio 1' in file_playing:
        return "BBC Radio One", file_playing

    try:
        if 'icy-' in file_playing:  # looking at an ICY stream
            x = file_playing.rfind('/')
            station_list = file_playing[x + 1:]
            if ('.' in station_list) and ("http" not in station_list):
                station, ending = station_list.split('.')

        elif '|' in file_playing:
            y = file_playing.rfind('|')
            station_list = file_playing[:y]
            x = station_list.rfind('/')
            station = station_list[x + 1:]
        else:
            if 'http://' in file_playing:
                station_list = file_playing.strip('http://')
            if 'https://' in file_playing:
                station_list = file_playing.strip('https://')
            if 'smb://' in file_playing:
                station_list = file_playing.strip('smb://')
            x = station_list.rfind(':')
            if x != -1:
                station = station_list[:x]
            else:
                station = station_list
        if not station_list:                    # If this is empty we haven't found anything to use as a station name yet
            if 'm3u' in file_playing:           # Sometimes kodi makes a playlist of one streaming channel so check for this
                station_list = file_playing.replace( '.m3u', '')
            else:
                station_list = file_playing     # just use whatever we have (rad.io addon filename will be the ID of the station (11524 for planet rock)
        try:
            station = next(v for k, v in replacelist.items()
                           if k in (station_list))
            log("Station is [%s], station_list is [%s]" %(station, station_list), xbmc.LOGDEBUG)
            return station, station_list
        except StopIteration:
            return station, station_list
    except Exception as e:
        log("Error trying to parse station name [ %s ]" % str(
            e), xbmc.LOGERROR)
        return 'Online Radio', file_playing

def get_year(artist, track, dict1, dict2, dict3, dict7, already_checked):
    """
    Look in local cache for album and year data corresponding to current track and artist.
    Return the local data if present, unless it is older than 7 days in which case re-lookup online.
    If data not present in cache, lookup online and add to cache
    If all data present in cache, just return that and don't lookup anything online.
    """
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    log("            Entered routine 'get_year'           ", xbmc.LOGDEBUG)
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    lun = False
    if (artist == "") and (track == ""):
        return True, None,None,None
    log("Looking up album and year data for artist %s and track %s" %(artist, track), xbmc.LOGDEBUG)
    my_size = len(dict1)
    log("Cache currently holds %d tracks" % my_size, xbmc.LOGDEBUG)
    keydata = artist.replace(" ","").lower() + track.replace(" ","").lower()
    log("keydata is %s" % keydata, xbmc.LOGDEBUG)
    if keydata in dict1 and already_checked == False :
        log("Track %s in local data cache" % track, xbmc.LOGDEBUG)
        albumname = dict1[keydata]
        log("Album Name is %s" % albumname, xbmc.LOGDEBUG)
        datechecked = dict3[keydata]
        try:
            trackinfo = dict7[keydata]
            log("Track info is [%s]" % trackinfo, xbmc.LOGDEBUG)
        except Exception as e:
            log("Updating info for track [%s]" % track, xbmc.LOGDEBUG)
            lun = True
            dict1[keydata], dict2[keydata], dict7[keydata] = tadb_trackdata(artist, track, dict1, dict2, dict3, dict7)
            dict3[keydata] = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
        log("Data for track '%s' on album '%s' last checked %s" % (track, dict1[keydata], str(datechecked.strftime("%d-%m-%Y"))), xbmc.LOGDEBUG)
        if (datechecked < (todays_date - time_diff)) or (xbmcvfs.exists(logostring + "refreshdata")):
            log( "Data might need refreshing", xbmc.LOGDEBUG)
            if (dict1[keydata] == '') or (dict1[keydata] == None) or (dict1[keydata] == 'None') or (dict1[keydata] == 'null') or (xbmcvfs.exists(logostring + "refreshdata")):
                log("No album data - checking TADB again", xbmc.LOGDEBUG)
                dict1[keydata], dict2[keydata], dict7[keydata] = tadb_trackdata(artist, track, dict1, dict2, dict3, dict7)
                dict3[keydata] = datetime.datetime.combine(datetime.date.today(),datetime.datetime.min.time())
                log("Data refreshed")
            elif (dict2[keydata] == None) or (dict2[keydata] == '0') or (dict2[keydata] == ''):
                log("No year data for album %s - checking TADB again" % dict1[keydata], xbmc.LOGDEBUG)
                dict1[keydata], dict2[keydata], dict7[keydata] = tadb_trackdata(artist, track, dict1, dict2, dict3, dict7)
                dict3[keydata] = datetime.datetime.combine(datetime.date.today(),datetime.datetime.min.time())
                log("Data refreshed", xbmc.LOGDEBUG)
            elif (dict7[keydata] == None) or (dict7[keydata] == "None") or (dict7[keydata] == "") and (lun == False): # don't lookup again if we have just done it (Line 196)
                log("No text data for track - re-checking TADB", xbmc.LOGDEBUG)
                dict1[keydata], dict2[keydata], dict7[keydata] = tadb_trackdata(artist,track,dict1,dict2,dict3, dict7)
                dict3[keydata] = datetime.datetime.combine(datetime.date.today(),datetime.datetime.min.time())
            elif lun == True:
                log("Track data just looked up. No need to refresh other data right now!", xbmc.LOGDEBUG)
            else:
                log( "All data present - No need to refresh", xbmc.LOGDEBUG)
            return True, dict1[keydata], dict2[keydata], dict7[keydata]
        else:
            log( "Using cached data", xbmc.LOGDEBUG )
            return True, dict1[keydata],dict2[keydata], dict7[keydata]
    elif already_checked == False:
        log("New track - get data for %s : %s" %(artist, track), xbmc.LOGDEBUG)
        dict1[keydata], dict2[keydata], dict7[keydata] = tadb_trackdata(artist,track,dict1,dict2,dict3, dict7)

        dict3[keydata] = datetime.datetime.combine(datetime.date.today(),datetime.datetime.min.time())
        log( "New data has been cached", xbmc.LOGDEBUG)
        return True, dict1[keydata], dict2[keydata], dict7[keydata]

def tadb_trackdata(artist,track,dict1,dict2,dict3, dict7):
    """
    Searches theaudiodb for an album containing track.  If a album is found, attempts
    to get the year of the album.  Returns album name and year if both are found, just the album name if
    no year is found, or none if nothing is found
    """
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    log("          Entered routine 'tadb_trackdata'          ", xbmc.LOGDEBUG)
    log("----------------------------------------------------", xbmc.LOGDEBUG)

    searchartist = artist.replace(" ","+").encode('utf-8')
    searchtrack = track.replace(" ","+").encode('utf-8')
    searchtrack = searchtrack.replace("&","and")
    searchtrack = searchtrack.rstrip("+")
    if "(Radio Edit)" in searchtrack:
        searchtrack = searchtrack.replace("(Radio Edit)","").strip()  # remove 'radio edit' from track name
    if "(Live)" in searchtrack:
        searchtrack = searchtrack.replace("(Live)","").strip()
    if "+&+" in searchtrack:
        searchtrack = searchtrack.replace("+&+"," and ").strip()
    url = 'https://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
    searchurl = url + '/searchtrack.php?s=' + searchartist + '&t=' + searchtrack
    log("Search artist, track with strings : %s,%s" %(searchartist,searchtrack), xbmc.LOGDEBUG)
    keydata = artist.replace(" ","").lower() + track.replace(" ","").lower()
    if keydata in dict1: # seen this artist/track before
        if keydata in dict7: # already possibly have some track info
            if dict7[keydata] is not None:
                log("Using cached data & not looking anything up online", xbmc.LOGDEBUG)
                return dict1[keydata], dict2[keydata], dict7[keydata]

    try:
        try:
            response = load_url(searchurl)
            searching = _json.loads(response)
        except ValueError:
            log("No json data to parse !!",xbmc.LOGDEBUG)
            searching = []

    #        log("JSON data = %s" % searching, xbmc.LOGDEBUG)
        try:
            album_title = searching['track'][0]['strAlbum']

        except:
            album_title = None
            pass
        trackinfo = None
        try:
            trackinfo = searching['track'][0]['strDescriptionEN']
        except:
            trackinfo = None
            log('No track info from TADB', xbmc.LOGDEBUG)
            pass
        if (trackinfo is not None) and (len (trackinfo) > 3) :
            dict7[keydata] = trackinfo
        else:
            trackinfo = None
            log("Not found any track data so far, continuing search on lastFM", xbmc.LOGDEBUG)
        if trackinfo is None :
            lastfmurl = "http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key=%s" % happy_hippo.decode( 'base64' )
            lastfmurl = lastfmurl+'&artist='+searchartist+'&track='+searchtrack+'&format=json'
            log("LastFM url is [%s] " % lastfmurl, xbmc.LOGDEBUG)
            try:
                response = load_url(lastfmurl)
                stuff = json.loads(response)
                searching = stuff['track']
            except:
                searching = []
                pass
    #                log("JSON from Last-FM [%s]" % searching)
            if 'wiki' in searching:
                    try:
                        trackinfo = searching['wiki']['content']
                    except:
                        pass
                    try:
                        trackinfo = searching['wiki']['summary']
                    except:
                        passstuff = json.loads(response)
            if trackinfo:
                trackinfo = clean_string(trackinfo)
            log("Trackinfo - [%s]" % trackinfo, xbmc.LOGDEBUG)
            if trackinfo is not None and len(trackinfo) < 3:
                log ("No track info found", xbmc.LOGDEBUG)
                trackinfo = None
            else:
                log("No track info found on lastFM", xbmc.LOGDEBUG)
                if trackinfo:
                    trackinfo = clean_string(trackinfo)
                log("Trackinfo - [%s]" % trackinfo, xbmc.LOGDEBUG)
        dict7[keydata] = trackinfo



        if (album_title == "") or (album_title == "null") or (album_title == None):
            log("No album data found on TADB ", xbmc.LOGDEBUG)
            log("trying to use LastFM data", xbmc.LOGDEBUG)
            try:
                album_title = searching['album']['title']
                log("Album title [%s]" % album_title, xbmc.LOGDEBUG)

            except Exception as e:
                trackinfo = None
                log("No album title", xbmc.LOGDEBUG)
                log("ERROR [%s]" % str(e))
                pass


        if album_title is not None:
            album_title_search = album_title.replace(" ","+").encode('utf-8')
            searchurl = url + '/searchalbum.php?s=' + searchartist + '&a=' + album_title_search
            log("Search artist,album with strings : %s,%s" %(searchartist,album_title_search), xbmc.LOGDEBUG)
            response = load_url(searchurl)
            try:
                searching = _json.loads(response)
                the_year = "null"
            except ValueError:
                log("No JSON from TADB - Site down ??", xbmc.LOGINFO)
                searching = []
                the_year = "null"
            try:
                the_year = searching['album'][0]['intYearReleased']
            except:
                pass
            if (the_year == "") or (the_year == "null"):
                log("No year found for album", xbmc.LOGDEBUG)
                return album_title, None, dict7[keydata]
            log("Got '%s' as the year for '%s'" % ( the_year, album_title), xbmc.LOGDEBUG)
            log("keydata is set to %s " % keydata, xbmc.LOGDEBUG)
            if keydata in dict7:
                return album_title, the_year, dict7[keydata]
            else:
                return album_title, the_year, None

        else:
            log("No album title to use as lookup - returning Null values")
            if keydata in dict7:
                return None, None, dict7[keydata]
            else:
                return None, None, None
    except IOError:
        log("Timeout connecting to TADB", xbmc.LOGERROR)
        if keydata in dict1 and keydata in dict7:
            return dict1[keydata], dict2[keydata], dict7[keydata]
        elif keydata in dict1 and keydata not in dict7:
            return dict1[keydata], dict2[keydata], None
        else:
            return None, None, None
    except Exception as e:
        log("Error searching theaudiodb for album and year data [ %s ]" % str(e), xbmc.LOGERROR)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)), xbmc.LOGERROR)
        if keydata in dict1 and keydata in dict7:
            return dict1[keydata], dict2[keydata], dict7[keydata]
        elif keydata in dict1:
            return dict1[keydata], dict2[keydata], None
        else:
            return None, None, None

def get_mbid(artist, dict6):
    """
    Gets the MBID for a given artist name.
    Note that radio stations often omit 'The' from band names so this may return the wrong MBID

    Returns the Artist MBID or a self generated one if the lookup fails and we haven't cached one previously
    """
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    log("            Entered routine 'get_mbid'              ", xbmc.LOGDEBUG)
    log("----------------------------------------------------", xbmc.LOGDEBUG)

    log("Getting mbid for artist %s " % artist, xbmc.LOGDEBUG)
    em_mbid = str(uuid.uuid5(uuid.NAMESPACE_DNS, artist.encode('utf-8')))  # generate an emergency mbid in case lookup fails
    try:
        if '/' in artist:
            artist = artist.replace('/',' ')
        elif artist.lower() == 'acdc':
            artist = "AC DC"
        if artist in dict6:
            log("Using cached MBID")
            return dict6[artist]
        url = 'http://musicbrainz.org/ws/2/artist/?query=artist:%s' % artist
        url = url.encode('utf-8')
        response = urllib.urlopen(url).read()
        if (response == '') or ("MusicBrainz web server" in response):
            log("Unable to contact Musicbrainz to get an MBID", xbmc.LOGDEBUG)
            log("using %s as emergency MBID" % em_mbid)
            return em_mbid
        index1 = response.find("artist id")
        index2 = response.find("type")
        mbid = response[index1+11:index2-2].strip()
        if '"' in mbid:
            mbid = mbid.strip('"')
        if len(mbid )> 36:
            mbid = mbid[0:36]
        log('Got an MBID of : %s' % mbid, xbmc.LOGDEBUG)
        if mbid == '':
            log("Didn't get an MBID for artist : %s" % artist, xbmc.LOGDEBUG)
            log("using %s as emergency MBID" % em_mbid)
            return em_mbid
        if artist not in dict6:
            log("Caching mbid [%s] for artist [%s]" %(mbid, artist), xbmc.LOGDEBUG)
            dict6[artist] = mbid
        return mbid
    except Exception as e:
        log ("There was an error getting the Musicbrainz ID [ %s ]" % str(e), xbmc.LOGERROR)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)), xbmc.LOGERROR)
        return em_mbid

def check_cached_logo(logopath, url):

    if (not xbmcvfs.exists(logopath)):
            xbmcvfs.mkdir(logopath)
            log("Created directory [%s] to download logo from [%s]" %( logopath, url), xbmc.LOGDEBUG)
            logopath = download_logo(logopath, url, "tadb")
            return logopath
    else:
        logopath = logopath + 'logo.png'
        logopath = xbmc.validatePath(logopath)

        if xbmcvfs.exists(logopath):
            log("Logo has already been downloaded and is in cache. Path is %s" % logopath, xbmc.LOGDEBUG)
            return logopath
        else:
            log("Nothing to return - this must be wrong !!", xbmc.LOGDEBUG)
            return None



def get_hdlogo(mbid, artist):
    """
    Get the first found HD clearlogo from fanart.tv if it exists.

    Args:
         The MBID of the artist and the artist name

    Returns :
        The fully qualified path to an existing logo or newly downloaded logo or
        None if the logo is not found
        """
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    log("            Entered routine 'get_hdlogo'            ", xbmc.LOGDEBUG)
    log("----------------------------------------------------", xbmc.LOGDEBUG)

    try:
        if checked_all_artists == False:
            url = "https://fanart.tv/artist/" + mbid
            logopath = logostring + mbid + "/logo.png"
            logopath = xbmc.validatePath(logopath)
            if not xbmcvfs.exists(logopath):
                log("Searching for HD logo on fanart.tv", xbmc.LOGDEBUG)
                response = urllib.urlopen(url).read()
                if response == '':
                    log("No response from fanart.tv", xbmc.LOGDEBUG)
                    return None
                index1 = response.find("<h2>HD ClearLOGO<div")
                if index1 != -1:
                    index2 = response.find('<div class="image_options">',index1)
                    anylogos = response[index1:index2]
                    if "currently no images" in anylogos:
                        log("No HD logos found for %s" % artist, xbmc.LOGDEBUG)
                        return None
                    index3= response.find('<a href="/api/download.php?type=download')
                    index4 = response.find('class="btn btn-inverse download"')
                    chop = response[index3+9:index4-2]
                    url = "https://fanart.tv" + chop
                    logopath = logostring + mbid + '/'
                    logopath = xbmc.ValidatePath(logopath)
                    xbmcvfs.mkdir(logopath)
                    logopath = download_logo(logopath,url)
                    return logopath
            else:
                logopath = logostring + mbid + '/logo.png'
                logopath = xbmc.validatePath(logopath)
                if xbmcvfs.exists(logopath):
                    log("Logo downloaded previously", xbmc.LOGDEBUG)
                    return logopath
                else:
                    log("No logo found on fanart.tv", xbmc.LOGDEBUG)
                    return None
        else:
            logopath = logostring + mbid + '/logo.png'
            logopath = xbmc.validatePath(logopath)
            if xbmcvfs.exists(logopath):
                log("Logo downloaded previously", xbmc.LOGDEBUG)
                return logopath
            else:
                log("No logo in cache for %s " % artist, xbmc.LOGDEBUG)
                return None
    except:
        log("Error searching fanart.tv for a logo", xbmc.LOGERROR)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)), xbmc.LOGERROR)
        return None

def search_tadb(tadb_json_data, local_logo, mbid, artist, dict4, dict5,checked_all_artists):
    """
    Checks to see if there is an existing logo locally in the scripts addon_data directory.
    If not, attempts to find a logo on theaudiodb and download it into the cache. As radio stations often
    drop 'The' from band names (eg 'Who' for 'The Who', 'Kinks' for 'The Kinks') if we fail to find a match
    for the artist we try again with 'The ' in front of the artist name
    Finally we do a search with the MBID we previously obtained

    Args:
         mbid   - the mbid from musicbrainz
         artist - name of the artist to search for
         dict4  - dictionary of banner URL's
         dict5  - dictionary of thumbnail URL's

    returns:
         artist   - artist name
         logopath - full path to downloaded logo
         URL1     - URL to artist banner on TADB
         URL2     - URL to artist thumb on TADB
    """
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    log("            Entered routine 'search_tadb'           ", xbmc.LOGDEBUG)
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    logopath = ''
    url = ''
    if tadb_json_data: # already got some data to work with
        searchartist = artist.replace(" ", "+")
        searching = tadb_json_data
        log("Using json from default.py", xbmc.LOGDEBUG)
        #if artist == None:
            #log("Error, artist is None", xbmc.LOGERROR)
        #elif searching == None:
            #log("Error, searching is None", xbmc.LOGERROR)
        #elif searchartist == None:
            #log("Error, searchartist is None", xbmc.LOGERROR)
        #elif dict4 == None:
            #log("Error, dict4 is None", xbmc.LOGERROR)
        #elif dict5 == None:
            #log("Error, dict5 is None", xbmc.LOGERROR)
        #elif mbid == None:
            #log("Error, artist is None", xbmc.LOGERROR)

        artist, url, dict4, dict5, mbid = parse_data(artist, searching, searchartist, dict4, dict5, mbid)

    else:
        log("Looking up %s on tadb.com" % artist, xbmc.LOGDEBUG)
        searchartist = artist.replace( " ", "+" )
        log ("[search_tadb] : searchartist = %s" % searchartist)
        url = 'https://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
        searchurl = url + '/search.php?s=' + (searchartist.encode('utf-8'))

        log("URL for TADB is : %s" % searchurl, xbmc.LOGDEBUG)


        response = load_url(searchurl)
        if response :
            if (response == '{"artists":null}') or (response == '') or ('!DOCTYPE' in response) or (response == None):
                searchartist = 'The+' + searchartist
                url = 'https://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
                searchurl = url + '/search.php?s=' + (searchartist.encode('utf-8'))
                log("Looking up %s on tadb.com with URL %s" % (searchartist, searchurl), xbmc.LOGDEBUG)
                response = load_url(searchurl)
                log(response, xbmc.LOGDEBUG)
        if response:
            if (response == '{"artists":null}') or (response == '') or ('!DOCTYPE' in response) or (response == None):
                log("Artist not found on tadb", xbmc.LOGDEBUG)
                    # Lookup failed on name - try with MBID
                log("Looking up with MBID", xbmc.LOGDEBUG)
                url = 'https://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
                searchurl = url + '/artist-mb.php?i=' + mbid
                log("MBID URL is : %s" % searchurl, xbmc.LOGDEBUG)
                response = load_url(searchurl)
                log("Response : %s " % str(response), xbmc.LOGDEBUG)
        if not response:
            log("Failed to find any artist info on theaudiodb", xbmc.LOGDEBUG)
            return artist, None, None, None


        searching = _json.loads(response)
        artist, url, dict4, dict5, mbid = parse_data(artist, searching, searchartist, dict4, dict5, mbid)
    if (not local_logo) and url:
        log("No local logo", xbmc.LOGDEBUG)
        logopath = logostring + mbid + '/'
        logopath = xbmc.validatePath(logopath)
        logopath = check_cached_logo (logopath, url)
    if searchartist in dict4:
        return artist, logopath, dict4[searchartist], dict5[searchartist]
    else:
        return artist, logopath, None, None

    #except IOError:
            #log("IOError in function [search_tadb] No data from TADB was collected", xbmc.LOGERROR)
            #if searchartist in dict4:
                #if xbmcvfs.exists(logopath):
                    #return artist, logopath,dict4[searchartist], dict5[searchartist]
                #else:
                    #return artist, None, dict4[searchartist], dict5[searchartist]
            #return artist, logopath, None, None
    #except Exception as e:
        #log("Error searching theaudiodb for a logo : [ %s ]" % str(e), xbmc.LOGERROR)
        #exc_type, exc_value, exc_traceback = sys.exc_info()
        #log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
        #log("Artist is type %s, searching - %s,searchartist - %s, dict4 - %s, dict5 - %s, mbid - %s" %(type(artist), type(searching), type(searchartist), type(dict4), type(dict5), type(mbid)), xbmc.LOGDEBUG)

    return artist, None, None, None
    #logopath = logostring + mbid + "/logo.png"
    #logopath = xbmc.validatePath(logopath)
    #if (not xbmcvfs.exists(logopath)) and ( local_logo = True ) and not checked_all_artists: # Don't need to look up a logo as we found one in the local directory



            #logopath = logostring + mbid + '/'
            #logopath = xbmc.validatePath(logopath)
            #if (not xbmcvfs.exists(logopath)) and (url != None):
                #xbmcvfs.mkdir(logopath)
                #logopath = download_logo(logopath,url,"tadb")
                #return artist, logopath, dict4[searchartist], dict5[searchartist]
            #else:
                #logopath = logostring + mbid + '/logo.png'
                #logopath = xbmc.validatePath(logopath)
                #if xbmcvfs.exists(logopath):
                    #log("Logo has already been downloaded and is in cache. Path is %s" % logopath, xbmc.LOGDEBUG)
                    #return artist, logopath, dict4[searchartist], dict5[searchartist]
                #else:
                    #return artist, None, dict4[searchartist], dict5[searchartist]


    #else:
        ##  at this point, we have a logo cached to disk previously so we have already looked up this artist at least once
        ##  we need to check if we have thumb or banner data and only look up if not

        #searchartist = artist.replace(" ","+")
        #log("searchartist is [%s] - checked_all_artists is [%s]" % (searchartist, checked_all_artists))
        #if searchartist in dict4:
            #log("Searchartist is in dict4 - we have previous thumb/banner data")
            #log("Window property 'haslogo' is [%s]" %(WINDOW.getProperty("srh.Haslogo")))
        #if searchartist in dict4 and (checked_all_artists == False):   # we have looked up this artist before
            #logopath = logostring + mbid + '/logo.png'
            #logopath = xbmc.validatePath(logopath)
            #if (xbmcvfs.exists(logopath)) and (WINDOW.getProperty("srh.Haslogo") == "false"):
                #log("Logo has already been downloaded and is in cache. Path is %s" % logopath, xbmc.LOGDEBUG)
                #log("Checking thumb and banner data")
                #if (dict4[searchartist] != None) and (dict5[searchartist] != None): # have both banner and thumb
                    #log("Thumb and banner both cached already ")
                    #return artist, logopath, dict4[searchartist], dict5[searchartist]
                #else:
                    #log("Artist or thumb data missing")
            #elif WINDOW.getProperty("srh.Haslogo") == "true":
                #log("Using logo from local music directory - checking thumb and banner data")
                #if (dict4[searchartist] != None) and (dict5[searchartist] != None): # have both
                    #log("Thumb and banner both cached already ")
                    #return artist, None, dict4[searchartist], dict5[searchartist] # Don't need the path as using local logo already
                #else:
                    #log("Thumb or banner data missing - TADB will be re-checked")
        #url = 'https://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
        #searchurl = url + '/artist-mb.php?i=' + mbid
        #log("MBID lookup to check artist name is correct")
        #if searchartist != "P!nk" or searchartist != "p!nk" or searchartist !="Pink" or searchartist != "pink":
            #try:
                #response = urllib.urlopen(searchurl).read()
                #if (response != '{"artists":null}') and (response != '') and ('!DOCTYPE' not in response):
                    #try:
                        #searching = _json.loads(response)
                        #artist, url, dict4, dict5, mbid = parse_data (artist, searching, searchartist, dict4, dict5, mbid)
                    #except ValueError:
                        #log ("JSON error in function [search_tadb]. It appears we have no data to return !!", xbmc.LOGERROR)
                        #if searchartist in dict4:
                            #log("Using cached URL data")
                            #return artist, logopath, dict4[searchartist], dict5[searchartist]  # Kodi's thumbnail cache will return images
                        #else:
                            #return artist, logopath, None, None
            #except IOError:
                #pass
        #if searchartist in dict4 and (not checked_all_artists):   # we have looked up this artist before
            #logopath = logostring + mbid + '/logo.png'
            #logopath = xbmc.validatePath(logopath)
            #if (xbmcvfs.exists(logopath)) and (WINDOW.getProperty("srh.Haslogo") == "false"):
                #log("Logo has already been downloaded and is in cache. Path is %s" % logopath, xbmc.LOGDEBUG)
                #log("Checking thumb and banner data")
                #if (dict4[searchartist] != None) and (dict5[searchartist] != None): # have both banner and thumb
                    #log("Thumb and banner both cached already ")
                    #return artist, logopath, dict4[searchartist], dict5[searchartist]
                #else:
                    #log("Artist or thumb data missing")
            #elif WINDOW.getProperty("srh.Haslogo") == "true":
                #log("Using logo from local music directory - checking thumb and banner data")
                #if (dict4[searchartist] != None) and (dict5[searchartist] != None): # have both
                    #log("Thumb and banner both cached already ")
                    #return artist, None, dict4[searchartist], dict5[searchartist] # Don't need the path as using local logo already
                #else:
                    #log("Thumb or banner data missing - TADB will be re-checked")
        ## We haven't got any thumb or banner data before up OR thumb or banner data is missing so look up on tadb
        #log("Looking up thumb and banner data for artist %s" % artist)
        #if (not checked_all_artists) and searchartist not in dict4:
            #url = 'https://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
            #searchurl = url + '/search.php?s=' + urllib.quote(searchartist.encode('utf-8'))
            #log("URL for TADB is : %s" % searchurl, xbmc.LOGDEBUG)
            #try:
                #response = urllib.urlopen(searchurl).read()
                #if response == '':
                    #log("No response from theaudiodb", xbmc.LOGDEBUG)
                    #return artist, None, None, None
                #log(response)
                #if response != '{"artists":null}':
                    #try:
                        #searching = _json.loads(response)
                        #artist, url, dict4, dict5, mbid = parse_data(artist, searching, searchartist, dict4, dict5, mbid, False)
                    #except ValueError:
                        #log ("No JSON data to parse", xbmc.LOGERROR)
                    #pass
                #else:
                    #searchartist = 'The+' + searchartist
                    #url = 'https://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )

                    #searchurl = url + '/search.php?s=' + urllib.quote(searchartist.encode('utf-8'))
                    #log("Looking up %s on tadb.com with URL %s" % (searchartist, searchurl), xbmc.LOGDEBUG)
                    #response = urllib.urlopen(searchurl).read()
                    #log(response)
                    #if (response == '') or (response == '{"artists":null}') or ("!DOCTYPE" in response):
                        #log("No info returned from tadb", xbmc.LOGDEBUG)
                        #log("Looking up with MBID", xbmc.LOGDEBUG)
                        #url = 'https://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
                        #searchurl = url + '/artist-mb.php?i=' + mbid
                        #log("MBID URL is : %s" % searchurl)
                        #response = urllib.urlopen(searchurl).read()
                        #log("Response was %s" %str(response), xbmc.LOGDEBUG)
                        #if (response != '{"artists":null}') and (response != '') and ('!DOCTYPE' not in response):
                            #searching = _json.loads(response)
                            #artist, url, dict4, dict5, mbid = parse_data (artist, searching, searchartist, dict4, dict5, mbid)
                        #else:
                            #log("Failed to find any artist info on theaudiodb", xbmc.LOGDEBUG)
                            #return artist, None, None, None

                    #else:
                        #searching = _json.loads(response)
                        #artist, url, dict4, dict5, mbid = parse_data(artist, searching, searchartist, dict4, dict5, mbid, False)

                #logopath = logostring + mbid + '/logo.png'
                #logopath = xbmc.validatePath(logopath)
                #if xbmcvfs.exists(logopath):
                    #log("Logo has already been downloaded and is in cache. Path is %s" % logopath, xbmc.LOGDEBUG)
                    #if searchartist in dict4:
                        #return artist, logopath, dict4[searchartist], dict5[searchartist]
                    #else:
                        #return artist, logopath, None, None
                #else:
                    #if searchartist in dict4:
                        #return artist, None, dict4[searchartist], dict5[searchartist]
                    #else:
                        #return artist, None, None, None
            #except IOError:
                #log("IOError in function [search_tadb] No data from TADB was collected", xbmc.LOGERROR)
                #if searchartist in dict4:
                    #if xbmcvfs.exists(logopath):
                        #return artist, logopath,dict4[searchartist], dict5[searchartist]
                    #else:
                        #return artist, None, dict4[searchartist], dict5[searchartist]
                #return artist, None, None, None
            #except Exception as e:
                #log("Error searching theaudiodb [ %s ]" % str(e), xbmc.LOGERROR)
                #exc_type, exc_value, exc_traceback = sys.exc_info()
                #log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
                #return artist, None, None, None
        #logopath = logostring + mbid + '/logo.png'
        #logopath = xbmc.validatePath(logopath)
        #if xbmcvfs.exists(logopath) and searchartist in dict4:
            #log("Logo has already been downloaded and is in cache. Path is %s" % logopath, xbmc.LOGDEBUG)
            #return artist, logopath, dict4[searchartist], dict5[searchartist]
        #elif searchartist in dict4:
                #return artist, None, dict4[searchartist], dict5[searchartist]
        #else:
            #return artist, None, None, None

def parse_data(artist, searching, searchartist, dict4, dict5, mbid):
    """
       Parse the JSON data for the values we want
       Also checks the artist name is correct if the first two lookups on TADB failed
       and corrects it if possible
    """
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    log("            Entered routine 'parse_data'            ", xbmc.LOGDEBUG)
    log("----------------------------------------------------", xbmc.LOGDEBUG)
    url = ''
    checkartist = ''
    try:
        try:
            if searching['artists'][0]['strArtist']:
                checkartist = searching['artists'][0]['strArtist']
        except:
            log("No artist found on tadb for %s. JSON data is %s" % ( artist, searching), xbmc.LOGDEBUG)
            log("checkartist is [%s], searchartist is [%s], artist is [%s]" %(checkartist, searchartist, artist), xbmc.LOGDEBUG)
            if (checkartist.replace(' ','+') != searchartist) and (artist !="P!nk"):
                log("Updated artist name (%s) with data from tadb [%s]" % (artist, checkartist), xbmc.LOGDEBUG)
                artist = checkartist
    #            searchartist = checkartist
        try:
            _artist_thumb = searching['artists'][0]['strArtistThumb']
        except:
            log("error getting artist thumb", xbmc.LOGDEBUG)
            _artist_thumb = None
            pass
        try:
            _artist_banner = searching['artists'][0]['strArtistBanner']
        except:
            log("error getting artist banner", xbmc.LOGDEBUG)

            _artist_banner = None
            pass
        log("Artist Banner - %s" % _artist_banner, xbmc.LOGDEBUG)
        log("Artist Thumb - %s" % _artist_thumb, xbmc.LOGDEBUG)
        if (_artist_thumb == "") or (_artist_thumb == "null") or (_artist_thumb == None):
            log("No artist thumb found for %s" % searchartist, xbmc.LOGDEBUG)
            _artist_thumb = None
        if (_artist_banner == "") or (_artist_banner == "null") or (_artist_banner == None):
            log("No artist banner found for %s" % searchartist, xbmc.LOGDEBUG)
            _artist_banner = None
        if searchartist not in dict4:
            dict4[searchartist] = _artist_thumb
        if searchartist not in dict5:
            dict5[searchartist] = _artist_banner
        try:
            chop = searching['artists'][0]['strArtistLogo']
            if (chop == "") or (chop == "null"):
                log("No logo found on tadb", xbmc.LOGDEBUG)
                chop = None
        except:
            log("No logo data found", xbmc.LOGDEBUG)
            chop = None
            pass
        try:
            check_mbid = searching['artists'][0]['strMusicBrainzID']
            if (mbid != check_mbid) and (check_mbid != 'null'):
                mbid = check_mbid
        except:
            log("Unable to check mbid", xbmc.LOGDEBUG)
            pass
        url = chop
        return artist, url, dict4, dict5, mbid

    except Exception as e:
        log("[Parse_Data] error [%s]" %str(e), xbmc.LOGERROR)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)),xbmc.LOGERROR)
#        log(artist, url, searchartist,dict4[searchartist], dict5[searchartist],xbmc.LOGERROR)
        return artist, url, dict4, dict5, mbid

def get_bbc_radio_info(bbc_channel):
#    log("Get BBC Radio Info",xbmc.LOGINFO)
    lastfmurl = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=bbcradio%s" % bbc_channel
    lastfmurl = lastfmurl +"&api_key=%s" % happy_hippo.decode( 'base64' )
    lastfmurl = lastfmurl  + "&format=json&limit=1"
    try:
        _featuredartists = []
        response = load_url(lastfmurl)
        stuff = _json.loads(response)
        if stuff.has_key('message'):
            log("Error getting BBC data from last.fm", xbmc.LOGERROR)
            log("%s" %str(stuff), xbmc.LOGERROR)
            return ''
        track = stuff['recenttracks']['track'][0]['name']
        artist = stuff['recenttracks']['track'][0]['artist']['#text']
        if 'feat. ' in track:           # got at least one featured artist
            _f=track.find('feat.')          # remove the () around featured artist(s)
            _s=track.rfind(')')
            temptrack=track[:_f-2]
            temptrack2=track[_f:_s]
            track = temptrack + " " + temptrack2
            track=track.replace('feat.','~').replace(' & ',' ~ ')
            _featuredartists=track.split('~')
            track=_featuredartists[0].strip()
            del _featuredartists[0]
        artist=artist.replace(', ',' & ')
        for _artists in range(0,len(_featuredartists)):
            artist = artist + " & " + _featuredartists[_artists].strip()
#            log("BBC RADIO INFO - GOT [%s] - [%s]" %(track, artist), xbmc.LOGINFO)
        return track + " - " + artist

    except Exception as e:
        log("[get_bbc_radio_info] error [%s] " %str(e), xbmc.LOGERROR)
        return ''



def slice_string(string1, string2, n):
    if string2 == "" or string2 is None:
        return -1
    start = string1.find(string2)
    while start >= 0 and n > 1:
        start = string1.find(string2, start + len(string2))
        n -= 1
    return start

def set_timer(delay):
    cs = datetime.datetime.now().time().second
    et = cs + delay
    if (et) >= 60:
        et = et - 60
    return et


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
