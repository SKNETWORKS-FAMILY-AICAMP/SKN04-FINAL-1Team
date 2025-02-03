class DataProcessingError(Exception):
    """데이터 처리 관련 기본 예외"""
    pass

class APIError(DataProcessingError):
    """API 관련 오류"""
    def __init__(self, api_name: str, message: str):
        self.api_name = api_name
        self.message = message
        super().__init__(f"{api_name} API 오류: {message}")

class DatabaseError(DataProcessingError):
    """데이터베이스 관련 오류"""
    def __init__(self, operation: str, message: str):
        self.operation = operation
        self.message = message
        super().__init__(f"데이터베이스 {operation} 오류: {message}") 