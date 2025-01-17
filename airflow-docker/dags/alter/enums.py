import enum

class SeoulDistrictCode(enum.Enum):
    """서울시 구별 법정동 코드"""
    강남구 = '1168000000'
    강동구 = '1174000000'
    강북구 = '1130500000'
    강서구 = '1150000000'
    관악구 = '1162000000'
    광진구 = '1121500000'
    구로구 = '1153000000'
    금천구 = '1154500000'
    노원구 = '1135000000'
    도봉구 = '1132000000'
    동대문구 = '1123000000'
    동작구 = '1159000000'
    마포구 = '1144000000'
    서대문구 = '1141000000'
    서초구 = '1165000000'
    성동구 = '1120000000'
    성북구 = '1129000000'
    송파구 = '1171000000'
    양천구 = '1147000000'
    영등포구 = '1156000000'
    용산구 = '1117000000'
    은평구 = '1138000000'
    종로구 = '1111000000'
    중구 = '1114000000'
    중랑구 = '1126000000'

class Gender(enum.Enum):
    """성별"""
    M = "M" #남
    F = "F" #여
    O = "O" #기타

class MessageType(enum.Enum):
    """메시지 유형"""
    USER = "user" #사용자
    BOT = "bot" #봇

class NoticeStatus(enum.Enum):
    """공지사항 상태"""
    ACTIVE = "active" #활성
    INACTIVE = "inactive" #비활성

class MoveInType(enum.Enum):
    """입주가능유형 코드"""
    IMMEDIATE = "30063INSTANT" #즉시입주
    INMONTH = "30063INMONTH" #개월 이내
    AFTERMONTH = "30063AFTERMONTH" #개월 이후
    AFTER = "30063AFTER" #이후
    NULL = ""

class PropertyType(enum.Enum):
    """매물 타입"""
    APARTMENT = "30000C01" #아파트
    OFFICETEL = "30000C02" #오피스텔
    HOUSE = "30000C03" #분양권
    VILLA = "30000C04" #주택
    LAND = "30000C05" #토지
    ONE_ROOM = "30000C06" #원룸
    COMMERCIAL = "30000C07" #상가
    OFFICE = "30000C08" #사무실
    FACTORY = "30000C09" #공장
    REDEVELOPED = "30000C10" #재개발
    BUILDING = "30000C11" #건물

# 추가
class MoveInFeeType(enum.Enum):
    """관리비 포함 코드"""
    ELECTRICITY = "30071ELECTRICITY" #전기료
    GAS = "30071GAS" #가스
    WATER = "30071WATER" #수도
    INTERNET = "30071INTERNET" #인터넷
    TV = "30071TV" #TV

# 추가
class MoveInMonthType(enum.Enum):
    """입주가능일 코드"""
    EARLY = "30064EARLY" #초순
    MID = "30064MID" #중순
    LATE = "30064LATE" #하순

class BuildingFeatureType(enum.Enum):
    """건축물 특징"""
    NEWBUILD = "30072NEWBUILD" #신축
    FULLOPTION = "30072FULLOPTION" #풀옵션
    MAINROAD = "30072MAINROAD" #큰길가
    PARKING = "30072PARKING" #주차가능
    ELEVATOR = "30072ELEVATOR" #엘리베이터
    PET = "30072PET" #애완동물

