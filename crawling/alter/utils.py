import logging
from typing import List, Callable
from datetime import datetime
import time
from functools import wraps
import os

def setup_logger(name: str, log_file: str, level=logging.INFO):
    """로거 설정 함수"""
    # 로그 디렉토리 생성
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger

def batch_process(items: List, batch_size: int, process_func: Callable, logger: logging.Logger):
    """배치 처리 유틸리티 함수"""
    total_items = len(items)
    processed = 0
    failed_items = []
    
    for i in range(0, total_items, batch_size):
        batch = items[i:i + batch_size]
        batch_start_time = time.time()
        
        try:
            process_func(batch)
            processed += len(batch)
            
            batch_end_time = time.time()
            logger.info(
                f"Processed batch {i//batch_size + 1}: "
                f"{len(batch)} items in {batch_end_time - batch_start_time:.2f} seconds. "
                f"Progress: {processed}/{total_items}"
            )
            
        except Exception as e:
            failed_items.extend(batch)
            logger.error(f"Batch processing failed: {str(e)}")
            
        # 배치 처리 사이에 잠시 대기
        time.sleep(1)
    
    return failed_items

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """실패 시 재시도 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise e
                    time.sleep(delay)
            return None
        return wrapper
    return decorator 