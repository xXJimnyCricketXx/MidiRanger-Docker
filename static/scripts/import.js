(function () {
    var form = document.getElementById('importForm');
    if (!form) return;

    function getCookie(name) {
        var match = document.cookie.match('(^|;\\s*)' + name + '=([^;]*)');
        return match ? decodeURIComponent(match[2]) : null;
    }

    var midiInput = document.getElementById('midiFileInput');
    var midiDisplay = document.getElementById('midiFileDisplay');
    document.getElementById('midiBrowseBtn').addEventListener('click', function () {
        midiInput.click();
    });

    midiInput.addEventListener('change', function () {
        var file = midiInput.files[0];
        if (!file) return;

        midiDisplay.value = file.name;

        var data = new FormData();
        data.append('midi_file', file);

        fetch('/songs/import/analyze', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: data
        })
            .then(function (res) { return res.json(); })
            .then(function (json) {
                if (json.error) return;
                document.getElementById('tempId').value = json.temp_id;
                document.getElementById('originalFilename').value = json.original_filename;
                document.getElementById('durationFormatted').value = json.duration_formatted;
                document.getElementById('titleInput').value = json.title;
                document.getElementById('bpmInput').value = json.bpm;
                if (json.key) document.getElementById('keyInput').value = json.key;
            });
    });

    var lyricsInput = document.getElementById('lyricsFileInput');
    var lyricsDisplay = document.getElementById('lyricsFileDisplay');
    document.getElementById('lyricsBrowseBtn').addEventListener('click', function () {
        lyricsInput.click();
    });

    lyricsInput.addEventListener('change', function () {
        var file = lyricsInput.files[0];
        if (file) lyricsDisplay.value = file.name;
    });
})();
