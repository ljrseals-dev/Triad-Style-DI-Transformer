#pragma once

#include <cmath>
#include <algorithm>

/**
 * TransformerHysteresis
 *
 * Real-time friendly approximation of a high-nickel audio input transformer
 * with magnetic hysteresis and low-frequency preferential saturation.
 *
 * Designed for DI / line-amp style colour (Triad A-11/12J family character).
 *
 * Not a measured model of any specific commercial product.
 */
class TransformerHysteresis
{
public:
    TransformerHysteresis() = default;

    void prepare (double sampleRate)
    {
        sr = sampleRate > 0.0 ? sampleRate : 44100.0;
        reset();
        updateCoefficients();
    }

    void reset()
    {
        m = 0.0f;
        prevH = 0.0f;
        preState = 0.0f;
        postState = 0.0f;
        dcState = 0.0f;
    }

    /** Drive amount 0 = almost clean, 1 = strong DI weight */
    void setDrive (float drive01)
    {
        drive = std::clamp (drive01, 0.0f, 1.0f);
        updateCoefficients();
    }

    void setMix (float mix01)
    {
        mix = std::clamp (mix01, 0.0f, 1.0f);
    }

    void setOutputGain (float gainLin)
    {
        outGain = gainLin;
    }

    float processSample (float x)
    {
        // very gentle DC blocker (transformer cannot pass DC)
        dcState += 0.995f * (x - dcState);
        float in = x - dcState;

        // Drive
        float driven = in * (0.7f + 1.6f * drive);

        // Pre-emphasis: mild low boost so lows hit the core harder
        // one-pole low-shelf-ish via simple state
        float pre = driven + preCoeff * preState;
        preState = pre;

        // ----- Non-linear magnetising stage -----
        float H = pre;                     // normalised field
        float deltaH = H - prevH;

        // target magnetisation (saturation shape)
        float target = std::tanh (beta * H);

        // hysteresis / memory update
        m += alpha * (target - m) + gamma * deltaH;

        // prevent slow drift
        m = std::clamp (m, -1.8f, 1.8f);

        // output = linear path + magnetisation contribution
        float nonlinear = H + k * m;

        prevH = H;

        // De-emphasis (complementary)
        float post = nonlinear - postCoeff * postState;
        postState = post;

        // Mix + output gain
        float y = mix * post + (1.0f - mix) * in;
        return y * outGain;
    }

    // stereo convenience
    void processBlock (float* left, float* right, int numSamples)
    {
        for (int i = 0; i < numSamples; ++i)
        {
            left[i]  = processSample (left[i]);
            if (right)
                right[i] = processSample (right[i]);
        }
    }

private:
    void updateCoefficients()
    {
        // map drive 0..1 into model coefficients
        beta  = 1.7f + 2.3f * drive;   // saturation sharpness
        alpha = 0.20f + 0.22f * drive; // follow speed
        gamma = 0.06f + 0.14f * drive; // hysteresis / rate
        k     = 0.30f + 0.85f * drive; // non-linear depth

        // pre/de-emphasis coefficients (sample-rate dependent)
        // mild emphasis around low-mids
        float freq = 180.0f; // Hz
        float w = 2.0f * 3.14159265f * freq / static_cast<float>(sr);
        preCoeff  = std::exp (-w);
        postCoeff = preCoeff;
    }

    double sr = 44100.0;

    // user parameters
    float drive   = 0.5f;
    float mix     = 1.0f;
    float outGain = 1.0f;

    // model coefficients (derived from drive)
    float alpha = 0.3f;
    float beta  = 2.5f;
    float gamma = 0.12f;
    float k     = 0.7f;

    // state
    float m        = 0.0f;
    float prevH    = 0.0f;
    float preState = 0.0f;
    float postState= 0.0f;
    float dcState  = 0.0f;

    float preCoeff  = 0.0f;
    float postCoeff = 0.0f;
};
