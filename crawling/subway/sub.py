import json
import pandas as pd

def convert_seoul_subway_to_csv():
    # JSON 파일 읽기
    with open('subway.json', 'r', encoding='utf-8') as file:
        subway_data = json.load(file)
    
    # 서울특별시 데이터만 필터링
    seoul_stations = [station for station in subway_data if station['local1'] == '서울특별시']
    
    # 데이터 변환을 위한 리스트 생성
    transformed_data = []
    
    for station in seoul_stations:
        # 각 호선 정보를 문자열로 변환
        lines_info = [f"{line['short_name']}호선({line['color']})" for line in station['lines']]
        lines_str = ', '.join(lines_info)
        
        station_info = {
            '역ID': station['id'],
            '역이름': station['name'],
            '설명': station['description'],
            '지하철권역': station['subway_area'] or '',
            '위도': station['lat'],
            '경도': station['lng'],
            '호선정보': lines_str
        }
        transformed_data.append(station_info)
    
    # DataFrame 생성 및 CSV 저장
    df = pd.DataFrame(transformed_data)
    
    # 역이름 기준으로 정렬
    df = df.sort_values('역이름')
    
    df.to_csv('seoul_subway_stations.csv', index=False, encoding='utf-8-sig')
    print(f"서울특별시의 총 {len(transformed_data)}개의 역 정보가 seoul_subway_stations.csv 파일로 저장되었습니다.")

    # 호선별 역 수 출력
    print("\n호선별 역 수:")
    line_counts = {}
    for station in seoul_stations:
        for line in station['lines']:
            line_name = line['short_name']
            line_counts[line_name] = line_counts.get(line_name, 0) + 1
    
    for line, count in sorted(line_counts.items()):
        print(f"{line}호선: {count}개 역")

if __name__ == "__main__":
    convert_seoul_subway_to_csv()