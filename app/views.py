import logging
from pathlib import Path

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .models import Song, Playlist, PlaylistSong, Source, Settings
from .themes import resolve_theme, list_themes, resolve_all_themes
from .status_messages import log_status, log_status_text
from . import status_messages
from .version import APP_VERSION
from .session_log import SessionLog
from . import log_viewer

logger = logging.getLogger('midiranger')

CHANGELOG_PATH = django_settings.BASE_DIR / 'CHANGELOG.txt'


def _load_changelog() -> str:
    if not CHANGELOG_PATH.exists():
        logger.error('❌ CHANGELOG.txt nicht gefunden.')
        return 'Keine Changelog-Daten gefunden.'
    try:
        return CHANGELOG_PATH.read_text(encoding='utf-8')
    except OSError as e:
        logger.error(f'❌ Fehler beim Lesen der CHANGELOG.txt: {e}')
        return 'Fehler beim Laden des Changelogs.'


def _format_recent_line(entry) -> str:
    """Port von home_view.py's _format_line_compact/_format_ts_ddmmyy:
    "YYYY-MM-DD HH:MM:SS" -> "DD/MM/YY – Titel"."""
    title = entry.get('title') or '(ohne Titel)'
    date_part = (entry.get('ts') or '').split(' ')[0]
    parts = date_part.split('-')
    short = f"{parts[2]}/{parts[1]}/{parts[0][2:]}" if len(parts) == 3 else entry.get('ts', '')
    return f"{short} – {title}"


TONARTEN = [
    "", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
    "Cm", "C#m", "Dm", "D#m", "Em", "Fm", "F#m", "Gm", "G#m", "Am", "A#m", "Bm",
]


def _theme_context(request):
    import json as json_module
    import re

    settings = Settings.load()

    # Entspricht set_playlist_actions_enabled(): "Aus Playlist entfernen"/
    # "Playlist leeren" sind nur aktiv, wenn die aktuelle Seite eine
    # Playlist-Detailansicht ist.
    playlist_match = re.match(r'^/playlists/(\d+)$', request.path)
    playlist_context_id = int(playlist_match.group(1)) if playlist_match else None

    # django.contrib.messages: der Storage gilt als "gelesen", sobald man
    # einmal über get_messages() iteriert - deshalb hier in EINEM Durchlauf
    # alle tag-spezifischen Meldungen rausziehen, statt mehrfach zu iterieren
    # (sonst gehen z.B. 'songs'-Meldungen verloren, wenn nur nach 'import'
    # gefiltert wird).
    import_error = None
    songs_message = None
    for m in messages.get_messages(request):
        if 'import' in m.tags and import_error is None:
            import_error = m.message
        elif 'songs' in m.tags and songs_message is None:
            songs_message = m.message

    from .player import get_player
    player = get_player()

    return {
        'settings': settings,
        'theme': resolve_theme(settings.theme),
        'all_themes': list_themes(),
        'themes_json': json_module.dumps(resolve_all_themes()),
        'app_version': APP_VERSION,
        'changelog_content': _load_changelog(),
        'sources': Source.objects.all(),
        'playlists_all': Playlist.objects.all().order_by('name'),
        'tonarten': TONARTEN,
        'import_error': import_error,
        'songs_message': songs_message,
        'playlist_context_id': playlist_context_id,
        'now_playing': player.state.current_song if player.state.is_playing else None,
        'midi_output_name': settings.backend,
        'status_message': status_messages.get_current_status_message(),
    }


def _run_autoscan_if_enabled():
    """Entspricht dem AUTOSCAN BEIM START-Block in app_controller.py: läuft
    komplett still im Hintergrund (kein Dialog, keine Rückfrage, keine
    Löschoption) und markiert fehlende Dateien nur mit missing=1. Bei uns
    ist der Login der nächstliegende Ersatz für den Programmstart."""
    settings = Settings.load()
    if not settings.autoscan_on_start:
        return

    try:
        from . import missing_files

        logger.info('🔎 Autoscan aktiviert – prüfe auf fehlende Dateien …')
        missing = missing_files.list_missing_songs()
        for song in missing:
            song.missing = True
            song.save(update_fields=['missing'])
        logger.info(f'📌 Autoscan abgeschlossen – fehlende Dateien: {len(missing)}')
    except Exception:
        logger.warning('⚠️ Autoscan fehlgeschlagen', exc_info=True)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            logger.info(f"🔓 Angemeldet: {user.username}")
            _run_autoscan_if_enabled()
            return redirect('/')
        logger.warning(f"⚠️ Fehlgeschlagener Login-Versuch: {request.POST.get('username')}")
        error = 'Benutzername oder Passwort falsch.'

    return render(request, 'login.html', {**_theme_context(request), 'title': 'Anmelden', 'error': error})


def logout_view(request):
    if request.user.is_authenticated:
        logger.info(f"🔒 Abgemeldet: {request.user.username}")
    logout(request)
    return redirect('/login')


