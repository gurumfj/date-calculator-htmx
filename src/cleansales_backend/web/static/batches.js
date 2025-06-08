// 本地計算day_age (包含起始日期的日齡計算)
function dayAge(dateStr) {
    try {
        // 解析輸入日期，設定為本地時間的午夜
        const [year, month, day] = dateStr.split('-').map(Number);
        const inputDate = new Date(year, month - 1, day); // month-1 因為月份是0-11
        
        // 設定今天為本地時間的午夜
        const today = new Date();
        const todayMidnight = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    
        // 計算今天減去輸入日期的天數，然後 +1 (包含起始日期)
        const diffTime = todayMidnight.getTime() - inputDate.getTime();
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24)) + 1;
        
        return diffDays;
    } catch (error) {
        console.error(error);
        return 0;
    }
}

function weekAge(dayAge) {
    const dayOfWeek = [7, 1, 2, 3, 4, 5, 6];
    let week = dayAge % 7 === 0 ? Math.floor(dayAge / 7) - 1 : Math.floor(dayAge / 7);
    let day = dayAge % 7;
    return `${week}/${dayOfWeek[day]}`;
}

function computeAge(dateStr) {
    const dayAgeNum = dayAge(dateStr);
    const weekAgeStr = weekAge(dayAgeNum);
    return {
        dayAgeStr: dayAgeNum,
        weekAgeStr: weekAgeStr,
    }
}

function processBar(data) {
    return {
        startValue: 0,
        targetValue: data || 0,
        currentValue: 0,
        initTransition(){
            // this.currentValue = 0;
            // this.$nextTick(() => {
            //     this.currentValue = this.targetValue;
            //     console.log(this.currentValue);
            // });
            // this.currentValue = 0;
            setTimeout(() => {
                // console.log(this.targetValue);
                this.currentValue = this.targetValue;
            }, 100);
        }
    }
}