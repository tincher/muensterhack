from enum import Enum

from pydantic import BaseModel, Field


class Barrierefreiheitslevel(str, Enum):
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
    pp_barrierefreiheit_level: Barrierefreiheitslevel = Barrierefreiheitslevel.UNBEKANNT
    pp_ueberdacht: bool = False
    pp_schranke: bool = False
    pp_kostenlos: bool = False
    pp_belegt: bool | None = None
    pp_kommentare: list[str] = Field(default_factory=list)
