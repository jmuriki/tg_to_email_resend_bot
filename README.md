# tg_to_email_resend_bot

Telegram бот для автоматической пересылки на почту фотографий и ФИО, присланных в чат.

## Установка

Должен быть установлен python3.11

Если устанавливаете на Ubuntu, перейдите сначала в директорию `opt`:
```sh
cd /opt/
git clone https://github.com/jmuriki/tg_to_email_resend_bot.git
cd tg_to_email_resend_bot
```

Рекомендуется использовать venv для изоляции проекта.
В каталоге проекта создайте виртуальное окружение:
```sh
python -m venv venv
```
Активируйте его. На разных операционных системах это делается разными командами:

- Windows:
```sh
.\venv\Scripts\activate
```

- MacOS/Linux:
```sh
source venv/bin/activate
```

Затем используйте pip (или pip3, если есть конфликт с python2) для установки зависимостей:
```sh
pip install -r requirements.txt
```
или
```sh
pip3 install -r requirements.txt
```

## Ключи и параметры

Сохраните ключи/токены/параметры в `.env` файл в директорию проекта в следующем формате:

```
НАЗВАНИЕ_ПЕРЕМЕННОЙ=значение_переменной
```

```
TELEGRAM_BOT_TOKEN=
DEPARTMENTS="Администраторы,Бармены,Офис,Официанты,Повара,Сканировщики,Техники,Хостес,Гардеробщики"
SMTP_SERVER=
SMTP_PORT=587
SENDER_EMAIL=
SENDER_EMAIL_PASSWORD=
RECEIVER_EMAIL=
RECEIVER_EMAIL=
```

## Запуск

### tg_bot.py

Находясь в директории проекта, запустите с помощью python3 файл `tg_bot.py`

```sh
python3 tg_bot.py
```

## Запуск демона на Ubuntu для поддержание непрерывной работы

```sh
cp tg_bot.service /etc/systemd/system
systemctl enable tg_bot.service
systemctl start tg_bot.service
```
