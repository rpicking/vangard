from django.db import models

# Create your models here.
class PosterManager(models.Manager):
    def create_entry(self, ratingKey, filename, imdb_url, title, updatedAt):
        poster = self.create(ratingKey=ratingKey, filename=filename, imdb_url=imdb_url, title=title, updatedAt=updatedAt)
        return poster

    def update_entry(self, ratingKey, filename, updatedAt):
        poster = self.get(ratingKey=ratingKey)
        poster.filename = filename
        poster.updatedAt = updatedAt
        poster.save()

    def search_entry(self, ratingKey, updatedAt):
        try:
            poster = self.get(ratingKey=ratingKey)
            if poster.updatedAt < updatedAt:
                return poster.filename, True
            return "", True
        except models.ObjectDoesNotExist:
            return "", False
        
class Posters(models.Model):
    ratingKey = models.IntegerField()
    filename = models.CharField(max_length=140)
    imdb_url = models.CharField(max_length=140)
    title = models.CharField(max_length=140)
    updatedAt = models.IntegerField()

    objects = PosterManager()
