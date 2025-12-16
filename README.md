# Foodgram

## Запуск проекта

### Запуск в контейнерах

Для запуска в контейнерах необходимо перейти в папку `infra` и создать файл `.env` со следующими переменными

1. `POSTGRES_DB` - имя базы данных Postgres
2. `POSTGRES_USER` - имя пользователя Postgres
3. `POSTGRES_PASSWORD` - пароль пользователя Postgres
4. `DB_HOST` - адрес базы данных Postgres
5. `SECRET_KEY` - секретный ключ Django
6. `ALLOWED_HOSTS` - разрешённые хосты Django

После необходимо запустить контейнеры:

```
docker compose up
```

Работать будут 3 контейнера:
1. `foodgram-backend` - бекенд
2. `foodgram-proxy` - nginx
3. `db` - Postgres

Контейнер `foodgram-front` с фронтендом подготавливает статические файлы и прекращает работу

При желании можно загрузить фикстуры (в отдельном терминале):

1. Единицы измерения
```
docker-compose exec backend python manage.py loaddata fixtures/measurement_units.json
```

2. Ингредиенты
```
docker-compose exec backend python manage.py loaddata fixtures/ingredients.json
```

3. Пользователи
```
docker-compose exec backend python manage.py loaddata fixtures/users.json
```

4. Рецепты
```
docker-compose exec backend python manage.py loaddata fixtures/recipes.json
```

Примечание: Ингредиенты нельзя загружать до единиц измерения. Рецепты нельзя загружать до пользователей и ингредиентов. У рецептов после загрузки будут отсутствовать картинки, так как в фикстурах базы данных находятся только пути к ним. Чтобы картинки появились необходимо поставить новые при редактировании рецепта

### Запуск без контейнеров (доступ только к API и админке на порту 8000)

В папке `backend/foodgram_st_backend` в файл `settings.py` необходимо перенести настройки из `settings.py.debug`

После в папке `backend`:

#### Создайте виртуальное окружение:

На Windows:
```
python -m venv env
source env/Scripts/activate
```

На Linux и macOS:
```
python3 -m venv env
source env/bin/activate
```

#### Установите зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```

#### Выполните миграции:
```
python manage.py migrate
```

#### Фикстуры загружаются аналогично запуску в контейнерах, но без приставки:
```
docker-compose exec backend
```

#### Запустите сервер разработки:
```
python manage.py runserver
```

### Пользователи

В фикстурах созданы 4 пользоватея:
1. `aboba@mail.ru` - админ
2. `aboba2@mail.ru` - админ
3. `simpleuser@mail.ru`
4. `simpleuser2@mail.ru`

Все пользователи имеют пароль `asd45MNB`

### Адреса

* `http://localhost` - фронтенд веб-приложения
* `http://localhost/admin/` - админка
* `http://localhost/api/` - API
* `http://localhost/api/docs/` - документация API