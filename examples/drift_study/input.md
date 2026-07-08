# Effects of Sampling Interval on Model Drift

It should be noted that model drift remains the primary failure mode in deployed classifiers. It is important to note that drift detection is often added late in the lifecycle. This study exists in order to quantify that risk.

We chose to perform an analysis of 12 production models due to the fact that public benchmarks rarely include post-deployment data. Each team also agreed to conduct an evaluation of its alerting thresholds. The monitoring stack has the ability to sample predictions at intervals from 1 minute to 24 hours (see https://example.org/drift-study and [3]).

Accuracy declined by 4.7% over 90 days, which is consistent with earlier findings (Rabanser, 2019). The effect was strongest for models retrained less than quarterly, and weakest where teams sampled at intervals of an hour or less, although the relationship between sampling interval and detection latency was not strictly monotonic across every model family that we examined in the course of this ninety-day observation window.

In order to reproduce these results, use the configuration in [Appendix B].
