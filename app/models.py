from django.db import models


class Source(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Song(models.Model):
    filename = models.CharField(max_length=500)
    title = models.CharField(max_length=255, null=True, blank=True)
    artist = models.CharField(max_length=255, null=True, blank=True)
    genre = models.CharField(max_length=255, null=True, blank=True)
    collection = models.CharField(max_length=255, null=True, blank=True)
    source = models.ForeignKey(Source, null=True, blank=True, on_delete=models.SET_NULL, related_name='songs')
    duration = models.CharField(max_length=32, null=True, blank=True)
    bpm = models.IntegerField(null=True, blank=True)
    key = models.CharField(max_length=16, null=True, blank=True)
    time_sig = models.CharField(max_length=16, null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    is_selected = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)
    lyrics_filename = models.CharField(max_length=500, null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    missing = models.BooleanField(default=False)

    def __str__(self):
        return self.title or self.filename


class Playlist(models.Model):
    name = models.CharField(max_length=255, unique=True)
    songs = models.ManyToManyField(Song, through='PlaylistSong', related_name='playlists')

    def __str__(self):
        return self.name


class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = ('playlist', 'song')


class Settings(models.Model):
    """Singleton-Zeile (id immer 1), analog zu settings_model.py."""

    theme = models.CharField(max_length=64, default='bubblegum_pop')
    backend = models.CharField(max_length=16, default='fluidsynth')  # fluidsynth | roland, Engine folgt in Phase 3
    audio_output_device = models.CharField(max_length=255, null=True, blank=True)
    master_volume = models.IntegerField(default=80)
    autoscan_on_start = models.BooleanField(default=False)
    start_fullscreen = models.BooleanField(default=False)
    midi_init_mode = models.CharField(max_length=16, default='gm')
    export_path = models.CharField(max_length=500, null=True, blank=True)  # noch ohne Funktion, siehe export_dialog.py

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
