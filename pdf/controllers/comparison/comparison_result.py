
class Difference:

    def __init__(self, page: int, location: str, details: str):
        try:
            self.page = max(int(page), 0)
        except:
            pass
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

    def __init__(self, differences: list[Difference]):
        self.differences = differences

    def serialize(self):
        return {'differences': [difference.serialize() for difference in self.differences]}


