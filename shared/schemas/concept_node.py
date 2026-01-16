"""概念节点数据模型"""

from pydantic import BaseModel, Field
from typing import Optional


class ConceptNode(BaseModel):
    """概念节点数据模型"""
    
    id: str = Field(
        ..., 
        description="唯一标识，格式: {概念名}_{学科拼音}",
        min_length=1,
        max_length=200
    )
    label: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="概念名称"
    )
    discipline: str = Field(
        ..., 
        description="所属学科"
    )
    definition: str = Field(
        ..., 
        max_length=200, 
        description="简短定义"
    )
    credibility: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="可信度分数"
    )
    metadata: Optional[dict] = Field(
        default=None, 
        description="额外元数据"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "entropy_xinxilun",
                "label": "熵",
                "discipline": "信息论",
                "definition": "信息的不确定性度量",
                "credibility": 0.95,
                "metadata": {
                    "wikipedia_url": "https://zh.wikipedia.org/wiki/熵_(信息论)",
                    "keywords": ["信息", "不确定性", "香农"]
                }
            }
        }
