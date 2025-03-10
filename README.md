# FoodGraam - Рецепты для каждого дня

![FoodGraam](https://foodgraam.zapto.org/static/your-logo-if-any.png)

**FoodGraam** — это веб-приложение, где пользователи могут находить, создавать и делиться рецептами блюд. Это место для тех, кто любит готовить и ищет новые идеи для ежедневных обедов или особенных случаев.

## Оглавление

1. [О проекте](#о-проекте)
2. [Демонстрация](#демонстрация)
3. [Технологии](#технологии)
4. [Установка и запуск](#установка-и-запуск)
5. [Использование](#использование)
---

## О проекте

FoodGraam создан для людей, которые хотят легко находить рецепты, следить за своими любимыми блюдами и делиться ими с другими. Приложение позволяет:
- Просматривать коллекцию рецептов.
- Добавлять свои собственные рецепты.
- Искать рецепты по ингредиентам, категориям или названиям.
- Отмечать понравившиеся рецепты.

Приложение разработано с использованием Django и Django REST Framework, обеспечивая высокую производительность и удобство использования.

---

## Демонстрация

Вы можете протестировать приложение прямо сейчас:  
[https://foodgraam.zapto.org/recipes](https://foodgraam.zapto.org/recipes)
[http://84.201.167.207:8080](http://84.201.167.207:8080)

---

## Технологии

Проект построен на следующих технологиях:

- **Бэкенд**: Django 3.2.16, Django REST Framework 3.12.4
- **База данных**: PostgreSQL (через `psycopg2-binary`)
- **Аутентификация**: JWT (с помощью `djangorestframework-simplejwt`)
- **API**: Поддерживает RESTful API для взаимодействия с фронтендом
- **Дополнительные библиотеки**:
  - `django-filter` для фильтрации запросов
  - `pillow` для работы с изображениями
  - `gunicorn` для запуска production-сервера
  - `social-auth-app-django` для социальной аутентификации

---

## Установка и запуск

Чтобы запустить проект локально, выполните следующие шаги:

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/your-repo-url.git
   cd foodgraam
   ```

2. **Создайте виртуальное окружение**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Настройте переменные окружения**:
   Создайте файл `.env` в корне проекта и добавьте необходимые настройки, такие как секретный ключ Django, данные базы данных и другие параметры.

5. **Примените миграции**:
   ```bash
   python manage.py migrate
   ```

6. **Запустите сервер**:
   ```bash
   python manage.py runserver
   ```

7. **Откройте приложение**:
   Перейдите по адресу [http://127.0.0.1:8000/recipes](http://127.0.0.1:8000/recipes) в вашем браузере.

---

## Использование

### Для пользователей:
- Зарегистрируйтесь или войдите через существующий аккаунт.
- Просматривайте список рецептов на главной странице.
- Используйте поиск для быстрого нахождения нужных рецептов.
- Добавляйте свои рецепты через форму создания.

### Для администраторов:
- Войдите в админ-панель Django (`/admin`) для управления контентом.
- Управляйте пользователями, рецептами и категориями.

---

## Админская часть

### Логин и пароль:
- логин: admin@gmail.com
- пароль: 1

---
