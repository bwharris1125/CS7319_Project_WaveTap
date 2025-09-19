from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AircraftData:
    """Base container for decoded ADS-B message fields.

    Fields are optional because not every ADS-B message contains all fields.
    This class focuses on the common fields used in tracking and display.
    """

    icao: Optional[str] = None        # ICAO 24-bit hex string
    callsign: Optional[str] = None   # Flight callsign (if available)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None  # Altitude in meters
    heading_deg: Optional[float] = None
    groundspeed_m_s: Optional[float] = None
    vertical_rate_m_s: Optional[float] = None
    squawk: Optional[str] = None
    emergency: Optional[bool] = None
    timestamp: Optional[float] = None  # Unix epoch seconds

    # raw payload or extra fields if needed
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict representation (suitable for JSON)."""
        return {
            "icao": self.icao,
            "callsign": self.callsign,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_m": self.altitude_m,
            "heading_deg": self.heading_deg,
            "groundspeed_m_s": self.groundspeed_m_s,
            "vertical_rate_m_s": self.vertical_rate_m_s,
            "squawk": self.squawk,
            "emergency": self.emergency,
            "timestamp": self.timestamp,
            "raw": self.raw,
        }

    @classmethod
    def from_adsb_dict(cls, data: Dict[str, Any]) -> "AircraftData":
        """Factory: create AircraftData from a decoded ADS-B dict.

        Attempts to accept common key names and normalize units:
        - altitude in feet -> meters
        - groundspeed in knots -> m/s
        - vertical rate in fpm -> m/s
        """
        def ft_to_m(ft: Optional[float]) -> Optional[float]:
            return None if ft is None else float(ft) * 0.3048

        def knots_to_m_s(kts: Optional[float]) -> Optional[float]:
            return None if kts is None else float(kts) * 0.514444

        # extract vertical rate: prefer explicit m/s if present
        vr_m_s = None
        if data.get("vertical_rate_m_s") is not None:
            vr_m_s = float(data.get("vertical_rate_m_s"))
        else:
            vr_fpm = data.get("vertical_rate_fpm") or data.get("vr_fpm")
            if vr_fpm is not None:
                # fpm -> m/s
                vr_m_s = float(vr_fpm) / 60.0 * 0.3048

        altitude_ft = data.get("altitude_ft") or data.get("alt_ft") or data.get("altitude")
        # sometimes altitude may already be in meters under 'altitude_m'
        altitude_m = None
        if data.get("altitude_m") is not None:
            altitude_m = float(data.get("altitude_m"))
        else:
            # if altitude looks like feet (and key implies feet), convert
            if altitude_ft is not None:
                altitude_m = ft_to_m(altitude_ft)

        gs_kts = data.get("groundspeed_kts") or data.get("gs") or data.get("speed_kts") or data.get("groundspeed")
        groundspeed_m_s = None
        if data.get("groundspeed_m_s") is not None:
            groundspeed_m_s = float(data.get("groundspeed_m_s"))
        elif gs_kts is not None:
            groundspeed_m_s = knots_to_m_s(gs_kts)

        icao = data.get("icao24") or data.get("icao") or data.get("hex")

        return cls(
            icao=icao,
            callsign=(data.get("callsign") or data.get("flight") or None),
            latitude=(data.get("lat") or data.get("latitude")),
            longitude=(data.get("lon") or data.get("longitude")),
            altitude_m=altitude_m,
            heading_deg=(data.get("heading") or data.get("track") or data.get("heading_deg")),
            groundspeed_m_s=groundspeed_m_s,
            vertical_rate_m_s=vr_m_s,
            squawk=(data.get("squawk") or data.get("code")),
            emergency=(bool(data.get("emergency")) if data.get("emergency") is not None else None),
            timestamp=(data.get("timestamp") or data.get("time")),
            raw=data,
        )

