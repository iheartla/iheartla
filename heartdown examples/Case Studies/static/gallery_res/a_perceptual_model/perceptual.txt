---
title: A perceptual model of motion quality for rendering with adaptive refresh-rate and resolution
author:
- name: GYORGY DENES
  affiliation: University of Cambridge
- name: AKSHAY JINDAL
  affiliation: University of Cambridge
- name: ALIAKSEI MIKHAILIUK
  affiliation: University of Cambridge
- name: RAFAŁ K. MANTIUK
  affiliation: University of Cambridge
full_paper: False
sectionBase: [5, 3]
eqBase: 12
---
# A PERCEPTUAL MODEL FOR MOTION QUALITY
## From $\proselabel{σ}$ to quality
❤: perceptual
Blur introduced by eye motion, hold-type blur, and spatial resolution will result in the loss of sharpness. To quantify this in terms of loss of perceived quality, we map the physical amount of blur to the perceived quality difference in JND units. Our blur quality function is inspired by the energy models of blur detection [Watson and Ahumada 2011]. Such mapping is applied to the orthogonal ($σ_O$) and parallel ($σ_P$) components of the anisotropic blur separately, resulting in two independent quality values ($Q_O$ and $Q_P$).

As we are interested in content-independent predictions, we assume the worst-case scenario: an infinitely thin line (Dirac delta function $δ(x)$), which contains uniform energy across all spatial frequencies. When convolved with <span class="def:σ">a Gaussian blur kernel $σ$ in the spatial domain</span>, the resulting image is a Gaussian function with standard deviation $σ$. The Fourier transform of this signal is also a Gaussian, given by:

``` iheartla
m(ω;σ) = exp(-2π^2 ω^2 σ^2) where ω ∈ ℝ, σ∈ ℝ
```

where <span class="def:ω">$ω$ is in cpd</span>. To account for the spatial contrast sensitivity of visual system, we modulate the Fourier coefficients with the CSF


``` iheartla

m̃(ω;σ) = CSF(ω) m(ω;σ) where ω ∈ ℝ, σ∈ ℝ
where
CSF ∈ ℝ->ℝ

```
where CSF is Barten’s CSF model with the recommended standard observer parameters and the background luminance of 100 $cd/m^2$ [Barten 2003].

To compute the overall energy in a distorted signal, we sample a range of frequencies $ω_i={1,2,...,64}$[cpd],andcomputethe blur energy as:

``` iheartla
`$E_b$`(σ) = sum_i ( (m̃(ω_i ; σ))/`$m̃_{t,b}$`)^`$β_b$`  where σ ∈ ℝ
where
ω_i ∈ ℝ
`$m̃_{t,b}$` ∈ ℝ
`$β_b$` ∈ ℝ
```

where <span class="def:m̃_{t,b}">$m̃_{t,b}$ is the threshold parameter</span> and <span class="def:β_b">$β_b$ is the power parameter of the model</span>. Both of these are fitted to psychophysical data in Section 6.3.

Energy differences can be interpreted as quality differences, yielding:

``` iheartla
`$∆Q_P$` = `$E_b$`(`$σ_P^A$`) - `$E_b$`(`$σ_P^B$`)
`$∆Q_O$` = `$E_b$`(`$σ_O^A$`) - `$E_b$`(`$σ_O^B$`)
where
`$σ_P^A$` ∈ ℝ
`$σ_P^B$` ∈ ℝ
`$σ_O^A$` ∈ ℝ
`$σ_O^B$` ∈ ℝ
```
substituting in the standard deviations of the blur components for $A$ and $B$, in the directions parallel ($P$) and orthogonal ($O$) to SPEM. 

We further explain why an energy model is suitable to predict JND differences in the supplemental material (Section S.1).
















