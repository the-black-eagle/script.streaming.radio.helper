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

import xbmc ,xbmcvfs, xbmcaddon
import xbmcgui
import urllib
import uuid
import sys, traceback
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
logfile = xbmc.translatePath('special://temp/srh.log').decode('utf-8')
was_playing =""
dict1 = {} # Key = artistname+trackname, value = Album name
dict2 = {} # Key = artistname+trackname, value = Album year
dict3 = {} # Key = artistname+trackname, value = date last looked up
dict4 = {} # Key = Artist Name, Value = URL to artist thumb
dict5 = {} # Key = Artist Name, Value = URL to artist banner
dict6 = {} # Key = artist Name, value = MBID
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
replace1 = addon.getSetting('remove1').decode('utf-8')
replace2 = addon.getSetting('remove2').decode('utf-8')
replace3 = addon.getSetting('remove3').decode('utf-8')
firstpass = 0
previous_track = None
WINDOW = xbmcgui.Window(12006)
debugging = addon.getSetting('debug')
if debugging == 'true' :
    debugging = True
else:
    debugging = False

def log(txt, mylevel=xbmc.LOGDEBUG):
    """
    Logs to Kodi's standard logfile
    """
    
    if debugging :
        mylevel=xbmc.LOGNOTICE

    if isinstance(txt, str):
        txt = txt.decode('utf-8')
    message = u'%s : %s' % (addonname, txt)
    xbmc.log(msg=message.encode('utf-8'), level=mylevel)

def load_pickle():
    """
    Loads cache data from file in the addon_data directory of the script
    """

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
        d6={}
        log("created new pickle data for MBID storage")
    pfile.close()
    return d1,d2,d3,d4,d5,d6

def save_pickle(d1,d2,d3,d4,d5,d6):
    """
    Saves local cache data to file in the addon_data directory of the script
    """

    log("Saving data to pickle file")
    pfile = open(logostring + 'data.pickle',"wb")
    pickle.dump(d1,pfile)
    pickle.dump(d2,pfile)
    pickle.dump(d3,pfile)
    pickle.dump(d4,pfile)
    pickle.dump(d5,pfile)
    pickle.dump(d6,pfile)
    pfile.close()

def get_year(artist,track,dict1,dict2,dict3):
    """
    Look in local cache for album and year data corresponding to current track and artist.
    Return the local data if present, unless it is older than 7 days in which case re-lookup online.
    If data not present in cache, lookup online and add to cache
    If all data present in cache, just retur taht and don't lookup anything online.
    """
    if (artist == "") and (track == ""):
        return None,None
    log("Looking up album and year data for artist %s and track %s" %(artist, track), xbmc.LOGDEBUG)
    my_size = len(dict1)
    log("Cache currently holds %d tracks" % my_size, xbmc.LOGDEBUG)
    keydata = artist.replace(" ","").lower() + track.replace(" ","").lower()
    log("keydata is %s" % keydata, xbmc.LOGDEBUG)
    if keydata in dict1:
        log("Track %s in local data cache" % track, xbmc.LOGDEBUG)
        albumname = dict1[keydata]
        log("Album Name is %s" % albumname, xbmc.LOGDEBUG)
        datechecked = dict3[keydata]
        log("Data for track '%s' on album '%s' last checked %s" % (track, albumname, str(datechecked.strftime("%d-%m-%Y"))), xbmc.LOGDEBUG)
        if (datechecked < (todays_date - time_diff)) or (xbmcvfs.exists(logostring + "refreshdata")):
            log( "Data might need refreshing", xbmc.LOGDEBUG)
            if (dict1[keydata] == '') or (dict1[keydata] == None) or (dict1[keydata] == 'None') or (dict1[keydata] == 'null') or (xbmcvfs.exists(logostring + "refreshdata")):
                log("No album data - checking TADB again", xbmc.LOGDEBUG)
                dict1[keydata], dict2[keydata] = tadb_trackdata(artist,track,dict1,dict2,dict3)
                dict3[keydata] = datetime.datetime.combine(datetime.date.today(),datetime.datetime.min.time())
                log("Data refreshed")
            elif (dict2[keydata] == None) or (dict2[keydata] == '0') or (dict2[keydata] == ''):
                log("No year data for album %s - checking TADB again" % dict1[keydata], xbmc.LOGDEBUG)
                dict1[keydata], dict2[keydata] = tadb_trackdata(artist,track,dict1,dict2,dict3)
                dict3[keydata] = datetime.datetime.combine(datetime.date.today(),datetime.datetime.min.time())
                log("Data refreshed", xbmc.LOGDEBUG)
            else:
                log( "All data present - No need to refresh", xbmc.LOGDEBUG)
            return dict1[keydata], dict2[keydata]
        else:
            log( "Using cached data", xbmc.LOGDEBUG )
            return dict1[keydata],dict2[keydata]
    else:
        log("New track - get data for %s : %s" %(artist, track), xbmc.LOGDEBUG)
        dict1[keydata], dict2[keydata] = tadb_trackdata(artist,track,dict1,dict2,dict3)

        dict3[keydata] = datetime.datetime.combine(datetime.date.today(),datetime.datetime.min.time())
        log( "New data has been cached", xbmc.LOGDEBUG)
        return dict1[keydata], dict2[keydata]

