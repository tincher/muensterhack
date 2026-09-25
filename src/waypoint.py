from enum import Enum

from pydantic import BaseModel, Field


class RollstuhlgerechtLevel(str, Enum):
    VOLL = "voll"
    TEILWEISE = "teilweise"
    NICHT = "nicht"
    UNBEKANNT = "unbekannt"


class Zugangsseite(str, Enum):
    LINKS = "links"
    RECHTS = "rechts"
    BEIDSEITIG = "beidseitig"
    UNBEKANNT = "unbekannt"


class Waypoint(BaseModel):
    pp_id: str
    pp_lat: float
    pp_lon: float
    pp_bildpfad: str | None = None
    pp_ladesaeule_kw: float | None = None
    pp_zugangsseite: Zugangsseite = Zugangsseite.UNBEKANNT
    pp_rollstuhlgerecht_level: RollstuhlgerechtLevel = RollstuhlgerechtLevel.UNBEKANNT
    pp_ueberdacht: bool = False
    pp_schranke: bool = False
    pp_kostenlos: bool = False
    pp_belegt: bool = False
    pp_kommentare: list[str] = Field(default_factory=list)
    
    def get_sql_values(self):
        return f"{self.pp_id}, {self.pp_lat}, {self.pp_lon}, {self.pp_ladesaeule_kw}, '{self.pp_zugangsseite.value}', '{self.pp_rollstuhlgerecht_level.value}', {self.pp_ueberdacht}, {self.pp_schranke}, '{self.pp_bildpfad}', {self.pp_kostenlos}, {self.pp_belegt}"