from django.db import models



class Album(models.Model):
    title = models.CharField(
        max_length=150,
        verbose_name="Название альбома"
    )

    artist = models.CharField(
        max_length=100,
        verbose_name="Исполнитель"
    )

    year = models.PositiveIntegerField(
        verbose_name="Год выпуска"
    )

    genre = models.CharField(
        max_length=80,
        verbose_name="Жанр"
    )

    class Meta:
        verbose_name = "Музыкальный альбом"
        verbose_name_plural = "Музыкальные альбомы"

        constraints = [
            models.UniqueConstraint(
                fields=["title", "artist", "year", "genre"],
                name="unique_album"
            )
        ]

    def __str__(self):
        return f"{self.title} — {self.artist}"