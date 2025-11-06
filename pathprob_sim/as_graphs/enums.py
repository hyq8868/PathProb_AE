from bgpy.shared.enums import ASGroups as BaseASGroups
from bgpy.shared.enums import YamlAbleEnum


class ExtendedASGroups(YamlAbleEnum):

    IXPS = BaseASGroups.IXPS.value
    STUBS = BaseASGroups.STUBS.value
    MULTIHOMED = BaseASGroups.MULTIHOMED.value
    STUBS_OR_MH = BaseASGroups.STUBS_OR_MH.value
    INPUT_CLIQUE = BaseASGroups.INPUT_CLIQUE.value
    ETC = BaseASGroups.ETC.value
    TRANSIT = BaseASGroups.TRANSIT.value
    ALL_WOUT_IXPS = BaseASGroups.ALL_WOUT_IXPS.value

    LEAKER = "leaker"
