from datetime import date

from django import forms


CURRENT_YEAR = date.today().year
REQUIRED_FIELDS = ("title", "artist", "year", "genre")


def validate_album(data):
    """Проверяет данные альбома и возвращает ошибки по полям."""
    errors = {}

    if not isinstance(data, dict):
        return {"__all__": "Данные альбома должны быть объектом."}

    missing = set(REQUIRED_FIELDS) - set(data)
    extra = set(data) - set(REQUIRED_FIELDS)

    if missing:
        errors["__all__"] = (
            "Отсутствуют поля: " + ", ".join(sorted(missing))
        )

    if extra:
        errors["__all__"] = (
            errors.get("__all__", "")
            + (" " if errors.get("__all__") else "")
            + "Лишние поля: " + ", ".join(sorted(extra))
        )

    for field, label, limit in [
        ("title", "Название альбома", 150),
        ("artist", "Исполнитель", 100),
        ("genre", "Жанр", 80),
    ]:
        value = data.get(field)

        if not isinstance(value, str):
            errors[field] = f"Поле «{label}» должно быть текстом."
        elif not value.strip():
            errors[field] = f"Поле «{label}» не должно быть пустым."
        elif len(value) > limit:
            errors[field] = (
                f"Поле «{label}»: максимум {limit} символов."
            )

    year = data.get("year")

    if isinstance(year, bool) or not isinstance(year, int):
        errors["year"] = "Поле «Год выпуска» должно быть целым числом."
    elif not 1900 <= year <= CURRENT_YEAR:
        errors["year"] = (
            f"Поле «Год выпуска» должно быть от 1900 до {CURRENT_YEAR}."
        )

    return errors


class AlbumForm(forms.Form):
    title = forms.CharField(
        label="Название альбома",
        max_length=150,
    )
    artist = forms.CharField(
        label="Исполнитель",
        max_length=100,
    )
    year = forms.IntegerField(
        label="Год выпуска",
        min_value=1900,
        max_value=CURRENT_YEAR,
    )
    genre = forms.CharField(
        label="Жанр",
        max_length=80,
    )
    file_format = forms.ChoiceField(
        label="Формат сохранения",
        choices=[
            ("json", "JSON"),
            ("xml", "XML"),
        ],
    )

    def clean(self):
        cleaned_data = super().clean()

        fields = REQUIRED_FIELDS

        if all(field in cleaned_data for field in fields):
            errors = validate_album({
                field: cleaned_data[field]
                for field in fields
            })

            for field, message in errors.items():
                if field in fields:
                    self.add_error(field, message)
                elif field == "__all__":
                    raise forms.ValidationError(message)

        return cleaned_data
