import logging
from functools import wraps
import time
from airflow.models import Variable
from contextlib import contextmanager
from typing import Generator, Any
import os

def setup_logger(name, log_file, level=logging.INFO):
    """로거 설정"""
    # 로그 디렉토리 생성
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 파일 핸들러 추가
    handler = logging.FileHandler(log_file)
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(handler)
    
    return logger

# 기본 로거 설정
main_logger = setup_logger('alter_main', 'logs/alter_main.log')
error_logger = setup_logger('alter_error', 'logs/alter_error.log', level=logging.ERROR)
db_logger = setup_logger('alter_db', 'logs/alter_db.log')

def retry_on_failure(max_attempts=3, delay=1):
    """재시도 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        error_logger.error(f"최대 시도 횟수 초과: {str(e)}")
                        raise
                    error_logger.warning(f"시도 {attempt + 1} 실패, 재시도 중: {str(e)}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def get_api_key(key_name):
    """Airflow Variable에서 API 키 가져오기"""
    try:
        return Variable.get(key_name)
    except Exception as e:
        error_logger.error(f"API 키 '{key_name}' 로드 실패: {str(e)}")
        raise 

@contextmanager
def timing_context(operation_name: str) -> Generator[None, Any, None]:
    """작업 시간 측정 컨텍스트 매니저"""
    start_time = time.time()
    try:
        yield
    finally:
        elapsed_time = time.time() - start_time
        main_logger.info(f"{operation_name} 완료: {elapsed_time:.2f}초 소요")

def batch_process(items, batch_size, process_func, logger=None):
    """배치 처리 유틸리티"""
    if logger is None:
        logger = main_logger
        
    total = len(items)
    failed_items = []
    
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        try:
            process_func(batch)
            logger.info(f"Processed batch {i//batch_size + 1}/{(total-1)//batch_size + 1}")
        except Exception as e:
            logger.error(f"Failed to process batch: {str(e)}")
            failed_items.extend(batch)
            
    return failed_items

class BatchProcessor:
    """배치 처리 클래스"""
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.current_batch = []

    def add(self, item):
        self.current_batch.append(item)
        if len(self.current_batch) >= self.batch_size:
            self.process_batch()

    def process_batch(self):
        if self.current_batch:
            with timing_context(f"{len(self.current_batch)}개 아이템 처리"):
                # 실제 처리 로직
                self.current_batch = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.process_batch()  # 남은 배치 처리 