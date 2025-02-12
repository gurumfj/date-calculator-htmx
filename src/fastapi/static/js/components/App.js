const { useState, useEffect } = React;

function App() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [selectedBreed, setSelectedBreed] = useState('all');

    useEffect(() => {
        fetchBreedingData();
    }, []);

    const fetchBreedingData = async () => {
        try {
            const response = await fetch('/breeds/not-completed');
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

    if (error) return <div className="text-red-500 p-4 text-center">{error}</div>;
    if (!data) return <div className="text-gray-600 p-4 text-center">載入中...</div>;
    if (data.batches.length === 0) return <div className="text-gray-600 p-4 text-center">目前沒有可用的資料</div>;

    const totalMale = data.batches.reduce((sum, batch) => sum + batch.total_male, 0);
    const totalFemale = data.batches.reduce((sum, batch) => sum + batch.total_female, 0);

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold text-center text-primary mb-8">繁殖資料查詢</h1>
            <div className="bg-white rounded-lg shadow p-4 mb-6 text-center">
                總計：{data.batches.length} 批次，公雞 {totalMale} 隻，母雞 {totalFemale} 隻
            </div>
            <FilterButtons 
                batches={data.batches}
                selectedBreed={selectedBreed}
                onBreedSelect={setSelectedBreed}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
                {data.batches.map((batch, index) => (
                    <Card 
                        key={index}
                        batch={batch}
                        selectedBreed={selectedBreed}
                    />
                ))}
            </div>
        </div>
    );
} 