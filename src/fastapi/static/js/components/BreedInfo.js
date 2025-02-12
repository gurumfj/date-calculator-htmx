function BreedInfo({ date, supplier, breed, male, female, weekAge }) {
    const formatDate = (dateStr) => {
        return new Date(dateStr).toLocaleDateString('zh-TW');
    };

    return (
        <div className="sub-card">
            <div className="sub-card-info">
                <div className="sub-card-date">{formatDate(date)}</div>
                <div className="sub-card-supplier">{supplier}</div>
                <div className="sub-card-breed">{breed}</div>
                <div className="sub-card-week-age">{weekAge}週</div>
            </div>
            <div className="sub-card-numbers">
                <div className="sub-card-number">
                    <span className="sub-card-number-label">公</span>
                    <span className="sub-card-number-value">{male}</span>
                </div>
                <div className="sub-card-number">
                    <span className="sub-card-number-label">母</span>
                    <span className="sub-card-number-value">{female}</span>
                </div>
            </div>
        </div>
    );
} 