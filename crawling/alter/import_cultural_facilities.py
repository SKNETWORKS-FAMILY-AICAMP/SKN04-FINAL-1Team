import pandas as pd

# 유틸 임포트
from import_utils import import_with_address, process_cultural_facility_data

@import_with_address(process_cultural_facility_data)
def import_cultural_facilities():
    """문화시설 데이터 가져오기"""
    all_data = []
    
    # 1. 기본 문화시설 (나혼자, 실내놀이, 실외놀이)
    facility_files = [
        '나혼자 문화시설 데이터.csv',
        '아이랑 실내 놀이 시설 데이터.csv',
        '아이랑 실외 놀이 시설 데이터.csv'
    ]
    
    for file_name in facility_files:
        try:
            df = pd.read_csv(f'./data/문화시설/{file_name}')
            # 서울 데이터만 필터링
            df = df[df['CTPRVN_NM'].str.contains('서울', na=False)]
            
            for _, row in df.iterrows():
                facility = {
                    'facility_name': row['FCLTY_NM'],
                    'facility_type': row['MLSFC_NM'],
                    'area_name': f"{row['FCLTY_ROAD_NM_ADDR']}",
                    'FCLTY_LA': row['FCLTY_LA'],
                    'FCLTY_LO': row['FCLTY_LO']
                }
                all_data.append(facility)
        except Exception as e:
            print(f"파일 처리 중 오류 ({file_name}): {str(e)}")
            continue
    
    # 2. 영화관, 전시관
    other_files = [
        '전국 영화관 시설 데이터.csv',
        '전국 전시관 데이터.csv'
    ]
    
    for file_name in other_files:
        try:
            df = pd.read_csv(f'./data/문화시설/{file_name}')
            # 서울 데이터만 필터링
            df = df[df['CTPRVN_NM'].str.contains('서울', na=False)]
            
            for _, row in df.iterrows():
                try:
                    # 도로명주소와 건물번호 합치기
                    if pd.isna(row.get('RDNMADR_NM')):
                        # 지번 주소 사용
                        full_address = f"{row['SIGNGU_NM']} {row['LEGALDONG_NM']}"
                        if pd.notna(row.get('LNM_ADDR')):  # 지번 주소가 있으면 추가
                            full_address += f" {row['LNM_ADDR']}"
                    else:
                        full_address = row['RDNMADR_NM']
                        if pd.notna(row.get('BULD_NO')):
                            full_address = f"{row['RDNMADR_NM']} {row['BULD_NO']}"
                    
                    # POI_NM과 BHF_NM 합치기
                    if pd.isna(row.get('POI_NM')):  # POI_NM이 없는 경우 건너뛰기
                        continue
                        
                    facility_name = row['POI_NM']
                    if pd.notna(row.get('BHF_NM')):
                        facility_name = f"{row['POI_NM']} {row['BHF_NM']}"
                    
                    facility = {
                        'facility_name': facility_name,
                        'facility_type': row.get('CL_NM', '기타'),
                        'area_name': full_address,
                        'FCLTY_LA': row.get('LC_LA', row.get('FCLTY_LA')),  # 위도
                        'FCLTY_LO': row.get('LC_LO', row.get('FCLTY_LO'))   # 경도
                    }
                    all_data.append(facility)
                except Exception as e:
                    print(f"행 처리 중 오류: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"파일 처리 중 오류 ({file_name}): {str(e)}")
            continue
    
    return all_data

def load_cultural_facilities():
    """문화시설 데이터 로드"""
    all_facilities = []
    
    # 1. 기본 문화시설 (나혼자, 실내놀이, 실외놀이)
    facility_files = [
        '나혼자 문화시설 데이터.csv',
        '아이랑 실내 놀이 시설 데이터.csv',
        '아이랑 실외 놀이 시설 데이터.csv'
    ]
    
    for file_name in facility_files:
        try:
            df = pd.read_csv(f'./data/문화시설/{file_name}')
            for _, row in df.iterrows():
                facility = {
                    'FCLTY_NM': row['FCLTY_NM'],
                    'MLSFC_NM': row['MLSFC_NM'],
                    'CTPRVN_NM': row['CTPRVN_NM'],
                    'SIGNGU_NM': row['SIGNGU_NM'],
                    'LEGALDONG_NM': row['LEGALDONG_NM'],
                    'FCLTY_ROAD_NM_ADDR': row['FCLTY_ROAD_NM_ADDR'],
                    'FCLTY_LA': row['FCLTY_LA'],
                    'FCLTY_LO': row['FCLTY_LO'],
                    'ADIT_DC': row.get('ADIT_DC')
                }
                all_facilities.append(facility)
        except Exception as e:
            print(f"파일 로드 중 오류 ({file_name}): {str(e)}")
            continue
    
    # 2. 영화관, 전시관
    other_files = [
        '전국 영화관 시설 데이터.csv',
        '전국 전시관 데이터.csv'
    ]
    
    for file_name in other_files:
        try:
            df = pd.read_csv(f'./data/문화시설/{file_name}')
            for _, row in df.iterrows():
                facility = {
                    'FCLTY_NM': row['POI_NM'],
                    'MLSFC_NM': row['CL_NM'],
                    'CTPRVN_NM': row['CTPRVN_NM'],
                    'SIGNGU_NM': row['SIGNGU_NM'],
                    'LEGALDONG_NM': row['LEGALDONG_NM'],
                    'FCLTY_ROAD_NM_ADDR': f"{row['RDNMADR_NM']} {row['BULD_NO']}",
                    'FCLTY_LA': row['LC_LA'],
                    'FCLTY_LO': row['LC_LO'],
                    'ADIT_DC': None
                }
                all_facilities.append(facility)
        except Exception as e:
            print(f"파일 로드 중 오류 ({file_name}): {str(e)}")
            continue
    
    return all_facilities

if __name__ == "__main__":
    import_cultural_facilities() 