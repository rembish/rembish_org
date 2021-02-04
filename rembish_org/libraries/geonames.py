from urllib.parse import urljoin

from requests import get


class Geonames:
    BASE_URL = "http://api.geonames.org"

    def __init__(self, app=None):
        self.username = None
        self.language = "en"

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.username = app.config.get("GEONAMES_USERNAME")

    def call(self, uri, **parameters):
        parameters.setdefault("username", self.username)
        return get(urljoin(self.BASE_URL, uri), params=parameters)

    def get_code_by(self, latitude, longitude):
        response = self.call("/countryCode", lat=latitude, lng=longitude)
        code = response.text
        if code.startswith("err:"):
            return None
        return code.strip().lower()

    def get_country_by(self, code):
        response = self.call("/countryInfoJSON", lang=self.language, country=code)
        json = response.json()
        return json["geonames"][0]

    def get_settlement_by(self, name, country):
        response = self.call("/search", name=name, lang=self.language, country=country, featureClass="P", type="json")
        json = response.json()
        try:
            return json["geonames"][0]
        except (KeyError, IndexError):
            return None


geonames = Geonames()
