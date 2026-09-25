"""Pydantic strict models for 10 inputs (1.1.0)."""
from typing import Literal
from pydantic import BaseModel, Field

AssetType = Literal["substation", "transmission_tower", "arterial_road",
                    "hospital", "cyclone_shelter", "water_plant", "telecom_tower"]


class Asset(BaseModel):
    model_config = {"extra": "allow"}
    asset_id: str
    asset_name: str
    asset_type: AssetType
    lat: float
    lon: float


class Met(BaseModel):
    model_config = {"extra": "allow"}
    cyclone_name: str
    cyclone_category: int
    eta_landfall: str
    intensity_kmh: float
    forward_speed_kmh: float
    rainfall_72h_mm: float
    tide_phase: str


class Ward(BaseModel):
    model_config = {"extra": "allow"}
    ward_code: str
    ward_name: str
    population: int
    vulnerability_index: float


class Dependency(BaseModel):
    model_config = {"extra": "allow"}
    from_asset: str
    to_asset: str
    dependency_type: Literal["power", "access", "function"] = "power"


class Regional(BaseModel):
    model_config = {"extra": "allow"}
    forecast_id: str
    district_name: str
    district_population: int
    primary_language: str
    bbox: list[float] = Field(min_length=4, max_length=4)


class ForecastInput(BaseModel):
    model_config = {"extra": "allow"}
    assets: list[Asset]
    met: Met
    wards: list[Ward]
    dependencies: list[Dependency]
    audience: dict[str, str]
    regional: Regional
    insurance: list[dict] = []
    raw: dict = {}