def tadb_trackdata(artist,track,dict1,dict2,dict3):
    """
    Searches theaudiodb for an album containing track.  If a album is found, attempts
    to get the year of the album.  Returns album name and year if both are found, just the album name if
    no year is found, or none if nothing is found
    """

    searchartist = artist.replace(" ","+").encode('utf-8')
    searchtrack = track.replace(" ","+").encode('utf-8')
    searchtrack = searchtrack.rstrip("+")
    url = 'http://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
    searchurl = url + '/searchtrack.php?s=' + searchartist + '&t=' + searchtrack
    log("Search artist, track with strings : %s,%s" %(searchartist,searchtrack), xbmc.LOGDEBUG)
    keydata = artist.replace(" ","").lower() + track.replace(" ","").lower()
    try:
        response = urllib.urlopen(searchurl).read().decode('utf-8')
        if "service" in response:                # theaudiodb not available
            log("No response from theaudiodb", xbmc.LOGDEBUG)
            if keydata in dict1:
                log("Using data from cache and not refreshing", xbmc.LOGDEBUG)
                return dict1[keydata], dict2[keydata]    # so return the data we already have
            else:
                return None,None # unless we don't have any
        searching = _json.loads(response)
        log("JSON data = %s" % searching, xbmc.LOGDEBUG)
        try:
            album_title = searching['track'][0]['strAlbum']
        except:
            album_title = None
            pass
        if (album_title == "") or (album_title == "null") or (album_title == None):
            log("No album data found ", xbmc.LOGDEBUG)
            return None, None

        album_title_search = album_title.replace(" ","+").encode('utf-8')
        searchurl = url + '/searchalbum.php?s=' + searchartist + '&a=' + album_title_search
        log("Search artist,album with strings : %s,%s" %(searchartist,album_title_search), xbmc.LOGDEBUG)
        response = urllib.urlopen(searchurl).read()
        searching = _json.loads(response)
        the_year = "null"
        try:
            the_year = searching['album'][0]['intYearReleased']
        except:
            pass
        if (the_year == "") or (the_year == "null"):
            log("No year found for album", xbmc.LOGDEBUG)
            return album_title, None
        log("Got '%s' as the year for '%s'" % ( the_year, album_title), xbmc.LOGDEBUG)
        return album_title, the_year
    except Exception as e:
        log("Error searching theaudiodb for album and year data [ %s ]" % str(e), xbmc.LOGERROR)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)), xbmc.LOGERROR)
        if keydata in dict1:
            return dict1[keydata], dict2[keydata]
        else:
            return None, None

