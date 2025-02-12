const { useState } = React;

function Card({ batch, selectedBreed }) {
    const [isExpanded, setIsExpanded] = useState(false);

    const shouldShow = selectedBreed === 'all' || 
        batch.chicken_breed.some(breed => breed === selectedBreed);

    if (!shouldShow) return null;

    return (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="p-4 border-b border-gray-200">
                <div className="text-lg font-semibold text-primary">
                    {batch.batch_name || '未命名批次'}
                </div>
            </div>
            <div className="p-4 space-y-4">
                <div className="flex justify-between items-center">
                    <div className="space-y-1">
                        <div className="text-gray-600">牧場</div>
                        <div className="font-medium">{batch.farm_name}</div>
                    </div>
                    <div className="flex space-x-4 bg-gray-50 px-4 py-2 rounded-lg">
                        <div className="text-center">
                            <div className="text-gray-600 text-xs">公</div>
                            <div className="text-accent font-semibold">{batch.total_male}</div>
                        </div>
                        <div className="text-center">
                            <div className="text-gray-600 text-xs">母</div>
                            <div className="text-accent font-semibold">{batch.total_female}</div>
                        </div>
                    </div>
                </div>
                <button 
                    className={`w-full py-2 px-4 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors ${isExpanded ? 'bg-gray-200' : ''}`}
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    {isExpanded ? '收起' : '詳細資訊'}
                </button>
                <div className={`space-y-2 ${isExpanded ? 'block' : 'hidden'}`}>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <div className="text-gray-600 text-sm">地址</div>
                            <div>{batch.address}</div>
                        </div>
                        <div>
                            <div className="text-gray-600 text-sm">畜主</div>
                            <div>{batch.farmer_name}</div>
                        </div>
                        <div>
                            <div className="text-gray-600 text-sm">獸醫</div>
                            <div>{batch.veterinarian}</div>
                        </div>
                        <div>
                            <div className="text-gray-600 text-sm">狀態</div>
                            <div>{batch.batch_state}</div>
                        </div>
                    </div>
                </div>
                <div className="space-y-2">
                    {batch.breed_date.map((date, index) => (
                        <BreedInfo
                            key={index}
                            date={date}
                            supplier={batch.supplier[index]}
                            breed={batch.chicken_breed[index]}
                            male={batch.male[index]}
                            female={batch.female[index]}
                            weekAge={batch.week_age[index]}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}

export default Card; 