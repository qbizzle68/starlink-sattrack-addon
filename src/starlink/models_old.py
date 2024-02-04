import re

from abc import ABC, abstractmethod
from copy import deepcopy
from math import degrees
from statistics import stdev

# noinspection PyUnresolvedReferences
from sattrack.api import TwoLineElement, TLEResponseIterator, Satellite, TWOPI, now, PassFinder, SatellitePass,\
    PositionInfo, EARTH_EQUITORIAL_RADIUS

from . import _starlinkConfig

from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from sattrack.api import JulianDate, GeoPosition


RAAN_STDEV_OUTLIER = 1.25
MAXIMUM_TRAIN_GAP = 5


def _round(value: float | None, n: int = 5) -> float | None:
    if value is not None:
        return round(value, n)
    return value


class StarlinkSatelliteOld(Satellite):
    __slots__ = '_phase', '_latitudeArgument', '_raan', '_height', '_gap'

    def __init__(self, tle: TwoLineElement):
        super().__init__(tle)
        self._phase = None
        self._latitudeArgument = None
        self._raan = None
        self._height = None
        self._gap = None

    def __hash__(self):
        return super().__hash__()

    def __repr__(self):
        return f'{self._tle.name}, raan: {_round(self._raan, 3)}, ' \
               f'latitude: {_round(self._latitudeArgument)}, ' \
               f'phase: {_round(self._phase)}, ' \
               f'gap: {_round(self._gap)} ' \
               f'height: {_round(self._height, 2)}'

    @property
    def phase(self) -> float:
        return self._phase

    @phase.setter
    def phase(self, value: float):
        self._phase = value

    @property
    def latitudeArgument(self) -> float:
        return self._latitudeArgument

    @latitudeArgument.setter
    def latitudeArgument(self, value: float):
        self._latitudeArgument = value

    @property
    def raan(self) -> float:
        return self._raan

    @raan.setter
    def raan(self, value: float):
        self._raan = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value: float):
        self._height = value

    @property
    def gap(self):
        return self._gap

    @gap.setter
    def gap(self, value: float):
        self._gap = value


StarlinkList = List[StarlinkSatelliteOld]


class TLEImporter(ABC):

    @abstractmethod
    def fetchBatch(self, intDes: str) -> list[TwoLineElement]:
        pass

    @abstractmethod
    def fetchSatellite(self, name: str) -> TwoLineElement:
        pass


class TLEFileImporter(TLEImporter):
    STARLINK_PATTERN = re.compile(r'^STARLINK-\d{4,}(.|\n)*')
    INTDES_PATTERN = re.compile(r'(^\d{5})[A-Z]{0,3}$')

    def __init__(self, filename: str):
        self._filename = filename

    @property
    def filename(self):
        return self._filename

    def fetchBatch(self, intDes: str) -> list[TwoLineElement]:
        intDesMatch = self.INTDES_PATTERN.match(intDes)
        if not intDesMatch:
            raise ValueError('intDes does not match an international designator pattern')

        intDesNumber = intDesMatch.group(0)
        tleList = []
        with open(self._filename, 'r') as file:
            lines = file.readlines()

        iterator = TLEResponseIterator(lines)
        for tle in iterator:
            # the TLEResponseIterator puts two '\n' characters between lines right now
            line1 = tle.split('\n', 2)[-1]
            tleIntDes = line1[9:14]

            if tleIntDes == intDesNumber and self.STARLINK_PATTERN.match(tle):
                tleList.append(TwoLineElement(tle))

        if not tleList:
            raise LookupError(f'no satellites matching international designator {intDes}')

        return tleList

    def fetchSatellite(self, name: str) -> TwoLineElement:
        if not self.STARLINK_PATTERN.match(name):
            raise ValueError('name does not match a starlink pattern')

        with open(self._filename, 'r') as file:
            lines = file.readlines()

        iterator = TLEResponseIterator(lines)
        for tle in iterator:
            # we should want TLEResponseIterator to return the lines, so we don't have to re-split it
            tleName = tle.split('\n', 1)[0]
            if name == tleName.strip():
                return TwoLineElement(tle)

        raise LookupError(f'unable to find starlink satellite named {name}')


