// Type definitions
/**
 * @typedef {Object} BreedInfo
 * @property {string} breed_date - 入雛日期
 * @property {string} supplier - 供應商
 * @property {string} chicken_breed - 品種
 * @property {number} male - 公雞數
 * @property {number} female - 母雞數
 * @property {number} day_age - 日齡
 * @property {string} week_age - 週齡
 */

/**
 * @typedef {Object} BatchAggregateModel
 * @property {string} batch_name - 批次名稱
 * @property {string} farm_name - 農場名稱
 * @property {string} address - 農場地址
 * @property {string} farmer_name - 畜主姓名
 * @property {number} total_male - 總公雞數
 * @property {number} total_female - 總母雞數
 * @property {string} veterinarian - 獸醫師
 * @property {string} batch_state - 批次狀態
 * @property {string[]} breed_date - 入雛日期列表
 * @property {string[]} supplier - 供應商列表
 * @property {string[]} chicken_breed - 品種列表
 * @property {number[]} male - 公雞數列表
 * @property {number[]} female - 母雞數列表
 * @property {number[]} day_age - 日齡列表
 * @property {string[]} week_age - 週齡列表
 */

/**
 * @typedef {Object} ApiResponse
 * @property {string} status - 回應狀態
 * @property {string} msg - 回應訊息
 * @property {Object} content - 回應內容
 * @property {Batch[]} content.batches - 批次列表
 */

// Pure functions
export function formatTotalInfo(totals) {
    return `總計：${totals.total_batches} 批次，公雞 ${totals.total_male} 隻，母雞 ${totals.total_female} 隻`;
}

export function formatFieldValue(field, value) {
    if (value === null || value === undefined) {
        return '-';
    }

    if (field === 'breed_date') {
        return new Date(value).toLocaleDateString('zh-TW');
    }

    if (field === 'male' || field === 'female' || field === 'total_male' || field === 'total_female') {
        return value.toString();
    }

    if (field === 'batch_name' && !value) {
        return '未命名批次';
    }

    if (field === 'batch_state') {
        return value;
    }

    if (field === 'week_age') {
        return `${value}週`;
    }

    return value.toString();
} 