@login_required
def dashboard(request):
    top_artists = (
        Song.objects.exclude(artist__isnull=True).exclude(artist__exact='')
        .values('artist').annotate(cnt=Count('id')).order_by('-cnt')[:10]
    )

    stats = {
        'songs_total': Song.objects.count(),
        'playlists_total': Playlist.objects.count(),
        'sources_total': Source.objects.count(),
        'backend_label': None,  # kommt in Phase 3 (Engine-Port) aus midi_engine
        'missing_files_count': Song.objects.filter(missing=True).count(),
        'missing_meta_count': Song.objects.filter(
            Q(bpm__isnull=True) | Q(key__isnull=True) | Q(time_sig__isnull=True) | Q(duration__isnull=True)
        ).count(),
        'recent_play': [_format_recent_line(e) for e in SessionLog().get_recent('recent_play', 10)],
        'recent_import': [_format_recent_line(e) for e in SessionLog().get_recent('recent_import', 10)],
        'top_artists': [f"{row['artist']}  ({row['cnt']})" for row in top_artists],
    }

    return render(request, 'index.html', {
        **_theme_context(request),
        'title': 'Dashboard',
        'stats': stats,
    })


@login_required
def settings_save(request):
    back_to = request.META.get('HTTP_REFERER', '/')
    settings = Settings.load()

    old_backend = settings.backend

    new_theme = request.POST.get('theme') or settings.theme
    if new_theme != settings.theme:
        logger.info(f'🎨 Theme geladen: {new_theme}')

    settings.theme = new_theme
    settings.backend = request.POST.get('backend') or settings.backend
    settings.master_volume = max(0, min(100, int(request.POST.get('master_volume', 80))))
    settings.autoscan_on_start = request.POST.get('autoscan_on_start') == 'on'
    settings.start_fullscreen = request.POST.get('start_fullscreen') == 'on'
    settings.save()

    from .player import get_player
    player = get_player()

    if settings.backend != old_backend:
        logger.info(f'🔄 Audio-Backend wechseln: {old_backend} → {settings.backend}')
        try:
            player.engine.switch_backend(
                settings.backend,
                roland_device_name=settings.audio_output_device,
                roland_init_mode=settings.midi_init_mode,
            )
        except Exception as e:
            logger.error(f'💥 Backend-Wechsel fehlgeschlagen: {e}')

    try:
        player.engine.set_volume(settings.master_volume / 100)
    except Exception as e:
        logger.error(f'💥 Volume setzen fehlgeschlagen: {e}')

    logger.info('💾 Settings gespeichert.')
    log_status(logger, 720)

    return redirect(back_to)


@login_required
def settings_reset_defaults(request):
    back_to = request.META.get('HTTP_REFERER', '/')

    logger.info('🧯 Werkseinstellungen wiederherstellen …')
    Settings.objects.filter(pk=1).delete()
    Settings.load()

    return redirect(back_to)


@login_required
def placeholder_view(request):
    feature = request.GET.get('feature', 'Demnächst verfügbar')
    return render(request, 'placeholder.html', {
        **_theme_context(request),
        'title': feature,
    })


@login_required
def log_content(request):
    from django.utils.html import escape

    filter_name = request.GET.get('filter', 'NORMAL')
    lines = log_viewer.filter_lines(log_viewer.read_lines(), filter_name)

    html = '<div class="log-line log-header">────── Start der aktuellen Session ──────</div><br>'
    if not lines:
        html += '<p class="mr-list-empty">Noch keine Einträge in dieser Ansicht.</p>'
    else:
        html += ''.join(
            f'<div class="log-line log-{log_viewer.line_level(line)}">{escape(line.rstrip())}</div>'
            for line in lines
        )
    return HttpResponse(html)


@login_required
def log_client_event(request):
    """Loggt Menü-Aktionen, deren "geöffnet"-Status im Original an den
    tatsächlichen Menü-Klick gebunden ist (Modal ODER echte Navigation wie
    Alle Songs/Favoriten/Dashboard/Playlist) - nicht an jedes Server-Rendern
    der Zielseite. Sonst würde z.B. ein Redirect zurück zu "Alle Songs" nach
    dem Speichern der Einstellungen dessen "Einstellungen übernommen"-Status
    sofort wieder mit "Alle Songs geöffnet" überschreiben."""
    event = request.POST.get('event')

    if event == 'documentation':
        logger.info('📖 Dokumentation geöffnet')
        log_status(logger, 850)
        doc_path = django_settings.BASE_DIR / 'static' / 'docs' / 'documentation.html'
        if doc_path.exists():
            logger.info(f'📖 Dokumentation geladen: {doc_path}')
        else:
            logger.warning('⚠️ Dokumentation nicht gefunden – Fallback angezeigt.')
        logger.info('📘 Hilfe-Dialog geöffnet.')
    elif event == 'shortcuts':
        logger.info('⌨️ Tastenkürzel geöffnet')
        log_status(logger, 851)
    elif event == 'logviewer':
        logger.info('📜 Log Viewer geöffnet')
        log_status(logger, 852)
    elif event == 'about':
        logger.info('ℹ️ About-Fenster geöffnet')
        log_status(logger, 853)
        logger.info('ℹ️ About-Dialog geöffnet.')
    elif event == 'changelog':
        log_status(logger, 854)
    elif event == 'export':
        logger.info('📤 Export-Dialog geöffnet')
        log_status(logger, 701)
    elif event == 'backup':
        logger.info('💾 Backup-Dialog geöffnet.')
        log_status(logger, 710)
    elif event == 'metadata':
        logger.info('🎵 Öffne Metadaten-Analyse...')
        log_status(logger, 704)
    elif event == 'dbcheck':
        logger.info('💾 Starte DB-Integritätsprüfung ...')
        log_status(logger, 930)
    elif event == 'scan':
        logger.info('🔄 MIDI-Scan wird gestartet...')
        log_status(logger, 903)
    elif event == 'dashboard':
        log_status(logger, 800)
    elif event == 'all_songs':
        logger.info('📄 Ansicht: Alle Songs')
        log_status(logger, 801)
    elif event == 'favorites':
        logger.info('⭐ Ansicht: Favoriten')
        log_status(logger, 802)
    elif event == 'playlist':
        pid = request.POST.get('id')
        logger.info(f'📂 Öffne Playlist ID={pid}')
        log_status(logger, 511)

    return HttpResponse('ok')