class BuildingUseType(enum.Enum):
    """건축물용도"""
    DUPLEX = "30073USG01" #단독주택
    COMPOUND = "30073USG02" #공동주택
    LIVING_FACILITY_1 = "30073USG03" #제1종 근린생활시설
    LIVING_FACILITY_2 = "30073USG04" #제2종 근린생활시설
    CULTURAL_FACILITY = "30073USG05" #문화 및 집회시설
    RELIGIOUS_FACILITY = "30073USG06" #종교시설
    SALE_FACILITY = "30073USG07" #판매시설
    TRANSPORT_FACILITY = "30073USG08" #운수시설
    MEDICAL_FACILITY = "30073USG09" #의료시설
    EDUCATION_FACILITY = "30073USG10" #교육연구시설
    ELDERLY_FACILITY = "30073USG11" #노유자(노인 및 어린이)시설
    LEARNING_FACILITY = "30073USG12" #수련시설
    EXERCISE_FACILITY = "30073USG13" #운동시설
    BUSINESS_FACILITY = "30073USG14" #업무시설
    ACCOMMODATION_FACILITY = "30073USG15" #숙박시설
    ENTERTAINMENT_FACILITY = "30073USG16" #위락시설
    FACTORY = "30073USG17" #공장
    WAREHOUSE = "30073USG18" #창고시설
    HAZARDOUS_MATERIAL_FACILITY = "30073USG19" #위험물 저장 및 처리 시설
    CAR_RELATED_FACILITY = "30073USG20" #자동차 관련 시설
    ANIMAL_AND_PLANT_FACILITY = "30073USG21" #동물 및 식물 관련 시설
    RESOURCE_RECYCLING_FACILITY = "30073USG22" #자원순환 관련 시설
    CORRECTION_AND_MILITARY_FACILITY = "30073USG23" #교정 및 군사 시설
    BROADCASTING_AND_COMMUNICATION_FACILITY = "30073USG24" #방송통신시설
    POWER_GENERATION_FACILITY = "30073USG25" #발전시설
    CEMETERY_FACILITY = "30073USG26" #묘지 관련 시설
    TOURISM_RECREATION_FACILITY = "30073USG27" #관광 휴게시설
    FUNERAL_FACILITY = "30073USG28" #장례시설
    CAMPGROUND_FACILITY = "30073USG29" #야영장 시설
    UNREGISTERED_BUILDING = "30073USG30" #미등기건물
    OTHER_SETTLEMENT = "30073USG31" #그 밖에 토지의 정착물
    NULL = ""

class HeatingType(enum.Enum):
    """난방방식 유형 코드"""
    SEPARATE = "30081SEPARATE" # 개별난방
    CENTER = "30081CENTER" # 중앙난방
    LOCAL = "30081LOCAL" # 지역난방
    NULL = ""

class HeatingFuel1(enum.Enum):
    """난방연료 유형 코드"""
    GAS = "30082GAS" # 도시가스
    HEAT = "30082HEAT" # 열병합
    OIL = "30082OIL" # 기름
    ELECTRIC = "30082ELECTRIC" # 전기
    NIGHT = "30082NIGHT" # 심야전기
    SUN = "30082SUN" # 태양열
    LPG = "30082LPG" # LPG

# class HeatingType2(enum.Enum):
#     """난방방식 유형 코드"""
#     SEPARATE = "20003SEPARATE" #개별난방
#     CENTER = "20003CENTER" #중앙난방
#     LOCAL = "20003LOCAL" #지역난방
#     SEPARATECOLD = "20003SEPARATECOLD" #개별냉난방
#     CENTERCOLD = "20003CENTERCOLD" #중앙냉난방
#     NONE = "20003NONE" #선택안함

class HeatingFuel2(enum.Enum):
    """난방연료 선택"""
    GAS = "20005GAS" #도시가스
    OIL = "20005OIL" #기름보일러
    ELECTRIC = "20005ELECTRIC" #전기보일러
    NIGHT = "20005NIGHT" #심야전기
    LPG = "20005LPG" #LPG
    HEAT = "20005HEAT" #열병합
    COAL = "20005COAL" #연탄보일러
    SUN = "20005SUN" #태양열
    ETC = "20005ETC" #기타

class DirectionType(enum.Enum):
    """방향 코드"""
    EAST = "30002EAST" #동
    WEST = "30002WEST" #서
    SOUTH = "30002SOUTH" #남
    NORTH = "30002NORTH" #북
    NORTHEAST = "30002NORTHEAST" #북동
    SOUTHEAST = "30002SOUTHEAST" #남동
    NORTHWEST = "30002NORTHWEST" #북서
    SOUTHWEST = "30002SOUTHWEST" #남서

class EntranceType(enum.Enum):
    """현관유형"""
    STAIRWAY = "30003STAIRWAY" #계단식
    HALLWAY = "30003HALLWAY" #복도식
    COMPOSITE = "30003COMPOSITE" #복합식

class RoomType(enum.Enum):
    """방구조 선택"""
    OPEN = "30004OPEN" #오픈형
    SPLIT = "30004SPLIT" #분리형

