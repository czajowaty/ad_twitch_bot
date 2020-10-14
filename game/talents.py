import enum


class Talents(enum.Flag):
    Empty = 0x0
    Quick = 0x1
    HpIncreased = 0x2
    MpIncreased = 0x4
    StrengthIncreased = 0x8
    Hard = 0x10
    GrowthPromoted = 0x20
    MagicAttackIncreased = 0x80
    MpConsumptionDecreased = 0x100
    ElectricShock = 0x8000
    DoesNotSurviveFusion = 0x400000
    SurvivesFusion = 0x800000

    def has(self, talents) -> bool:
        return (self & talents) == talents
