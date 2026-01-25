from pydantic import BaseModel


class TravelStats(BaseModel):
    un_visited: int
    un_total: int
    tcc_visited: int
    tcc_total: int
    nm_visited: int
    nm_total: int


class MicrostateData(BaseModel):
    name: str
    longitude: float
    latitude: float
    map_region_code: str


class UNCountryData(BaseModel):
    name: str
    continent: str
    visit_date: str | None  # ISO date or null


class TCCDestinationData(BaseModel):
    name: str
    region: str
    visit_date: str | None  # ISO date or null


class NMRegionData(BaseModel):
    name: str
    country: str
    first_visited_year: int | None
    last_visited_year: int | None


class TravelData(BaseModel):
    stats: TravelStats
    visited_map_regions: dict[str, str]  # region_code -> first_visit_date (ISO)
    visited_countries: list[str]
    microstates: list[MicrostateData]
    un_countries: list[UNCountryData]
    tcc_destinations: list[TCCDestinationData]
    nm_regions: list[NMRegionData]


class MapData(BaseModel):
    stats: TravelStats
    visited_map_regions: dict[str, str]  # region_code -> first_visit_date (ISO)
    visited_countries: list[str]
    microstates: list[MicrostateData]


class UNCountriesResponse(BaseModel):
    countries: list[UNCountryData]


class TCCDestinationsResponse(BaseModel):
    destinations: list[TCCDestinationData]


class UploadResult(BaseModel):
    total: int
    visited: int
    message: str


class TripDestinationData(BaseModel):
    name: str
    is_partial: bool


class TripCityData(BaseModel):
    name: str
    is_partial: bool


class TripParticipantData(BaseModel):
    id: int
    name: str | None
    nickname: str | None
    picture: str | None


class TripData(BaseModel):
    id: int
    start_date: str  # ISO date
    end_date: str | None  # ISO date
    trip_type: str  # regular, work, relocation
    flights_count: int | None
    working_days: int | None
    rental_car: str | None
    description: str | None
    destinations: list[TripDestinationData]
    cities: list[TripCityData]
    participants: list[TripParticipantData]
    other_participants_count: int | None


class TripsResponse(BaseModel):
    trips: list[TripData]
    total: int


# Request models for trip CRUD
class TripDestinationInput(BaseModel):
    tcc_destination_id: int
    is_partial: bool = False


class TripCityInput(BaseModel):
    name: str
    is_partial: bool = False


class TripCreateRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str | None = None
    trip_type: str = "regular"
    flights_count: int | None = None
    working_days: int | None = None
    rental_car: str | None = None
    description: str | None = None
    destinations: list[TripDestinationInput] = []
    cities: list[TripCityInput] = []
    participant_ids: list[int] = []
    other_participants_count: int | None = None


class TripUpdateRequest(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    trip_type: str | None = None
    flights_count: int | None = None
    working_days: int | None = None
    rental_car: str | None = None
    description: str | None = None
    destinations: list[TripDestinationInput] | None = None
    cities: list[TripCityInput] | None = None
    participant_ids: list[int] | None = None
    other_participants_count: int | None = None


# Option models for form selectors
class TCCDestinationOption(BaseModel):
    id: int
    name: str
    region: str
    country_code: str | None  # ISO alpha-2 for Nominatim filtering


class TCCDestinationOptionsResponse(BaseModel):
    destinations: list[TCCDestinationOption]


class CitySearchResult(BaseModel):
    name: str
    country: str | None
    country_code: str | None  # ISO alpha-2 for flag display
    display_name: str | None
    lat: float | None
    lng: float | None
    source: str  # "local" or "nominatim"


class CitySearchResponse(BaseModel):
    results: list[CitySearchResult]


class UserOption(BaseModel):
    id: int
    name: str | None
    nickname: str | None
    picture: str | None


class UserOptionsResponse(BaseModel):
    users: list[UserOption]
