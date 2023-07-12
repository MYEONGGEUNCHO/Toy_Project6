"""
LOGGING MODULE
날짜 기반 이름으로 파일을 생성하는 로거 클래스 모듈

"""
from datetime import datetime
import logging
import socket
import time
import os
import sys

from logging import Logger
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Dict, List
from uuid import uuid4

from kafka import KafkaProducer

from core.config import settings, Settings


RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

COLORS = {
    'YELLOW': YELLOW,
    'WHITE': WHITE,
    'BLUE': BLUE,
    'YELLOW': YELLOW,
    'RED': RED
}

def formatter_message(message, use_color = True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
        for k, v in COLORS.items():
            message = message.replace(f"${k}", COLOR_SEQ % (30 + v))
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color = True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, *args, suffix: str = '', **kwargs) -> None:
        self.suffix = suffix
        super().__init__(*args, **kwargs)

    def doRollover(self):
        """
        Built-in TimedRotatinFileHandler을 상속받아 파일 이름을 커스터마이징한 
        핸들러 클래스
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        head, tail = os.path.split(self.baseFilename)
        tail_base = os.path.basename(tail)
        dfn = self.rotation_filename( os.path.join(head, tail_base) + "." +
                                     time.strftime(self.suffix, timeTuple) + ".log")
        if os.path.exists(dfn):
            os.remove(dfn)
        self.rotate(self.baseFilename, dfn)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.stream = self._open()
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt


def get_rotate_logger(
    logger_name: str,
    logger_level: int,
    logger_file_name: str,
    logger_format: str,
    logger_date_format: str,
    handler_suffix: str,
    rotate_when: str,
    encoding: str = 'utf-8',
) -> Logger:

    """로거 팩토리 함수.
    정해진 매개변수를 입력하여 로거를 생성.

    Args:
        logger_name (str): 로거 이름
        logger_level (int): 로거 수준(DEBUG, WARN, INFO, ERROR, ...)
        logger_file_name (str): 로거 데이터 저장 파일 이름
        logger_format (str): 로깅 포맷
        logger_date_format (str): 로깅 데이트 포맷
        handler_suffix (str): 로거 데이터 저장 파일 접미사
        rotate_when (str): 파일 롤오버 시점
        encoding (str, optional): 로거 데이터 파일 인코딩. 기본값은 'utf-8'.

    Returns:
        Logger: 수정된 TimedRotatingFileHandler 반환
    """
    
    rotate_logger = logging.getLogger(logger_name)
    rotate_logger.setLevel(logger_level)
    
    handler = CustomTimedRotatingFileHandler(
        logger_file_name, # settings.get_rt_log_file_name(),
        suffix=handler_suffix, #suffix=settings.RT_LOG_SUFFIX,
        when=rotate_when, # when=settings.RT_LOG_WHEN,
        encoding=encoding
    )

    formatter = logging.Formatter(
        logger_format, # settings.RT_LOG_FORMAT,
        datefmt=logger_date_format, # datefmt=settings.RT_LOG_DTF
        style='{'
    )

    handler.setFormatter(formatter)

    # print(len(rotate_logger.handlers),rotate_logger.handlers)
    if len(rotate_logger.handlers) == 0:
        rotate_logger.addHandler(handler)

    return rotate_logger


def get_logger(token: List[str] = []):
    """get_rotate_logger를 일반 파라매터로 생성"""

    return get_rotate_logger(
        settings.get_logger_name(additional_token=token),
        settings.get_logging_level(),
        settings.get_rt_log_file_name(additional_token=token),
        settings.RT_LOGGING_FORMAT,
        settings.RT_LOGGING_DTF,
        settings.RT_LOGGING_SUFFIX,
        settings.RT_LOGGING_WHEN
    )


class KafkaLoggingHandler(logging.Handler):

    def __init__(self, producer: KafkaProducer, topic: str):
        logging.Handler.__init__(self)
        self.producer = producer
        self.topic = topic

    def generate_msg_dict(self, name: str, msg: str, lvl: str) -> Dict[str, Any]:
        """
        로그 메시지를 Kafka용 딕셔너리 객체로 변환

        Parameters
        ----------
        - `name: str`, 로거 이름
        - `msg: str`, 로그 메시지

        Returns
        -------
        - `: Dict[str, Any]`, Kafka log topic 저장용 객체

        """

        record = {}
        record['name'] = name
        record['timestamp'] = str(datetime.now().astimezone().isoformat(timespec='seconds'))
        record['uuid'] = str(uuid4())
        record['source'] = {}
        record['source']['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        record['source']['server_ip'] = socket.gethostbyname(socket.gethostname())
        record['source']['loglevel'] = lvl
        record['source']['message'] = msg
    
        return record


    def emit(self, record: logging.LogRecord):
        if record.name == 'kafka':
            return
        try:
            msg = self.format(record)
            value = self.generate_msg_dict(record.name.lower(), msg, record.levelname)
            self.producer.send(self.topic, value=value)
        except:
            import traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            del ei

    def close(self):
        self.producer.close()
        logging.Handler.close(self)


# def generate_kafka_logger(logger_name: str, logger_level: int, logger_file_name: str,
#         logger_format: str, logger_date_format: str, handler_suffix: str,
#         rotate_when: str, encoding: str = 'utf-8') -> Logger:
#     """
#     카프카로깅용 핸들러
#     """

#     kafka_logger = logging.getLogger(logger_name)
#     kafka_logger.setLevel(logger_level)

#     handler = KafkaLoggingHandler(generate_producer(), 'log')


#     formatter = logging.Formatter(
#         logger_format, # settings.RT_LOG_FORMAT,
#         datefmt=logger_date_format, # datefmt=settings.RT_LOG_DTF
#         style='{'
#     )

#     handler.setFormatter(formatter)
#     if len(kafka_logger.handlers) == 0:
#         kafka_logger.addHandler(handler)
#     kafka_logger.addHandler(handler)

#     return kafka_logger


# def get_kafka_logger(token: List[str] = []):
#     """get_rotate_logger를 일반 파라매터로 생성"""
#     defualt_token = ['kafka']
#     token += defualt_token
#     return generate_kafka_logger(
#         settings.get_logger_name(additional_token=token),
#         settings.get_logging_level(),
#         settings.get_rt_log_file_name(additional_token=token),
#         settings.RT_LOGGING_FORMAT,
#         settings.RT_LOGGING_DTF,
#         settings.RT_LOGGING_SUFFIX,
#         settings.RT_LOGGING_WHEN
#     )