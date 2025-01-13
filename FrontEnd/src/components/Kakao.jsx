import '../styles/Kakao.css';
import Sidebar from "./Sidebar";
import ChatWindow from "./ChatWindow";
import { useEffect, useState, useRef } from "react";
import ErrorBoundary from './ErrorBoundary';
import ReactDOMServer from 'react-dom/server';
import DetailModal from './DetailModal.jsx';
import axios from 'axios';

const InfoWindowContent = ({ markerInfo, onOpenDetailModal }) => {
  const { name, deposit, sale_price, monthly_rent, description, rental_type, move_in_type } = markerInfo;

  // 가격 포맷 함수
  const formatPrice = (price) => {
    if (price === null || price === undefined) return "정보 없음";
    return `${price.toLocaleString()}원`;
  };

  const monthlyYearlyClassification = (rental_type) => {
    if (rental_type === 'MONTHLY') {
      return '전세';
    } else if (rental_type === 'YEARLY') {
      return '월세';
    }
  };

  const move_in_type_classification = (move_in_type) => {
    if (move_in_type === 'IMMEDIATE') {
      return '즉시 입주 가능';
    } else if (move_in_type === 'AFTER') {
      return '추후 입주 가능';
    } else if (move_in_type === 'null') {
      return '정보 없음';
    }
  };

  return (
    <div className="box">
      <strong>{name}</strong>
      <br />
      <strong>유형: {monthlyYearlyClassification(rental_type)}</strong>
      {rental_type === 'MONTHLY' && (
        <>
          <strong>전세가: {formatPrice(deposit)}</strong>
          <strong> 즉시 입주: {move_in_type_classification(move_in_type)} </strong>
        </>
      )}
      {rental_type === 'YEARLY' && (
        <>
          <strong>전세가: {formatPrice(deposit)}</strong>
          <strong>월세: {formatPrice(monthly_rent)}</strong>
          <strong> 즉시 입주: {move_in_type_classification(move_in_type)} </strong>
        </>
      )}
      <hr />
      <span className='recommend-reason'>
        <img src='/images/home.png' alt='aibot' />
        AI 추천 이유!
      </span>
      <br />
      <div className='preserved-text'>
        {description}
      </div>
      <button
        className='detail-btn'
        onClick={() => onOpenDetailModal(markerInfo)}>
        상세보기
      </button>
    </div>
  );
};

export default function Kakao() {
  // state 설정 (필요 없는 경우 삭제 가능)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedMarker, setSelectedMarker] = useState(null);
  const mapRef = useRef(null);

  const openDetailModal = (markerInfo) => {
    console.log('마커정보', markerInfo);
    setSelectedMarker(markerInfo);
    setIsDetailModalOpen(true);
  };

  const closeDetailModal = () => {
    setIsDetailModalOpen(false);
  };

  useEffect(() => {
    const dummyMarkers = [
      {
        name: "서초푸르지오써밋",
        latitude: 37.501493,
        longitude: 127.0217076,
        deposit: 980000000,
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

    // 카카오맵 로드
    const loadKakaoMap = () => {
      if (!window.kakao || !window.kakao.maps) {
        const script = document.createElement('script');
        script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=14184ad2e38efd5cb6898242be23f625&autoload=false&libraries=services`;
        script.async = true;
        script.onload = () => {
          window.kakao.maps.load(() => initializeMap(dummyMarkers)); // dummyMarkers 사용
        };
        document.head.appendChild(script);
      } else {
        window.kakao.maps.load(() => initializeMap(dummyMarkers));
      }
    };

    const initializeMap = (markersData) => {
      if (markersData.length === 0) {
        console.error('마커 데이터가 없습니다.');
        return;
      }

      const container = mapRef.current;
      const options = {
        center: new window.kakao.maps.LatLng(
          markersData[0].latitude || 37.5665,
          markersData[0].longitude || 126.9780
        ),
        level: 4,
      };
      const map = new window.kakao.maps.Map(container, options);

      // 이벤트 리스너에 passive 옵션 추가
      container.addEventListener('wheel', (event) => {
        event.preventDefault();
      }, { passive: true });
      container.addEventListener('mousewheel', (event) => {
        event.preventDefault();
      }, { passive: true });
      container.addEventListener('touchstart', (event) => {
        event.preventDefault();
      }, { passive: true });

      let openInfoWindow = null;

      // 각 마커를 지도에 추가
      markersData.forEach(markerInfo => {
        const markerPosition = new window.kakao.maps.LatLng(markerInfo.latitude, markerInfo.longitude);
        const marker = new window.kakao.maps.Marker({
          position: markerPosition,
          map: map,
        });

        // 정보창 추가
        const content = ReactDOMServer.renderToString(
          <InfoWindowContent markerInfo={markerInfo} onOpenDetailModal={openDetailModal} />
        );
        const infowindow = new window.kakao.maps.InfoWindow({
          content: content,
        });

        window.kakao.maps.event.addListener(marker, 'click', () => {
          if (openInfoWindow) openInfoWindow.close();
          infowindow.open(map, marker);
          openInfoWindow = infowindow;
        });

        // 지도 클릭 시 정보창 닫기
        window.kakao.maps.event.addListener(map, 'click', () => {
          if (openInfoWindow) openInfoWindow.close();
        });
      });
    };

    loadKakaoMap();
    setLoading(false);
  }, []);

  const toggleSidebar = () => {
    setIsSidebarOpen(prev => !prev);
  };

  if (loading) {
    return <div>로딩 중...</div>;
  }

  if (error) {
    return <div>에러: {error.message}</div>;
  }

  return (
    <div className="kakao-container">
      <div id="map" className="map" ref={mapRef}></div>
      <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
      <ChatWindow isSidebarOpen={isSidebarOpen} />
      <ErrorBoundary />
      <DetailModal isOpen={isDetailModalOpen} closeModal={closeDetailModal} markerInfo={selectedMarker} />
    </div>
  );
}