def get_mbid(artist):
    """
    Gets the MBID for a given artist name.
    Note that radio stations often omit 'The' from band names so this may return the wrong MBID

    Returns the Artist MBID or a self generated one if the lookup fails and we haven't cached one previously
    """

    log("Getting mbid for artist %s " % artist, xbmc.LOGDEBUG)
    em_mbid = str(uuid.uuid5(uuid.NAMESPACE_DNS, artist.encode('utf-8')))  # generate an emergency mbid in case lookup fails
    try:
        if '/' in artist:
            artist = artist.replace('/',' ')
        elif artist.lower() == 'acdc':
            artist = "AC DC"
        
        url = 'http://musicbrainz.org/ws/2/artist/?query=artist:%s' % artist
        url = url.encode('utf-8')
        response = urllib.urlopen(url).read()
        if (response == '') or ("MusicBrainz web server" in response):
            log("Unable to contact Musicbrainz to get an MBID", xbmc.LOGDEBUG)
            if artist in dict6:
                log("Using cached MBID")
                return dict6[artist] 
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
            log("Didn't get an MBID for artist : %s", xbmc.LOGDEBUG)
            log("using %s as emergency MBID" % em_mbid)
            return em_mbid
        if artist not in dict6:
            dict6[artist] = mbid
        return mbid
    except Exception as e:
        log ("There was an error getting the Musicbrainz ID [ %s ]" % str(e), xbmc.LOGERROR)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)), xbmc.LOGERROR)
        return em_mbid

def get_hdlogo(mbid, artist):
    """
    Get the first found HD clearlogo from fanart.tv if it exists.

    Args:
         The MBID of the artist and the artist name

    Returns :
        The fully qualified path to an existing logo or newly downloaded logo or
        None if the logo is not found
        """
    try:
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
                xbmcvfs.mkdir(logopath)
                log("Downloading logo from fanart.tv and cacheing in %s" % logopath, xbmc.LOGDEBUG)
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
                log("Logo downloaded previously", xbmc.LOGDEBUG)
                return logopath
            else:
                log("No logo found on fanart.tv", xbmc.LOGDEBUG)
                return None
    except:
        log("Error searching fanart.tv for a logo", xbmc.LOGERROR)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)), xbmc.LOGERROR)
        return None

