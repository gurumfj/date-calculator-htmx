import { formatFieldValue, formatMergedFieldValue, formatTotalInfo, mergeBreedsByBatch, groupMergedBreedsByType } from './pure.js';

// DOM manipulation functions
export function createMergedCard(mergedBreed) {
    const template = document.getElementById('card-template');
    const card = template.content.cloneNode(true);
    
    // 設定批次名稱
    const title = card.querySelector('[data-field="batch_name"]');
    title.textContent = formatMergedFieldValue('batch_name', mergedBreed.batch_name);

    // 設定其他欄位
    const fields = {
        'farm_name': mergedBreed.farm_name,
        'address': mergedBreed.address,
        'farmer_name': mergedBreed.farmer_name,
        'chicken_breed': mergedBreed.chicken_breeds,
        'total_male': mergedBreed.total_male,
        'total_female': mergedBreed.total_female,
        'veterinarian': mergedBreed.veterinarians,
        'supplier': mergedBreed.suppliers,
        'is_completed': mergedBreed.is_completed
    };

    Object.entries(fields).forEach(([field, value]) => {
        const element = card.querySelector(`[data-field="${field}"]`);
        if (element) {
            element.textContent = formatMergedFieldValue(field, value);
        }
    });

    // 建立子卡片
    const subCardsContainer = card.querySelector('[data-field="sub_cards"]');
    const subCardTemplate = document.getElementById('sub-card-template');

    mergedBreed.individual_records.forEach(record => {
        const subCard = subCardTemplate.content.cloneNode(true);
        
        // 設定子卡片欄位值
        const fields = {
            'breed_date': record.breed_date,
            'male': record.male,
            'female': record.female,
            'supplier': record.supplier
        };

        Object.entries(fields).forEach(([field, value]) => {
            const element = subCard.querySelector(`[data-field="${field}"]`);
            if (element) {
                element.textContent = formatFieldValue(field, value);
            }
        });
        
        subCardsContainer.appendChild(subCard);
    });
    
    return card;
}

export function createBreedSection(breedType, breeds) {
    const template = document.getElementById('breed-section-template');
    const section = template.content.cloneNode(true);
    
    const title = section.querySelector('.breed-title');
    title.textContent = breedType;
    
    const stats = section.querySelector('.breed-stats');
    const totalStats = {
        count: breeds.length,
        totalMale: breeds.reduce((sum, breed) => sum + breed.total_male, 0),
        totalFemale: breeds.reduce((sum, breed) => sum + breed.total_female, 0)
    };
    stats.textContent = `${totalStats.count} 批次 | 公雞 ${totalStats.totalMale} 隻 | 母雞 ${totalStats.totalFemale} 隻`;
    
    const grid = section.querySelector('.cards-grid');
    breeds.forEach(breed => {
        const card = createMergedCard(breed);
        grid.appendChild(card);
    });
    
    return section;
}

export function createFilterButtons(breedTypes, content) {
    const container = content.querySelector('.filter-buttons');
    const allButton = document.createElement('button');
    allButton.textContent = '全部';
    allButton.className = 'breed-filter active';
    allButton.onclick = () => handleFilter('all');
    container.appendChild(allButton);
    
    breedTypes.forEach(type => {
        const button = document.createElement('button');
        button.textContent = type;
        button.className = 'breed-filter';
        button.onclick = () => handleFilter(type);
        container.appendChild(button);
    });
}

export function handleFilter(selectedType) {
    const container = document.getElementById('data-container');
    const buttons = container.querySelectorAll('.breed-filter');
    buttons.forEach(button => {
        button.classList.toggle('active', 
            button.textContent === selectedType || 
            (selectedType === 'all' && button.textContent === '全部')
        );
    });

    const sections = container.querySelectorAll('.breed-section');
    sections.forEach(section => {
        const breedType = section.querySelector('.breed-title').textContent;
        section.style.display = 
            selectedType === 'all' || breedType === selectedType ? 'block' : 'none';
    });
}

export function showError(message) {
    const container = document.getElementById('data-container');
    container.innerHTML = `<div class="error">錯誤：${message}</div>`;
}

export function showNoData() {
    const container = document.getElementById('data-container');
    container.innerHTML = '<div class="total-info">目前沒有可用的資料</div>';
}

export function renderCards(breeds) {
    const container = document.getElementById('data-container');
    const template = document.getElementById('table-template');
    const content = template.content.cloneNode(true);
    
    // 合併相同批次的資料
    const mergedBreeds = mergeBreedsByBatch(breeds);
    
    // 更新總計資訊
    const totals = {
        totalMale: mergedBreeds.reduce((sum, breed) => sum + breed.total_male, 0),
        totalFemale: mergedBreeds.reduce((sum, breed) => sum + breed.total_female, 0),
        totalBatches: mergedBreeds.length
    };
    const totalInfo = content.querySelector('.total-info');
    totalInfo.textContent = formatTotalInfo(totals);
    
    // 分類資料
    const groupedBreeds = groupMergedBreedsByType(mergedBreeds);
    const breedTypes = Object.keys(groupedBreeds).sort();
    
    // 建立篩選按鈕
    createFilterButtons(breedTypes, content);
    
    // 建立各品種區段
    const sectionsContainer = content.querySelector('#breed-sections');
    breedTypes.forEach(type => {
        const section = createBreedSection(type, groupedBreeds[type]);
        sectionsContainer.appendChild(section);
    });
    
    container.innerHTML = '';
    container.appendChild(content);
}

// API operations
export async function fetchBreedingDataFromApi() {
    const response = await fetch('/breeding');
    return await response.json();
}

export async function fetchBreedingData() {
    try {
        const data = await fetchBreedingDataFromApi();
        
        if (data.status === 'success') {
            if (data.content?.breeds?.length > 0) {
                renderCards(data.content.breeds);
            } else {
                showNoData();
            }
        } else {
            throw new Error(data.msg || '發生錯誤');
        }
    } catch (error) {
        showError(error.message);
    }
} 