@login_required
def song_import_analyze(request):
    import uuid
    from django.http import JsonResponse
    from . import metadata_extractor, paths

    midi_file = request.FILES.get('midi_file')
    if not midi_file:
        return JsonResponse({'error': 'Keine Datei erhalten.'}, status=400)

    paths.ensure(paths.TMP_DIR)
    temp_name = f"{uuid.uuid4().hex}_{midi_file.name}"
    temp_path = paths.TMP_DIR / temp_name

    with open(temp_path, 'wb') as f:
        for chunk in midi_file.chunks():
            f.write(chunk)

    logger.info(f'📂 MIDI gewählt: {midi_file.name}')

    try:
        meta = metadata_extractor.analyze_midi(str(temp_path))
        logger.debug(f'🎵 Analyse erfolgreich: {meta}')
    except Exception as e:
        logger.exception(e)
        meta = {}

    stem = Path(midi_file.name).stem.replace('_', ' ').replace('-', ' ').strip()

    return JsonResponse({
        'temp_id': temp_name,
        'original_filename': midi_file.name,
        'title': meta.get('title') or stem,
        'bpm': meta.get('bpm') or '',
        'key': meta.get('key') or '',
        'duration_formatted': meta.get('duration_formatted') or '',
    })


@login_required
def song_import_submit(request):
    from . import paths

    temp_id = request.POST.get('temp_id')
    original_filename = request.POST.get('original_filename')

    back_to = request.META.get('HTTP_REFERER', '/')

    if not temp_id or not original_filename:
        messages.error(request, 'Bitte zuerst eine MIDI-Datei auswählen.', extra_tags='import')
        return redirect(back_to)

    temp_path = paths.TMP_DIR / temp_id
    if not temp_path.exists():
        messages.error(request, 'Die Datei existiert nicht mehr, bitte erneut auswählen.', extra_tags='import')
        return redirect(back_to)

    paths.ensure(paths.UPLOADS_DIR)
    dest_midi = paths.UPLOADS_DIR / original_filename

    if dest_midi.exists():
        messages.error(request, f'Die Datei "{original_filename}" existiert im Upload-Ordner bereits.', extra_tags='import')
        return redirect(back_to)

    temp_path.replace(dest_midi)
    logger.info(f'📥 MIDI kopiert → {dest_midi}')

    lyrics_rel_path = ''
    lyrics_file = request.FILES.get('lyrics_file')
    if lyrics_file:
        paths.ensure(paths.LYRICS_DIR)
        dest_lyrics = paths.LYRICS_DIR / lyrics_file.name
        if dest_lyrics.exists():
            logger.warning(f'⚠ Lyrics existieren bereits, werden überschrieben: {dest_lyrics}')
        with open(dest_lyrics, 'wb') as f:
            for chunk in lyrics_file.chunks():
                f.write(chunk)
        lyrics_rel_path = f'lyrics/{lyrics_file.name}'
        logger.info(f'📝 Lyrics kopiert → {dest_lyrics}')

    source_id = request.POST.get('source_id') or None
    bpm = request.POST.get('bpm') or None

    song = Song.objects.create(
        filename=f'uploads/{original_filename}',
        title=request.POST.get('title', '').strip(),
        artist=request.POST.get('artist', '').strip(),
        genre=request.POST.get('genre', '').strip(),
        source_id=source_id,
        collection=request.POST.get('collection', '').strip(),
        bpm=int(bpm) if bpm and bpm.isdigit() else None,
        key=request.POST.get('key', ''),
        time_sig=request.POST.get('time_sig', '').strip(),
        is_edited=request.POST.get('is_edited') == 'on',
        comment=request.POST.get('comment', '').strip(),
        lyrics_filename=lyrics_rel_path,
        duration=request.POST.get('duration_formatted', ''),
    )

    SessionLog().add_recent_import(title=song.title or '(ohne Titel)')
    log_status(logger, 700)
    logger.info('🎵 Song erfolgreich importiert.')

    return redirect('/')


@login_required
def log_raw(request):
    if not log_viewer.LOG_PATH.exists():
        content = 'Noch keine Logdatei vorhanden.'
    else:
        content = log_viewer.LOG_PATH.read_text(encoding='utf-8', errors='ignore')
    return HttpResponse(content, content_type='text/plain; charset=utf-8')


@login_required
def backup_create(request):
    from django.http import JsonResponse
    from . import backup

    try:
        zip_path = backup.create_backup()
    except Exception as e:
        logger.exception('💥 Fehler beim Backup')
        return JsonResponse({'error': str(e)}, status=500)

    logger.info(f'💾 Backup abgeschlossen → {zip_path}')

    return JsonResponse({'filename': Path(zip_path).name})


