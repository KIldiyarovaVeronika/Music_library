import json
import uuid
import xml.etree.ElementTree as ET

from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from django import forms

from .forms import AlbumForm


DATA_DIR = Path(settings.BASE_DIR) / "myapp" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_FIELDS = {"title", "artist", "year", "genre"}

def validate_album(data):
    """Проверяет структуру и значения одного альбома."""
    if not isinstance(data, dict):
        return False

    if set(data.keys()) != REQUIRED_FIELDS:
        return False

    title = data["title"]
    artist = data["artist"]
    genre = data["genre"]
    year = data["year"]

    if not all(isinstance(x, str) for x in [title, artist, genre]):
        return False

    if not title.strip() or not artist.strip() or not genre.strip():
        return False

    if any(len(x) > limit for x, limit in [
        (title, 150), (artist, 100), (genre, 80)
    ]):
        return False

    if isinstance(year, bool) or not isinstance(year, int):
        return False

    if not 1900 <= year <= __import__("datetime").date.today().year:
        return False

    return True


def parse_file(path):
    """Читает и проверяет JSON- или XML-файл."""
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

    elif path.suffix.lower() == ".xml":
        root = ET.parse(path).getroot()

        if root.tag != "album":
            raise ValueError("Неверный корневой элемент XML")

        data = {}
        for field in REQUIRED_FIELDS:
            element = root.find(field)
            if element is None or element.text is None:
                raise ValueError("Не хватает полей альбома")
            data[field] = element.text

        try:
            data["year"] = int(data["year"])
        except ValueError:
            raise ValueError("Год должен быть числом")

    else:
        raise ValueError("Неподдерживаемый формат")

    if not validate_album(data):
        raise ValueError("Неверная структура или значения альбома")

    return data


def save_album(data, file_format):
    """Сохраняет альбом в файл с уникальным именем."""
    filename = f"{uuid.uuid4().hex}.{file_format}"
    path = DATA_DIR / filename

    if file_format == "json":
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    elif file_format == "xml":
        root = ET.Element("album")

        for key, value in data.items():
            element = ET.SubElement(root, key)
            element.text = str(value)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ")
        tree.write(path, encoding="utf-8", xml_declaration=True)

    return filename


def index(request):
    message = ""
    error = ""
    form = AlbumForm(request.POST or None)

    # Сохранение данных, введённых через HTML-форму
    if request.method == "POST" and "save_album" in request.POST:
        if form.is_valid():
            data = {
                "title": form.cleaned_data["title"].strip(),
                "artist": form.cleaned_data["artist"].strip(),
                "year": form.cleaned_data["year"],
                "genre": form.cleaned_data["genre"].strip(),
            }

            save_album(data, form.cleaned_data["file_format"])
            message = "Альбом успешно сохранён."

            form = AlbumForm()
        else:
            error = "Проверьте правильность заполнения формы."

    # Загрузка JSON- или XML-файла
    if request.method == "POST" and "upload_file" in request.POST:
        uploaded = request.FILES.get("data_file")

        if not uploaded:
            error = "Выберите файл для загрузки."
        elif uploaded.size > 2 * 1024 * 1024:
            error = "Размер файла не должен превышать 2 МБ."
        else:
            extension = Path(uploaded.name).suffix.lower()

            if extension not in {".json", ".xml"}:
                error = "Разрешены только файлы JSON и XML."
            else:
                filename = f"{uuid.uuid4().hex}{extension}"
                path = DATA_DIR / filename

                try:
                    # Имя файла создаём сами, не используя имя пользователя.
                    with path.open("wb") as destination:
                        for chunk in uploaded.chunks():
                            destination.write(chunk)

                    parse_file(path)
                    message = "Файл успешно загружен и проверен."

                except (ValueError, TypeError, KeyError,
                        json.JSONDecodeError, ET.ParseError,
                        OSError, UnicodeError):
                    if path.exists():
                        path.unlink()
                    error = (
                        "Файл содержит некорректные данные "
                        "или имеет неверный формат. Файл удалён."
                    )

    # Чтение всех существующих файлов
    albums = []

    for path in sorted(DATA_DIR.iterdir()):
        if path.suffix.lower() not in {".json", ".xml"}:
            continue

        try:
            data = parse_file(path)
            albums.append({
                "filename": path.name,
                "format": path.suffix[1:].upper(),
                "data": data,
            })
        except (ValueError, TypeError, KeyError,
                json.JSONDecodeError, ET.ParseError,
                OSError, UnicodeError):
            # Не показываем некорректные файлы.
            continue

    return render(request, "myapp/index.html", {
        "form": form,
        "albums": albums,
        "message": message,
        "error": error,
    })
