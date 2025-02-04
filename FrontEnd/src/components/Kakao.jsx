import '../styles/Kakao.css';
import Sidebar from "./Sidebar";
import { useEffect, useState, useRef } from "react";
import ErrorBoundary from './ErrorBoundary';
import DetailModal from './DetailModal.jsx';

export default function Kakao() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedMarker, setSelectedMarker] = useState(null);

  const mapRef = useRef(null);
  const kakaoMapRef = useRef(null);

  useEffect(() => {
    window.openDetailModal = (markerData) => {
      setSelectedMarker(markerData);
      setIsDetailModalOpen(true);
    };
  }, []);

  const closeDetailModal = () => {
    setIsDetailModalOpen(false);
  };

  useEffect(() => {
    if (!mapRef.current) {
      console.error("맵 컨테이너가 존재하지 않습니다.");
      setError(new Error("맵 컨테이너가 존재하지 않습니다."));
      setLoading(false);
      return;
    }

    if (kakaoMapRef.current) {
      setLoading(false);
      return;
    }

    const dummyMarkers = [
      {
        name: "서초푸르지오써밋",
        latitude: 37.501493,
        longitude: 127.0217076,
        deposit: 980000000,
        monthly_rent: 3000,
        address: '서울 서초구 서운로 201',
        buildingCoverage: '18%',
        floorAreaRatio: '299%',
        apartmentNumber: '907 세대',
        floor: '11층/35층',
        area: '80A㎡, 81C㎡, 81B㎡, 100B㎡, 100A㎡, 112A㎡, 113B㎡, 130B㎡, 130A㎡, 137A㎡, 138C㎡, 138B㎡, 149㎡, 159A㎡, 160B㎡',
        bathroom: '1개',
        room: '3개',
        description: `상담 02-534-8949 / 문의 010-4355-0030

◑ 매물 정보 ◑
◈ 전세 금액: 10억 
◈ 2025년 1월 입주 가능
◈ 50평, 방 5개 욕실 2개 
◈ 대형 거실과 넓은 침실
◈ 구조 좋은 남향
◈ 관리비 약 40만원
◈ 신논현역, 언주역 도보 10분 거리
◈ 쾌적하고 조용한 1동 아파트

◐중개사 정보◑
등록번호11650-2023-00068 (서초구)
대표/공인중개사, 매경부동산자산관리사, 빌딩관리사1급 
저희는 손님 유도 광고나 허위매물·과장 광고는 하지 않습니다.
기타 궁금하신 사항은 전화 주시면 친절히 응대 도와드리겠습니다.
상 담 02-534-8949 / 문 의 010-4355-0030
감사합니다.`,
        rental_type: "MONTHLY",
        move_in_type: "AFTER"
      }
    ];

    const loadKakaoMap = () => {
      if (!window.kakao || !window.kakao.maps) {
        const script = document.createElement('script');
        script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=14184ad2e38efd5cb6898242be23f625&autoload=false&libraries=services`;
        script.async = true;
        script.onload = () => {
          window.kakao.maps.load(() => {
            try {
              kakaoMapRef.current = initializeMap(dummyMarkers);
              setLoading(false);
            } catch (err) {
              console.error("카카오맵 초기화 중 오류 발생:", err);
              setError(err);
              setLoading(false);
            }
          });
        };
        script.onerror = () => {
          console.error("카카오맵 스크립트 로드 실패");
          setError(new Error("카카오맵 스크립트 로드 실패"));
          setLoading(false);
        };
        document.head.appendChild(script);
      } else {
        window.kakao.maps.load(() => {
          try {
            kakaoMapRef.current = initializeMap(dummyMarkers);
            setLoading(false);
          } catch (err) {
            console.error("카카오맵 초기화 중 오류 발생:", err);
            setError(err);
            setLoading(false);
          }
        });
      }
    };

    const initializeMap = (markersData) => {
      if (markersData.length === 0) {
        console.error('마커 데이터가 없습니다.');
        return null;
      }

      const container = mapRef.current;

      if (!container) {
        console.error('맵 컨테이너가 없어요:', container);
        return null;
      }

      const options = {
        center: new window.kakao.maps.LatLng(
          markersData[0].latitude || 37.5665,
          markersData[0].longitude || 126.9780
        ),
        level: 2,
      };

      const map = new window.kakao.maps.Map(container, options);

      let openInfoWindow = null;

      markersData.forEach(markerInfo => {
        const markerPosition = new window.kakao.maps.LatLng(markerInfo.latitude, markerInfo.longitude);
        const marker = new window.kakao.maps.Marker({
          position: markerPosition,
          map: map,
        });

        const content =
          '<div class="wrap" style="border-radius: 10px;">' +
          '    <div class="info" style="border-radius: 10px;">' +
          '        <div class="title">' +
          `${markerInfo.name}` +
          '            <div class="close" onclick="document.querySelectorAll(\'.wrap\').forEach(el => el.style.display = \'none\');" title="닫기"></div>' +
          '        </div>' +
          '        <div class="body">' +
          '            <div class="desc">' +
          '                <div class="sigungu">시군구 넣을 예정</div>' +
          '                <div class="recommend-reason">챗봇 추천 이유 넣을 예정</div>' +
          `                <div class="ellipsis">${markerInfo.rental_type === 'MONTHLY' ? '월세' : '전세'}</div>` +
          `                <div class="ellipsis">${markerInfo.rental_type === 'MONTHLY' ? markerInfo.deposit.toLocaleString() + '원' : markerInfo.monthly_rent.toLocaleString() + '원'}</div>` +
          '                <button class="content-btn" onclick=\'window.openDetailModal(' + JSON.stringify(markerInfo) + ')\'>상세정보</button>' +
          '            </div>' +
          '        </div>' +
          '    </div>' +
          '</div>';

        const infowindow = new window.kakao.maps.InfoWindow({
          content: content,
        });

        window.kakao.maps.event.addListener(marker, 'click', () => {
          if (openInfoWindow) openInfoWindow.close();
          infowindow.open(map, marker);
          openInfoWindow = infowindow;
        });

        window.kakao.maps.event.addListener(map, 'click', () => {
          if (openInfoWindow) openInfoWindow.close();
        });
      });

      return map;
    };

    loadKakaoMap();
  }, []);

  const toggleSidebar = () => {
    setIsSidebarOpen(prev => !prev);
  };

  return (
    <div className="kakao-container">
      <div id="map" className="map" ref={mapRef}></div>

      {loading && <div className="loading-overlay">로딩 중...</div>}

      {error && <div className="error-overlay">에러: {error.message}</div>}

      <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
      <ErrorBoundary />

      <DetailModal
        isOpen={isDetailModalOpen}
        closeModal={closeDetailModal}
        markerInfo={selectedMarker}
      />
    </div>
  );
}
