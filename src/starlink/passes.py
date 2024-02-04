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

        # maxInfo = max([nextPass.maxInfo for nextPass in validPasses], key=lambda o: o.time if o else 0)
        # maxIlluminatedInfo = max([np.maxIlluminatedInfo for np in validPasses], key=lambda o: o.time if o else 0)
        # maxUnobscuredInfo = max([np.maxUnobscuredInfo for np in validPasses], key=lambda o: o.time if o else 0)
        # maxVisibleInfo = max([np.maxVisibleInfo for np in validPasses], key=lambda o: o.time if o else 0)
        # firstUnobscuredInfo = lastUnobscuredInfo = firstIlluminatedInfo = firstVisibleInfo = lastVisible = None
        # for np in validPasses:
        #     if firstUnobscuredInfo is None:
        #         if np.firstUnobscuredInfo is not None:
        #             firstUnobscuredInfo = np.firstUnobscuredInfo
        #     if lastUnobscuredInfo is None:
        #         if np.lastUnobscuredInfo is not None:
        #             lastUnobscuredInfo = np.lastUnobscuredInfo
        #     if firstIlluminatedInfo is None:
        #         if np.firstIlluminatedInfo is not None:
        #             firstIlluminatedInfo = np.firstIlluminatedInfo
        #     if firstVisibleInfo is None:
        #         if np.firstVisibleInfo is not None:
        #             firstVisibleInfo = np.firstVisibleInfo
        #     if lastVisible is None:
        #         if np.lastVisible is not None:
        #             lastVisible = np.lastVisible
        #
        # lastIlluminatedInfo = None
        # for np in reversed(validPasses):
        #     if lastIlluminatedInfo is None:
        #         if np.lastIlluminatedInfo is not None:
        #             lastIlluminatedInfo = np.lastIlluminatedInfo
        #
        # infos = [validPasses[0].riseInfo, validPasses[-1].setInfo, maxInfo,]

    def computePassList(self, time: 'JulianDate', duration: float) -> list[StarlinkPass]:
        pass

    @property
    def train(self) -> 'StarlinkTrain':
        return self._train

    @property
    def geo(self) -> 'GeoPosition':
        return self._geo
