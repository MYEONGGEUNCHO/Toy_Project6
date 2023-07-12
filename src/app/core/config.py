import os
import logging

from binascii import a2b_base64
from typing import Any, Set, Dict, List, Optional, Tuple, TypeVar
from pydantic import ( 
    BaseModel
    , BaseSettings
    , Field
    , AnyHttpUrl
    , EmailStr
    , PostgresDsn
    , validator
)
from urllib.parse import quote
from urllib.parse import quote_plus as urlquote

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
LOG_DIR = os.path.join(SRC_DIR, 'logs')



class Settings(BaseSettings):
    DEBUG: bool = True
    
    APP_NAME: str = 'Toy_Project6'
    
    # 빈문자열('')이 아니라면 로깅 파일 이름에 추가
    APP_NAME_OPTION: str = ''
    
    # COMMON Utils 관련 환경설정
    DATE_FMT = [
        '%Y%m%d',
        '%Y-%m-%d',
        '%Y/%m/%d'
    ]
    
    # Logging
    LOGGING_LOGGER_NAME: str = 'Toy_Project6_LOGGER'
    LOGGING_PATH: str = LOG_DIR
    LOGGING_LEVEL: str = 'DEBUG'
    LOGGING_FORMAT: str = '[$RED$BOLD%(levelname)s$RESET %(asctime)s %(processName)s %(filename)s > %(funcName)s:%(lineno)d] %(message)s'

    # rotate logger 환경설정
    RT_LOGGING_FILE_NAME: str = "data.log"
    RT_LOGGING_SUFFIX: str = "%Y%m%d"
    # RT_LOGGING_FORMAT: str = "%(levelname)s||%(asctime)s||%(message)s"
    RT_LOGGING_FORMAT: str = "{levelname:<8s}||{asctime}||{message}"
    RT_LOGGING_DTF: str = "%Y-%m-%d %H:%M:%S"
    RT_LOGGING_WHEN: str = "midnight"
    
    def get_logger_name(self, additional_token: List[str] = []) -> str:
        """_summary_

        Args:
            additional_token (List[str], optional): _description_. Defaults to [].

        Returns:
            str: _description_
        """
        general = f'{self.LOGGING_LOGGER_NAME}'
        additional = '.'.join(additional_token)

        if additional == '':
            return general
        else:
            return f'{general}.{additional}'
    
    def get_rt_log_file_name(self, additional_token: List[str] = []) -> str:        
        """_summary_

        Args:
            additional_token (List[str], optional): _description_. Defaults to [].

        Returns:
            str: _description_
        """
        general = f'{self.APP_NAME}.{self.RT_LOGGING_FILE_NAME}'
        additional = '.'.join(additional_token)

        if additional != '':
            general = f'{additional}.{general}'
            
        return os.path.join(self.LOGGING_PATH, general)
    
    def get_logging_level(self) -> int:
        """Setting에 설정된 LOGGING_LEVEL 문자열을 바탕으로 정수 값 반환

        Returns:
            int: LOGGING_LEVEL
        """
        return logging.getLevelName(self.LOGGING_LEVEL)
    
    
    # RDBMS
    ## MariaDB
    DB_URI_TYPE: str = 'MARIA'
    DB_URI_TEMPLATE: Dict[str, str] = {
        'MARIA' : 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4'
    }
    
    DB_CONNECTION_INFO: Dict[str, Dict[str, str]] = {
        'MARIA': {
            'user': 'root'
            , 'pwd': '1234'
            , 'host': 'localhost'
            , 'port': '3306'
            , 'database': 'test'
        }
    }
    
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = -1

    def get_db_uri(
        self,
        uri_type: str,
        user: str,
        pwd: str,
        host: str,
        port: str,
        database: str
    
    ) -> str:
        """대상 db 이름을 입력받아 db 연결을 위한 URI 반환

        Args
        ----
            uri_type (str): _description_
            user (str): db_user
            pwd (str): db_pwd
            host (str): db_host
            port (str): db_port
            database (str): 

        Returns
        -------
            str: 대상 DB URI        
        """
        
        
        print(self.DB_URI_TEMPLATE[uri_type].format(
            user,
            quote(pwd),
            host,
            port,
            database
        ))
        return self.DB_URI_TEMPLATE[uri_type].format(
            user,
            quote(pwd),
            host,
            port,
            database
        )
    
    # NoSQL
    ## MongoDB
    MONGO_HOST: str = 'localhost'
    MONGO_PORT: int = 27017
    MONGO_USER: str = 'root'
    MONGO_PWD: str = '1234'
    
    class Config:
        env_prefix = 'Toy_Project6'
        
settings = Settings()
    
    