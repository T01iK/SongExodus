import logging
import plistlib as pl
import re
import sys

from strsimpy.normalized_levenshtein import NormalizedLevenshtein

import CustomFormatter

log = logging.getLogger('utils')
log.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setStream(sys.stdout)
console.setFormatter(CustomFormatter.CustomFormatter())
log.addHandler(console)


def parse_library(filename):
    with open(filename, 'rb') as fp:
        a_music = pl.load(fp)
    log.info('Tracks Count: ' + str(len(a_music['Tracks'])))

    return a_music


def cleanse_string(string):
    regex = r'\([^)]*\)'
    cleansed_str = re.sub(regex, '', string)  # Remove everything within parenthesis ()
    cleansed_str = ' '.join(cleansed_str.split())  # Remove double spaces

    # print(cleansed_str)
    return cleansed_str


def build_query(track, pattern='artist,name'):
    artist = track.get('Artist', '')
    name = cleanse_string(track.get('Name', ''))
    album = cleanse_string(track.get('Album', ''))

    match pattern:
        case "artist,name":
            query = "artist:" + artist + " track:" + name
        case "name,album":
            query = "track:" + name + ' album:' + album
        case "raw:artist,name":
            query = artist + ' ' + name
        case _:
            query = "artist:" + artist + " track:" + name

    # print(query)
    return query


def best_match(a_track, s_tracks):
    normalized_levenshtein = NormalizedLevenshtein()
    a_artist = a_track.get('Artist', '')
    a_name = a_track.get('Name', '')
    a_album = a_track.get('Album', '')
    a_track_number = a_track.get('Track Number', -1)

    best_score = 0.0
    best_index = -1
    best_id = ''

    for jdx, s_track in enumerate(s_tracks):
        s_artist = s_track['artists'][0]['name']
        s_name = s_track['name']
        s_album = s_track['album']['name']
        s_track_number = s_track['track_number']

        artist_sim = normalized_levenshtein.similarity(a_artist, s_artist)
        name_sim = normalized_levenshtein.similarity(a_name, s_name)
        album_sim = normalized_levenshtein.similarity(a_album, s_album)
        track_number_sim = a_track_number == s_track_number

        # print('--- ', jdx, ' ---')
        # print('S // ',
        #       s_track['artists'][0]['name'], " // ",
        #       s_track['name'], " // ",
        #       s_track['album']['name'], " // ",
        #       s_track['album']['images'][0]['url'], " // ",
        #       s_track['external_urls']['spotify'])
        # print('A // ', a_track['Artist'], ' // ', a_track['Name'], ' // ', a_track['Album'])
        # print("Artist Similarity:   ", artist_sim)
        # print("Name Similarity: ", name_sim)
        # print("Album Similarity:    ", album_sim)
        # print("Same track #:    ", track_number_sim, " // ", int(track_number_sim))
        score = artist_sim + name_sim + album_sim + int(track_number_sim)
        if score > best_score:
            best_score = score
            best_index = jdx
            best_id = s_track['id']
    log.debug("Winner: " + best_id + ' // With score: ' + str(best_score))
    if best_score == 4.0:
        log.info("!Perfect Match!")
    log.info('S // ' +
             s_tracks[best_index]['artists'][0]['name'] + " // " +
             s_tracks[best_index]['name'] + " // " +
             s_tracks[best_index]['album']['name'] + " // " +
             s_tracks[best_index]['album']['images'][0]['url'] + " // " +
             s_tracks[best_index]['external_urls']['spotify'])
    log.info('A // ' +
             a_track.get('Artist', '<NULL>') + ' // ' +
             a_track.get('Name', '<NULL>') + ' // ' +
             a_track.get('Album', '<NULL>'))
    if best_score < 2.0:
        log.error("Bad score! Appending to no match...")
        return None
    else:
        return best_id


def generate_tsv(input_list, filename):
    with open('out/' + filename + r'.tsv', 'w', encoding='utf-8') as fp:
        fp.write("Artist\tName\tAlbum\tYear\tPersistent ID\n")
        for item in input_list:
            # write each item on a new line
            row = item.get('Artist', '<NULL>') + "\t" + \
                  item.get('Name', '<NULL>') + "\t" + \
                  item.get('Album', '<NULL>') + "\t" + \
                  str(item.get('Year', '<NULL>')) + "\t" + \
                  item.get('Persistent ID', '<NULL>')
            fp.write("%s\n" % row)
        log.info('Saved ' + filename + r'.tsv')
