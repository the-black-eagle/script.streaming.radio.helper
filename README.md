#script.radio.streaming.helper
-----------------------------

Because of the way most ICY radio streams are formatted, kodi doesn't display the artist
and track info in the same way as when it is playing music from a local library.  The artist
and track info are both in the track portion and seperated by ' - '.  This at least has proved
to be the case with all the radio streams I listen to.  Eventually my OCD got in the way and I
had to see if I could do something about it and find a way to make my streaming radio look better.

This script is the result of that.

It runs in the background when kodi is streaming audio, split the track info into 
seperate artist and track details and set some window properties so that skins can present the 
information in the same way as with a track from a local library.

The script also supplies the full path to a logo (if found) as a property.  If there is no logo in
the local music library the script will look in it's own cached logos.  If it still does not find
one it will attempt to download one from fanart.tv and cache it for future re-use.

All window properties are set for the full screen visualisation window (12006).

##Settings
###General Settings

The path to the top level of the users music directory.

Use Fanart - whether or not to look up logos online at fanart.tv

use theaudiodb - whether or not to look up logos at theaudiodb

###Station Names
***

As streaming radio stations don't name their streams exactly the same as the station name
it's possible to set a couple of strings here to change what is displayed in the skin.
eg - set 'replace' to 'planetrock' and 'with' to 'Planet Rock' to pretty format the name.

The actual stream will be something like 'http://some-streaming-radio-server/station-related-name.mp3'
Without setting any replacement strings, the addon will display 'station-related-name'
You can use replace 'station-related-name' with 'Proper Station Name'


Window properties set by the script
---

artiststring - string. Contains name of artist.

trackstring - string. Contains track name.

haslogo - boolean. true if the script found or downloaded a logo, false otherwise.

logopath - fully qualified path to any logo found.

Window properties can be used as follows -

#####To display the artist name as parsed by the script when streaming

```
<control type="label">
    <label>$INFO[Window(12006).Property(artiststring)]</label>
    <scroll>true</scroll>
    <visible>Player.IsInternetStream</visible>
</control>
```

#####Similarly, to display the track name 

```<control type="label">
    <label>$INFO[Window(12006).Property(trackstring)]</label>
    <scroll>true</scroll>
    <scrollout>false</scrollout>
    <visible>Player.IsInternetStream</visible>
</control>
```

#####Displaying a logo

```<control type="image">
    <left>0</left>
    <top>-90</top>
    <width>400</width>
    <height>155</height>
    <texture>$INFO[Window.(12006).Property(logopath)]</texture>
    <fadetime>300</fadetime>
    <aspectratio align="left">keep</aspectratio>
    <animation effect="fade" end="100" condition="true">Conditional</animation>
    <visible>Player.IsInternetStream+StringCompare(Window.(12006).Property(haslogo),Control.GetLabel(9998))</visible>
</control>
```

In the above, label id 9998 is an invisible label with the text set to 'true'


The script is started by adding the following line to MusicVisualisation.xml

######<onload>RunScript(script.radio.streaming.helper)</onload>

This means the script is started when entering the full screen music visualisation window.  It will
continue to run as long as kodi is playing audio however it only sets any window properties or downloads
logos if the audio is an internet stream.  The script exits when kodi stops playing audio.
