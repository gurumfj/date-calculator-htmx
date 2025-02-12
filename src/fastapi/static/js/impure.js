import { formatFieldValue } from './pure.js';

// DOM manipulation functions
function createCard(batch) {
    console.log('Creating card for batch:', batch); // 加入除錯訊息
    const template = document.getElementById('card-template');
    const cardElement = template.content.cloneNode(true);
    
    // 設定基本欄位
    const fields = {
        'batch_name': batch.batch_name,
        'farm_name': batch.farm_name,
        'address': batch.address,
        'farmer_name': batch.farmer_name,
        'total_male': batch.total_male,
        'total_female': batch.total_female,
        'veterinarian': batch.veterinarian,
        'batch_state': batch.batch_state
    };

    Object.entries(fields).forEach(([field, value]) => {
        const element = cardElement.querySelector(`[data-field="${field}"]`);
        if (element) {
            element.textContent = formatFieldValue(field, value);
        }
    });

    // 建立繁殖記錄
    const breedsInfoContainer = cardElement.querySelector('[data-field="breeds_info"]');
    if (breedsInfoContainer && batch.breed_date?.length > 0) {
        console.log('Processing breeds_info:', batch.breed_date); // 加入除錯訊息
        const breedInfoTemplate = document.getElementById('breed-info-template');
        
        batch.breed_date.forEach((date, index) => {
            console.log('Creating breed info element:', { date, supplier: batch.supplier[index], chicken_breed: batch.chicken_breed[index], male: batch.male[index], female: batch.female[index], week_age: batch.week_age[index] }); // 加入除錯訊息
            const breedInfoElement = breedInfoTemplate.content.cloneNode(true);
            
            const fields = {
                'breed_date': batch.breed_date[index],
                'supplier': batch.supplier[index],
                'chicken_breed': batch.chicken_breed[index],
                'male': batch.male[index],
                'female': batch.female[index],
                'week_age': batch.week_age[index]
            };

            Object.entries(fields).forEach(([field, value]) => {
                const element = breedInfoElement.querySelector(`[data-field="${field}"]`);
                if (element) {
                    element.textContent = formatFieldValue(field, value);
                }
            });
            
            breedsInfoContainer.appendChild(breedInfoElement);
        });
    } else {
        console.log('No breeds_info found or empty:', batch.breed_date); // 加入除錯訊息
    }
    
    return cardElement;
}

function showError(message) {
    const container = document.getElementById('data-container');
    if (container) {
        container.innerHTML = `<div class="error">錯誤：${message}</div>`;
    }
}

function showNoData() {
    const container = document.getElementById('data-container');
    if (container) {
        container.innerHTML = '<div class="total-info">目前沒有可用的資料</div>';
    }
}

function renderCards(data) {
    console.log('Rendering data:', data); // 加入除錯訊息
    const container = document.getElementById('data-container');
    const template = document.getElementById('table-template');
    if (!container || !template) return;

    const content = template.content.cloneNode(true);
    
    // 更新總計資訊
    const totalInfo = content.querySelector('.total-info');
    if (totalInfo) {
        const totalMale = data.batches.reduce((sum, batch) => sum + batch.total_male, 0);
        const totalFemale = data.batches.reduce((sum, batch) => sum + batch.total_female, 0);
        totalInfo.textContent = `總計：${data.batches.length} 批次，公雞 ${totalMale} 隻，母雞 ${totalFemale} 隻`;
    }
    
    // 建立篩選按鈕
    const filterContainer = content.querySelector('.filter-buttons');
    if (filterContainer) {
        // 取得所有不重複的品種
        const breeds = [...new Set(
            data.batches.flatMap(batch => 
                batch.chicken_breed
            )
        )].sort();

        // 建立全部按鈕
        const allButton = document.createElement('button');
        allButton.textContent = '全部';
        allButton.className = 'breed-filter active';
        allButton.onclick = () => handleFilter('all');
        filterContainer.appendChild(allButton);

        // 建立各品種按鈕
        breeds.forEach(breed => {
            const button = document.createElement('button');
            button.textContent = breed;
            button.className = 'breed-filter';
            button.onclick = () => handleFilter(breed);
            filterContainer.appendChild(button);
        });
    }
    
    // 建立卡片
    const cardsGrid = content.querySelector('.cards-grid');
    if (cardsGrid) {
        data.batches.forEach(batch => {
            const cardElement = createCard(batch);
            if (cardElement) {
                cardsGrid.appendChild(cardElement);
            }
        });
    }
    
    container.innerHTML = '';
    container.appendChild(content);
}

function handleFilter(selectedType) {
    const container = document.getElementById('data-container');
    if (!container) return;

    // 更新按鈕狀態
    const buttons = container.querySelectorAll('.breed-filter');
    buttons.forEach(button => {
        button.classList.toggle('active', 
            button.textContent === selectedType || 
            (selectedType === 'all' && button.textContent === '全部')
        );
    });

    // 更新卡片顯示
    const cards = container.querySelectorAll('.card');
    cards.forEach(card => {
        const breedInfos = card.querySelectorAll('.sub-card-breed');
        const hasBreed = selectedType === 'all' || 
            Array.from(breedInfos).some(info => info.textContent === selectedType);
        card.style.display = hasBreed ? 'block' : 'none';
    });
}

// API operations
async function fetchBreedingDataFromApi() {
    try {
        const response = await fetch('/breeds/not-completed');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('API Response:', data); // 加入除錯訊息
        return data;
    } catch (error) {
        console.error('API 請求失敗:', error);
        throw new Error('無法取得繁殖資料，請稍後再試');
    }
}

export async function fetchBreedingData() {
    try {
        const data = await fetchBreedingDataFromApi();
        console.log('Processed Data:', data); // 加入除錯訊息
        
        if (data.status === 'success' && data.content && data.content.batches) {
            if (data.content.batches.length > 0) {
                renderCards(data.content);
            } else {
                showNoData();
            }
        } else {
            throw new Error(data.msg || '發生錯誤');
        }
    } catch (error) {
        console.error('處理資料時發生錯誤:', error); // 加入除錯訊息
        showError(error.message);
    }
} 