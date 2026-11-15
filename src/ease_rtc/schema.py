"""Versioned, closed schemas: identifiers and oracle metadata never become model inputs."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Condition = Literal["normal", "capture_pause", "connection_close"]


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Scenario(ClosedModel):
    name: str
    intervention: Condition
    seed: int = Field(default=42, ge=0)
    duration_s: float = Field(default=6.0, ge=3)
    intervention_start_s: float = Field(default=2.0, gt=0)
    intervention_end_s: float = Field(default=4.0, gt=0)
    sample_interval_ms: int = Field(default=250, ge=100, le=1000)
    width: int = Field(default=320, ge=64, le=1920)
    height: int = Field(default=180, ge=64, le=1080)
    fps: int = Field(default=20, ge=5, le=60)

    @model_validator(mode="after")
    def timing(self):
        if not 0 < self.intervention_start_s < self.intervention_end_s < self.duration_s:
            raise ValueError("Require 0 < intervention start < end < duration")
        if self.intervention_end_s - self.intervention_start_s < 1:
            raise ValueError("Observation of an intervention requires at least one second")
        return self


class Features(ClosedModel):
    receive_kbps: float | None = Field(default=None, ge=0)
    decoded_fps: float | None = Field(default=None, ge=0)
    jitter_ms: float | None = Field(default=None, ge=0)
    rtt_ms: float | None = Field(default=None, ge=0)
    packet_loss_ratio: float | None = Field(default=None, ge=0, le=1)
    dropped_frame_ratio: float | None = Field(default=None, ge=0, le=1)
    connected_fraction: float | None = Field(default=None, ge=0, le=1)
    closed_fraction: float | None = Field(default=None, ge=0, le=1)
    video_change_fraction: float | None = Field(default=None, ge=0, le=1)


class FeatureWindow(ClosedModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: str
    session_id: str
    window_start_ms: float = Field(ge=0)
    window_end_ms: float = Field(gt=0)
    features: Features

    @model_validator(mode="after")
    def ordered_window(self):
        if self.window_end_ms <= self.window_start_ms:
            raise ValueError("Window must have positive duration")
        return self


class OracleEvent(ClosedModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: str
    session_id: str
    requested_condition: Condition
    verification_status: Literal["verified", "failed", "ambiguous"]
    verified_condition: Condition | None
    observed_degradation: Literal["yes", "no", "unknown"]
    causal_root_cause: Literal["unestablished"] = "unestablished"
    label_confidence: Literal["medium", "low"]
    requested_start_ms: float
    requested_end_ms: float
    actual_start_ms: float | None
    actual_end_ms: float | None
    measurements: dict[str, float | int | str | bool | None]
    evidence_paths: list[str]
    limitation: str

    @model_validator(mode="after")
    def no_unverified_labels(self):
        if self.verification_status != "verified" and self.verified_condition is not None:
            raise ValueError("Unverified interventions must not receive a training label")
        if self.verification_status == "verified":
            if self.verified_condition != self.requested_condition:
                raise ValueError("Verified condition must match the observed requested condition")
        return self


class RunManifest(ClosedModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: str
    session_id: str
    environment_id: str
    started_at_utc: str
    config: Scenario
    browser_version: str
    browser_executable: str
    platform: str
    python_version: str
    cpu_count: int
    git_commit: str | None
    git_dirty: bool
    source_tree_sha256: str
    dependency_lock_sha256: str | None
    media_source_sha256: str
    media_source: Literal["synthetic_canvas_v1"] = "synthetic_canvas_v1"
    network_profile: Literal["local_turn_tcp_loopback", "local_host_candidates_no_stun"] = (
        "local_turn_tcp_loopback"
    )
    turn_binary_sha256: str | None = None
    clock: str
    codecs: list[dict]
    sample_count: int
    collection_duration_s: float
    process_cpu_s: float
    process_peak_rss_bytes: int
    execution_status: Literal["completed", "failed"]
    failure_reason: str | None
    files: dict[str, str]
