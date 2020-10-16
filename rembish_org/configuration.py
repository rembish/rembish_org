class Configuration:
    pass


class DevelopmentConfiguration(Configuration):
    SECRET_KEY = "3PhbRh2bJrfgN1K8AS9Q"


class ProductionConfiguration(Configuration):
    pass