class StarlinkSatelliteContainer(ABC):
    __slots__ = '_satellites'

    def __init__(self, satellites: list[StarlinkSatelliteOld]):
        self._satellites = satellites

    def _sortSatellites(self, key, reverse: bool):
        self._satellites.sort(key=key, reverse=reverse)

    def __len__(self):
        return len(self._satellites)

    def __getitem__(self, index: int):
        return self._satellites.__getitem__(index)

    def __repr__(self):
        content = '\n'.join([str(satellite) for satellite in self._satellites])
        return f'[{content}]'

    @property
    def satellites(self):
        return self._satellites


class StarlinkBatch(StarlinkSatelliteContainer):
    __slots__ = '_time', '_batch', '_groupNumber', '_intDes', '_planes', '_trains'

    def __init__(self, importer: TLEImporter, batch: str, time: 'JulianDate' = None):
        """Imports a satellite batch by looking up the international designator of the launch
        from the configuration file using the batch number. The batch string must be of the form
        '{group}-{launch}' and must be set in the configuration file to its international designator."""

        match = re.match(r'^(\d+)-(\d+)$', batch)
        if not match:
            raise ValueError(f'invalid batch number syntax({batch})')

        self._intDes = _starlinkConfig['launches'].get(batch)
        self._batch = batch
        self._groupNumber = match.group(1)

        if time is None:
            time = now()
        self._time = time

        # todo: i think we should finish computing the satellite array, then call super().__init__()
        batch = importer.fetchBatch(self._intDes)
        super().__init__([StarlinkSatelliteOld(tle) for tle in batch])
        self._fillSatelliteAttributes()

        planes = self._splitIntoPlanes()
        self._planes = [GroupPlane(plane, self._groupNumber) for plane in planes]

        self._trains = []
        for plane in self._planes:
            for train in plane.trains:
                self._trains.append(train)

        # self._sortFinalSatellites()

    def _splitIntoPlanes(self) -> 'list[GroupPlane]':
        """Split the internal satellites list into any separate planes, if the batch
        contains multiple planes."""

        satellites = sorted(self._satellites, key=lambda o: o.raan)
        satellitesCount = len(satellites)

        planes = []
        startIndex = 0
        while startIndex < satellitesCount:
            endIndex = satellitesCount
            remainingSatellites = satellitesCount - startIndex - 1
            if remainingSatellites == 1:
                planes.append([satellites[-1]])
                break

            for j in range(startIndex + 2, satellitesCount):
                array = [satellite.raan for satellite in satellites[startIndex:j]]
                standardDeviation = stdev(array)
                if standardDeviation >= RAAN_STDEV_OUTLIER:
                    endIndex = j - 1
                    break

            planes.append(satellites[startIndex:endIndex])
            startIndex = endIndex

        return planes

    def _fillSatelliteAttributes(self):
        """Computes and sets the latitudeArgument and raan attributes of each
        StarlinkSatellite object."""

        for satellite in self._satellites:
            elements = satellite.getElements(self._time)
            latitudeArgument = (elements.aop + elements.trueAnomaly) % TWOPI
            satellite.latitudeArgument = degrees(latitudeArgument)
            satellite.raan = degrees(elements.raan)
            satellite.height = elements.sma - EARTH_EQUITORIAL_RADIUS

    def _sortFinalSatellites(self):
        sortedPlanes = sorted(self._planes, key=lambda o: o[0].raan)
        self._satellites = []
        for plane in sortedPlanes:
            self._satellites.extend(plane.satellites)

    @property
    def batch(self) -> str:
        return self._batch

    @property
    def planes(self) -> 'list[GroupPlane]':
        return self._planes

    @property
    def time(self) -> 'JulianDate':
        return self._time

    @property
    def groupNumber(self) -> str:
        return self._groupNumber

    @property
    def internationalDesignator(self) -> str:
        return self._intDes

    @property
    def trains(self) -> 'list[StarlinkTrain]':
        return self._trains


