const { useState, useEffect } = React;

// 提取計算總數的純函數
const calculateTotals = (batches, selectedBreed) => {
    return {
        totalMale: batches.reduce((sum, batch) => {
            if (selectedBreed === 'all') {
                return sum + batch.total_male;
            }
            // 計算特定品種的公雞總數
            return sum + batch.breed_date.reduce((breedSum, _, index) => {
                if (batch.chicken_breed[index] === selectedBreed) {
                    return breedSum + batch.male[index];
                }
                return breedSum;
            }, 0);
        }, 0),
        totalFemale: batches.reduce((sum, batch) => {
            if (selectedBreed === 'all') {
                return sum + batch.total_female;
            }
            // 計算特定品種的母雞總數
            return sum + batch.breed_date.reduce((breedSum, _, index) => {
                if (batch.chicken_breed[index] === selectedBreed) {
                    return breedSum + batch.female[index];
                }
                return breedSum;
            }, 0);
        }, 0),
        totalBatches: selectedBreed === 'all' 
            ? batches.length 
            : batches.filter(batch => 
                batch.chicken_breed.some(breed => breed === selectedBreed)
              ).length
    };
};

// 提取錯誤顯示組件
const ErrorMessage = ({ message }) => (
    <div className="text-red-500 p-4 text-center">{message}</div>
);

// 提取載入中組件
const LoadingMessage = () => (
    <div className="text-gray-600 p-4 text-center">載入中...</div>
);

// 提取無資料組件
const NoDataMessage = () => (
    <div className="text-gray-600 p-4 text-center">目前沒有可用的資料</div>
);

// 提取總計資訊組件
const TotalInfo = ({ totalBatches, totalMale, totalFemale }) => (
    <div className="bg-white rounded-lg shadow p-4 mb-6 text-center">
        總計：{totalBatches} 批次，公雞 {totalMale} 隻，母雞 {totalFemale} 隻
    </div>
);

const STATE_STYLES = {
    '養殖中': 'bg-blue-50',
    '銷售中': 'bg-yellow-50'
};

function BatchRow({ batch, selectedBreed }) {
    const [isExpanded, setIsExpanded] = useState(false);
    
    const shouldShow = selectedBreed === 'all' || 
        batch.chicken_breed.some(breed => breed === selectedBreed);

    if (!shouldShow) return null;

    // 從批次名稱解析資訊
    const [location, type] = batch.batch_name.split('-');

    return (
        <tr className={`${STATE_STYLES[batch.batch_state]} border-b border-gray-100`}>
            <td className="p-4" colSpan="6">
                {/* 主要批次資訊 */}
                <div className="flex items-center gap-4">
                    <div className="flex-1">
                        <div className="text-lg font-semibold text-primary">
                            {location}
                            <span className="ml-2 text-sm font-normal text-gray-500">
                                {batch.batch_state}
                            </span>
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                            {batch.farm_name} · {batch.farmer_name}
                        </div>
                    </div>
                    <div className="flex gap-6 px-4">
                        <div className="text-center">
                            <div className="text-gray-600 text-xs">週齡</div>
                            <div className="text-accent font-semibold">{batch.week_age[0]}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-gray-600 text-xs">公</div>
                            <div className="text-accent font-semibold text-lg">{batch.total_male}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-gray-600 text-xs">母</div>
                            <div className="text-accent font-semibold text-lg">{batch.total_female}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-gray-600 text-xs">銷售進度</div>
                            <div className={`font-semibold ${batch.sales_percentage >= 0.8 ? 'text-green-600' : 'text-blue-600'}`}>
                                {(batch.sales_percentage * 100).toFixed(1)}%
                            </div>
                        </div>
                    </div>
                    <button 
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                        onClick={() => setIsExpanded(!isExpanded)}
                    >
                        {isExpanded ? '收起' : '詳細'}
                    </button>
                </div>

                {/* 詳細資訊 */}
                {isExpanded && (
                    <div className="mt-4">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-200">
                                    <th className="py-2 text-left font-medium text-gray-600">進雞日期</th>
                                    <th className="py-2 text-left font-medium text-gray-600">供應商</th>
                                    <th className="py-2 text-left font-medium text-gray-600">品種</th>
                                    <th className="py-2 text-center font-medium text-gray-600 w-20">週齡</th>
                                    <th className="py-2 text-center font-medium text-gray-600 w-20">公</th>
                                    <th className="py-2 text-center font-medium text-gray-600 w-20">母</th>
                                </tr>
                            </thead>
                            <tbody>
                                {batch.breed_date.map((date, index) => (
                                    <tr key={index} className="border-b border-gray-50">
                                        <td className="py-2">{new Date(date).toLocaleDateString('zh-TW')}</td>
                                        <td className="py-2">{batch.supplier[index] || '-'}</td>
                                        <td className="py-2 font-medium">{batch.chicken_breed[index]}</td>
                                        <td className="py-2 text-center">{batch.week_age[index]}</td>
                                        <td className="py-2 text-center text-accent">{batch.male[index]}</td>
                                        <td className="py-2 text-center text-accent">{batch.female[index]}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span className="text-gray-600">地址：</span>
                                {batch.address}
                            </div>
                            <div>
                                <span className="text-gray-600">獸醫：</span>
                                {batch.veterinarian}
                            </div>
                        </div>
                    </div>
                )}
            </td>
        </tr>
    );
}

function App() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [selectedBreed, setSelectedBreed] = useState('all');

    useEffect(() => {
        fetchBreedingData();
    }, []);

    const fetchBreedingData = async () => {
        try {
            const response = await fetch('/api/not-completed');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            if (result.status === 'success' && result.content && result.content.batches) {
                setData(result.content);
            } else {
                throw new Error(result.msg || '發生錯誤');
            }
        } catch (error) {
            console.error('API 請求失敗:', error);
            setError('無法取得繁殖資料，請稍後再試');
        }
    };

    if (error) return <ErrorMessage message={error} />;
    if (!data) return <LoadingMessage />;
    if (data.batches.length === 0) return <NoDataMessage />;

    const { totalMale, totalFemale, totalBatches } = calculateTotals(data.batches, selectedBreed);

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold text-center text-primary mb-8">繁殖資料查詢</h1>
            <TotalInfo 
                totalBatches={totalBatches}
                totalMale={totalMale}
                totalFemale={totalFemale}
            />
            <FilterButtons 
                batches={data.batches}
                selectedBreed={selectedBreed}
                onBreedSelect={setSelectedBreed}
            />
            <div className="mt-6 bg-white rounded-lg shadow overflow-hidden">
                <table className="w-full">
                    <tbody>
                        {data.batches.map((batch, index) => (
                            <BatchRow 
                                key={index}
                                batch={batch}
                                selectedBreed={selectedBreed}
                            />
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
} 