// function selectTab(tab_id) {
//     const cssSelectedRemove = ["border-transparent", "bg-gray-100", "text-gray-600"];
//     const cssSelectedAdd = ["border-blue-500", "bg-white", "text-blue-600"];
//     document.querySelectorAll('.tab-button').forEach(button => {
//         button.classList.remove(...cssSelectedAdd);
//         button.classList.add(...cssSelectedRemove);
//         button.disabled = false;
//     });
//     document.getElementById(tab_id).classList.add(...cssSelectedAdd);
//     document.getElementById(tab_id).disabled = true;
// }

// 本地計算day_age
function dayAge(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    const diffTime = Math.abs(today - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
}

function weekAge(dayAge) {
    const dayOfWeek = [7, 1, 2, 3, 4, 5, 6];
    let week = Math.floor(dayAge / 7);
    let day = dayAge % 7;
    return `${week}/${dayOfWeek[day]}`;
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

            setTimeout(() => {
                this.currentValue = this.targetValue;
            }, 100);
        }
    }
}