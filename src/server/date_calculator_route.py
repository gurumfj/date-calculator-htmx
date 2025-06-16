import json
import uuid
from datetime import date, datetime, timedelta
from typing import List

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/server/templates")


class DateData:
    def __init__(self, id: str, base_date: date, operation: str, amount: int, unit: str, result: date):
        self.id = id
        self.base_date = base_date
        self.operation = operation
        self.amount = amount
        self.unit = unit
        self.result = result
        
        if self.operation not in ["before", "after"]:
            raise ValueError("wrong operation")
        elif self.unit not in ["days", "weeks", "months"]:
            raise ValueError("wrong unit")

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'base_date': self.base_date.strftime('%Y-%m-%d'),
            'operation': self.operation,
            'amount': self.amount,
            'unit': self.unit,
            'result': self.result.strftime('%Y-%m-%d')
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "DateData":
        return cls(
            id=data['id'],
            base_date=datetime.strptime(data['base_date'], '%Y-%m-%d').date(),
            operation=data['operation'],
            amount=data['amount'],
            unit=data['unit'],
            result=datetime.strptime(data['result'], '%Y-%m-%d').date()
        )

    @classmethod
    def from_json(cls, json_str: str) -> "DateData":
        data = json.loads(json_str)
        return cls.from_dict(data)

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
        )


def get_session_store(request: Request) -> List[DateData]:
    """Get date calculations from session"""
    if not hasattr(request, 'session'):
        return []
    
    store_json = request.session.get('date_store', [])
    return [DateData.from_json(json_str) for json_str in store_json]


def save_to_session(request: Request, store: List[DateData]):
    """Save date calculations to session"""
    if not hasattr(request, 'session'):
        return
    
    request.session['date_store'] = [data.to_json() for data in store]


@router.get("/", response_class=HTMLResponse)
async def get_date_calculator(request: Request):
    """日期計算機主頁面"""
    store = get_session_store(request)
    
    context = {
        "request": request,
        "store": store,
        "current_date": datetime.now().date().strftime('%Y-%m-%d')
    }
    
    return templates.TemplateResponse("date_calculator/index.html", context)


@router.post("/calculate", response_class=HTMLResponse)
async def calculate_date(
    request: Request,
    base_date: str = Form(...),
    operation: str = Form(...),
    amount: int = Form(...),
    unit: str = Form(...),
    id: str = Form(...)
):
    """執行日期計算"""
    try:
        base_date_obj = datetime.strptime(base_date, '%Y-%m-%d').date()
        
        # Generate new ID if it's a new calculation
        if id == "new_calc":
            id = str(uuid.uuid4().hex)
            
        data = DateData(
            id=id,
            base_date=base_date_obj,
            operation=operation,
            amount=amount,
            unit=unit,
            result=base_date_obj  # Will be calculated
        )
        
        result = DateData.calculate_date(data)
        
        # Add to session store
        store = get_session_store(request)
        store.append(result)
        save_to_session(request, store)
        
        context = {
            "request": request,
            "date_data": result
        }
        
        return templates.TemplateResponse("date_calculator/result_row.html", context)
        
    except ValueError as e:
        return HTMLResponse(content=f'<div style="color: red;">計算錯誤: {str(e)}</div>', status_code=400)


@router.post("/pickup", response_class=HTMLResponse)
async def pickup_date(
    request: Request,
    base_date: str = Form(...),
    operation: str = Form(...),
    amount: int = Form(...),
    unit: str = Form(...),
    id: str = Form(...)
):
    """拾取日期到表單"""
    try:
        base_date_obj = datetime.strptime(base_date, '%Y-%m-%d').date()
        
        data = DateData(
            id=id,
            base_date=base_date_obj,
            operation=operation,
            amount=amount,
            unit=unit,
            result=base_date_obj
        )
        
        context = {
            "request": request,
            "data": data
        }
        
        return templates.TemplateResponse("date_calculator/form.html", context)
        
    except ValueError as e:
        return HTMLResponse(content=f'<div style="color: red;">格式錯誤: {str(e)}</div>', status_code=400)


@router.delete("/delete/{id}", response_class=HTMLResponse)
async def delete_date_calculation(request: Request, id: str):
    """刪除單個計算記錄"""
    store = get_session_store(request)
    updated_store = [data for data in store if data.id != id]
    save_to_session(request, updated_store)
    
    return HTMLResponse(content="")


@router.post("/delete/all", response_class=HTMLResponse)
async def delete_all_calculations(request: Request):
    """清除所有計算記錄"""
    if hasattr(request, 'session'):
        request.session.pop('date_store', None)
    
    context = {
        "request": request,
        "store": []
    }
    
    return templates.TemplateResponse("date_calculator/result_table.html", context)