@login_required
def backup_download(request, filename):
    from django.http import FileResponse, Http404
    from . import backup

    zip_path = backup.BACKUPS_DIR / filename
    if '/' in filename or '\\' in filename or not zip_path.exists():
        raise Http404
    return FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=filename)


@login_required
def export_create(request):
    from django.http import JsonResponse
    from . import export as export_module

    songs = Song.objects.filter(is_selected=True)

    try:
        zip_path, count = export_module.create_export(songs)
    except export_module.ExportError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.exception('💥 Fehler beim Export')
        return JsonResponse({'error': str(e)}, status=500)

    Song.objects.filter(is_selected=True).update(is_selected=False)
    logger.info(f'📤 Export abgeschlossen → {zip_path}')

    return JsonResponse({'filename': Path(zip_path).name, 'count': count})


@login_required
def export_download(request, filename):
    from django.http import FileResponse, Http404
    from . import export as export_module

    zip_path = export_module.EXPORTS_DIR / filename
    if '/' in filename or '\\' in filename or not zip_path.exists():
        raise Http404
    return FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=filename)


@login_required
def source_add(request):
    back_to = request.META.get('HTTP_REFERER', '/') + '#sourcesModal'
    name = (request.POST.get('name') or '').strip()
    if not name:
        log_status(logger, 9002)
        return redirect(back_to)

    Source.objects.get_or_create(name=name)
    logger.info(f'📁 Quelle hinzugefügt: {name}')
    log_status(logger, 400)
    return redirect(back_to)


@login_required
def source_rename(request):
    back_to = request.META.get('HTTP_REFERER', '/') + '#sourcesModal'
    source_id = request.POST.get('source_id')
    new_name = (request.POST.get('new_name') or '').strip()

    if not source_id:
        log_status(logger, 9001)
        return redirect(back_to)
    if not new_name:
        log_status(logger, 9002)
        return redirect(back_to)

    Source.objects.filter(pk=source_id).update(name=new_name)
    logger.info(f'✏️ Quelle umbenannt: id={source_id} → \'{new_name}\'')
    log_status(logger, 402)
    return redirect(back_to)


@login_required
def source_delete(request):
    back_to = request.META.get('HTTP_REFERER', '/') + '#sourcesModal'
    source_id = request.POST.get('source_id')
    reassign_to = request.POST.get('reassign_to') or None

    if not source_id:
        log_status(logger, 9001)
        return redirect(back_to)

    try:
        source = Source.objects.get(pk=source_id)
    except Source.DoesNotExist:
        log_status(logger, 9001)
        return redirect(back_to)

    if source.name.lower() == 'unbekannt':
        messages.info(request, 'Die Quelle „Unbekannt“ kann nicht gelöscht werden.', extra_tags='sources')
        return redirect(back_to)

    Song.objects.filter(source=source).update(source_id=reassign_to)
    source.delete()

    logger.info(f'🗑️ Quelle gelöscht: ID={source_id} → Songs auf ID={reassign_to} umgebucht.')
    log_status(logger, 401)
    return redirect(back_to)


@login_required
def playlist_add(request):
    back_to = request.META.get('HTTP_REFERER', '/') + '#playlistsModal'
    name = (request.POST.get('name') or '').strip()
    if not name:
        log_status(logger, 9002)
        return redirect(back_to)

    Playlist.objects.get_or_create(name=name)
    logger.info(f"🎧 Playlist angelegt: '{name}'")
    logger.info(f"🎧 Playlist hinzugefügt: '{name}'")
    return redirect(back_to)


@login_required
def playlist_rename(request):
    back_to = request.META.get('HTTP_REFERER', '/') + '#playlistsModal'
    playlist_id = request.POST.get('playlist_id')
    new_name = (request.POST.get('new_name') or '').strip()

    if not playlist_id:
        log_status(logger, 9001)
        return redirect(back_to)
    if not new_name:
        log_status(logger, 9002)
        return redirect(back_to)

    Playlist.objects.filter(pk=playlist_id).update(name=new_name)
    logger.info(f"✏️ Playlist umbenannt (ID={playlist_id}) → '{new_name}'")
    return redirect(back_to)


@login_required
def playlist_delete(request):
    back_to = request.META.get('HTTP_REFERER', '/') + '#playlistsModal'
    playlist_id = request.POST.get('playlist_id')
    reassign_to = request.POST.get('reassign_to') or None

    if not playlist_id:
        log_status(logger, 9001)
        return redirect(back_to)

    try:
        playlist = Playlist.objects.get(pk=playlist_id)
    except Playlist.DoesNotExist:
        log_status(logger, 9001)
        return redirect(back_to)

    if reassign_to:
        target = Playlist.objects.filter(pk=reassign_to).first()
        if target:
            for song in playlist.songs.all():
                PlaylistSong.objects.get_or_create(playlist=target, song=song)
        logger.info(f'🗑️ Playlist gelöscht (ID={playlist_id}) → Songs auf Playlist {reassign_to} umgebucht.')
    else:
        logger.info(f'🗑️ Playlist gelöscht (ID={playlist_id})')

    playlist.delete()
    return redirect(back_to)


def _render_song_table(request, header_title, songs, page_title, favorites_view=False, hide_source=False):
    return render(request, 'songs.html', {
        **_theme_context(request),
        'title': page_title,
        'header_title': header_title,
        'songs': songs,
        'songs_count': songs.count(),
        'favorites_view': favorites_view,
        'hide_source': hide_source,
    })


