from django.contrib import admin

from .models import Source, Song, Playlist, PlaylistSong, Settings

admin.site.register(Source)
admin.site.register(Song)
admin.site.register(Playlist)
admin.site.register(PlaylistSong)
admin.site.register(Settings)
