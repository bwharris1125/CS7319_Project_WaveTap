"""
Spectrum analyzer utility for visualizing and analyzing IQ data streams.
"""

import matplotlib.pyplot as plt
import numpy as np

from arbiter.arbiter_iq_client import IQStreamClient


class SpectrumAnalyzer(IQStreamClient):
    """
    Spectrum analyzer client for visualizing IQ data.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        center_freq: float = 1.090e9,
        sample_rate: float = 2.048e6,
    ):
        super().__init__(host, port)
        self.center_freq = center_freq
        self.sample_rate = sample_rate
        self.plot_enabled = False

    def process_samples(self, samples: np.ndarray):
        """Process samples for spectrum analysis."""
        # Calculate FFT
        fft = np.fft.fftshift(np.fft.fft(samples))
        power_db = 20 * np.log10(np.abs(fft) + 1e-10)  # Avoid log(0)

        # Frequency bins
        freqs = np.fft.fftshift(
            np.fft.fftfreq(len(samples), 1 / self.sample_rate)
        )
        freqs += self.center_freq  # Shift to actual frequencies

        # Find peak
        peak_idx = np.argmax(power_db)
        peak_freq = freqs[peak_idx]
        peak_power = power_db[peak_idx]

        self.logger.info(
            f"Peak: {peak_freq / 1e6:.3f} MHz at {peak_power:.1f} dB "
            f"({len(samples)} samples)"
        )

        # Optional: Real-time plotting (requires matplotlib)
        if self.plot_enabled:
            plt.figure(figsize=(12, 6))
            plt.plot(freqs / 1e6, power_db)
            plt.xlabel("Frequency (MHz)")
            plt.ylabel("Power (dB)")
            plt.title(
                f"Power Spectrum - Center: {self.center_freq / 1e6:.1f} MHz"
            )
            plt.grid(True)
            plt.pause(0.01)
            # plt.clf()


def plot_spec_an(plot_en: bool = False, max_samples: int = 5):
    """Generate a spectrum analyzer plot of the IQ stream for debugging."""
    print("\nStarting spectrum analyzer...")
    analyzer = SpectrumAnalyzer("localhost", 8080, center_freq=1.090e9)
    analyzer.plot_enabled = plot_en

    try:
        analyzer.start_receiving(max_samples=1)
        if analyzer.plot_enabled:
            plt.show()
    except KeyboardInterrupt:
        print("Analyzer stopped.")


def main():
    """Example usage of the IQ stream client."""
    plot_spec_an(plot_en=True, max_samples=5)


if __name__ == "__main__":
    main()