@login_required
def songs_all(request):
    from django.db.models.functions import Lower

    songs = Song.objects.select_related('source').order_by(Lower('title'))

    return _render_song_table(request, '🎵 Alle Songs', songs, 'Alle Songs')


@login_required
def songs_favorites(request):
    from django.db.models.functions import Lower

    songs = Song.objects.select_related('source').filter(is_favorite=True).order_by(Lower('title'))

    return _render_song_table(request, '⭐ Favoriten', songs, 'Favoriten', favorites_view=True)


@login_required
def playlist_detail(request, playlist_id):
    from django.db.models.functions import Lower

    playlist = get_object_or_404(Playlist, pk=playlist_id)
    songs = playlist.songs.order_by(Lower('title'))

    # Original (PlaylistsModel.get_songs) joint hier NICHT gegen sources,
    # anders als get_all()/get_favorites() - die Quelle bleibt in dieser
    # Ansicht deshalb leer statt "Unbekannt"/dem echten Namen.
    return _render_song_table(
        request,
        f'🎧 Playlist: {playlist.name}',
        songs,
        f'Playlist: {playlist.name}',
        hide_source=True,
    )


@login_required
def search_view(request):
    from django.db.models.functions import Lower

    query = (request.GET.get('q') or '').strip()

    if not query:
        logger.info('🔍 Ansicht: Suche')
        log_status(logger, 803)
        return render(request, 'search.html', {
            **_theme_context(request),
            'title': 'Suche',
        })

    songs = Song.objects.select_related('source').filter(
        Q(title__icontains=query) | Q(artist__icontains=query) | Q(genre__icontains=query) |
        Q(source__name__icontains=query) | Q(collection__icontains=query)
    ).order_by(Lower('title'))

    logger.info(f'🔍 Suche ausgeführt: "{query}"')
    log_status(logger, 804)

    return _render_song_table(request, '🔍 Suchergebnisse', songs, 'Suchergebnisse')


@login_required
def song_toggle_selected(request, song_id):
    from django.http import JsonResponse

    song = get_object_or_404(Song, pk=song_id)
    song.is_selected = not song.is_selected
    song.save(update_fields=['is_selected'])
    return JsonResponse({'is_selected': song.is_selected})


@login_required
def song_toggle_favorite(request, song_id):
    from django.http import JsonResponse

    song = get_object_or_404(Song, pk=song_id)
    song.is_favorite = not song.is_favorite
    song.save(update_fields=['is_favorite'])
    return JsonResponse({'is_favorite': song.is_favorite})


@login_required
def song_data(request, song_id):
    from django.http import JsonResponse

    song = get_object_or_404(Song, pk=song_id)
    return JsonResponse({
        'id': song.id,
        'title': song.title or '',
        'artist': song.artist or '',
        'genre': song.genre or '',
        'source_id': song.source_id,
        'collection': song.collection or '',
        'bpm': song.bpm or '',
        'key': song.key or '',
        'time_sig': song.time_sig or '',
        'is_edited': song.is_edited,
        'comment': song.comment or '',
        'lyrics_filename': song.lyrics_filename or '',
    })


@login_required
def song_edit(request, song_id):
    from . import paths

    back_to = request.META.get('HTTP_REFERER', '/')
    song = get_object_or_404(Song, pk=song_id)

    title = (request.POST.get('title') or '').strip()
    if not title:
        messages.error(request, 'Titel darf nicht leer sein.', extra_tags='songs')
        return redirect(back_to)

    song.title = title
    song.artist = (request.POST.get('artist') or '').strip()
    song.genre = (request.POST.get('genre') or '').strip()
    song.source_id = request.POST.get('source_id') or None
    song.collection = (request.POST.get('collection') or '').strip()
    bpm = (request.POST.get('bpm') or '').strip()
    song.bpm = int(bpm) if bpm.isdigit() else None
    song.key = request.POST.get('key') or ''
    # Takt (time_sig) wird hier bewusst NICHT übernommen - im Original
    # (SongsModel.update_song) fehlt es ebenfalls im UPDATE-Statement,
    # obwohl das Formularfeld existiert.
    song.is_edited = request.POST.get('is_edited') == 'on'
    song.comment = (request.POST.get('comment') or '').strip()

    lyrics_file = request.FILES.get('lyrics_file')
    if lyrics_file:
        paths.ensure(paths.LYRICS_DIR)
        old_lyrics = song.lyrics_filename
        dest_lyrics = paths.LYRICS_DIR / lyrics_file.name
        with open(dest_lyrics, 'wb') as f:
            for chunk in lyrics_file.chunks():
                f.write(chunk)
        song.lyrics_filename = f'lyrics/{lyrics_file.name}'
        logger.info(f'📝 Neue Lyrics kopiert → {dest_lyrics}')

        if old_lyrics:
            old_path = paths.MIDI_DIR / old_lyrics
            if old_path.exists():
                try:
                    old_path.unlink()
                    logger.info(f'🗑 Alte Lyrics gelöscht: {old_path}')
                except OSError:
                    logger.warning(f'⚠ Alte Lyrics konnten nicht gelöscht werden: {old_path}')

    song.save()
    logger.info(f'💾 Song-ID {song.id} erfolgreich gespeichert.')
    log_status(logger, 600)
    return redirect(back_to)


