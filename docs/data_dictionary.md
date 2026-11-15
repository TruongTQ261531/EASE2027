# Observation dictionary v1.0

Raw `getStats()` objects are preserved as browser reports. Missing browser fields remain null
after normalization. No synthetic values are substituted. The parser supports exactly one inbound
video stream; multiple streams require an explicit policy. Counter resets, stream ID changes,
unavailable fields, and negative deltas become missing, not zero. A true zero increment remains zero.

| Feature | API / observation | Calculation and unit |
|---|---|---|
| receive_kbps | inbound-rtp.bytesReceived | Δbytes × 8 / Δseconds / 1000, kilobits/s |
| decoded_fps | inbound-rtp.framesDecoded | Δframes / Δseconds, frames/s |
| jitter_ms | inbound-rtp.jitter | Seconds × 1000, ms |
| rtt_ms | transport.selectedCandidatePairId → candidate-pair.currentRoundTripTime | Seconds × 1000, ms; missing if unavailable |
| packet_loss_ratio | inbound-rtp.packetsLost, packetsReceived | Δlost / (Δlost + Δreceived); undefined denominator → null |
| dropped_frame_ratio | inbound-rtp.framesDropped, framesDecoded | Δdropped / (Δdropped + Δdecoded); operational proxy, not perceptual QoE |
| connected_fraction | RTCPeerConnection.connectionState | Fraction of samples equal to connected |
| closed_fraction | RTCPeerConnection.connectionState | Fraction of samples equal to closed; legitimate state observation, easy explicit-closure signal |
| video_change_fraction | Receiver video drawn to 8×8 canvas | Fraction of adjacent pixel fingerprints that differ; not a validated freeze metric |

Reference: W3C WebRTC Statistics API, https://www.w3.org/TR/webrtc-stats/ . Access to the published
site is pending; primary specification source is https://github.com/w3c/webrtc-stats . API presence
must also be checked against actual raw observations for the pinned browser.

`monotonic_ms` uses the Python `perf_counter` midpoint around sequential sender and receiver
sampling. `collection_span_ms` bounds the call interval and estimates temporal uncertainty. Raw
browser timestamps are retained but not treated as a shared cross-page clock. Sampling delay is
observable; configured cadence is not asserted as achieved cadence. Feature windows average
available observations; long gaps and aliasing need stronger QC before the main study.

Source canvas fingerprints are stored **only** in `oracle/<uuid>/source.jsonl`. The separate receiver
fingerprint is an observation used for visual-change features. Neither source seeds nor fingerprints
themselves are numerical model inputs. Missing features are imputed using training data only,
with missing-value indicators in the scikit-learn pipeline.

Run manifests include the full scenario, browser/OS/Python/CPU, synthetic generator checksum,
Git HEAD plus dirty flag and source-tree checksum, lockfile checksum, relay binary checksum,
codecs, UTC start, monotonic-clock definition, collector-only CPU/RSS, file hashes and execution
status. Never publish raw ICE candidate addresses or environment identifiers without review.
No camera, microphone, personal call data, SDP credentials or relay credentials are recorded.