class Category1(enum.Enum):
    """카테고리1"""
    REDEVELOPED = "30010C020" #재개발
    HOUSE = "30010C021" #주택
    ONE_ROOM = "30010C022" #원룸
    HOUSE_RESIDENTIAL = "30010C023" #빌라/연립
    OFFICE = "30010C024" #사무실
    COMMERCIAL = "30010C025" #상가점포
    KNOWLEDGE = "30010C026" #지식산업센터
    BUILDING = "30010C027" #빌당/건물
    ACCOMMODATION = "30010C028" #숙박/콘도
    ETC = "30010C029" #기타
    COMMERCIAL_BUILDING = "30010C030" #상가건물
    FACTORY = "30010C031" #공장/창고
    LAND = "30010C032" #토지

class NaverSubCategory(enum.Enum):
    """네이버 부동산 서브카테고리 코드"""
    APARTMENT = "30001SC011" #아파트
    COMPOUND = "30001SC012" #주상복합
    REBUILD = "30001SC013" #재건축
    OFFICETEL = "30001SC021" #오피스텔
    APARTMENT_SALE = "30001SC031" #아파트 분양권
    OFFICETEL_SALE = "30001SC032" #오피스텔 분양권
    COMPOUND_SALE = "30001SC033" #주상복합 분양권
    APARTMENT_HOUSE = "30001SC041" #주택-빌라/연립
    HOUSE_DUPLEX = "30001SC042" #주택-단독/다가구
    HOUSE_RESIDENTIAL = "30001SC043" #주택-전원주택
    HOUSE_COMMERCIAL = "30001SC044" #주택-상가주택
    HOUSE_KOREAN = "30001SC045" #주택-한옥주택
    LAND = "30001SC051" #토지/임야
    ROOM = "30001SC061" #원룸/방
    COMMERCIAL = "30001SC071" #상가/상가점포
    OFFICE = "30001SC081" #사무실
    FACTORY = "30001SC091" #공장-공장/창고
    FACTORY_KNOWLEDGE = "30001SC092" #공장-지식산업센터
    REDEVELOPED = "30001SC101" #재개발
    BUILDING_BUILDING = "30001SC111" #건물-빌딩/건물
    BUILDING_COMMERCIAL = "30001SC112" #건물-상가건물
    BUILDING_ACCOMMODATION = "30001SC113" #건물-숙박/콘도
    BUILDING_ETC = "30001SC114" #건물-기타

class UseType(enum.Enum):
    """용도지역"""
    RESIDENTIALEXCLUSIVE1 = "30032C010" #제1종전용주거지역
    RESIDENTIALEXCLUSIVE2 = "30032C011" #제2종전용주거지역
    RESIDENTIALGENERAL1 = "30032C012" #제1종일반주거지역
    RESIDENTIALGENERAL2 = "30032C013" #제2종일반주거지역
    RESIDENTIALGENERAL3 = "30032C014" #제3종일반주거지역
    SEMIRESIDENTIAL = "30032C015" #준주거지역
    CENTRALCOMMERCIAL = "30032C016" #중심상업지역
    GENERALCOMMERCIAL = "30032C017" #일반상업지역
    NEIGHBORHOODCOMMERCIAL = "30032C018" #근린상업지역
    DISTRIBUTIONCOMMERCIAL = "30032C019" #유통상업지역
    EXCLUSIVEINDUSTRIAL = "30032C020" #전용공업지역
    GENERALINDUSTRIAL = "30032C021" #일반공업지역
    SEMIINDUSTRIAL = "30032C022" #준공업지역
    CONSERVATIONGREEN = "30032C023" #보전녹지지역
    PRODUCTIONGREEN = "30032C024" #생산녹지지역
    NATURALGREEN = "30032C025" #자연녹지지역
    CONSERVATIONMANAGEMENT = "30032C026" #보전관리지역
    PRODUCTIONMANAGEMENT = "30032C027" #생산관리지역
    PLANNEDMANAGEMENT = "30032C028" #계획관리지역
    AGRICULTURALFOREST = "30032C029" #농림지역
    NATURALENVIRONMENTCONSERVATION = "30032C030" #자연환경보전지역
    ETC = "30032C999" #기타

