import { formatFieldValue, formatTotalInfo } from './pure.js';

// DOM manipulation functions
export function createMergedCard(card) {
    const template = document.getElementById('card-template');
    const cardElement = template.content.cloneNode(true);
    
    // 設定批次名稱
    const title = cardElement.querySelector('[data-field="batch_name"]');
    title.textContent = formatFieldValue('batch_name', card.batch_name);

    // 設定其他欄位
    const fields = {
        'farm_name': card.farm_name,
        'address': card.address,
        'farmer_name': card.farmer_name,
        'chicken_breed': card.chicken_breed,
        'total_male': card.total_male,
        'total_female': card.total_female,
        'veterinarian': card.veterinarian,
        'is_completed': card.is_completed
    };

    Object.entries(fields).forEach(([field, value]) => {
        const element = cardElement.querySelector(`[data-field="${field}"]`);
        if (element) {
            element.textContent = formatFieldValue(field, value);
        }
    });

    // 單筆記錄時，顯示入雛日期和供應商
    if (card.sub_cards?.length === 0 && (card.breed_date || card.supplier)) {
        const dateField = cardElement.querySelector('.essential-info');
        if (dateField) {
            if (card.breed_date) {
                const dateElement = document.createElement('div');
                dateElement.className = 'card-field';
                dateElement.innerHTML = `
                    <span class="field-label">入雛日期</span>
                    <span class="field-value">${formatFieldValue('breed_date', card.breed_date)}</span>
                `;
                dateField.insertBefore(dateElement, dateField.firstChild);
            }
            
            if (card.supplier) {
                const supplierElement = document.createElement('div');
                supplierElement.className = 'card-field';
                supplierElement.innerHTML = `
                    <span class="field-label">供應商</span>
                    <span class="field-value">${formatFieldValue('supplier', card.supplier)}</span>
                `;
                dateField.insertBefore(supplierElement, dateField.firstChild.nextSibling);
            }
        }
    }

    // 建立子卡片
    const subCardsContainer = cardElement.querySelector('[data-field="sub_cards"]');
    if (subCardsContainer) {
        if (card.sub_cards?.length > 0) {
            const subCardTemplate = document.getElementById('sub-card-template');
            if (subCardTemplate) {
                card.sub_cards.forEach(record => {
                    const subCard = subCardTemplate.content.cloneNode(true);
                    
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
            }
        } else {
            subCardsContainer.remove();
        }
    }
    
    return cardElement;
}

export function createBreedSection(section) {
    const template = document.getElementById('breed-section-template');
    if (!template) return null;

    const sectionElement = template.content.cloneNode(true);
    
    const title = sectionElement.querySelector('.breed-title');
    if (title) {
        title.textContent = section.breed_type;
    }
    
    const stats = sectionElement.querySelector('.breed-stats');
    if (stats) {
        stats.textContent = `${section.total_batches} 批次 | 公雞 ${section.total_male} 隻 | 母雞 ${section.total_female} 隻`;
    }
    
    const grid = sectionElement.querySelector('.cards-grid');
    if (grid && Array.isArray(section.cards)) {
        section.cards.forEach(card => {
            const cardElement = createMergedCard(card);
            if (cardElement) {
                grid.appendChild(cardElement);
            }
        });
    }
    
    return sectionElement;
}

export function createFilterButtons(sections, content) {
    const container = content.querySelector('.filter-buttons');
    if (!container || !Array.isArray(sections)) return;

    // 建立全部按鈕
    const allButton = document.createElement('button');
    allButton.textContent = '全部';
    allButton.className = 'breed-filter active';
    allButton.onclick = () => handleFilter('all');
    container.appendChild(allButton);
    
    // 建立各品種按鈕
    sections.forEach(section => {
        const button = document.createElement('button');
        button.textContent = section.breed_type;
        button.className = 'breed-filter';
        button.onclick = () => handleFilter(section.breed_type);
        container.appendChild(button);
    });
}

export function handleFilter(selectedType) {
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

    // 更新區段顯示
    const sections = container.querySelectorAll('.breed-section');
    sections.forEach(section => {
        const breedType = section.querySelector('.breed-title')?.textContent;
        if (breedType) {
            section.style.display = 
                selectedType === 'all' || breedType === selectedType ? 'block' : 'none';
        }
    });
}

export function showError(message) {
    const container = document.getElementById('data-container');
    if (container) {
        container.innerHTML = `<div class="error">錯誤：${message}</div>`;
    }
}

export function showNoData() {
    const container = document.getElementById('data-container');
    if (container) {
        container.innerHTML = '<div class="total-info">目前沒有可用的資料</div>';
    }
}

export function renderCards(data) {
    const container = document.getElementById('data-container');
    const template = document.getElementById('table-template');
    if (!container || !template) return;

    const content = template.content.cloneNode(true);
    
    // 更新總計資訊
    const totalInfo = content.querySelector('.total-info');
    if (totalInfo) {
        totalInfo.textContent = formatTotalInfo(data);
    }
    
    // 建立篩選按鈕
    createFilterButtons(data.sections, content);
    
    // 建立各品種區段
    const sectionsContainer = content.querySelector('#breed-sections');
    if (sectionsContainer && Array.isArray(data.sections)) {
        data.sections.forEach(section => {
            const sectionElement = createBreedSection(section);
            if (sectionElement) {
                sectionsContainer.appendChild(sectionElement);
            }
        });
    }
    
    container.innerHTML = '';
    container.appendChild(content);
}

// API operations
export async function fetchBreedingDataFromApi() {
    try {
        const response = await fetch('/breeds/not-completed');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API 請求失敗:', error);
        throw new Error('無法取得繁殖資料，請稍後再試');
    }
}

export async function fetchBreedingData() {
    try {
        const data = await fetchBreedingDataFromApi();
        
        if (data.status === 'success' && data.content) {
            if (data.content.sections?.length > 0) {
                renderCards(data.content);
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