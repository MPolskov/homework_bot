import os
import sys
import requests
import logging
import time
import telegram

from dotenv import load_dotenv
from json import JSONDecodeError
from http import HTTPStatus


from exceptions import LostEnvVarError, UnknownStatusError, KeyError

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
# logger.setLevel(logging.INFO)
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
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.debug(f'Сообщение успешно отправлено: {message}.')


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


def check_response(response):
    """Проверка ответа от API Практикума."""
    if isinstance(response, dict) :
        logger.debug('Ответ является словарем')
    else:
        logger.error('Неверный тип данных ответа')
        raise TypeError()
    if 'homeworks' not in response:
        logger.error('Отсутствует ключ "homeworks"!')
        raise KeyError()
    homeworks = response.get('homeworks')
    if isinstance(homeworks, list):
        logger.debug('ключ "homeworks" содержит список')
    else:
        logger.error('Ключ "homeworks" имеет неверный тип данных!')
        raise TypeError()
    return homeworks


def parse_status(homework):
    """Выгрузка статуса проверки задания."""
    if isinstance(homework, list):
        homework, *_ = homework
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует ключ "homework_name"!')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise UnknownStatusError()
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0  # int(time.time())
    last_status = ''
    payload = {'from_date': timestamp}

    while True:
        try:
            response = get_api_answer(payload)
            homework = check_response(response)
            if homework:
                status_hw = parse_status(homework)
                if status_hw and status_hw != last_status:
                    send_message(bot, status_hw)
                    payload['from_date'] = int(response['current_date'])
                    last_status = status_hw
                else:
                    logger.debug('Статус работы не изменился')
        except requests.exceptions.HTTPError:
            logger.error('Ошибка доступа к API Я.Практикума'
                         f'HTTPStatus = {response.status_code}')
        except telegram.error.TelegramError as error:
            logging.error(f'Ошибка при отправке сообщения: {error}')
        except UnknownStatusError as error:
            logger.error(f'Неизвестный статус домашнего задания: {error}')
        except TypeError as error:
            logger.error(f'Неверный тип данных ответа: {error}')
        except KeyError as error:
            logger.error(error)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
