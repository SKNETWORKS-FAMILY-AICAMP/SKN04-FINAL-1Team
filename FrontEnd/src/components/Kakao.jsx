import '../styles/Kakao.css';
import { useEffect, useState, useRef } from "react";
import DetailModal from "./DetailModal";
import { fetchPropertyInfoById, fetchPropertyLocationById } from '../api';

export default function Kakao({ properties }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [propertyDetail, setPropertyDetail] = useState(null);

  const mapRef = useRef(null);
  const kakaoMapRef = useRef(null);
  const markersRef = useRef([]);

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

    const loadKakaoMapScript = () => {
      if (!window.kakao || !window.kakao.maps) {
        const script = document.createElement('script');
        script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=14184ad2e38efd5cb6898242be23f625&autoload=false&libraries=services`;
        script.async = true;
        script.onload = () => {
          window.kakao.maps.load(() => {
            try {
              initializeMap();
              setLoading(false);
            } catch (err) {
              console.error("카카오맵 초기화 중 오류:", err);
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
            initializeMap();
            setLoading(false);
          } catch (err) {
            console.error("카카오맵 초기화 중 오류:", err);
            setError(err);
            setLoading(false);
          }
        });
      }
    };

    loadKakaoMapScript();
  }, []);

  const initializeMap = () => {
    const center = new window.kakao.maps.LatLng(37.5665, 126.9780);
    const options = { center, level: 5 };
    const container = mapRef.current;
    const map = new window.kakao.maps.Map(container, options);
    kakaoMapRef.current = map;
  };

  useEffect(() => {
    if (!kakaoMapRef.current || !properties || properties.length === 0) return;
    drawMarkers(properties);
  }, [properties]);

  const drawMarkers = (markersData) => {
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];

    const map = kakaoMapRef.current;
    let openInfoWindow = null;
    const bounds = new window.kakao.maps.LatLngBounds();

    markersData.forEach(markerInfo => {
      const { latitude, longitude, property_id } = markerInfo;
      if (!latitude || !longitude) return;

      const markerPosition = new window.kakao.maps.LatLng(latitude, longitude);
      const marker = new window.kakao.maps.Marker({ position: markerPosition, map });
      markersRef.current.push(marker);
      bounds.extend(markerPosition);

      const infowindow = new window.kakao.maps.InfoWindow();

      window.kakao.maps.event.addListener(marker, 'click', async () => {
        if (openInfoWindow) openInfoWindow.close();

        try {
          const data = await fetchPropertyInfoById(property_id);
          const data1 = await fetchPropertyLocationById(property_id);

          const mergedPropertyDetail = { ...data, ...data1 };
          console.log("🏡 Merged Property Detail:", mergedPropertyDetail);

          setPropertyDetail(mergedPropertyDetail);

          const buildingName = data?.building_name || "이름 없음";
          const prid = property_id
          const fullAddress = [
            data1?.sido,
            data1?.sigungu || data?.sigungu,
            data1?.dong || data?.dong,
            data1?.jibun_main || data?.jibun_main,
            data1?.jibun_sub || data?.jibun_sub
          ]
            .filter(Boolean)
            .join(" ") || "주소 정보 없음";

          const content = document.createElement("div");
          content.className = "wrap";
          content.innerHTML = `
            <div class="info">
              <div class="title">${buildingName}</div>
              <div class="body">
                <div class="desc">
                  <div class="ellipsis">매물 번호 : ${prid}</div>
                  <div class="ellipsis">${fullAddress}</div>
                  <div class="ellipsis">월세: ${markerInfo.monthly_rent
              ? markerInfo.monthly_rent.toLocaleString() + '원'
              : '정보 없음'
            }</div>
                </div>
              </div>
            </div>
          `;

          const detailButton = document.createElement("button");
          detailButton.innerText = "상세정보 보기";
          detailButton.className = "detail-btn";
          detailButton.onclick = () => {
            setIsDetailModalOpen(true);
          };

          content.querySelector(".desc").appendChild(detailButton);
          infowindow.setContent(content);

        } catch (error) {
          console.error("매물 정보 가져오는 중 오류:", error);
          infowindow.setContent(`<div>매물 정보를 불러올 수 없습니다.</div>`);
        }

        infowindow.open(map, marker);
        openInfoWindow = infowindow;
      });
    });

    map.setBounds(bounds);
  };

  return (
    <>
      <div className="kakao-container">
        <div id="map" className="map" ref={mapRef}></div>
        {loading && <div className="loading-overlay">로딩 중...</div>}
        {error && <div className="error-overlay">에러: {error?.message}</div>}
      </div>

      {isDetailModalOpen && propertyDetail && (
        <DetailModal
          isOpen={isDetailModalOpen}
          closeModal={() => setIsDetailModalOpen(false)}
          propertyDetail={propertyDetail}
        />
      )}
    </>
  );
}
