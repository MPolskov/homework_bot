import os
import sys
import logging
import time
from json import JSONDecodeError
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions as ex  # Импорт польз. исключений.
import event_descriptions as ed  # Импорт описания событий

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
    filename='main.log',
    encoding='UTF-8',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)
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
            logging.error(ed.TOKEN_MISSING_LOG.format(token))
    # if not all(value is not None for value in tokens.values())
    # Данный вариант не работает, если в .env отсутствует значение токена.
    # на сколько я понял, пустая строка при выполнении этого выражения
    # не воспринимается как None. Почему? - пока не разобрался...
    # Вариант if None in tokens.values() тоже не работает как ожидалось...
    empty = (None, '',)
    if not all(value not in empty for value in tokens.values()):
        raise ex.LostEnvVarError(ed.TOKEN_CRIT_ERROR)
    else:
        logger.info(ed.TOKEN_CHECK_SUCCESSFUL)


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        logger.debug(ed.SEND_MESSAGE_LOG)
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(ed.SEND_MESSAGE_SECCESSFUL.format(message))
    except telegram.error.TelegramError as error:
        logging.error(error)


def get_api_answer(timestamp):
    """Запрос к API Практикума."""
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=timestamp
        )
    except requests.RequestException as error:
        logger.error(ed.UNIVERSAL_ERROR.format(error))
    if homework_statuses.status_code != HTTPStatus.OK:
        raise ex.HTTPStatusError(
            ed.HTTP_STATUS_ERROR.format(homework_statuses.status_code)
        )
    try:
        hw_dict = homework_statuses.json()
        return hw_dict
    except JSONDecodeError:
        logger.error(ed.JSON_DECODE_ERROR)


def check_response(response):
    """Проверка ответа от API Практикума."""
    if isinstance(response, dict):
        logger.debug(ed.CHECK_DICT_DEBUG)
    else:
        raise ex.ResponseFormatError(ed.CHECK_DICT_ERROR)
    if 'homeworks' not in response:
        logger.error(ed.HOMEWORKS_MISSING_ERROR)
        raise ex.MissingKeyError(ed.HOMEWORKS_MISSING_ERROR)
    homeworks = response.get('homeworks')
    if isinstance(homeworks, list):
        logger.debug(ed.CHECK_LIST_DEBUG)
    else:
        raise ex.ResponseFormatError(ed.CHECK_LIST_ERROR)
    return homeworks


def parse_status(homework):
    """Выгрузка статуса проверки задания."""
    # По идее эта функция срабатывает после check_response,
    # где данная проверка уже есть, но у pytest видимо своя логика.
    if isinstance(homework, list):
        homework, *_ = homework
    if 'homework_name' not in homework:
        raise ex.MissingKeyError(ed.MISSING_KEY_ERROR)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ex.UnknownStatusError(ed.UNKNOWN_STATUS_ERROR
                                    .format(homework_status))
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except ex.LostEnvVarError as error:
        logger.critical(error)
        sys.exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_status = ''
    last_error = ''
    payload = {'from_date': timestamp}

    while True:
        try:
            response = get_api_answer(payload)
            homework = check_response(response)
            if homework:
                status_hw = parse_status(homework)
                if status_hw != last_status:
                    send_message(bot, status_hw)
                    payload['from_date'] = int(response['current_date'])
                    last_status = status_hw
            else:
                logger.debug(ed.STATUS_NOT_CHANGED_LOG)
        except (
            ex.ResponseFormatError,
            ex.MissingKeyError,
            ex.UnknownStatusError,
            ex.HTTPStatusError
        ) as error:
            logging.error(error)
            if error != last_error:
                last_error = error
                send_message(bot, error)
        except Exception as error:
            message = ed.UNIVERSAL_ERROR.format(error)
            logging.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
