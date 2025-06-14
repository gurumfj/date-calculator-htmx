from typing import Optional
from pydantic import BaseModel, Field, field_validator


class FarmProductionValidator(BaseModel):
    """養殖場生產記錄驗證器 - 匹配資料庫表結構"""
    
    # 添加 unique_id 欄位以符合其他 validator 的格式
    unique_id: Optional[str] = Field(None, description="唯一識別碼")
    
    # 必填欄位
    batch_name: str = Field(..., description="批次名稱", alias="BatchName")
    
    # 基本資訊
    farm_location: Optional[str] = Field(None, description="場別", alias="場別")
    farmer: Optional[str] = Field(None, description="飼養者", alias="飼養者")
    chick_in_count: Optional[int] = Field(None, description="入雛數量", alias="入雛")
    chicken_out_count: Optional[int] = Field(None, description="出雞數量", alias="出雞")
    
    # 生產數據
    feed_weight: Optional[float] = Field(None, description="飼料總重量", alias="飼料總重")
    sale_weight_jin: Optional[float] = Field(None, description="銷售重量(斤)", alias="銷售重量_jin")
    fcr: Optional[float] = Field(None, description="換肉率 (Feed Conversion Ratio)", alias="換肉率")
    
    # 成本相關
    meat_cost: Optional[float] = Field(None, description="造肉成本", alias="造肉成本")
    avg_price: Optional[float] = Field(None, description="平均價格", alias="平均價")
    cost_price: Optional[float] = Field(None, description="成本價", alias="成本價")
    
    # 收支
    revenue: Optional[float] = Field(None, description="總收入", alias="總收入")
    expenses: Optional[float] = Field(None, description="總支出", alias="總支出")
    
    # 各項成本明細
    feed_cost: Optional[float] = Field(None, description="飼料費用", alias="飼料")
    vet_cost: Optional[float] = Field(None, description="獸醫防疫費用", alias="獸醫防疫")
    feed_med_cost: Optional[float] = Field(None, description="飼料自備藥費用", alias="飼料自備藥")
    farm_med_cost: Optional[float] = Field(None, description="公司藥品費用", alias="公司藥品")
    leg_band_cost: Optional[float] = Field(None, description="腳環費用", alias="腳環")
    chick_cost: Optional[float] = Field(None, description="雛雞款", alias="雛雞款")
    grow_fee: Optional[float] = Field(None, description="代養費", alias="代養費")
    catch_fee: Optional[float] = Field(None, description="抓工費用", alias="抓工")
    weigh_fee: Optional[float] = Field(None, description="磅單費用", alias="磅單")
    gas_cost: Optional[float] = Field(None, description="瓦斯費用", alias="瓦斯")
    
    @field_validator(
        'feed_weight', 'sale_weight_jin', 'fcr', 'meat_cost', 'avg_price', 'cost_price',
        'revenue', 'expenses', 'feed_cost', 'vet_cost', 'feed_med_cost', 'farm_med_cost',
        'leg_band_cost', 'chick_cost', 'grow_fee', 'catch_fee', 'weigh_fee', 'gas_cost',
        mode='before'
    )
    @classmethod
    def parse_float(cls, v):
        """解析浮點數值"""
        if v is None or v == '' or (hasattr(v, '__float__') and v != v):  # NaN check
            return None
        if isinstance(v, str):
            return float(v)
        return float(v)
    
    @field_validator(
        'farm_location', 'farmer',
        mode='before'
    )
    @classmethod
    def parse_string(cls, v):
        """解析字串值，處理 NaN"""
        if v is None or v == '' or (hasattr(v, '__float__') and v != v):  # NaN check
            return None
        return str(v)
    
    class Config:
        # 允許使用field名稱作為JSON key
        populate_by_name = True