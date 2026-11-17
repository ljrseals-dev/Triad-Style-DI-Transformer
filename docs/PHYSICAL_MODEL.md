# Physical Model Description  
Triad-Style Audio Input Transformer (DI / Line Amp)

## 1. Goal

Reproduce the characteristic “weight”, density and harmonic behaviour of a high-nickel audio input transformer of the type used in classic DI boxes (Triad A-11/12J family / Wolfbox style).

Key audible traits we target:

- Preferential saturation of low frequencies → thick low-mid weight
- Mostly odd-order harmonics (3rd dominant)
- Mild even-order content for warmth
- Soft, musical onset of saturation rather than hard clipping
- Slight memory / hysteresis so the transfer curve is path-dependent

## 2. High-Level Structure

```
Input
  → optional gentle high-pass (DC blocker / transformer LF roll-off)
  → Drive gain
  → Frequency-dependent pre-emphasis (boost lows into the core)
  → Non-linear magnetising stage (hysteresis + saturation)
  → De-emphasis
  → Output gain + optional dry/wet
```

The heart of the model is the non-linear magnetising stage.

## 3. Continuous-Time Inspiration

Ideal transformer relation:

\[
v = N \frac{d\Phi}{dt}
\]

Flux and field:

\[
B = \frac{\Phi}{A}, \quad H = \frac{N i_m}{l}
\]

\[
B = \mu_0 (H + M)
\]

\(M\) (magnetisation) is the source of hysteresis and saturation.

## 4. Discrete Practical Model Used

We do **not** solve a full Jiles-Atherton ODE in real time (too expensive and stiff).  
Instead we use a stable, explicit memory-based approximation that still produces the desired hysteresis loop and rate dependence:

```text
H[n]     = drive * input[n]          (normalised magnetising force)
deltaH   = H[n] - H[n-1]

// core saturation shape
target   = tanh(β * H[n])

// hysteresis / memory
M[n]     = M[n-1] + α * (target - M[n-1]) + γ * deltaH

// output is linear part + non-linear magnetisation contribution
y[n]     = G * H[n] + k * M[n]
```

### Coefficient meanings

| Symbol | Role                                      | Typical range |
|--------|-------------------------------------------|---------------|
| α      | How fast magnetisation follows the target | 0.15 – 0.45  |
| β      | Saturation sharpness                      | 1.5 – 4.0    |
| γ      | Rate / hysteresis width contribution      | 0.05 – 0.25  |
| k      | Overall non-linear strength               | 0.3 – 1.2    |

These are exposed (or derived from a single Drive parameter) so the user can move from almost clean to heavy DI weight.

## 5. Frequency-Dependent Weight

Real transformers saturate more easily at low frequencies because the magnetising inductance has to support more flux for a given voltage at low f.

We approximate this with a mild pre-emphasis / de-emphasis pair:

- Before the non-linearity: gentle low-shelf boost (or 1st-order high-shelf cut of the highs)
- After the non-linearity: complementary cut

This makes the low end hit the core harder and is the main reason the model produces “weight” instead of generic broadband saturation.

## 6. Relation to Cytomic-Style Techniques

Cytomic’s published work emphasises:

- Careful discretisation of continuous-time circuit equations
- Robust handling of stiff non-linearities
- Trapezoidal (bilinear) integration where appropriate

This model adopts the same philosophy:

- All filters are bilinear-transformed one-pole or SVF-style
- The non-linear stage is kept explicit but heavily smoothed and rate-aware so it remains stable at audio rates
- State is updated with a convex combination that cannot explode

It is **not** a direct port of any Cytomic circuit; it simply follows the same numerical discipline.

## 7. Limitations & Future Work

- No measured B-H loop of a real A-11/12J is used (none is publicly available in usable form)
- Core losses (eddy currents) are only approximated by the rate term γ
- Temperature and DC magnetisation effects are omitted
- For highest accuracy one would replace the analytic `tanh` + memory with a lookup table or neural surrogate trained on real measurements

## 8. Recommended Parameter Mapping for a Plugin

Single user-facing “Drive” control (0–1):

```
drive = userDrive;               // 0..1
β     = 1.8 + 2.2 * drive;
α     = 0.22 + 0.18 * drive;
γ     = 0.08 + 0.12 * drive;
k     = 0.35 + 0.75 * drive;
```

This keeps the harmonic balance reasonably consistent while increasing both depth of saturation and hysteresis width with Drive.
