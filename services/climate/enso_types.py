"""
services/climate/enso_types.py — Type definitions, Enums, and Data Models for ENSO Intelligence
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class EnsoPhase(str, Enum):
    EL_NINO = "EL_NINO"
    LA_NINA = "LA_NINA"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


class EnsoIntensity(str, Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    UNKNOWN = "UNKNOWN"


class ImpactLevel(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


class SourceMeta(BaseModel):
    name: str = "NOAA Climate Prediction Center (CPC)"
    url: str = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"


class EnsoDataModel(BaseModel):
    phase: EnsoPhase = EnsoPhase.UNKNOWN
    intensity: EnsoIntensity = EnsoIntensity.UNKNOWN
    confidence: float = 0.0
    anomaly: Optional[float] = None
    observationPeriod: Optional[str] = None
    forecastPeriod: Optional[str] = None
    source: SourceMeta = Field(default_factory=SourceMeta)
    updatedAt: str = ""
    # Additional MIRROR CITY extensions (nullable/defaulted)
    soi: Optional[float] = None
    sstObserved: Optional[float] = None
    statusDescription: Optional[str] = None
    available: bool = True
    cached: bool = False


class ImpactItem(BaseModel):
    level: ImpactLevel = ImpactLevel.MODERATE
    confidence: float = 0.60
    drivers: List[str] = Field(default_factory=list)
    explanation: str = ""


class CityImpactData(BaseModel):
    city: str
    country: Optional[str] = None
    enso: Dict[str, Any]
    impacts: Dict[str, Any]
    drivers: List[str] = Field(default_factory=list)
    climateDna: Optional[Dict[str, Any]] = None
