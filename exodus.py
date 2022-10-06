import logging
import sys

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import CustomFormatter
import utils

log = logging.getLogger('main')
log.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setStream(sys.stdout)
console.setFormatter(CustomFormatter.CustomFormatter())
log.addHandler(console)

scope = "user-library-modify,user-library-read"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope),
                     requests_timeout=15,
                     retries=5)

fileName = "examples/Медиатека.xml"
a_music = utils.parse_library(fileName)
no_match = []
errors = []

for idx, aItem in enumerate(a_music['Tracks']):
    # if idx < 9013:
    #     continue
    aTrack = a_music['Tracks'][aItem]

    log.debug('### Track №' + str(idx) + ' // ' +
              aTrack.get('Artist', '<NULL>') + ' // ' +
              aTrack.get('Name', '<NULL>') + ' // ' +
              aTrack.get('Album', '<NULL>'))

    if aTrack.get('Playlist Only', False):
        log.warning("Song not added to Library (playlist only). Skipping...")
        continue
    if aTrack.get('Movie', False):
        log.warning("Track is not music. Skipping...")
        continue

    searchQuery = utils.build_query(aTrack)
    try:
        results = sp.search(searchQuery, 3, 0, 'track')
    except spotipy.SpotifyException:
        log.error("!!!Spotipy Error!!! Search Query is probably too long!")
        log.error(searchQuery)
        errors.append(aTrack)
        continue

    matches = results['tracks']['total']
    if matches == 0:
        log.warning('!No Matches! Trying raw search!')
        searchQuery = utils.build_query(aTrack, 'raw:artist,name')
        results = sp.search(searchQuery, 3, 0, 'track')
        matches = results['tracks']['total']
    sItems = results['tracks']['items']
    if matches == 0:
        log.error('!!!STILL NO MATCHES!!! :(')
        no_match.append(aTrack)
    elif matches == 1:
        log.debug('!Perfect Match! Adding to Saved Tracks...')
        ids = [sItems[0]['id']]
        # sp.current_user_saved_tracks_add(ids)
    else:
        log.debug('!Multiple Matches!')
        best_id = utils.best_match(aTrack, sItems)
        if best_id is None:
            no_match.append(aTrack)
        else:
            ids = [best_id]
            # sp.current_user_saved_tracks_add(ids)

log.info('Saving reports...')
if len(no_match) > 0:
    utils.generate_tsv(no_match, 'no_match')
if len(errors) > 0:
    utils.generate_tsv(errors, 'errors')

log.info('Script finished!')
