import os
import sys
import requests
import logging
import time
import telegram

from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from json import JSONDecodeError
from http import HTTPStatus


from exceptions import LostEnvVarError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename="main.log",
    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def check_tokens():
    """Проверка наличие значения переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN}
    for token, value in tokens.items():
        if not value:
            logging.error(f'Значение переменной {token} не найдено!')
    if not all(tokens.values()):
        logger.critical('Отсутствуют необходимые переменные окаружения!'
                        'Продолжение выполнения программы невозможно!')
        raise LostEnvVarError()
    else:
        logger.info('Проверка переменных окружения прошла успешно.')


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')
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
    except requests.RequestException as error:
        logger.error(f'Сбой в работе программы: {error}')
    if homework_statuses.status_code != HTTPStatus.OK:
        raise requests.exceptions.HTTPError
    try:
        hw_dict = homework_statuses.json()
        return hw_dict
    except JSONDecodeError:
        logger.error('Ответ не может быть преобразован в словарь')


def check_response(response: dict):
    """Проверка ответа от API Практикума."""
    if type(response) == dict:
        logger.debug('Ответ является словарем')
    else:
        logger.error('Неверный тип данных ответа')
        raise TypeError()
    if 'homeworks' in response.keys:
        logger.debug('В ответе есть ключ "homeworks"')
    else:
        logger.error('Отсутствует ключ "homeworks"!')
        return False
    if type(response['homeworks']) == list:
        logger.debug('ключ "homeworks" содержит список')
    else:
        logger.error('Ключ "homeworks" имеет неверный тип данных!')
        return False
    if 'current_date' in response.keys:
        logger.debug('В ответе есть ключ "current_date"')
    else:
        logger.error('Отсутствует ключ "current_date"!')
        return False
    return True


def parse_status(homework):
    """Выгрузка статуса проверки задания."""
    last_hw, *_ = homework.get('homeworks')
    homework_name = last_hw['homework_name']
    homework_status = last_hw['status']
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logger.error(f'Неизвестный статус домашнего задания {homework_status}')


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_status = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            timestamp = int(response['current_date'])
            if response['homeworks']:
                status_hw = parse_status(response)
                if status_hw and status_hw != last_status:
                    send_message(bot, status_hw)
                    logger.debug('Сообщение успешно отправлено.')
                else:
                    logger.debug('Статус работы не изменился')
        except requests.exceptions.HTTPError:
            logger.error('Ошибка доступа к API Я.Практикума'
                        f'HTTPStatus = {homework_statuses.status_code}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
