import json
import uuid
from datetime import date, datetime, timedelta

from pydantic import BaseModel, Field, field_validator


class DateData(BaseModel):
    id: str = Field(..., max_length=100, description="Calculation ID")
    base_date: date = Field(..., description="Base date for calculation")
    operation: str = Field(..., pattern="^(before|after)$", description="Must be 'before' or 'after'")
    amount: int = Field(..., ge=1, le=3650, description="Amount between 1 and 3650")
    unit: str = Field(..., pattern="^(days|weeks|months)$", description="Must be 'days', 'weeks', or 'months'")
    result: date = Field(..., description="Calculated result date")
    description: str = Field("", max_length=500, description="Description text, max 500 characters")

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        # Remove any potentially dangerous characters
        if v:
            # Strip whitespace and limit length
            v = v.strip()[:500]
            # Remove control characters but keep basic punctuation
            v = ''.join(char for char in v if char.isprintable() or char.isspace())
        return v

    def to_dict(self) -> dict:
        # 使用 Pydantic 的 model_dump，但自定義日期格式
        data = self.model_dump()
        data['base_date'] = self.base_date.strftime('%Y-%m-%d')
        data['result'] = self.result.strftime('%Y-%m-%d')
        data['type'] = 'calculation'  # 標記為日期推算類型
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "DateData":
        # 解析日期字串
        parsed_data = data.copy()
        parsed_data['base_date'] = datetime.strptime(data['base_date'], '%Y-%m-%d').date()
        parsed_data['result'] = datetime.strptime(data['result'], '%Y-%m-%d').date()
        parsed_data.pop('type', None)  # 移除類型標記
        return cls(**parsed_data)

    @classmethod
    def from_json(cls, json_str: str) -> "DateData":
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_form_input(cls, base_date: str, operation: str, amount: int, unit: str, id: str, description: str = "") -> "DateData":
        """從表單輸入創建 DateData，包含日期字串驗證和轉換"""
        # 驗證日期格式
        try:
            base_date_obj = datetime.strptime(base_date, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        
        # 處理新計算的 ID
        calc_id = id
        if calc_id == "new_calc":
            calc_id = str(uuid.uuid4().hex)
            
        return cls(
            id=calc_id,
            base_date=base_date_obj,
            operation=operation,
            amount=amount,
            unit=unit,
            result=base_date_obj,  # Will be calculated
            description=description
        )

    @classmethod
    def calculate_date(cls, data: "DateData") -> "DateData":
        if data.unit == "days":
            delta = timedelta(days=data.amount)
        elif data.unit == "weeks":
            delta = timedelta(weeks=data.amount)
        elif data.unit == "months":
            # More accurate month calculation
            if data.operation == "after":
                result_date = data.base_date
                for _ in range(data.amount):
                    if result_date.month == 12:
                        result_date = result_date.replace(year=result_date.year + 1, month=1)
                    else:
                        result_date = result_date.replace(month=result_date.month + 1)
                return cls(
                    id=str(uuid.uuid4().hex),
                    base_date=data.base_date,
                    operation=data.operation,
                    amount=data.amount,
                    unit=data.unit,
                    result=result_date,
                    description=data.description
                )
            else:
                result_date = data.base_date
                for _ in range(data.amount):
                    if result_date.month == 1:
                        result_date = result_date.replace(year=result_date.year - 1, month=12)
                    else:
                        result_date = result_date.replace(month=result_date.month - 1)
                return cls(
                    id=str(uuid.uuid4().hex),
                    base_date=data.base_date,
                    operation=data.operation,
                    amount=data.amount,
                    unit=data.unit,
                    result=result_date,
                    description=data.description
                )
        else:
            delta = timedelta(days=data.amount * 30)
        
        if data.operation == "after":
            result_date = data.base_date + delta
        else:
            result_date = data.base_date - delta
            
        return cls(
            id=str(uuid.uuid4()),
            base_date=data.base_date,
            operation=data.operation,
            amount=data.amount,
            unit=data.unit,
            result=result_date,
            description=data.description
        )


class DateInterval:
    def __init__(self, id: str, start_date: date, end_date: date, days_diff: int, description: str = ""):
        self.id = id
        self.start_date = start_date
        self.end_date = end_date
        self.days_diff = days_diff
        self.description = description
        
        # 計算詳細的週數和月數
        abs_days = abs(days_diff)
        
        # 週數計算：x週又y日
        self.weeks_full = abs_days // 7
        self.weeks_remainder_days = abs_days % 7
        
        # 月數計算：使用實際月份差異計算
        if start_date <= end_date:
            calc_start, calc_end = start_date, end_date
        else:
            calc_start, calc_end = end_date, start_date
            
        # 計算實際月份差異
        self.months_full = 0
        current_date = calc_start
        
        while True:
            # 計算下個月的同一天
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1)
            
            # 如果下個月超過結束日期，停止計算
            if next_month > calc_end:
                break
                
            self.months_full += 1
            current_date = next_month
        
        # 計算月數的餘數天數
        self.months_remainder_days = (calc_end - current_date).days
        
        # 保留原有的概算值以便向後相容
        self.weeks_approx = self.weeks_full
        self.months_approx = self.months_full
        
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'days_diff': self.days_diff,
            'weeks_approx': self.weeks_approx,
            'months_approx': self.months_approx,
            'weeks_full': self.weeks_full,
            'weeks_remainder_days': self.weeks_remainder_days,
            'months_full': self.months_full,
            'months_remainder_days': self.months_remainder_days,
            'description': self.description,
            'type': 'interval'  # 標記為間隔計算類型
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: dict) -> "DateInterval":
        return cls(
            id=data['id'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
            days_diff=data['days_diff'],
            description=data.get('description', '')
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "DateInterval":
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def calculate_interval(cls, start_date: date, end_date: date, description: str = "") -> "DateInterval":
        """計算兩個日期之間的間隔"""
        days_diff = (end_date - start_date).days
        
        return cls(
            id=str(uuid.uuid4().hex),
            start_date=start_date,
            end_date=end_date,
            days_diff=days_diff,
            description=description
        )
    
    @classmethod
    def from_form_input(cls, start_date: str, end_date: str, description: str = "") -> "DateInterval":
        """從表單輸入創建 DateInterval，包含日期字串驗證和轉換"""
        # 驗證日期格式
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        
        return cls.calculate_interval(start_date_obj, end_date_obj, description)