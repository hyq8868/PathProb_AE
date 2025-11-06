from dataclasses import dataclass, field
from typing import Set, Dict, Tuple, Optional, Any
from frozendict import frozendict
import os


@dataclass(frozen=True)
class PathProbData:
    asrel_prob: Dict[Tuple[int, int], Tuple[float, float, float]] = field(
        default_factory=dict
    )
    file_path: str = ""

    def get_prob(self, as1: int, as2: int) -> Optional[Tuple[float, float, float]]:
        return self.asrel_prob.get((as1, as2), (1 / 3, 1 / 3, 1 / 3))


    @classmethod
    def load_asrel_prob_from_file(cls, file_path: str) -> "PathProbData":
        asrel_prob: Dict[Tuple[int, int], Tuple[float, float, float]] = {}
        try:
            if "pathprob" in file_path:
                with open(file_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue

                        parts = line.split("|")
                        if len(parts) != 5:
                            raise ValueError(
                                f"Invalid line format in {file_path}: {line}"
                            )

                        as1 = int(parts[0])
                        as2 = int(parts[1])
                        p1 = float(parts[2])
                        p2 = float(parts[3])
                        p3 = float(parts[4])

                        asrel_prob[(as1, as2)] = (p1, p2, p3)
                        asrel_prob[(as2, as1)] = (p3, p2, p1)
            else:
                with open(file_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue

                        parts = line.split("|")
                        if len(parts) != 3:
                            raise ValueError(
                                f"Invalid line format in {file_path}: {line}"
                            )
                        if parts[-1] == "1":
                            continue
                        as1, as2 = int(parts[0]), int(parts[1])
                        if parts[-1] == "-1":
                            p1, p2, p3 = 1.0, 0.0, 0.0
                        elif parts[-1] == "0":
                            p1, p2, p3 = 0.0, 1.0, 0.0
                        else:
                            raise ValueError(
                                f"Invalid line format in {file_path}: {line}"
                            )
                        asrel_prob[(as1, as2)] = (p1, p2, p3)
                        asrel_prob[(as2, as1)] = (p1, p2, p3)

        except FileNotFoundError:
            raise FileNotFoundError(f"The file path '{file_path}' was not found.")
        except (ValueError, IndexError) as e:
            raise ValueError(f"Error processing file {file_path}: {e}")

        return cls(asrel_prob=asrel_prob, file_path=file_path)
