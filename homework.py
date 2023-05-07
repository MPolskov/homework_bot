import os
import requests
import logging

from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

from exceptions import LostEnvVarError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TOKENS = (
    'PRACTICUM_TOKEN',
    'TELEGRAM_TOKEN',
    'TELEGRAM_CHAT_ID'
)

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename="main.log",
    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)


def check_tokens():
    """Проверка наличие значения переменных окружения."""
    lost_vars = ''
    for token in TOKENS:
        if os.getenv(token) is None:
            lost_vars += token
    if lost_vars:
        logger.critical(f'Отсутсвутю токины:{lost_vars}')
        raise LostEnvVarError()
    else:
        logger.info('Проверка переменных окружения прошла успешно.')


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение отправлено')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Запрос к API Практикума."""
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=timestamp
        )
    except Exception as error:
        logging.error(f'Ошибка при запросе к API: {error}')

    return homework_statuses.json()


def check_response(response: dict):
    """Проверка ответа от API Практикума."""
    if type(response) == dict:
        logger.info('Ответ является словарем')
    else:
        ... # Ошибка типа данных
    if 'homeworks' in response.keys:
        logger.info('В ответе есть ключ "homeworks"')
    else:
        ... # ошибка 
    if type(response['homeworks']) == list:
        logger.info('ключ "homeworks" содержит список')
    else:
        ... # Error


def parse_status(homework):
    """Выгрузка статуса проверки задания."""
    last_homework = homework['homeworks'][0]
    homework_name = last_homework['homework_name']
    verdict = HOMEWORK_VERDICTS[last_homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    ...

    while True:
        try:
            get_api_answer()
            if check_response():
                parse_status()
                send_message()

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
