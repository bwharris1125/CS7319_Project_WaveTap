"""Control RTL-SDR Module."""

from rtlsdr import RtlSdr


def main():
    """Run RTL-SDR Module."""
    sdr = RtlSdr()
    sdr.sample_rate = 2.048e6
    sdr.center_freq = 1.09e9
    # sdr.gain = "auto"
    sdr.gain = 30

    print("RtlSdr configured with:")
    print(f"  Sample Rate: {sdr.sample_rate}")
    print(f"  Center Frequency: {sdr.center_freq}")
    print(f"  Gain: {sdr.gain}")

    sdr.close()


if __name__ == "__main__":
    main()
