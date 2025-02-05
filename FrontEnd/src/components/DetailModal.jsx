import '../styles/DetailModal.css';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';

const DetailModal = ({ isOpen, closeModal, propertyDetail }) => {
    if (!isOpen || !propertyDetail) return null;

    const {
        building_name,
        sido, sigungu, dong, jibun_main, jibun_sub,

        room_count,
        bathroom_count,
        total_area,
        exclusive_area,
        monthly_rent,
        description,
    } = propertyDetail;

    const address = [sido, sigungu, dong, jibun_main, jibun_sub]
        .filter(Boolean)
        .join(" ") || '정보 없음';

    const TableComponent = () => {
        const rows = [
            { label: '주소', key: address },
            { label: '방 개수', key: room_count },
            { label: '욕실 개수', key: bathroom_count },
            { label: '공급면적', key: total_area },
            { label: '전용면적', key: exclusive_area },
            {
                label: '월세',
                key: monthly_rent
                    ? `${monthly_rent.toLocaleString()} 원`
                    : '정보 없음'
            },
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
                                    <ReactMarkdown remarkPlugins={[remarkBreaks]}>
                                        {description || '설명 없음'}
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
