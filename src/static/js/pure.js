// Type definitions
/**
 * @typedef {Object} BreedRecord
 * @property {string} [batch_name] - 批次名稱
 * @property {string} [farm_name] - 農場名稱
 * @property {string} [address] - 農場地址
 * @property {string} [farmer_name] - 畜主姓名
 * @property {string} [chicken_breed] - 品種
 * @property {number} [male] - 公雞數
 * @property {number} [female] - 母雞數
 * @property {string} breed_date - 入雛日期
 * @property {string} [veterinarian] - 獸醫師
 * @property {string} [supplier] - 供應商
 * @property {string} [is_completed] - 狀態
 */

/**
 * @typedef {Object} TotalInfo
 * @property {number} totalMale - 公雞總數
 * @property {number} totalFemale - 母雞總數
 * @property {number} totalBatches - 批次總數
 */

/**
 * @typedef {Object} MergedBreedRecord
 * @property {string} [batch_name] - 批次名稱
 * @property {string} [farm_name] - 農場名稱
 * @property {string} [address] - 農場地址
 * @property {string} [farmer_name] - 畜主姓名
 * @property {string[]} chicken_breeds - 品種列表
 * @property {number} total_male - 總公雞數
 * @property {number} total_female - 總母雞數
 * @property {string[]} veterinarians - 獸醫師列表
 * @property {string[]} suppliers - 供應商列表
 * @property {string[]} is_completed - 狀態列表
 * @property {Object[]} individual_records - 個別記錄
 */

// Pure functions
export function calculateTotals(breeds) {
    return {
        totalMale: breeds.reduce((sum, breed) => sum + (breed.male || 0), 0),
        totalFemale: breeds.reduce((sum, breed) => sum + (breed.female || 0), 0),
        totalBatches: breeds.length
    };
}

export function formatTotalInfo(totals) {
    return `總計：${totals.totalBatches} 批次，公雞 ${totals.totalMale} 隻，母雞 ${totals.totalFemale} 隻`;
}

export function formatFieldValue(field, value) {
    if (field === 'breed_date') {
        return new Date(value).toLocaleDateString('zh-TW');
    }
    if (field === 'male' || field === 'female') {
        return value || '0';
    }
    if (field === 'batch_name' && !value) {
        return '未命名批次';
    }
    return value || '-';
}

export function formatMergedFieldValue(field, value) {
    if (field === 'breed_date') {
        return new Date(value).toLocaleDateString('zh-TW');
    }
    if (field === 'total_male' || field === 'total_female') {
        return value || '0';
    }
    if (field === 'chicken_breeds' || field === 'veterinarians' || field === 'suppliers' || field === 'is_completed') {
        return Array.isArray(value) ? value.join('、') || '-' : '-';
    }
    if (field === 'batch_name' && !value) {
        return '未命名批次';
    }
    return value || '-';
}

export function mergeBreedsByBatch(breeds) {
    const batchGroups = breeds.reduce((groups, breed) => {
        const batchName = breed.batch_name || '未命名批次';
        if (!groups[batchName]) {
            groups[batchName] = [];
        }
        groups[batchName].push(breed);
        return groups;
    }, {});

    return Object.entries(batchGroups).map(([batchName, records]) => {
        const firstRecord = records[0];
        return {
            batch_name: batchName,
            farm_name: firstRecord.farm_name,
            address: firstRecord.address,
            farmer_name: firstRecord.farmer_name,
            chicken_breeds: [...new Set(records.map(r => r.chicken_breed || '未分類'))],
            total_male: records.reduce((sum, r) => sum + (r.male || 0), 0),
            total_female: records.reduce((sum, r) => sum + (r.female || 0), 0),
            veterinarians: [...new Set(records.map(r => r.veterinarian).filter(Boolean))],
            suppliers: [...new Set(records.map(r => r.supplier).filter(Boolean))],
            is_completed: [...new Set(records.map(r => r.is_completed).filter(Boolean))],
            individual_records: records.map(r => ({
                breed_date: r.breed_date,
                male: r.male || 0,
                female: r.female || 0,
                chicken_breed: r.chicken_breed || '未分類',
                supplier: r.supplier || '-'
            }))
        };
    });
}

export function groupMergedBreedsByType(mergedBreeds) {
    const result = {};
    mergedBreeds.forEach(breed => {
        breed.chicken_breeds.forEach(type => {
            if (!result[type]) {
                result[type] = [];
            }
            if (!result[type].includes(breed)) {
                result[type].push(breed);
            }
        });
    });
    return result;
} 