def search_tadb(mbid, artist, dict4, dict5):
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

    logopath = logostring + mbid + "/logo.png"
    logopath = xbmc.validatePath(logopath)
    if (not xbmcvfs.exists(logopath)) and (WINDOW.getProperty("haslogo") == "false"): # Don't need to look up a logo as we found one in the local directory
        log("Looking up %s on tadb.com" % artist, xbmc.LOGDEBUG)
        searchartist = artist.replace(" ","+")
        log ("[search_tadb] : searchartist = %s" % searchartist)
        url = 'http://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
        searchurl = url + '/search.php?s=' + searchartist.encode('utf-8')
        log("URL for TADB is : %s" % searchurl, xbmc.LOGDEBUG)
        try:
            response = urllib.urlopen(searchurl).read()
            if response == '':
                log("No response from theaudiodb", xbmc.LOGDEBUG)
                return artist, None ,None, None
            log(response)
            if response != '{"artists":null}':
                searching = _json.loads(response)
                artist, url, dict4, dict5, mbid = parse_data(artist, searching, searchartist, dict4, dict5, mbid)
            else:
                searchartist = 'The+' + searchartist
                url = 'http://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )

                searchurl = url + '/search.php?s=' + searchartist
                log("Looking up %s on tadb.com with URL %s" % (searchartist, searchurl), xbmc.LOGDEBUG)
                response = urllib.urlopen(searchurl).read()
                log(response)
                if (response == '') or (response == '{"artists":null}') or ("!DOCTYPE" in response):
                    log("No logo found on tadb", xbmc.LOGDEBUG)
                    # Lookup failed on name - try with MBID
                    log("Looking up with MBID")
                    url = 'http://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
                    searchurl = url + '/artist-mb.php?i=' + mbid
                    log("MBID URL is : %s" % searchurl)
                    response = urllib.urlopen(searchurl).read()
                    log("Response : %s " % str(response))
                    if (response == '{"artists":null}') or (response == '') or ('!DOCTYPE' in response):
                        log("Failed to find any artist info on theaudiodb")
                        return artist, None, None, None
                    else:
                        searching = _json.loads(response)
                        artist, url, dict4, dict5, mbid = parse_data (artist, searching, searchartist, dict4, dict5, mbid)
                else:
                    searching = _json.loads(response)
                    artist, url, dict4, dict5, mbid = parse_data(artist, searching, searchartist, dict4, dict5, mbid)

            logopath = logostring + mbid + '/'
            logopath = xbmc.validatePath(logopath)
            if (not xbmcvfs.exists(logopath)) and (url != None):
                xbmcvfs.mkdir(logopath)
                log("Downloading logo from tadb and cacheing in %s" % logopath, xbmc.LOGDEBUG)
                logopath = logopath + "logo.png"
                imagedata = urllib.urlopen(url).read()
                f = open(logopath,'wb')
                f.write(imagedata)
                f.close()
                return artist, logopath, dict4[searchartist], dict5[searchartist]
            else:
                logopath = logostring + mbid + '/logo.png'
                logopath = xbmc.validatePath(logopath)
                if xbmcvfs.exists(logopath):
                    log("Logo has already been downloaded and is in cache. Path is %s" % logopath, xbmc.LOGDEBUG)
                    return artist, logopath, dict4[searchartist], dict5[searchartist]
                else:
                    return artist, None, dict4[searchartist], dict5[searchartist]

        except Exception as e:
            log("Error searching theaudiodb for a logo : [ %s ]" % str(e), xbmc.LOGERROR)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
            return artist, logopath, dict4[searchartist], dict5[searchartist]

    else:
        #  at this point, we have a logo cached to disk previously so we have already looked up this artist at least once
        #  we need to check if we have thumb or banner data and only look up if not
        
        searchartist = artist.replace(" ","+")
        url = 'http://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
        searchurl = url + '/artist-mb.php?i=' + mbid
        log("MBID lookup to check artist name is correct")
        response = urllib.urlopen(searchurl).read()
        if (response != '{"artists":null}') and (response != '') and ('!DOCTYPE' not in response):
            searching = _json.loads(response)
            artist, url, dict4, dict5, mbid = parse_data (artist, searching, searchartist, dict4, dict5, mbid)
        if searchartist in dict4:   # we have looked up this artist before
            logopath = logostring + mbid + '/logo.png'
            logopath = xbmc.validatePath(logopath)
            if (xbmcvfs.exists(logopath)) and (WINDOW.getProperty("haslogo") == "false"):
                log("Logo has already been downloaded and is in cache. Path is %s" % logopath, xbmc.LOGDEBUG)
                log("Checking thumb and banner data")
                if (dict4[searchartist] != None) and (dict5[searchartist] != None): # have both banner and thumb
                    log("Thumb and banner both cached already ")
                    return artist, logopath, dict4[searchartist], dict5[searchartist]
                else:
                    log("Artist or thumb data missing")
            elif WINDOW.getProperty("haslogo") == "true":
                log("Using logo from local music directory - checking thumb and banner data")
                if (dict4[searchartist] != None) and (dict5[searchartist] != None): # have both
                    log("Thumb and banner both cached already ")
                    return artist, None, dict4[searchartist], dict5[searchartist] # Don't need the path as using local logo already
                else:
                    log("Thumb or banner data missing - TADB will be re-checked")        
        # We haven't got any thumb or banner data before up OR thumb or banner data is missing so look up on tadb
        log("Looking up thumb and banner data for artist %s (logo already obtained)" % artist)
        url = 'http://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
        searchurl = url + '/search.php?s=' + searchartist.encode('utf-8')
        log("URL for TADB is : %s" % searchurl, xbmc.LOGDEBUG)
        try:
            response = urllib.urlopen(searchurl).read()
            if response == '':
                log("No response from theaudiodb", xbmc.LOGDEBUG)
                return artist, None, None, None
            log(response)
            if response != '{"artists":null}':
                searching = _json.loads(response)
                artist, url, dict4, dict5, mbid = parse_data(artist, searching, searchartist, dict4, dict5, mbid, False)

            else:
                searchartist = 'The+' + searchartist
                url = 'http://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )

                searchurl = url + '/search.php?s=' + searchartist
                log("Looking up %s on tadb.com with URL %s" % (searchartist, searchurl), xbmc.LOGDEBUG)
                response = urllib.urlopen(searchurl).read()
                log(response)
                if (response == '') or (response == '{"artists":null}') or ("!DOCTYPE" in response):
                    log("No info returned from tadb", xbmc.LOGDEBUG)
                    log("Looking up with MBID")
                    url = 'http://www.theaudiodb.com/api/v1/json/%s' % rusty_gate.decode( 'base64' )
                    searchurl = url + '/artist-mb.php?i=' + mbid
                    log("MBID URL is : %s" % searchurl)
                    response = urllib.urlopen(searchurl).read()
                    log("Response was %s" %str(response))
                    if (response != '{"artists":null}') and (response != '') and ('!DOCTYPE' not in response):
                        searching = _json.loads(response)
                        artist, url, dict4, dict5, mbid = parse_data (artist, searching, searchartist, dict4, dict5, mbid)
                    else:
                        log("Failed to find any artist info on theaudiodb")
                        return artist, None, None, None
                    
                else:
                    searching = _json.loads(response)
                    artist, url, dict4, dict5, mbid = parse_data(artist, searching, searchartist, dict4, dict5, mbid, False)

            logopath = logostring + mbid + '/logo.png'
            logopath = xbmc.validatePath(logopath)
            if xbmcvfs.exists(logopath):
                log("Logo has already been downloaded and is in cache. Path is %s" % logopath, xbmc.LOGDEBUG)
                return artist, logopath, dict4[searchartist], dict5[searchartist]
            else:
                return artist, None, dict4[searchartist], dict5[searchartist]
        except Exception as e:
            log("Error searching theaudiodb [ %s ]" % str(e), xbmc.LOGERROR)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
            log(artist, logopath, searchartist)
            return artist, None, None, None

