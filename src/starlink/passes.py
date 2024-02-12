from sattrack.api import SatellitePass, PassFinder
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sattrack.api import PositionInfo, GeoPosition, JulianDate
    from .models.starlink import StarlinkTrain


class StarlinkPass(SatellitePass):
    __slots__ = '_passes'

    def __init__(self, infos: 'PositionInfo', singlePasses: 'list[SatellitePass]', batchTag: str):
        super().__init__(infos, f'Starlink batch {batchTag}')
        self._passes = singlePasses

    @property
    def passes(self) -> 'list[StarlinkPass]':
        return self._passes


class StarlinkPassFinder:
    __slots__ = '_train', '_geo', '_passControllers'

    def __init__(self, train: 'StarlinkTrain', geo: 'GeoPosition'):
        self._train = train
        self._geo = geo
        self._passControllers = [PassFinder(satellite, self._geo) for satellite in train.satellites]

    def computeNextPass(self, time: 'JulianDate', nextOccurrence: bool = True, timeout: float = 7) -> StarlinkPass:
        if isinstance(time, StarlinkPass):
            time = time.setInfo.time.future(0.0001)

        nextPasses = [controller.computeNextPass(time, nextOccurrence, timeout)
                      for controller in self._passControllers]
        validPasses = [nextPasses[0]]
        for i, nextPass in enumerate(nextPasses[1:], 1):
        # for i in range(1, len(nextPasses) - 1):
            if nextPasses[i-1].setInfo.time > nextPass.riseInfo.time:
                validPasses.append(nextPass)
            else:
                break

        allInfos = []
        for np in validPasses:
            for info in np._infos.values():
                if info is not None:
                    allInfos.append(info)

        return StarlinkPass(allInfos, validPasses, self._train.batchTag)

    def computePassList(self, time: 'JulianDate', duration: float) -> list[StarlinkPass]:
        if duration > 0:
            nextOccurrence = True
        elif duration < 0:
            nextOccurrence = False
        else:
            raise ValueError(f'duration must be a non-zero number')

        stopTime = time.future(duration)
        passList = []
        while True:
            # remainingTime = stopTime - time
            try:
                nextPass = self.computeNextPass(time, nextOccurrence, 14)
            except Exception as e:
                if passList:
                    return passList
                raise e

            if nextPass.riseInfo.time >= stopTime:
                break

            passList.append(nextPass)
            time = nextPass.setInfo.time.future(0.001)

        return passList

    @property
    def train(self) -> 'StarlinkTrain':
        return self._train

    @property
    def geo(self) -> 'GeoPosition':
        return self._geo
