import sys
import inspect
import logging
from functools import wraps
from typing import Callable, List, TypeVar
from typing_extensions import ParamSpec

from core.config import Settings, settings
from common.logging import get_rotate_logger

_P = ParamSpec('_P')
_R = TypeVar('_R')

# 의존성 주입용 사전
dependency = {}

# 의존성 객체 생성 시작 
if len(sys.argv) > 1 and sys.argv[0] == 'main.py':
    cmd_name = sys.argv[1].replace('-', '_')
    settings.APP_NAME = f'{settings.APP_NAME}.{cmd_name}'
    if settings.APP_NAME_OPTION != '':
        settings.APP_NAME = f'{settings.APP_NAME}.{settings.APP_NAME_OPTION}'

dependency['settings'] = settings

# decorator
def inject(f: Callable[_P, _R]) -> Callable[_P, _R]:
    """
    

    Args:
        f (Callable[_P, _R]): _description_

    Returns:
        Callable[_P, _R]: _description_
    """
    di = dict()
    
    #
    sig = inspect.signature(f)

    # 의존성 사전에서 주입할 의존성이 있는지 확인
    for k, v in sig.parameters.items():
        if k in dependency:
            di[k] = dependency[k]
            
    # 주입된 의존성을 기존 시그니처에서 삭제(반영되지 않음. 삭제 필요)
    new_sig = sig.replace(
        parameters=[
            param.replace(default=None) 
                if param.default is param.empty
                else param
                for param in sig.parameters.values()
                if param.name not in di and param.name != 'log'
        ]
    )
    
    # ParamSpec 문서 확인하여 데코레이터 시그니처 포워딩 방법 확인
    @wraps(f)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        # di 및 di의 기본 값 적용 방법 개선 필요
        # logging의 경우 프로그램 시작시 파일 이름이 결정되면 로거 파일이름 설정에
        # 문제가 발생하므로 함수 실행시점에 로거를 생성하는 방식으로 변경
        if 'additional_token' in kwargs:
            additional_token = kwargs.get('additional_token')
        else:
            additional_token = []
            
        if 'log' in sig.parameters:
            log = get_rotate_logger(
                settings.get_logger_name(additional_token=additional_token),
                settings.get_logging_level(),
                settings.get_rt_log_file_name(additional_token=additional_token),
                settings.RT_LOGGING_FORMAT,
                settings.RT_LOGGING_DTF,
                settings.RT_LOGGING_SUFFIX,
                settings.RT_LOGGING_WHEN
            )
            return f(*args, **di, **kwargs, log=log)
        else:
            return f(*args, **di, **kwargs)
        
    wrapper.__signature__ = new_sig
    return wrapper
    
if __name__ == '__main__':
    
    @inject
    def test(
        test_param: int,
        settings: Settings,
        log: logging.Logger
    ) -> None:
        log.debug(settings)
        log.info(test_param)
        
    print(inspect.signature(test))
    test(100)