from abc import ABC

# noinspection PyUnresolvedReferences
from sattrack.api import Satellite, TwoLineElement


class StarlinkSatellite(Satellite):
    __slots__ = 'raan', 'latitudeArgument', 'phase', 'gap', 'height'

    def __init__(self, tle: TwoLineElement):
        super().__init__(tle)
        self.raan = self.latitudeArgument = self.phase = self.gap = self.height = None

    def __hash__(self):
        return super().__hash__()

    def __repr__(self):
        return f'{self._tle.name}, raan: {self._round(self.raan, 3)}, ' \
               f'latitude: {self._round(self.latitudeArgument)}, ' \
               f'phase: {self._round(self.phase)}, ' \
               f'gap: {self._round(self.gap)} ' \
               f'height: {self._round(self.height, 2)}'

    @staticmethod
    def _round(value: float | None, n: int = 5) -> float | None:
        if value is not None:
            return round(value, n)
        return value

    def __getstate__(self):
        return {'tle': self._tle, 'raan': self.raan, 'latitudeArgument': self.latitudeArgument,
                'phase': self.phase, 'gap': self.gap, 'height': self.height}

    def __setstate__(self, state):
        self.__init__(state['tle'])
        self.raan = state.get('raan')
        self.latitudeArgument = state.get('latitudeArgument')
        self.phase = state.get('phase')
        self.gap = state.get('gap')
        self.height = state.get('height')


class StarlinkSatelliteContainer(ABC):
    __slots__ = '_satellites'

    def __init__(self, satellites: list[StarlinkSatellite]):
        self._satellites = satellites

    def __len__(self):
        return self._satellites.__len__()

    def __getitem__(self, index: int) -> StarlinkSatellite:
        return self._satellites.__getitem__(index)

    def __repr__(self):
        content = '\n'.join([str(satellite) for satellite in self._satellites])
        return f'[{content}]'

    @property
    def satellites(self):
        return self._satellites
