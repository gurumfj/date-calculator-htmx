function BreedInfo({ date, supplier, breed, male, female, weekAge }) {
    const formatDate = (dateStr) => {
        return new Date(dateStr).toLocaleDateString('zh-TW');
    };

    return (
        <div className="bg-white rounded-lg shadow p-4 mb-2">
            <div className="flex justify-between items-center">
                <div className="space-y-1">
                    <div className="text-gray-600 text-sm">{formatDate(date)}</div>
                    <div className="text-gray-800">{supplier}</div>
                    <div className="text-accent font-medium">{breed}</div>
                    <div className="text-gray-600 text-sm">{weekAge}週</div>
                </div>
                <div className="flex space-x-4 bg-gray-50 px-4 py-2 rounded-lg">
                    <div className="text-center">
                        <div className="text-gray-600 text-xs">公</div>
                        <div className="text-accent font-semibold">{male}</div>
                    </div>
                    <div className="text-center">
                        <div className="text-gray-600 text-xs">母</div>
                        <div className="text-accent font-semibold">{female}</div>
                    </div>
                </div>
            </div>
        </div>
    );
} 