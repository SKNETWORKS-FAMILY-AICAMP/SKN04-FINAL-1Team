from sqlalchemy.orm import Session
from import_subway_stations import import_subway_stations
from import_cultural_facilities import import_cultural_facilities
from import_cultural_festivals import import_cultural_festivals
from import_crime_stats import import_crime_stats
from import_population_stats import import_population_stats
from models import Base
from import_utils import create_engine_and_session

def import_all_data():
    try:
        engine, session = create_engine_and_session()
        
        # Base.metadata.create_all(engine)  # 테이블 생성
        
        # 각 데이터 임포트 함수에 session 전달
        import_subway_stations(session)
        import_cultural_facilities(session)
        import_cultural_festivals(session)
        import_crime_stats(session)
        import_population_stats(session)
        
        session.close()
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        print("상세 에러:")
        import traceback
        print(traceback.format_exc())
        return

if __name__ == "__main__":
    import_all_data() 