# satellites should have basic attributes filled in before instantiating a plane (i.e. latitudeArgument and raan)
# GroupPlane will fill rest of attributes while sorting their layout in the plane.
class GroupPlane(StarlinkSatelliteContainer):
    __slots__ = '_groupNumber', '_raan', '_config', '_trains'

    def __init__(self, satellites: StarlinkList, number: int | str):
        # noinspection GrazieInspection
        """The satellites argument should be a list of StarlinkSatellite's with their latitudeArgument
        and raan attributes set. The constructor will fill the remaining attributes and correctly sort
        the list."""

        self._groupNumber = str(number)
        # This doesn't necessarily need to be minimum, in fact the average might be more accurate.
        self._raan = min(satellites, key=lambda o: o.raan)
        self._config = _starlinkConfig['groups'][self._groupNumber]

        sortedSatellites = self._fillAndSortSatellites(satellites)
        super().__init__(sortedSatellites)
        self._setSatellitePhases()

        self._trains = []
        trains = self._findTrains()
        for train in trains:
            if len(train) > 1:
                self._trains.append(StarlinkTrain(train))

    @staticmethod
    def _fillAndSortSatellites(satellites: StarlinkList) -> StarlinkList:
        """Fill the satellite gap attributes and sort the list appropriately."""

        sortedSatellites = sorted(satellites, key=lambda o: o.latitudeArgument, reverse=True)
        gaps = [sortedSatellites[i].latitudeArgument - sortedSatellites[i + 1].latitudeArgument
                for i in range(len(sortedSatellites) - 1)]
        gaps.append(sortedSatellites[-1].latitudeArgument - sortedSatellites[0].latitudeArgument)
        for satellite, gap in zip(sortedSatellites, gaps):
            satellite.gap = gap if gap >= 0 else gap + 360

        maximumGapSatellite = max(sortedSatellites, key=lambda o: o.gap)
        indexArray = [maximumGapSatellite.gap == satellite.gap for satellite in sortedSatellites]
        maximumIndex = indexArray.index(True)

        if maximumIndex == len(sortedSatellites) - 1:
            filledSatellites = sortedSatellites
        else:
            splitIndex = maximumIndex + 1
            filledSatellites = sortedSatellites[splitIndex:] + sortedSatellites[:splitIndex]

        return filledSatellites

    def _setSatellitePhases(self):
        self._satellites[0].phase = 0.0
        basePhase = self._satellites[0].latitudeArgument
        for satellite in self._satellites[1:]:
            phase = satellite.latitudeArgument - basePhase
            satellite.phase = phase if phase <= 0 else phase - 360

    def _findTrains(self) -> list['StarlinkTrain']:
        trains = []
        i = 0
        while i < self.__len__() - 1:
            train = [self._satellites[i]]
            for satellite in self._satellites[i + 1:]:
                if train[-1].gap < MAXIMUM_TRAIN_GAP:
                    train.append(satellite)
                else:
                    break
            trains.append(train)
            i += len(train)

        return trains
        
    @property
    def config(self):
        return self._config

    @property
    def raan(self):
        return self._raan

    @property
    def groupNumber(self):
        return self._groupNumber

    @property
    def trains(self):
        return self._trains


class StarlinkTrain(StarlinkSatelliteContainer):

    def __init__(self, satellites: list[StarlinkSatelliteOld]):
        # have to do this right now because we can't pickle StarlinkSatellite for whatever reason
        satellitesCopy = [StarlinkSatelliteOld(sat.tle) for sat in satellites]
        for original, cpy in zip(satellites, satellitesCopy):
            cpy.raan = original.raan
            cpy.gap = original.gap
            cpy.phase = original.phase
            cpy.latitudeArgument = original.latitudeArgument
            cpy.height = original.height
        # satellitesCopy = deepcopy(satellites)
        super().__init__(satellitesCopy)
        self._adjustPhase()

    def _adjustPhase(self):
        phaseOffset = self._satellites[0].phase
        for satellite in self._satellites:
            satellite.phase -= phaseOffset


class StarlinkPass(SatellitePass):
    __slots__ = '_passes'

    def __init__(self, infos: 'list[PositionInfo]', individualPasses: 'list[SatellitePass]', batch: str):
        name = f'Satellite Batch {batch}'
        super().__init__(infos, name)
        self._passes = individualPasses

    def __len__(self):
        return len(self._passes)

    def __getitem__(self, index) -> SatellitePass:
        return self._passes.__getitem__(index)

    @property
    def passes(self) -> list[SatellitePass]:
        return self._passes


class StarlinkPassFinder(PassFinder):

    def __init__(self, satellite: StarlinkSatelliteOld, geo: 'GeoPosition'):
        pass
