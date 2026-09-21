
class Difference:

    def __init__(self, page: int, location: str, details: str):
        try:
            self.page = max(int(page), 0)
        except:
            self.page = -1
        try:
            self.details = str(details)
        except:
            self.details = ''
        try:
            self.location = str(location)
        except:
            self.location = 'unknown'

    def serialize(self):
        return {'page': self.page,
                'details': self.details,
                'location': self.location
                }

    def __eq__(self, other):
        return self.page == other.page and self.details == other.details and self.location == other.location

class ComparisonResult:

    differences = []

    def __init__(self, differences: list[Difference], full_response: bytes=b'{}'):
        self.differences = differences
        self.full_response = full_response

    def serialize(self):
        return {'differences': [difference.serialize() for difference in self.differences],
                'full_response': self.full_response.decode("utf-8")}


