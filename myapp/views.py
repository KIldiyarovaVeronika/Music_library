import json
import uuid
import xml.etree.ElementTree as ET

from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .forms import AlbumForm, AlbumModelForm, validate_album, REQUIRED_FIELDS
from .models import Album

DATA_DIR = Path(settings.BASE_DIR) / "myapp" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def parse_file(path):
    """Читает файл и проверяет данные альбома."""
    if path.suffix.lower() == ".json":
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            raise ValueError("Файл содержит ошибку JSON.")
        except UnicodeError:
            raise ValueError("Файл должен быть в кодировке UTF-8.")

    elif path.suffix.lower() == ".xml":
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            raise ValueError("Файл содержит ошибку XML.")

        if root.tag != "album":
            raise ValueError(
                "Неверная структура XML: корневой элемент должен быть album."
            )

        data = {}

        for field in REQUIRED_FIELDS:
            element = root.find(field)

            if element is None or element.text is None:
                raise ValueError(
                    f"Отсутствует поле «{field}» в XML-файле."
                )

            data[field] = element.text

        try:
            data["year"] = int(data["year"])
        except ValueError:
            raise ValueError(
                "Поле «Год выпуска» в XML должно быть целым числом."
            )

    else:
        raise ValueError("Поддерживаются только JSON и XML.")

    errors = validate_album(data)

    if errors:
        messages = list(errors.values())
        raise ValueError(" ".join(messages))

    return data


def save_album(data, file_format):
    """Сохраняет данные формы в JSON/XML."""
    filename = f"{uuid.uuid4().hex}.{file_format}"
    path = DATA_DIR / filename

    if file_format == "json":
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    elif file_format == "xml":
        root = ET.Element("album")

        for key in REQUIRED_FIELDS:
            element = ET.SubElement(root, key)
            element.text = str(data[key])

        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ")
        tree.write(path, encoding="utf-8", xml_declaration=True)

    return filename


def index(request):
    message = ""
    error = ""
    form = AlbumForm()
    checked_files = {}

    # Сохранение альбома из HTML-формы
    if request.method == "POST" and "save_album" in request.POST:
        form = AlbumForm(request.POST)

        if form.is_valid():
            data = {
                "title": form.cleaned_data["title"].strip(),
                "artist": form.cleaned_data["artist"].strip(),
                "year": form.cleaned_data["year"],
                "genre": form.cleaned_data["genre"].strip(),
            }

            storage_type = form.cleaned_data["storage_type"]

            if storage_type == "database":
                duplicate = Album.objects.filter(
                    title=data["title"],
                    artist=data["artist"],
                    year=data["year"],
                    genre=data["genre"],
                ).exists()

                if duplicate:
                    error = (
                        "Такой альбом уже существует "
                        "в базе данных."
                    )
                else:
                    Album.objects.create(**data)
                    message = (
                        "Альбом успешно сохранён "
                        "в базе данных."
                    )

                form = AlbumForm()

            else:
                save_album(
                    data,
                    form.cleaned_data["file_format"]
                )

                message = "Альбом успешно сохранён в файл."
                form = AlbumForm()

    # Загрузка готового JSON- или XML-файла
    elif request.method == "POST" and "upload_file" in request.POST:
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
                    with path.open("wb") as destination:
                        for chunk in uploaded.chunks():
                            destination.write(chunk)

                    data = parse_file(path)

                    checked_files[filename] = {
                        "data": data,
                        "error": "",
                    }
                    message = "Файл успешно загружен и проверен."

                except (ValueError, TypeError, KeyError, OSError) as exc:
                    checked_files[filename] = {
                        "data": None,
                        "error": str(exc),
                    }
                    error = (
                        "Файл сохранён, но содержит ошибки. "
                        "Подробности указаны в разделе "
                        "«Сохранённые альбомы»."
                    )

    # Чтение всех файлов, включая некорректные
    albums = []

    for path in sorted(DATA_DIR.iterdir()):
        if path.suffix.lower() not in {".json", ".xml"}:
            continue

        album = {
            "filename": path.name,
            "format": path.suffix[1:].upper(),
            "data": None,
            "error": "",
        }

        if path.name in checked_files:
            # Используем результат проверки загрузки
            album.update(checked_files[path.name])
        else:
            # Проверяем ранее сохранённые файлы
            try:
                album["data"] = parse_file(path)
            except (ValueError, TypeError, KeyError, OSError) as exc:
                album["error"] = str(exc)

        albums.append(album)

    return render(request, "myapp/index.html", {
        "form": form,
        "albums": albums,
        "message": message,
        "error": error,
    })
def search_albums(request):
    query = request.GET.get("q", "").strip()

    albums = Album.objects.filter(
        title__icontains=query
    ) | Album.objects.filter(
        artist__icontains=query
    ) | Album.objects.filter(
        genre__icontains=query
    )

    results = []

    for album in albums.distinct():
        results.append({
            "id": album.id,
            "title": album.title,
            "artist": album.artist,
            "year": album.year,
            "genre": album.genre,
        })

    return JsonResponse({"albums": results})


def edit_album(request, album_id):
    album = get_object_or_404(Album, id=album_id)

    if request.method == "POST":
        form = AlbumModelForm(
            request.POST,
            instance=album
        )

        if form.is_valid():
            data = form.cleaned_data

            duplicate = Album.objects.filter(
                title=data["title"].strip(),
                artist=data["artist"].strip(),
                year=data["year"],
                genre=data["genre"].strip(),
            ).exclude(id=album.id).exists()

            if duplicate:
                form.add_error(
                    None,
                    "Такой альбом уже существует в базе данных."
                )
            else:
                form.save()
                return redirect("index")

    else:
        form = AlbumModelForm(instance=album)

    return render(
        request,
        "myapp/edit_album.html",
        {
            "form": form,
            "album": album,
        }
    )


@require_POST
def delete_album(request, album_id):
    album = get_object_or_404(Album, id=album_id)

    album.delete()

    return JsonResponse({
        "success": True,
        "message": "Альбом успешно удалён."
    })