class LandUse(enum.Enum):
    """토지 이용"""
    LANDUSE = "30036C010" #국토이용
    CITYPLANNING = "30036C011" #도시계획
    BUILDINGPERMIT = "30036C012" #건축허가
    LANDTRANSACTIONPERMIT = "30036C013" #토지거래허가
    ACCESSROAD = "30036C014" #진입도로

class FloorExposureType(enum.Enum):
    """층노출방식"""
    FLOOREXPOSURE = "30044C010" #층노출
    HIGH_MID_LOW = "30044C011" #고/중/저 노출

class SaleType(enum.Enum):
    """분양타입"""
    GENERAL = "30047C010" #일반분양
    COOPERATIVE = "30047C011" #조합원

class CoolingType(enum.Enum):
    """시설-냉방"""
    WALL = "30076WALL" #벽걸이에어컨
    STAND = "30076STAND" #스탠드에어컨
    TOP = "30076TOP" #천장에어컨

class LivingFacilityType(enum.Enum):
    """시설 유형 코드(생활)"""
    BED = "30077BED" #침대
    DESK = "30077DESK" #책상
    WARDROBE = "30077WARDROBE" #옷장
    CLOSET = "30077CLOSET" #붙박이장
    DINNINGTABLE = "30077DINNINGTABLE" #식탁
    SOFA = "30077SOFA" #소파
    SHOESBOX = "30077SHOESBOX" #신발장
    REFRIGERATOR = "30077REFRIGERATOR" #냉장고
    WASHER = "30077WASHER" #세탁기
    DRYER = "30077DRYER" #건조기
    SHOWERBOOTH = "30077SHOWERBOOTH" #샤워부스
    BATHTUB = "30077BATHTUB" #욕조
    BIDET = "30077BIDET" #비데
    SINK = "30077SINK" #싱크대
    DISHWASHER = "30077DISHWASHER" #식기세척기
    GASRANGE = "30077GASRANGE" #가스레인지
    INDUCTIONRANGE = "30077INDUCTIONRANGE" #인덕션레인지
    ELECTRONICRANGE = "30077ELECTRONICRANGE" #전자레인지
    GASOVEN = "30077GASOVEN" #가스오븐
    TV = "30077TV" #TV

class SecurityType(enum.Enum):
    """시설 유형 코드(보안)"""
    GUARD = "30078GUARD" #경비원
    VIDEOPHONE = "30078VIDEOPHONE" #비디오폰
    INTERPHONE = "30078INTERPHONE" #인터폰
    CARDKEY = "30078CARDKEY" #카드키
    CCTV = "30078CCTV" #CCTV
    PRIVATE = "30078PRIVATE" #사설경비
    DOOR = "30078DOOR" #현관보안
    WINDOW = "30078WINDOW" #방범창

class FacilityType(enum.Enum):
    """시설 유형 코드(기타)"""
    ELEVATOR = "30079ELEVATOR" #엘리베이터
    FIREALARM = "30079FIREALARM" #화재경보기
    VERANDA = "30079VERANDA" #베란다
    TERRACE = "30079TERRACE" #테라스
    YARD = "30079YARD" #마당
    UNMANNEDBOX = "30079UNMANNEDBOX" #무인택배함

class DirectionType2(enum.Enum):
    """방향 기준"""
    BDRM = "30086BDRM" #안방
    LVRM = "30086LVRM" #거실

class BuildingDateType(enum.Enum):
    """건축물일자 유형"""
    USEAPPROVAL = "30087CDY01" #사용승인일
    USEINSPECTION = "30087CDY02" #사용검사일
    COMPLETIONPERMIT = "30087CDY03" #준공인가일

class LoanAvailability(enum.Enum):
    """대출가능여부"""
    NO_LOAN = "30053C010"     # 융자금 없음
    LOAN_UNDER_30 = "30053C011"    # 융자금 시세대비 30%미만
    LOAN_OVER_30 = "30053C012" # 시세대비 30%이상
    NULL = ""

class TransactionType(enum.Enum):
    """거래구분"""
    SALE = "30051A1" # 매매
    YEARLY = "30051B1" # 전세
    MONTHLY = "30051B2" # 월세
    SHORT_TERM_RENT = "30051B3" # 단기임대
