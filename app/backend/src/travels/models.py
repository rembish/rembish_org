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
    country_code: str | None = None


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


class FlightMapAirport(BaseModel):
    iata_code: str
    name: str | None
    lat: float
    lng: float
    flights_count: int = 0


class FlightMapRoute(BaseModel):
    from_iata: str
    to_iata: str
    count: int


class FlightMapData(BaseModel):
    airports: list[FlightMapAirport]
    routes: list[FlightMapRoute]
    country_regions: dict[str, int]  # map region code -> airport count


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


class HealthVaccination(BaseModel):
    vaccine: str
    priority: str  # "required", "recommended", "consider", "cdc_recommended"
    notes: str | None = None
    covered: bool = False  # True if user has this vaccination


class MalariaInfo(BaseModel):
    risk: bool = False
    areas: str | None = None
    species: str | None = None
    prophylaxis: list[str] = []
    drug_resistance: list[str] = []


class HealthRequirements(BaseModel):
    vaccinations_required: list[HealthVaccination] = []
    vaccinations_recommended: list[HealthVaccination] = []
    vaccinations_routine: list[str] = []
    malaria: MalariaInfo | None = None
    other_risks: list[str] = []


class TripTravelDocInfo(BaseModel):
    id: int
    doc_type: str
    label: str
    valid_until: str | None
    entry_type: str | None
    passport_label: str | None = None
    expires_before_trip: bool = False
    has_files: bool = False


class TripFixerInfo(BaseModel):
    id: int
    name: str
    type: str
    whatsapp: str | None
    phone: str | None
    rating: int | None
    is_assigned: bool


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
    health: HealthRequirements | None = None
    travel_docs: list[TripTravelDocInfo] = []
    fixers: list[TripFixerInfo] = []


class TripCountryInfoResponse(BaseModel):
    countries: list[CountryInfoData]


class VacationSummary(BaseModel):
    annual_days: int  # 30
    used_days: float  # past regular trips
    planned_days: float  # future regular trips
    remaining_days: float  # annual - used - planned


# Personal events models
class EventData(BaseModel):
    id: int
    event_date: str  # ISO date YYYY-MM-DD
    end_date: str | None  # ISO date or null for single-day
    title: str
    note: str | None
    category: str
    category_emoji: str


class EventsResponse(BaseModel):
    events: list[EventData]
    total: int
    categories: dict[str, str]  # category name -> emoji


class EventCreateRequest(BaseModel):
    event_date: str  # YYYY-MM-DD
    end_date: str | None = None
    title: str
    note: str | None = None
    category: str = "other"


class EventUpdateRequest(BaseModel):
    event_date: str | None = None
    end_date: str | None = None
    title: str | None = None
    note: str | None = None
    category: str | None = None


# Flight models
class AirportData(BaseModel):
    id: int
    iata_code: str
    name: str | None
    city: str | None
    country_code: str | None


class FlightData(BaseModel):
    id: int
    trip_id: int
    flight_date: str  # ISO date (departure)
    flight_number: str
    airline_name: str | None
    departure_airport: AirportData
    arrival_airport: AirportData
    departure_time: str | None
    arrival_time: str | None
    arrival_date: str | None  # ISO date, null if same as flight_date
    terminal: str | None
    arrival_terminal: str | None
    gate: str | None
    aircraft_type: str | None
    seat: str | None
    booking_reference: str | None
    notes: str | None


class FlightLookupLeg(BaseModel):
    flight_number: str
    airline_name: str | None
    departure_iata: str
    departure_name: str | None
    arrival_iata: str
    arrival_name: str | None
    departure_time: str | None  # "HH:MM"
    arrival_time: str | None  # "HH:MM"
    departure_date: str | None  # YYYY-MM-DD
    arrival_date: str | None  # YYYY-MM-DD (if different from departure)
    terminal: str | None
    arrival_terminal: str | None
    aircraft_type: str | None


class FlightLookupResponse(BaseModel):
    legs: list[FlightLookupLeg]
    error: str | None = None


class FlightCreateRequest(BaseModel):
    flight_date: str  # YYYY-MM-DD (departure)
    flight_number: str
    airline_name: str | None = None
    departure_iata: str
    arrival_iata: str
    departure_time: str | None = None
    arrival_time: str | None = None
    arrival_date: str | None = None  # YYYY-MM-DD, null if same day
    terminal: str | None = None
    arrival_terminal: str | None = None
    gate: str | None = None
    aircraft_type: str | None = None
    seat: str | None = None
    booking_reference: str | None = None
    notes: str | None = None


class ExtractedFlightResponse(BaseModel):
    flight_date: str | None = None
    flight_number: str | None = None
    airline_name: str | None = None
    departure_iata: str | None = None
    arrival_iata: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    arrival_date: str | None = None
    terminal: str | None = None
    arrival_terminal: str | None = None
    aircraft_type: str | None = None
    seat: str | None = None
    booking_reference: str | None = None
    is_duplicate: bool = False


class FlightExtractResponse(BaseModel):
    flights: list[ExtractedFlightResponse] = []
    error: str | None = None


class FlightsResponse(BaseModel):
    flights: list[FlightData]


# Car rental models
class CarRentalData(BaseModel):
    id: int
    trip_id: int
    rental_company: str
    car_class: str | None
    actual_car: str | None
    transmission: str | None
    pickup_location: str | None
    dropoff_location: str | None
    pickup_datetime: str | None
    dropoff_datetime: str | None
    is_paid: bool | None
    total_amount: str | None
    confirmation_number: str | None
    notes: str | None


class CarRentalCreateRequest(BaseModel):
    rental_company: str
    car_class: str | None = None
    actual_car: str | None = None
    transmission: str | None = None
    pickup_location: str | None = None
    dropoff_location: str | None = None
    pickup_datetime: str | None = None
    dropoff_datetime: str | None = None
    is_paid: bool | None = None
    total_amount: str | None = None
    confirmation_number: str | None = None
    notes: str | None = None


class ExtractedCarRentalResponse(BaseModel):
    rental_company: str | None = None
    car_class: str | None = None
    transmission: str | None = None
    pickup_location: str | None = None
    dropoff_location: str | None = None
    pickup_datetime: str | None = None
    dropoff_datetime: str | None = None
    is_paid: bool | None = None
    total_amount: str | None = None
    confirmation_number: str | None = None
    notes: str | None = None
    is_duplicate: bool = False


class CarRentalExtractResponse(BaseModel):
    rental: ExtractedCarRentalResponse | None = None
    error: str | None = None


class CarRentalsResponse(BaseModel):
    car_rentals: list[CarRentalData]


class RankedItem(BaseModel):
    name: str
    count: int
    extra: str | None = None


class YearFlightCount(BaseModel):
    year: int
    count: int


class FlightStatsResponse(BaseModel):
    total_flights: int
    total_airports: int
    total_airlines: int
    total_aircraft_types: int
    top_airlines: list[RankedItem]
    top_airports: list[RankedItem]
    top_routes: list[RankedItem]
    aircraft_types: list[RankedItem]
    flights_by_year: list[YearFlightCount]
