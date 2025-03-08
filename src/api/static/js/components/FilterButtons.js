function FilterButtons({ batches, selectedBreed, onBreedSelect }) {
    const breeds = [...new Set(batches.flatMap(batch => batch.chicken_breed))].sort();

    return (
        <div className="space-y-2">
            <div className="text-gray-700 font-medium">品種篩選：</div>
            <div className="flex flex-wrap gap-2">
                <button 
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
                        ${selectedBreed === 'all' 
                            ? 'bg-accent text-white' 
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
                    onClick={() => onBreedSelect('all')}
                >
                    全部
                </button>
                {breeds.map(breed => (
                    <button
                        key={breed}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
                            ${selectedBreed === breed 
                                ? 'bg-accent text-white' 
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
                        onClick={() => onBreedSelect(breed)}
                    >
                        {breed}
                    </button>
                ))}
            </div>
        </div>
    );
} 