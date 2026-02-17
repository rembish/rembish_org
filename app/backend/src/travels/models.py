from pydantic import BaseModel


class TravelStats(BaseModel):
    un_visited: int
    un_total: int
    un_planned: int = 0
    tcc_visited: int
    tcc_total: int
    tcc_planned: int = 0
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
    visit_date: str | None  # ISO date (last visit) or null
    visit_count: int  # number of completed trips
    planned_count: int = 0  # number of future trips
    driving_type: str | None = None  # 'rental', 'own', or null
    drone_flown: bool | None = None


class TCCDestinationData(BaseModel):
    name: str
    region: str
    visit_date: str | None  # ISO date (first visit) or null
    visit_count: int  # number of completed trips
    planned_count: int = 0  # number of future trips


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
    visit_counts: dict[str, int]  # region_code -> number of trips
    region_names: dict[str, str]  # region_code -> display name (for territories)
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
    departure_type: str = "morning"
    arrival_type: str = "evening"
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
    departure_type: str = "morning"
    arrival_type: str = "evening"
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
    departure_type: str | None = None
    arrival_type: str | None = None
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


class PublicHoliday(BaseModel):
    date: str  # ISO date YYYY-MM-DD
    name: str
    local_name: str | None


class HolidaysResponse(BaseModel):
    holidays: list[PublicHoliday]


class UNCountryActivityUpdate(BaseModel):
    driving_type: str | None = None
    drone_flown: bool | None = None


class CityMarkerData(BaseModel):
    name: str
    lat: float
    lng: float
    is_partial: bool = False


class MapCitiesResponse(BaseModel):
    cities: list[CityMarkerData]


# Country info models for trip info tab
class CountryInfoTCCDestination(BaseModel):
    name: str
    is_partial: bool = False


class CurrencyInfo(BaseModel):
    code: str
    name: str | None = None  # full currency name, e.g. "US Dollar"
    rates: dict[str, float] | None  # {"CZK": 25.5, "EUR": 1.0, "USD": 1.08}


class WeatherInfo(BaseModel):
    avg_temp_c: float | None = None
    min_temp_c: float | None = None  # night / daily minimum
    max_temp_c: float | None = None  # day / daily maximum
    avg_precipitation_mm: float | None = None
    rainy_days: int | None = None  # days with precipitation > 0.5mm
    month: str  # "January", "February", etc.


class CountryHoliday(BaseModel):
    date: str  # ISO date YYYY-MM-DD
    name: str
    local_name: str | None


class SunriseSunset(BaseModel):
    sunrise: str  # "06:42"
    sunset: str  # "18:15"
    day_length_hours: float  # 11.5


class CountryInfoData(BaseModel):
    country_name: str
    iso_alpha2: str
    tcc_destinations: list[CountryInfoTCCDestination]
    socket_types: str | None
    voltage: str | None
    phone_code: str | None
    driving_side: str | None
    emergency_number: str | None
    tap_water: str | None
    currency: CurrencyInfo | None
    weather: WeatherInfo | None
    timezone_offset_hours: float | None  # +2.0 means "2h ahead of CET"
    holidays: list[CountryHoliday]
    languages: str | None
    tipping: str | None
    speed_limits: str | None  # "city/rural/highway" in km/h
    visa_free_days: int | None  # NULL = unlimited (EU)
    eu_roaming: bool | None
    adapter_needed: bool | None  # computed: True if country sockets differ from CZ
    sunrise_sunset: SunriseSunset | None


class TripCountryInfoResponse(BaseModel):
    countries: list[CountryInfoData]


class VacationSummary(BaseModel):
    annual_days: int  # 30
    used_days: float  # past regular trips
    planned_days: float  # future regular trips
    remaining_days: float  # annual - used - planned
