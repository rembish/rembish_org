export type TripTab = "edit" | "info" | "transport" | "stays";

export interface TCCDestinationOption {
  id: number;
  name: string;
  region: string;
  country_code: string | null;
}

export interface UserOption {
  id: number;
  name: string | null;
  nickname: string | null;
  picture: string | null;
}

export interface TripDestinationInput {
  tcc_destination_id: number;
  is_partial: boolean;
}

export interface TripCityInput {
  name: string;
  is_partial: boolean;
}

export interface CitySearchResult {
  name: string;
  country: string | null;
  country_code: string | null;
  display_name: string | null;
  source: string;
}

export interface TripHoliday {
  date: string;
  name: string;
  local_name: string | null;
  country_code: string;
  country_name: string;
}

export interface TripFormData {
  start_date: string;
  end_date: string | null;
  trip_type: string;
  flights_count: number | null;
  working_days: number | null;
  rental_car: string | null;
  description: string | null;
  departure_type: string;
  arrival_type: string;
  destinations: TripDestinationInput[];
  cities: TripCityInput[];
  participant_ids: number[];
  other_participants_count: number | null;
}

// Country info types
export interface CountryInfoTCCDest {
  name: string;
  is_partial: boolean;
}

export interface CurrencyInfo {
  code: string;
  name: string | null;
  rates: Record<string, number> | null;
}

export interface WeatherInfo {
  avg_temp_c: number | null;
  min_temp_c: number | null;
  max_temp_c: number | null;
  avg_precipitation_mm: number | null;
  rainy_days: number | null;
  month: string;
}

export interface CountryHoliday {
  date: string;
  name: string;
  local_name: string | null;
}

export interface SunriseSunset {
  sunrise: string;
  sunset: string;
  day_length_hours: number;
}

export interface HealthVaccination {
  vaccine: string;
  priority: string;
  notes: string | null;
  covered: boolean;
}

export interface MalariaInfo {
  risk: boolean;
  areas: string | null;
  species: string | null;
  prophylaxis: string[];
  drug_resistance: string[];
}

export interface HealthRequirements {
  vaccinations_required: HealthVaccination[];
  vaccinations_recommended: HealthVaccination[];
  vaccinations_routine: string[];
  malaria: MalariaInfo | null;
  other_risks: string[];
}

export interface TripTravelDocInfo {
  id: number;
  doc_type: string;
  label: string;
  valid_until: string | null;
  entry_type: string | null;
  passport_label: string | null;
  expires_before_trip: boolean;
  has_files: boolean;
}

export interface TripFixerInfo {
  id: number;
  name: string;
  type: string;
  whatsapp: string | null;
  phone: string | null;
  rating: number | null;
  is_assigned: boolean;
}

export interface CountryInfoData {
  country_name: string;
  iso_alpha2: string;
  tcc_destinations: CountryInfoTCCDest[];
  socket_types: string | null;
  voltage: string | null;
  phone_code: string | null;
  driving_side: string | null;
  emergency_number: string | null;
  tap_water: string | null;
  currency: CurrencyInfo | null;
  weather: WeatherInfo | null;
  timezone_offset_hours: number | null;
  holidays: CountryHoliday[];
  languages: string | null;
  tipping: string | null;
  speed_limits: string | null;
  visa_free_days: number | null;
  eu_roaming: boolean | null;
  adapter_needed: boolean | null;
  sunrise_sunset: SunriseSunset | null;
  health: HealthRequirements | null;
  travel_docs: TripTravelDocInfo[];
  fixers: TripFixerInfo[];
}

// Flight types
export interface AirportData {
  id: number;
  iata_code: string;
  name: string | null;
  city: string | null;
  country_code: string | null;
}

export interface FlightDataItem {
  id: number;
  trip_id: number;
  flight_date: string;
  flight_number: string;
  airline_name: string | null;
  departure_airport: AirportData;
  arrival_airport: AirportData;
  departure_time: string | null;
  arrival_time: string | null;
  arrival_date: string | null;
  terminal: string | null;
  arrival_terminal: string | null;
  gate: string | null;
  aircraft_type: string | null;
  seat: string | null;
  booking_reference: string | null;
  notes: string | null;
}

export interface ExtractedFlightData {
  flight_date: string | null;
  flight_number: string | null;
  airline_name: string | null;
  departure_iata: string | null;
  arrival_iata: string | null;
  departure_time: string | null;
  arrival_time: string | null;
  arrival_date: string | null;
  terminal: string | null;
  arrival_terminal: string | null;
  aircraft_type: string | null;
  seat: string | null;
  booking_reference: string | null;
  is_duplicate: boolean;
}

export interface FlightLookupLeg {
  flight_number: string;
  airline_name: string | null;
  departure_iata: string;
  departure_name: string | null;
  arrival_iata: string;
  arrival_name: string | null;
  departure_time: string | null;
  arrival_time: string | null;
  departure_date: string | null;
  arrival_date: string | null;
  terminal: string | null;
  arrival_terminal: string | null;
  aircraft_type: string | null;
}

export interface CarRentalItem {
  id: number;
  trip_id: number;
  rental_company: string;
  car_class: string | null;
  actual_car: string | null;
  transmission: string | null;
  pickup_location: string | null;
  dropoff_location: string | null;
  pickup_datetime: string | null;
  dropoff_datetime: string | null;
  is_paid: boolean | null;
  total_amount: string | null;
  confirmation_number: string | null;
  notes: string | null;
}

export interface ExtractedCarRentalData {
  rental_company: string | null;
  car_class: string | null;
  transmission: string | null;
  pickup_location: string | null;
  dropoff_location: string | null;
  pickup_datetime: string | null;
  dropoff_datetime: string | null;
  is_paid: boolean | null;
  total_amount: string | null;
  confirmation_number: string | null;
  notes: string | null;
  is_duplicate: boolean;
}

export interface TransportBookingItem {
  id: number;
  trip_id: number;
  type: string;
  operator: string | null;
  service_number: string | null;
  departure_station: string | null;
  arrival_station: string | null;
  departure_datetime: string | null;
  arrival_datetime: string | null;
  carriage: string | null;
  seat: string | null;
  booking_reference: string | null;
  has_document: boolean;
  document_name: string | null;
  document_mime_type: string | null;
  document_size: number | null;
  notes: string | null;
}

export interface ExtractedTransportBookingData {
  type: string | null;
  operator: string | null;
  service_number: string | null;
  departure_station: string | null;
  arrival_station: string | null;
  departure_datetime: string | null;
  arrival_datetime: string | null;
  carriage: string | null;
  seat: string | null;
  booking_reference: string | null;
  notes: string | null;
  is_duplicate: boolean;
}

export interface AccommodationItem {
  id: number;
  trip_id: number;
  property_name: string;
  platform: string | null;
  checkin_date: string | null;
  checkout_date: string | null;
  address: string | null;
  total_amount: string | null;
  payment_status: string | null;
  payment_date: string | null;
  guests: number | null;
  rooms: number | null;
  confirmation_code: string | null;
  booking_url: string | null;
  has_document: boolean;
  document_name: string | null;
  document_mime_type: string | null;
  document_size: number | null;
  notes: string | null;
}

export interface ExtractedAccommodationData {
  property_name: string | null;
  platform: string | null;
  checkin_date: string | null;
  checkout_date: string | null;
  address: string | null;
  total_amount: string | null;
  payment_status: string | null;
  payment_date: string | null;
  guests: number | null;
  rooms: number | null;
  confirmation_code: string | null;
  notes: string | null;
  is_duplicate: boolean;
}
