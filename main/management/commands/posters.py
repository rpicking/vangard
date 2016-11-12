from django.core.management.base import BaseCommand, CommandError
from main.models import Posters

import os
import re
import sys
import socket
import urllib.request
from imdbpie import Imdb
import xml.etree.ElementTree as ET

class Command(BaseCommand):
    help = 'Download/update poster database'

    def handle(self, *args, **options):
        PosterBot().run()


class PosterBot():
    def __init__(self):
        socket.setdefaulttimeout(30)
        self.plex_url = os.environ.get('PLEX_URL')
        self.plex_token = os.environ.get('PLEX_TOKEN')
        self.dir = os.environ.get('POSTER_DIR')
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        self.imdb = Imdb()

    def run(self):
        self.getMoviePosters()
        self.getTVPosters()

    def getMoviePosters(self):
        movie_xml = ET.fromstring(urllib.request.urlopen(''.join((self.plex_url, '/library/sections/1/all?X-Plex-Token=', self.plex_token))).read())
    
        for child in movie_xml:
            title = child.attrib.get('title')
            ratingKey = child.attrib.get('ratingKey')
            thumb = child.attrib.get('thumb')
            updatedAt = int(child.attrib.get('updatedAt'))
            oldfile, exists = Posters.objects.search_entry(ratingKey, updatedAt)
            if not exists:    # couldn't find in database
                newfile = self.downloadPoster(thumb, ratingKey, updatedAt)
                if newfile:
                    imdb_url = self.getImdbLink(title)
                    Posters.objects.create_entry(ratingKey, newfile, imdb_url, title, updatedAt)
            elif oldfile: # entry needs to be updated
                newfile = self.downloadPoster(thumb, ratingKey, updatedAt)
                if newfile:
                    os.remove(os.path.join(self.dir, oldfile))
                    Posters.objects.update_entry(ratingKey, newfile, updatedAt)

    def getTVPosters(self):
        tv_xml = ET.fromstring(urllib.request.urlopen(''.join((self.plex_url, '/library/sections/2/all?X-Plex-Token=', self.plex_token))).read())

        for child in tv_xml:
            title = child.attrib.get('title')
            ratingKey = child.attrib.get('ratingKey')
            thumb = child.attrib.get('thumb')
            updatedAt = int(thumb.rsplit('/', 1)[-1])
            oldfile, exists = Posters.objects.search_entry(ratingKey, updatedAt)
            if exists:
                imdb_url = self.getImdbLink(title, ratingKey=ratingKey)
            else: # couldn't find in database
                newfile = self.downloadPoster(thumb, ratingKey, updatedAt)
                if newfile:
                    imdb_url = self.getImdbLink(title, 'TV')
                    Posters.objects.create_entry(ratingKey, newfile, imdb_url, title, updatedAt)
            if oldfile: # entry needs to be updated
                newfile = self.downloadPoster(thumb, ratingKey, updatedAt)
                if newfile:
                    os.remove(os.path.join(self.dir, oldfile))
                    Posters.objects.update_entry(ratingKey, newfile, updatedAt)

            show_xml = ET.fromstring(urllib.request.urlopen(''.join((self.plex_url, '/library/metadata/', ratingKey, '/children?X-Plex-Token=', self.plex_token))).read())
            for season in show_xml: #loop for seasons in show
                ratingKey = season.get('ratingKey')
                if ratingKey is None:
                    continue
                thumb = season.get('thumb')
                updatedAt = int(season.get('updatedAt'))
                oldfile, exists = Posters.objects.search_entry(ratingKey, updatedAt)

                if not exists:  #couldn't find entry in database
                    newfile = self.downloadPoster(thumb, ratingKey, updatedAt)
                    if newfile:
                        Posters.objects.create_entry(ratingKey, newfile, imdb_url, title, updatedAt)
                elif oldfile: #entry needs to be updated
                    newfile = self.downloadPoster(thumb, ratingKey, updatedAt)
                    if newfile:
                        os.remove(os.path.join(self.dir, oldfile))
                        Posters.objects.update_entry(ratingKey, newfile, updatedAt)

    # save directory stored in environment variable for now (could switch to db)
    def downloadPoster(self, thumb, ratingKey, updatedAt):    
        url = ''.join((self.plex_url, thumb, '?X-Plex-Token=', self.plex_token))
        filename = ''.join((ratingKey, '-', str(updatedAt), '.jpg'))
        path = os.path.join(self.dir, filename)
        try:
            urllib.request.urlretrieve(url, path)
            return filename
        except socket.timeout:
            if os.path.exists(path):
                os.remove(path)
            print("timeout error: " + filename)
        except FileNotFoundError:
            print("File or folder doesn't exist: " + path)
        except socket.error:
            if os.path.exists(path):
                os.remove(path)
            print("socket error occured: ")
        except:
            if os.path.exists(path):
                os.remove(path)
            print("Unexpected error:", sys.exc_info()[0])
        return ""

    # specify type if TV show
    def getImdbLink(self, title, type='Movie', ratingKey=''):
        if ratingKey:
            poster = Posters.objects.get(ratingKey=ratingKey)
            return poster.imdb_url
        search = self.imdb.search_for_title(title)
        if len(search) > 0:
            imdb_id = search[0].get('imdb_id')
            return "http://imdb.com/title/" + imdb_id
        title = title.replace(' ', '+')
        if type == 'Movie':
            return ''.join(('http://www.imdb.com/find?q=', title, '&s=tt&ttype=ft'))
        return ''.join(('http://www.imdb.com/find?q=', title, '&s=tt&ttype=tv'))
