import '../styles/DetailModal.css';
import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks';

const DetailModal = ({ isOpen, closeModal, markerInfo }) => {
    if (!isOpen || !markerInfo) return null;

    const Tooltip = ({ text, tooltipText }) => {
        return (
            <div className='tooltip-container'>
                <span className='tooltip-icon'>
                    {text}
                </span>
                <span className='tooltip-text'>{tooltipText}</span>
            </div>
        )
    }


    const TableComponent = () => {
        // 각 행의 key와 헤더에 표시할 label
        const rows = [
            { key: `${markerInfo.address}`, label: '주소' },
            { key: `${markerInfo.buildingCoverage}`, label: '건폐율' },
            { key: `${markerInfo.floorAreaRatio}`, label: '용적율' },
            { key: `${markerInfo.apartmentNumber}`, label: '세대수' },
            { key: `${markerInfo.floor}`, label: '층수' },
            { key: `${markerInfo.area}`, label: '면적' },
            { key: `${markerInfo.bathroom}`, label: '욕실' },
            { key: `${markerInfo.room}`, label: '방수' },
        ];

        return (
            <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                <tbody>
                    {rows.map((row) => (
                        <tr key={row.key}>
                            {row.label === '건폐율' ?
                                <th className='table-header'>{row.label} <Tooltip text="?" tooltipText='
                                쉽게 말하면: 건물이 땅 위에 얼마나 많은 면적을 차지하고 있는지를 나타내는 비율이에요.
                                예시: 만약 100평의 부지에 50평의 건물을 지었다면, 건폐율은 50%가 돼요.
                                의미: 높게 나오면 땅에 많은 면적의 건물이 건축되었음을 의미하고, 낮으면 상대적으로 여유 있는 외부 공간(예: 마당, 주차장)이 많다는 뜻이에요.' />
                                </th> :
                                row.label === '용적율' ?
                                    <th className='table-header'>{row.label} <Tooltip text="?" tooltipText='123' /></th> :
                                    <th className='table-header'>{row.label}</th>}
                            {/* <th className='table-header'>{row.label}</th> */}
                            <td className='table-component'>{row.key}</td>
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
                    <h2>상세정보</h2>
                    <button className="detail-closebtn" onClick={closeModal}>
                        &times;
                    </button>
                </div>
                <hr className='hr' />
                <div className="detail-content">
                    <p className='detail-content-name'><strong> {markerInfo.name}</strong></p>
                    <TableComponent />
                    {/* <p>{markerInfo.rental_type === 'monthly' ? '월세가' : '전세가'} : {markerInfo.rental_type === 'monthly' ? markerInfo.deposit.toLocaleString() + '원' : markerInfo.monthly_rent.toLocaleString() + '원'}</p> */}
                    {/* <hr /> */}
                    <br />
                    <table className='table-second'>
                        <tbody>
                            <tr>
                                <th className='content-info'>정보</th>
                            </tr>
                            <tr>
                                <td className='content-markdown'><ReactMarkdown remarkPlugins={remarkBreaks} >{`${markerInfo.description}`}</ReactMarkdown></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        // document.body
    );
};

export default DetailModal;
