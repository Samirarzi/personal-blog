from django.db import models




class post(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)

    @property
    def word_count(self):
        return len(self.body.split())

    @property
    def reading_minutes(self):
        return max(1, (self.word_count + 199) // 200)


    def __str__(self):
        return self.title
# Create your models here.
