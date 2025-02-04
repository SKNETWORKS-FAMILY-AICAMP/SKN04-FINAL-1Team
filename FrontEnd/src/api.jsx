import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/';

axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

export const fetchAddresses = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}addresses/`);
        return response.data;
    } catch (error) {
        console.error("주소 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchAddressDetails = async (addressId) => {
    try {
        const response = await axios.get(`${API_BASE_URL}addresses/${addressId}/details/`);
        return response.data;
    } catch (error) {
        console.error("주소 상세 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};


export const fetchCulturalFacilities = async (params = {}) => {
    try {
        const response = await axios.get(`${API_BASE_URL}cultural-facilities/`, { params });
        return response.data;
    } catch (error) {
        console.error("문화 시설 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchPropertyLocations = async (params = {}) => {
    try {
        const response = await axios.get(`${API_BASE_URL}property-locations/`, { params });
        return response.data;
    } catch (error) {
        console.error("부동산 위치 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchPropertyLocationById = async (property_id) => {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error("인증 토큰이 없습니다. 로그인 후 다시 시도하세요.");
        }

        const response = await axios.get(`${API_BASE_URL}property-locations/${property_id}/`, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            withCredentials: true
        });

        return response.data;
    } catch (error) {
        console.error("property_id로 부동산 정보를 조회하는 중 오류:", error.response?.data || error.message);
        throw error;
    }
};
window.fetchPropertyLocationById = fetchPropertyLocationById;


export const fetchPropertyInfo = async (params = {}) => {
    try {
        const response = await axios.get(`${API_BASE_URL}property-info/`, { params });
        return response.data;
    } catch (error) {
        console.error("부동산 정보를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchActiveProperties = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}property-info/active_properties/`);
        return response.data;
    } catch (error) {
        console.error("활성화된 부동산 정보를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchPropertyInfoById = async (property_id) => {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error("인증 토큰이 없습니다. 로그인 후 다시 시도하세요.");
        }

        const response = await axios.get(`${API_BASE_URL}property-info/${property_id}/`, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            withCredentials: true
        });

        return response.data;
    } catch (error) {
        console.error("property_id로 부동산 정보를 조회하는 중 오류:", error.response?.data || error.message);
        throw error;
    }
};

// ✅ window 객체에 함수 추가 (테스트용)
window.fetchPropertyInfoById = fetchPropertyInfoById;




