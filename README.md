# Triad-Style DI Transformer Hysteresis Model

**Practical physical-inspired model of a high-nickel audio input transformer**  
(approximate character of the Triad A-11/12J family used in classic DI boxes such as the Wolfbox)

This is **not** a reverse-engineered model of any commercial plugin (including Pulsar Modular P42) and **not** a claim of exact hardware measurements of a specific vintage transformer.  
It is an engineering approximation suitable for real-time audio plugins that aims to capture:

- Magnetic hysteresis / memory
- Low-frequency preferential saturation (“weight”)
- Predominantly odd-order harmonics with mild even-order warmth
- Numerically stable, real-time friendly behaviour

Inspired by standard magnetic modelling practice and modern analog-modelling numerical techniques (trapezoidal-style thinking, careful non-linear solving).

## Contents

```
docs/
  PHYSICAL_MODEL.md      – full description of the equations and design choices
src/
  TransformerHysteresis.h
  TransformerHysteresis.cpp
python/
  reference_model.py     – offline reference / coefficient playground
LICENSE
README.md
```

## Quick Start (C++)

The DSP class is header-only friendly and designed to drop into a JUCE `AudioProcessor`.

```cpp
#include "TransformerHysteresis.h"

TransformerHysteresis tx;
tx.prepare(sampleRate);
tx.setDrive(0.7f);          // 0 = clean, 1 = strong DI weight
tx.setMix(1.0f);

// in processBlock
for (int i = 0; i < numSamples; ++i)
    buffer.setSample(0, i, tx.processSample(buffer.getSample(0, i)));
```

## Python Reference

```bash
cd python
python reference_model.py
```

Generates a short test tone through the model and writes a WAV + basic harmonic analysis.

## Design Goals

- Real-time safe (no allocations in process, denormal protection)
- Low CPU (suitable for many instances)
- Controllable “weight” via a single Drive parameter
- Extensible (easy to add measured curves later)

## License

MIT – free for commercial and non-commercial use.  
Attribution appreciated but not required.

## Disclaimer

This model is an approximation.  
For a production plugin that claims to model a specific vintage transformer you should still perform measurements on real hardware or licensed data.
