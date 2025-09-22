import logging

import pyModeS as pms
from pyModeS.extra.tcpclient import TcpClient

from database.adsb_db import AircraftState


class ADSBClient(TcpClient):
    def __init__(self, host, port, data_type):
        logging.info(f"Starting ADSBClient to {host}:{port} type={data_type}")
        super(ADSBClient, self).__init__(host, port, data_type)

    def handle_messages(self, messages):
        for msg, timestamp in messages:
            # logging.info(f"Raw message: [{msg}, {_}]")
            if len(msg) != 28 : # wrong length
                # logging.debug(f"Skipping wrong length message: {msg}")
                continue
            callsign = ""
            df = pms.df(msg)
            if pms.crc(msg) == 1: # bad CRC
                logging.debug(f"Skipping bad CRC message: {msg}")
                continue

            if df == 17 :
                """
                17 - Mode S, Extended Squitter (ADS-B)
                20 - Mode S, Comm-B Altitude Reply
                21 - Mode S, Comm-B Identity Reply
                """
                tc = pms.typecode(msg)
                icao = pms.icao(msg)

                if tc is None:
                    logging.error("Unknown typecode")
                    return

                if 1 <= tc <= 4:  # callsign
                    callsign = pms.adsb.callsign(msg)

                if 5 <= tc <= 8:  # surface position
                    oe = pms.adsb.oe_flag(msg)
                    msgbin = pms.common.hex2bin(msg)
                    cprlat = pms.common.bin2int(msgbin[54:71]) / 131072.0
                    cprlon = pms.common.bin2int(msgbin[71:88]) / 131072.0
                    v = pms.adsb.surface_velocity(msg)

                if 9 <= tc <= 18:  # airborne position
                    alt = pms.adsb.altitude(msg)
                    oe = pms.adsb.oe_flag(msg)
                    msgbin = pms.common.hex2bin(msg)
                    cprlat = pms.common.bin2int(msgbin[54:71]) / 131072.0
                    cprlon = pms.common.bin2int(msgbin[71:88]) / 131072.0

                if tc == 19:
                    velocity = pms.adsb.velocity(msg)
                    if velocity is not None:
                        spd, trk, vr, t = velocity
                        types = {"GS": "Ground speed", "TAS": "True airspeed"}

                if 20 <= tc <= 22:  # airborne position
                    alt = pms.adsb.altitude(msg)
                    oe = pms.adsb.oe_flag(msg)
                    msgbin = pms.common.hex2bin(msg)
                    cprlat = pms.common.bin2int(msgbin[54:71]) / 131072.0
                    cprlon = pms.common.bin2int(msgbin[71:88]) / 131072.0

                if tc == 29:  # target state and status
                    subtype = pms.common.bin2int((pms.common.hex2bin(msg)[32:])[5:7])
                    tcas_operational = pms.adsb.tcas_operational(msg)
                    types_29 = {0: "Not Engaged", 1: "Engaged"}
                    tcas_operational_types = {0: "Not Operational", 1: "Operational"}
                    if subtype == 0:
                        emergency_types = {
                            0: "No emergency",
                            1: "General emergency",
                            2: "Lifeguard/medical emergency",
                            3: "Minimum fuel",
                            4: "No communications",
                            5: "Unlawful interference",
                            6: "Downed aircraft",
                            7: "Reserved",
                        }
                        vertical_horizontal_types = {
                            1: "Acquiring mode",
                            2: "Capturing/Maintaining mode",
                        }
                        tcas_ra_types = {0: "Not active", 1: "Active"}
                        alt, alt_source, alt_ref = pms.adsb.target_altitude(msg)
                        angle, angle_type, angle_source = pms.adsb.target_angle(msg)
                        vertical_mode = pms.adsb.vertical_mode(msg)
                        horizontal_mode = pms.adsb.horizontal_mode(msg)
                        tcas_ra = pms.adsb.tcas_ra(msg)
                        emergency_status = pms.adsb.emergency_status(msg)
                    else:
                        alt, alt_source = pms.adsb.selected_altitude(msg)  # type: ignore
                        baro = pms.adsb.baro_pressure_setting(msg)
                        hdg = pms.adsb.selected_heading(msg)
                        autopilot = pms.adsb.autopilot(msg)
                        vnav = pms.adsb.vnav_mode(msg)
                        alt_hold = pms.adsb.altitude_hold_mode(msg)
                        app = pms.adsb.approach_mode(msg)
                        lnav = pms.adsb.lnav_mode(msg)

                logging.debug(f"Recieved message from {icao} (Callsign {callsign}).\n"
                            f"  Type Code: {tc}\n"
                            f"  Raw Message: {msg}")


def run_client():
    host = "192.168.50.106"
    port = 30002

    client = ADSBClient(host, port, "raw")
    client.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # # confirm library workign correctly
    # pms.tell("8D4840D6202CC371C32CE0576098")

    run_client()
