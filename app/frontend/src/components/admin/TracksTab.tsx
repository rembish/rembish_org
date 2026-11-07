import TripTracksTab from "../trip/TripTracksTab";

/** Logger upload for a whole card, and the days that belong to no trip. */
export default function TracksTab() {
  return (
    <div className="admin-tracks-tab">
      <p className="gps-tracks-intro">
        Upload every day file from the logger at once. Days inside a trip go to
        that trip's Tracks tab; days already on the site are skipped. Days in no
        trip, such as a day out in Czechia, are listed here.
      </p>
      <TripTracksTab />
    </div>
  );
}