@login_required
def song_lyrics(request, song_id):
    from django.http import JsonResponse
    from . import paths

    song = get_object_or_404(Song, pk=song_id)
    if not song.lyrics_filename:
        content = 'Keine Lyrics verfügbar.'
    else:
        full_path = paths.MIDI_DIR / song.lyrics_filename
        if not full_path.exists():
            content = 'Lyrics-Datei wurde nicht gefunden.'
        else:
            try:
                content = full_path.read_text(encoding='utf-8')
            except OSError:
                content = 'Fehler beim Laden der Lyrics.'

    return JsonResponse({'title': song.title or '', 'content': content})


@login_required
def song_lyrics_file(request, song_id):
    from django.http import Http404, FileResponse
    from . import paths

    song = get_object_or_404(Song, pk=song_id)
    if not song.lyrics_filename:
        raise Http404
    full_path = paths.MIDI_DIR / song.lyrics_filename
    if not full_path.exists():
        raise Http404
    return FileResponse(open(full_path, 'rb'), content_type='text/plain; charset=utf-8')


@login_required
def song_download(request, song_id):
    from django.http import FileResponse, Http404
    from . import paths

    song = get_object_or_404(Song, pk=song_id)
    full_path = paths.MIDI_DIR / song.filename
    if not full_path.exists():
        raise Http404
    return FileResponse(open(full_path, 'rb'), as_attachment=True, filename=Path(song.filename).name)


@login_required
def song_delete(request, song_id):
    from . import paths

    back_to = request.META.get('HTTP_REFERER', '/')
    song = get_object_or_404(Song, pk=song_id)

    full_path = (paths.MIDI_DIR / song.filename).resolve()
    originals_dir = paths.ORIGINALS_DIR.resolve()

    if originals_dir in full_path.parents:
        messages.warning(request, 'Original-MIDI-Dateien können nicht gelöscht werden.', extra_tags='songs')
        log_status(logger, 651)
        logger.warning(f'🚫 Löschen verweigert (Original): {full_path}')
        return redirect(back_to)

    try:
        if full_path.exists():
            full_path.unlink()
            logger.info(f'🗑 MIDI gelöscht: {full_path}')
    except OSError:
        logger.exception('Fehler beim Löschen der Datei')
        log_status(logger, 652)
        messages.error(request, 'Die Datei konnte nicht gelöscht werden.', extra_tags='songs')
        return redirect(back_to)

    if song.lyrics_filename:
        lyrics_path = paths.MIDI_DIR / song.lyrics_filename
        if lyrics_path.exists():
            try:
                lyrics_path.unlink()
                logger.info(f'🗑 Lyrics gelöscht: {lyrics_path}')
            except OSError:
                logger.warning(f'⚠ Konnte Lyrics nicht löschen: {lyrics_path}')

    song_id_val = song.id
    song.delete()
    logger.info(f'🗑 DB-Eintrag gelöscht: Song-ID {song_id_val}')
    log_status(logger, 650)
    return redirect(back_to)


def _playlist_id_from_referer(request):
    import re

    referer = request.META.get('HTTP_REFERER', '')
    match = re.search(r'/playlists/(\d+)', referer)
    return int(match.group(1)) if match else None


@login_required
def bearbeiten_reset_selection(request):
    back_to = request.META.get('HTTP_REFERER', '/')

    Song.objects.filter(is_selected=True).update(is_selected=False)
    logger.info('🔄 Auswahl zurücksetzen…')
    log_status(logger, 620)
    return redirect(back_to)


@login_required
def bearbeiten_add_to_playlist(request, playlist_id):
    back_to = request.META.get('HTTP_REFERER', '/')
    playlist = get_object_or_404(Playlist, pk=playlist_id)

    ids = list(Song.objects.filter(is_selected=True).values_list('id', flat=True))
    if not ids:
        logger.info('ℹ️ Kein Song ausgewählt.')
        log_status(logger, 520)
        return redirect(back_to)

    for sid in ids:
        PlaylistSong.objects.get_or_create(playlist=playlist, song_id=sid)

    Song.objects.filter(is_selected=True).update(is_selected=False)
    logger.info(f'🎵 {len(ids)} Song(s) zur Playlist hinzugefügt (Playlist-ID {playlist_id}).')
    log_status_text(logger, f'🎵 {len(ids)} Song(s) zur Playlist hinzugefügt', 'success')
    return redirect(back_to)


@login_required
def bearbeiten_remove_from_playlist(request):
    back_to = request.META.get('HTTP_REFERER', '/')
    playlist_id = _playlist_id_from_referer(request)

    if not playlist_id:
        logger.warning('⚠️ remove_selected_from_playlist() außerhalb einer Playlist aufgerufen.')
        log_status(logger, 521)
        return redirect(back_to)

    ids = list(Song.objects.filter(is_selected=True).values_list('id', flat=True))
    if not ids:
        logger.info('ℹ️ Kein Song zum Entfernen ausgewählt.')
        log_status(logger, 520)
        return redirect(back_to)

    PlaylistSong.objects.filter(playlist_id=playlist_id, song_id__in=ids).delete()
    Song.objects.filter(is_selected=True).update(is_selected=False)
    logger.info(f'➖ {len(ids)} Songs aus Playlist-ID {playlist_id} entfernt.')
    log_status_text(logger, f'➖ {len(ids)} Song(s) aus Playlist entfernt', 'info')
    return redirect(back_to)


