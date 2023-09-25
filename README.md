# Проект телеграм-бот
### Описание
Учебный проект по созданию телеграм-бота.

Функции бота:
- раз в 10 минут опрашивет API сервиса Практикум.Домашка и проверяет статус отправленной на ревью домашней работы;
- при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram;
- логирование своей работы и сообщение о важных проблемах сообщением в Telegram.

### Технологии
* Python 3.9
* Django 2.2
* python-telegram-bot 13.7

## Установка и запуск проекта:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:MPolskov/homework_bot.git
```
```
cd homework_bot
```
Cоздать и активировать виртуальное окружение:
```
# для Windows:
py -3.9 -m venv venv
# для Linux:
python3.9 -m venv venv
```
```
# для Windows:
source venv/Scripts/activate
# для Linux:
sourse venv/bin/activate
```
Установить зависимости из файла requirements.txt:
```
python -m pip install -r requirements.txt
```
Выполнить миграции:
```
python manage.py migrate
```
Запустить сервер:
```
python manage.py runserver 0.0.0.0:8000
```
### Автор
Полшков Михаил