export const fetchRentals = async (params = {}) => {
    try {
        const response = await axios.get(`${API_BASE_URL}rentals/`, { params });
        return response.data;
    } catch (error) {
        console.error("임대 정보를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchRentalPriceRange = async (params = {}) => {
    try {
        const response = await axios.get(`${API_BASE_URL}rentals/price_range/`, { params });
        return response.data;
    } catch (error) {
        console.error("임대 가격 범위 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchRentalByPropertyId = async (property_id) => {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error("로그인이 필요합니다.");
        }

        const response = await axios.get(`${API_BASE_URL}rentals/${property_id}/`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            withCredentials: true
        });

        if (response.status === 200) {
            console.log("✅ 임대 정보 조회 성공:", response.data);
        }

        return response.data;
    } catch (error) {
        console.error("property_id로 임대 정보를 조회하는 중 오류:", error.response?.data || error.message);
        return null;
    }
};




window.fetchRentalByPropertyId = fetchRentalByPropertyId;




export const fetchSales = async (params = {}) => {
    try {
        const response = await axios.get(`${API_BASE_URL}sales/`, { params });
        return response.data;
    } catch (error) {
        console.error("매매 정보를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchSalePriceRange = async (params = {}) => {
    try {
        const response = await axios.get(`${API_BASE_URL}sales/price_range/`, { params });
        return response.data;
    } catch (error) {
        console.error("매매 가격 범위 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchSaleByPropertyId = async (property_id) => {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error("로그인이 필요합니다.");
        }

        const response = await axios.get(`${API_BASE_URL}sales/${property_id}/`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            withCredentials: true
        });
        console.log(response)

        if (response.status === 200) {
            console.log("✅ 임대 정보 조회 성공:", response.data);
        }

        return response.data;
    } catch (error) {
        console.error("property_id로 임대 정보를 조회하는 중 오류:", error.response?.data || error.message);
        return null;
    }
};
window.fetchSaleByPropertyId = fetchSaleByPropertyId;



export const loginUser = async (credentials) => {
    try {
        const response = await axios.post(
            `${API_BASE_URL}auth/login/`,
            credentials,
            {
                headers: {
                    'Content-Type': 'application/json',
                },
            }
        );
        console.log("loginUser 응답:", response);
        const { access, refresh } = response.data.token;
        console.log("access:", access);
        console.log("refresh:", refresh);
        localStorage.setItem('token', access);
        return response.data;
    } catch (error) {
        console.error("로그인 중 오류 발생:", error);
        throw error;
    }
};

export const registerUser = async (data) => {
    try {
        const response = await axios.post(`${API_BASE_URL}auth/register/`, data);
        return response.data;
    } catch (error) {
        console.error("회원가입 중 오류 발생:", error);
        throw error;
    }
};

export const fetchChatSessions = async () => {
    try {
        const token = localStorage.getItem('token');
        if (!token) throw new Error("로그인 후 이용 가능합니다.");
        const response = await axios.get(`${API_BASE_URL}chats/sessions/`, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            withCredentials: true,
        });
        return response.data;
    } catch (error) {
        console.error("채팅 세션 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchChatSessionMessages = async (session_id) => {
    try {
        const token = localStorage.getItem('token');
        if (!token) throw new Error("로그인 후 이용 가능합니다.");
        const response = await axios.get(`${API_BASE_URL}chats/session-messages/`, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            params: { session_id },
            withCredentials: true,
        });
        return response.data;
    } catch (error) {
        console.error("채팅 메시지 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const postFeedback = async (feedbackData) => {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error("인증 토큰이 없습니다. 로그인 후 다시 시도해 주세요.");
        }
        const response = await axios.post(
            `${API_BASE_URL}feedbacks/`,
            feedbackData,
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
            }
        );
        return response.data;
    } catch (error) {
        console.error("피드백 전송 중 오류 발생:", error);
        throw error;
    }
};

export const fetchNotices = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}notices/`);
        return response.data;
    } catch (error) {
        console.error("공지사항 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const toggleNoticeActive = async (noticeId) => {
    try {
        const response = await axios.patch(`${API_BASE_URL}notices/${noticeId}/toggle-active/`);
        return response.data;
    } catch (error) {
        console.error("공지사항 활성화 토글 중 오류 발생:", error);
        throw error;
    }
};

export const postUserLog = async (logData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}user-logs/`, logData);
        return response.data;
    } catch (error) {
        console.error("사용자 로그 전송 중 오류 발생:", error);
        throw error;
    }
};

export const fetchMyFavorites = async () => {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error("인증 토큰이 없습니다. 로그인 후 다시 시도하세요.");
        }

        const response = await axios.get(`${API_BASE_URL}favorites/`, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            withCredentials: true
        });

        return response.data;
    } catch (error) {
        console.error("property_id로 부동산 정보를 조회하는 중 오류:", error.response?.data || error.message);
        throw error;
    }
};
window.fetchMyFavorites = fetchMyFavorites;



export const fetchCrimeStats = async (params = {}) => {
    try {
        const response = await axios.get(`${API_BASE_URL}crime-stats/`, { params });
        return response.data;
    } catch (error) {
        console.error("범죄 통계 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchSubwayStations = async (params = {}) => {
    try {
        const response = await axios.get(`${API_BASE_URL}subway-stations/`, { params });
        return response.data;
    } catch (error) {
        console.error("지하철 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchLocationDistances = async (params = {}) => {
    try {
        const response = await axios.get(`${API_BASE_URL}location-distances/`, { params });
        return response.data;
    } catch (error) {
        console.error("위치 거리 데이터를 가져오는 중 오류:", error);
        throw error;
    }
};

export const fetchLocationDistanceByProperty = async (property_id) => {
    try {
        const response = await axios.get(`${API_BASE_URL}location-distances/by_property/`, {
            params: { property_id }
        });
        return response.data;
    } catch (error) {
        console.error("property_id로 위치 거리 데이터를 조회하는 중 오류:", error);
        throw error;
    }
};