@login_required
def bearbeiten_clear_playlist(request):
    back_to = request.META.get('HTTP_REFERER', '/')
    playlist_id = _playlist_id_from_referer(request)

    if not playlist_id:
        logger.warning('⚠️ clear_playlist() außerhalb einer Playlist aufgerufen.')
        log_status(logger, 521)
        return redirect(back_to)

    PlaylistSong.objects.filter(playlist_id=playlist_id).delete()
    Song.objects.filter(is_selected=True).update(is_selected=False)
    logger.info(f'🧹 Playlist-ID {playlist_id} vollständig geleert.')
    log_status_text(logger, '🧹 Playlist geleert', 'warning')
    return redirect(back_to)


@login_required
def tools_metadata_analyze(request):
    from django.http import JsonResponse
    from . import metadata_extractor, paths

    selected = list(Song.objects.filter(is_selected=True))
    if selected:
        songs = selected
        logger.info(f'🎯 {len(songs)} selektierte Songs werden analysiert...')
    else:
        songs = list(Song.objects.filter(
            Q(bpm__isnull=True) |
            Q(key__isnull=True) | Q(key='') |
            Q(time_sig__isnull=True) | Q(time_sig='') |
            Q(duration__isnull=True) | Q(duration='')
        ))
        logger.info('📦 Keine Auswahl → analysiere Songs mit fehlenden Metadaten...')

    if not songs:
        return JsonResponse({'error': 'Keine Songs zum Analysieren gefunden.'}, status=400)

    for song in songs:
        full_path = paths.MIDI_DIR / song.filename
        try:
            meta = metadata_extractor.analyze_midi(str(full_path))
        except Exception:
            logger.exception(f'💥 Fehler bei der Analyse von Song-ID {song.id}')
            continue

        if song.bpm is None:
            song.bpm = meta.get('bpm')
        if not song.key:
            song.key = meta.get('key')
        if not song.time_sig:
            song.time_sig = meta.get('time_sig')
        if not song.duration:
            song.duration = meta.get('duration_formatted')
        song.save(update_fields=['bpm', 'key', 'time_sig', 'duration'])

    logger.info('🎵 Metadaten-Analyse abgeschlossen.')
    return JsonResponse({'count': len(songs)})


@login_required
def tools_db_check(request):
    from django.http import JsonResponse
    from . import missing_files

    missing = missing_files.list_missing_songs()
    logger.info(f'❗ Fehlende Dateien in DB: {len(missing)}')

    if not missing:
        log_status(logger, 931)

    return JsonResponse({
        'count': len(missing),
        'filenames': [s.filename for s in missing],
    })


@login_required
def tools_db_check_resolve(request):
    from django.http import JsonResponse
    from . import missing_files, paths

    action = request.POST.get('action')
    missing = missing_files.list_missing_songs()

    if action == 'delete':
        count = 0
        for song in missing:
            if song.lyrics_filename:
                lyrics_path = (paths.MIDI_DIR / song.lyrics_filename).resolve()
                try:
                    if lyrics_path.exists() and paths.MIDI_DIR.resolve() in lyrics_path.parents:
                        lyrics_path.unlink()
                        logger.info(f'🗑 Lyrics gelöscht: {lyrics_path}')
                except OSError:
                    logger.warning(f'⚠ Konnte Lyrics nicht löschen ({song.lyrics_filename})')
            song.delete()
            count += 1
        logger.info(f'🗑 DB-Eintrag gelöscht: {count} Einträge')
    else:
        action = 'flag'
        count = 0
        for song in missing:
            song.missing = True
            song.save(update_fields=['missing'])
            count += 1
        logger.info(f"🏷️ {count} Einträge auf 'fehlend' markiert.")

    log_status(logger, 931)
    return JsonResponse({'count': count, 'action': action})


@login_required
def tools_scan(request):
    from django.http import JsonResponse
    from . import scanner

    logger.info('🔍 ScannerWorker gestartet...')
    new_files, _missing_files = scanner.compare_with_database()

    if not new_files:
        log_status(logger, 904)

    return JsonResponse({'new_files': new_files, 'count': len(new_files)})


@login_required
def tools_scan_import(request):
    from django.http import JsonResponse
    from . import scanner, paths, metadata_extractor

    new_files, _missing_files = scanner.compare_with_database()
    logger.info(f'📥 ImportWorker startet → {len(new_files)} Dateien...')

    added = 0
    for rel_path in new_files:
        abs_path = paths.MIDI_DIR / rel_path
        if not abs_path.exists():
            logger.warning(f'⚠ Datei nicht gefunden: {rel_path}')
            continue

        meta = metadata_extractor.analyze_midi(str(abs_path))
        collection = abs_path.parent.name if abs_path.parent != paths.MIDI_DIR else ''
        title = abs_path.stem

        # time_sig wird hier bewusst NICHT übernommen - im Original
        # (ImportWorker) fehlt die Spalte ebenfalls im INSERT, obwohl
        # analyze_midi() sie liefert.
        Song.objects.create(
            filename=rel_path,
            title=title,
            bpm=meta.get('bpm'),
            key=meta.get('key'),
            duration=meta.get('duration_formatted'),
            collection=collection,
        )

        SessionLog().add_recent_import(title=title)
        added += 1

    logger.info(f'✅ Import abgeschlossen → {added} Songs hinzugefügt')
    log_status(logger, 904)
    return JsonResponse({'count': added})


