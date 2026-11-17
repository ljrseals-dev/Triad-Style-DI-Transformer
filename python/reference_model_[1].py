#!/usr/bin/env python3
"""
Reference implementation of the Triad-style DI transformer hysteresis model.

Used for offline testing, coefficient exploration and harmonic analysis.
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import get_window
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class TransformerHysteresis:
    def __init__(self, sample_rate=44100.0):
        self.sr = float(sample_rate)
        self.reset()
        self.set_drive(0.55)

    def reset(self):
        self.m = 0.0
        self.prev_H = 0.0
        self.pre_state = 0.0
        self.post_state = 0.0
        self.dc_state = 0.0

    def set_drive(self, drive01: float):
        self.drive = float(np.clip(drive01, 0.0, 1.0))
        self.beta  = 1.7 + 2.3 * self.drive
        self.alpha = 0.20 + 0.22 * self.drive
        self.gamma = 0.06 + 0.14 * self.drive
        self.k     = 0.30 + 0.85 * self.drive

        freq = 180.0
        w = 2.0 * np.pi * freq / self.sr
        self.pre_coeff = np.exp(-w)
        self.post_coeff = self.pre_coeff

    def process_sample(self, x: float) -> float:
        # DC blocker
        self.dc_state += 0.995 * (x - self.dc_state)
        inp = x - self.dc_state

        driven = inp * (0.7 + 1.6 * self.drive)

        # pre-emphasis
        pre = driven + self.pre_coeff * self.pre_state
        self.pre_state = pre

        H = pre
        delta_H = H - self.prev_H

        target = np.tanh(self.beta * H)
        self.m += self.alpha * (target - self.m) + self.gamma * delta_H
        self.m = np.clip(self.m, -1.8, 1.8)

        nonlinear = H + self.k * self.m
        self.prev_H = H

        # de-emphasis
        post = nonlinear - self.post_coeff * self.post_state
        self.post_state = post

        return post

    def process_block(self, x: np.ndarray) -> np.ndarray:
        y = np.zeros_like(x)
        for i, sample in enumerate(x):
            y[i] = self.process_sample(float(sample))
        return y


def main():
    sr = 44100
    duration = 1.5
    t = np.arange(int(sr * duration)) / sr

    # test signal: 110 Hz sine (low enough to show weight) + a little 440 Hz
    x = 0.45 * np.sin(2 * np.pi * 110 * t) + 0.15 * np.sin(2 * np.pi * 440 * t)

    model = TransformerHysteresis(sr)
    model.set_drive(0.65)
    y = model.process_block(x)

    # normalise for listening
    y = y / (np.max(np.abs(y)) + 1e-12) * 0.89

    wavfile.write("transformer_hysteresis_test.wav", sr, (y * 32767).astype(np.int16))
    print("Wrote transformer_hysteresis_test.wav")

    # simple harmonic snapshot on a steady portion
    start = int(0.4 * sr)
    segment = y[start:start + 4096]
    window = get_window("hann", len(segment))
    spectrum = np.abs(np.fft.rfft(segment * window))
    freqs = np.fft.rfftfreq(len(segment), 1.0 / sr)

    # find peaks around 110, 330, 550 Hz etc.
    def level_at(f0):
        idx = np.argmin(np.abs(freqs - f0))
        return 20 * np.log10(spectrum[idx] + 1e-12)

    print("\nApproximate harmonic levels (dB re fundamental):")
    fund = level_at(110)
    for n, name in [(1, "1st"), (3, "3rd"), (5, "5th"), (2, "2nd"), (4, "4th")]:
        print(f"  {name:4s} ({n*110:5.0f} Hz): {level_at(n*110) - fund:6.1f} dB")

    # quick plot
    plt.figure(figsize=(10, 4))
    plt.plot(t[:2000], x[:2000], label="input", alpha=0.7)
    plt.plot(t[:2000], y[:2000], label="output", alpha=0.9)
    plt.title("Triad-style Transformer Hysteresis – time domain (first 2000 samples)")
    plt.xlabel("Time (s)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("time_domain.png", dpi=120)
    print("Wrote time_domain.png")


if __name__ == "__main__":
    main()
