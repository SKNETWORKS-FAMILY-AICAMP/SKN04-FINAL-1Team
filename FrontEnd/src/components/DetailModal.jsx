import '../styles/DetailModal.css';
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import Tooltip from './Tooltip';
import { fetchPropertyInfoById, fetchPropertyLocationById } from '../api';

const DetailModal = ({ isOpen, closeModal, propertyId }) => {
    const [propertyDetail, setPropertyDetail] = useState(null);
    const [locationDetail, setLocationDetail] = useState(null);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!propertyId) return;

        const getPropertyDetail = async () => {
            try {
                console.log(`Fetching property details for ID: ${propertyId}`);
                const data = await fetchPropertyInfoById(propertyId);
                setPropertyDetail(data);
            } catch (error) {
                console.error("Error fetching property detail:", error);
                setError(error);
            }
        };

        const getLocationDetail = async () => {
            try {
                console.log(`Fetching location details for ID: ${propertyId}`);
                const data = await fetchPropertyLocationById(propertyId);
                setLocationDetail(data);
            } catch (error) {
                console.error("Error fetching location detail:", error);
                setError(error);
            }
        };

        setLoading(true);
        Promise.all([getPropertyDetail(), getLocationDetail()]).finally(() => setLoading(false));

    }, [propertyId]);



    if (!isOpen || !propertyDetail) return null;

    if (loading) return <div className="loading-overlay">로딩 중...</div>;
    if (error) return <div className="error-overlay">에러: {error.message}</div>;

    const TableComponent = () => {
        const rows = [
            {
                key: [locationDetail?.sido, locationDetail?.sigungu, locationDetail?.dong, locationDetail?.jibun_main, locationDetail?.jibun_sub]
                    .filter(Boolean)
                    .join(" ") || '정보 없음',
                label: '주소'
            },
            { key: propertyDetail.room_count, label: '방 개수' },
            { key: propertyDetail.bathroom_count, label: '욕실 개수' },
            { key: propertyDetail.total_area, label: '공급면적' },
            { key: propertyDetail.exclusive_area, label: '전용면적' },
            { key: propertyDetail.monthly_rent ? `${propertyDetail.monthly_rent.toLocaleString()} 원` : '정보 없음', label: '월세' },
        ];

        return (
            <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                <tbody>
                    {rows.map((row, index) => (
                        <tr key={index}>
                            <th className="table-header">{row.label}</th>
                            <td className="table-component">{row.key || '정보 없음'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        );
    };

    return (
        <div className="detail-overlay" onClick={closeModal}>
            <div className="detail-modal" onClick={(e) => e.stopPropagation()}>
                <div className="detail-header">
                    <h2>부동산 상세정보</h2>
                    <button className="detail-closebtn" onClick={closeModal}>
                        &times;
                    </button>
                </div>
                <hr className="hr" />
                <div className="detail-content">
                    <TableComponent />
                    <br />
                    <table className="table-second">
                        <tbody>
                            <tr>
                                <th className="content-info">설명</th>
                            </tr>
                            <tr>
                                <td className="content-markdown">
                                    <ReactMarkdown remarkPlugins={remarkBreaks}>
                                        {propertyDetail.description || '설명 없음'}
                                    </ReactMarkdown>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default DetailModal;