@login_required
def player_play(request, song_id):
    from django.http import JsonResponse
    from . import paths
    from .player import get_player

    song = get_object_or_404(Song, pk=song_id)
    full_path = paths.MIDI_DIR / song.filename

    if not full_path.exists():
        return JsonResponse({'error': f'Datei nicht gefunden: {song.filename}'}, status=404)

    player = get_player()
    player.play({
        'id': song.id,
        'path': str(full_path),
        'title': song.title or song.filename,
        'artist': song.artist,
    })

    if not player.state.is_playing:
        return JsonResponse({'error': 'Wiedergabe konnte nicht gestartet werden.'}, status=500)

    return JsonResponse({'id': song.id, 'title': song.title, 'artist': song.artist})


@login_required
def player_stop(request):
    from django.http import JsonResponse
    from .player import get_player

    get_player().stop()
    return JsonResponse({'ok': True})


@login_required
def mixer_open(request):
    """Tools > Mixer öffnen: nutzt den per Checkbox markierten Song. Liefert
    nur die Ziel-Song-ID zurück (JSON) - das Mixer-Modal selbst wird dann per
    mixer_view() nachgeladen, genau wie beim Zeilen-Kontextmenü."""
    from django.http import JsonResponse

    song = Song.objects.filter(is_selected=True).first()
    if not song:
        logger.warning('⚠️ Mixer ohne ausgewählten Song aufgerufen.')
        log_status(logger, 741)
        return JsonResponse({'error': 'Bitte einen Song auswählen.'}, status=400)
    return JsonResponse({'song_id': song.id})


@login_required
def mixer_view(request, song_id):
    """Liefert den Inhalt des Mixer-Modals als HTML-Fragment (per JS in
    #mixerModal geladen) - entspricht MixerDialog, das im Original ebenfalls
    ein Dialog/Modal ist, keine eigene Seite."""
    from . import paths, mixer

    song = get_object_or_404(Song, pk=song_id)
    full_path = paths.MIDI_DIR / song.filename

    logger.info('🎚 Mixer öffnen')

    if not full_path.exists():
        logger.error(f'❌ Mixer: Datei nicht gefunden: {full_path}')
        log_status(logger, 742)
        return render(request, 'partials/mixer_error.html', {'error_message': 'Song konnte nicht geladen werden.'})

    try:
        service = mixer.open_mixer(song_id, str(full_path))
    except Exception as e:
        logger.exception('💥 Mixer konnte nicht geladen werden')
        log_status(logger, 742)
        return render(request, 'partials/mixer_error.html', {'error_message': f'MIDI konnte nicht geladen werden: {e}'})

    log_status(logger, 740)

    return render(request, 'partials/mixer_content.html', {
        'song': song,
        'channels': service.get_channel_states(),
    })


def _mixer_service_or_error(song_id):
    from django.http import JsonResponse
    from . import mixer

    service = mixer.get_mixer_service(song_id)
    if not service:
        return None, JsonResponse({'error': 'Mixer-Sitzung abgelaufen, bitte Seite neu laden.'}, status=400)
    return service, None


@login_required
def mixer_set_volume(request, song_id):
    from django.http import JsonResponse

    service, error = _mixer_service_or_error(song_id)
    if error:
        return error

    channel = int(request.POST.get('channel'))
    value = int(request.POST.get('value'))
    service.set_volume(channel, value, live=True)
    return JsonResponse({'volume_db': service.channels[channel].volume_to_db()})


@login_required
def mixer_set_pan(request, song_id):
    from django.http import JsonResponse

    service, error = _mixer_service_or_error(song_id)
    if error:
        return error

    channel = int(request.POST.get('channel'))
    pan = int(request.POST.get('pan'))
    service.set_pan(channel, pan, live=True)
    return JsonResponse({'pan': service.channels[channel].pan})


@login_required
def mixer_set_mute(request, song_id):
    from django.http import JsonResponse

    service, error = _mixer_service_or_error(song_id)
    if error:
        return error

    channel = int(request.POST.get('channel'))
    muted = request.POST.get('muted') == 'true'
    service.set_mute(channel, muted)
    return JsonResponse({'ok': True})


@login_required
def mixer_set_solo(request, song_id):
    from django.http import JsonResponse

    service, error = _mixer_service_or_error(song_id)
    if error:
        return error

    channel = int(request.POST.get('channel'))
    solo = request.POST.get('solo') == 'true'
    service.set_solo(channel, solo)
    return JsonResponse({'ok': True})


@login_required
def mixer_export(request, song_id):
    from django.http import JsonResponse

    service, error = _mixer_service_or_error(song_id)
    if error:
        return error

    try:
        out_path = service.export_mix()
    except Exception as e:
        logger.exception('💥 Mixer-Export fehlgeschlagen')
        log_status(logger, 744)
        return JsonResponse({'error': str(e)}, status=500)

    log_status(logger, 743)
    return JsonResponse({'filename': Path(out_path).name})


@login_required
def mixer_export_download(request, filename):
    from django.http import FileResponse, Http404
    from . import paths

    file_path = paths.MIXER_OUTPUT_DIR / filename
    if '/' in filename or '\\' in filename or not file_path.exists():
        raise Http404
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
