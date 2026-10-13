from django import forms
from datetime import date


class AlbumForm(forms.Form):
    title = forms.CharField(
        label="Название альбома",
        max_length=150
    )
    artist = forms.CharField(
        label="Исполнитель",
        max_length=100
    )
    year = forms.IntegerField(
        label="Год выпуска",
        min_value=1900,
        max_value=date.today().year
    )
    genre = forms.CharField(
        label="Жанр",
        max_length=80
    )
    file_format = forms.ChoiceField(
        label="Формат сохранения",
        choices=[
            ("json", "JSON"),
            ("xml", "XML"),
        ]
    )