def parse_data(artist, searching, searchartist, dict4, dict5, mbid, logoflag="true"):
    """
       Parse the JSON data for the values we want
       Also checks the artist name is correct if the first two lookups on TADB failed
       and corrects it if possible
    """
    try:
        checkartist = searching['artists'][0]['strArtist']
        if (checkartist.replace(' ','+') != searchartist):
            artist = checkartist
            log("Updated artist name (%s) with data from tadb [%s]" % (searchartist.replace('+',' '), artist))
        _artist_thumb = searching['artists'][0]['strArtistThumb']
        _artist_banner = searching['artists'][0]['strArtistBanner']
        log("Artist Banner - %s" % _artist_banner)
        log("Artist Thumb - %s" % _artist_thumb)
        if (_artist_thumb == "") or (_artist_thumb == "null") or (_artist_thumb == None):
            log("No artist thumb found for %s" % searchartist)
            _artist_thumb = None
        if (_artist_banner == "") or (_artist_banner == "null") or (_artist_banner == None):
            log("No artist banner found for %s" % searchartist)
            _artist_banner = None
        if searchartist not in dict4:
            dict4[searchartist] = _artist_thumb
        if searchartist not in dict5:
            dict5[searchartist] = _artist_banner
        chop = searching['artists'][0]['strArtistLogo']
        if (chop == "") or (chop == "null"):
            log("No logo found on tadb", xbmc.LOGDEBUG)
            chop = None
        check_mbid = searching['artists'][0]['strMusicBrainzID']
        if (mbid != check_mbid) and (check_mbid != 'null'):
            mbid = check_mbid
        url = chop
        if logoflag:
            return artist, url, dict4, dict5, mbid
        else:
            return artist, None, dict4, dict5, mbid
    except Exception as e:
        log("[Parse_Data] error [%s]" %str(e))
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(repr(traceback.format_exception(exc_type, exc_value,exc_traceback)))
        log(artist, url, searchartist,dict4[searchartist], dict5[searchartist])
        return artist, url, dict4, dict5, mbid

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
