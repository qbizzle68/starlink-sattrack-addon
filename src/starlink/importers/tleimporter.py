import re
from abc import ABC, abstractmethod

# noinspection PyUnresolvedReferences
from sattrack.api import TwoLineElement
from sattrack.orbit.tle import TLEResponseIterator


class TLEImporter(ABC):

    @abstractmethod
    def fetchBatch(self, intDes: str) -> list[TwoLineElement]:
        pass

    @abstractmethod
    def fetchSatellite(self, name: str) -> TwoLineElement:
        pass


_STARLINK_PATTERN = re.compile(r'^STARLINK-\d{4,}(.|\n)*')
_INTDES_PATTERN = re.compile(r'(^\d{5})[A-Z]{0,3}$')


class TLEFileImporter(TLEImporter):

    def __init__(self, filename: str):
        self._filename = filename

    def fetchBatch(self, intDes: str) -> list[TwoLineElement]:
        intDesMatch = _INTDES_PATTERN.match(intDes)
        if not intDesMatch:
            raise ValueError('intDes does not match an international designator pattern')

        intDesNumber = intDesMatch.group(0)
        with open(self._filename, 'r') as file:
            lines = file.readlines()

        tleList = []
        iterator = TLEResponseIterator(lines)
        for tle in iterator:
            # the TLEResponseIterator puts two '\n' characters between lines right now
            line1 = tle.split('\n', 2)[-1]
            tleIntDes = line1[9:14]

            if tleIntDes == intDesNumber and _STARLINK_PATTERN.match(tle):
                tleList.append(TwoLineElement(tle))

        if not tleList:
            raise LookupError(f'no satellites matching international designator {intDes}')

        return tleList

    def fetchSatellite(self, name: str) -> TwoLineElement:
        if not _STARLINK_PATTERN.match(name):
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
