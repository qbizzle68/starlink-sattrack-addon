import re
from copy import deepcopy
from math import pi, degrees
from statistics import stdev

from sattrack.api import now, EARTH_EQUITORIAL_RADIUS

from .satellites import StarlinkSatelliteContainer, StarlinkSatellite
# from ..config.configImport import starlinkConfig
import starlink.config.configImport as configImport

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..importers.tleimporter import TLEImporter
    from sattrack.api import JulianDate


StarlinkList = 'List[StarlinkSatellite]'


class StarlinkBatch(StarlinkSatelliteContainer):
    __slots__ = '_time', '_batchTag', '_groupNumber', '_intDes', '_planes', '_trains'

    def __init__(self, importer: 'TLEImporter', batch: str, time: 'JulianDate' = None):

        match = re.match(r'^(\d+)-(\d+)$', batch)
        if not match:
            raise ValueError(f'invalid batch number syntax({batch})')

        self._intDes = configImport.starlinkConfig['launches'].get(batch)
        self._batchTag = batch
        self._groupNumber = match.group(1)

        if time is None:
            time = now()
        self._time = time

        importedBatch = importer.fetchBatch(self._intDes)
        batchSatellites = [StarlinkSatellite(tle) for tle in importedBatch]
        self._fillBasicAttributes(batchSatellites)
        planes = self._splitIntoPlanes(batchSatellites)
        self._planes = [GroupPlane(plane, self._groupNumber) for plane in planes]

        satellites = [sat for sat in self._planes[0].satellites]
        for plane in self._planes[1:]:
            satellites.extend(plane.satellites)
        super().__init__(satellites)

        self._trains = []
        for plane in self._planes:
            trains = self._findTrains(plane)
            for train in trains:
                if len(train) >= configImport.starlinkConfig['defaults']['MINIMUM_TRAIN_LENGTH']:
                    self._trains.append(StarlinkTrain(train, batch))

    def _fillBasicAttributes(self, satellites: StarlinkList):
        for satellite in satellites:
            elements = satellite.getElements(self._time)
            latitudeArgument = (elements.aop + elements.trueAnomaly) % (2 * pi)
            satellite.latitudeArgument = degrees(latitudeArgument)
            satellite.raan = degrees(elements.raan)
            satellite.height = elements.sma - EARTH_EQUITORIAL_RADIUS

    @staticmethod
    def _splitIntoPlanes(satellites: StarlinkList) -> 'list[GroupPlane]':
        RAAN_STDEV_OUTLIER = configImport.starlinkConfig['defaults']['RAAN_STDEV_OUTLIER']

        satellites = sorted(satellites, key=lambda o: o.raan)
        satellitesCount = len(satellites)

        planes = []
        startIndex = 0
        while startIndex < satellitesCount:
            endIndex = satellitesCount
            remainingSatellites = satellitesCount - startIndex - 1
            if remainingSatellites == 1:
                planes.append([satellites[-1]])
                break

            for i in range(startIndex + 2, satellitesCount):
                array = [satellite.raan for satellite in satellites[startIndex:i]]
                standardDeviation = stdev(array)
                if standardDeviation >= RAAN_STDEV_OUTLIER:
                    endIndex = i - 1
                    break

            planes.append(satellites[startIndex:endIndex])
            startIndex = endIndex

        return planes

    @staticmethod
    def _findTrains(plane: 'GroupPlane') -> StarlinkList:
        trains = []
        MAXIMUM_TRAIN_GAP = configImport.starlinkConfig['defaults']['MAXIMUM_TRAIN_GAP']
        MAXIMUM_TRAIN_HEIGHT = configImport.starlinkConfig['defaults']['MAXIMUM_TRAIN_HEIGHT']
        i = 0
        while i < len(plane) - 1:
            train = [plane.satellites[i]]
            for satellite in plane.satellites[i + 1:]:
                # place any other filters we want here
                if train[-1].gap < MAXIMUM_TRAIN_GAP and train[-1].height <= MAXIMUM_TRAIN_HEIGHT \
                        and satellite.height <= MAXIMUM_TRAIN_HEIGHT:
                    train.append(satellite)
                else:
                    break
            trains.append(train)
            i += len(train)

        return trains

    @property
    def time(self) -> 'JulianDate':
        return self._time

    @property
    def batchTag(self) -> str:
        return self._batchTag

    @property
    def groupNumber(self) -> str:
        return self._groupNumber

    @property
    def intDes(self) -> str:
        return self._intDes

    @property
    def planes(self) -> 'list[GroupPlane]':
        return self._planes

    @property
    def trains(self) -> 'list[StarlinkTrain]':
        return self._trains


def _applyPhases(satellites: StarlinkList):
    satellites[0].phase = 0.0
    basePhase = satellites[0].latitudeArgument
    for satellite in satellites[1:]:
        phase = satellite.latitudeArgument - basePhase
        satellite.phase = phase if phase <= 0 else phase - 360


class GroupPlane(StarlinkSatelliteContainer):
    __slots__ = '_groupNumber', '_raan', '_config'

    def __init__(self, satellites: StarlinkList, number: int | str):

        self._groupNumber = str(number)
        self._raan = min(satellites, key=lambda o: o.raan)
        self._config = configImport.starlinkConfig['groups'][self._groupNumber]

        sortedSatellites = self._sortSatellites(satellites)
        super().__init__(sortedSatellites)
        _applyPhases(self._satellites)

    @staticmethod
    def _sortSatellites(satellites: StarlinkList) -> StarlinkList:

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


class StarlinkTrain(StarlinkSatelliteContainer):
    __slots__ = '_batchTag'

    def __init__(self, satellites: StarlinkList, batchTag: str):
        satellitesCopy = deepcopy(satellites)
        super().__init__(satellitesCopy)
        _applyPhases(self._satellites)
        self._batchTag = batchTag

    @property
    def batchTag(self) -> str:
        return self._batchTag
