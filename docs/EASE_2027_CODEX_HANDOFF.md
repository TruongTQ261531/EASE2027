# EASE 2027 — Codex Handoff: Applied AI Research Blueprint


> **Trạng thái:** Bản bàn giao từ trao đổi hiện có, cập nhật 2026-11-11. **Chưa phải kết luận của Deep Research** và **chưa có literature/benchmark audit hoàn tất**. Mọi giả thuyết, ngưỡng, kiến trúc và đề tài dự phòng dưới đây đều là **đề xuất cần kiểm chứng**, trừ khi ghi rõ là ràng buộc do người dùng xác nhận.
>
> **Mục đích:** Cho Codex đủ ngữ cảnh để thiết kế repository, dựng prototype, lập thí nghiệm có thể tái lập, và **không tự ý biến ý tưởng chưa kiểm chứng thành claim khoa học**.


## 1. Quyết định và ràng buộc đã chốt


### 1.1 Mục tiêu


- Nhắm **EASE 2027 Main Research Track**: đóng góp empirical software engineering (SE) có giá trị, không chỉ tăng accuracy của một mô hình.
- Đề tài phải là **hệ thống AI ứng dụng thực sự**, có người dùng, tình huống sử dụng, workflow, artifact chạy được và demo rõ ràng.
- Nghiên cứu phải có **RQ, baseline mạnh, ablation, kiểm định thống kê, failure analysis, external validity**, và reproducibility.
- Ưu tiên bài toán thực tiễn mà dữ liệu/nhãn/đánh giá có thể **kiểm chứng độc lập**.
- Người dùng không muốn lặp lại hướng **du lịch**, **eKYC**; không quay về hướng **Dashboard Data-Fidelity QA** đã bị bác bỏ.
- **Multimodal không phải mục tiêu tự thân**. Chỉ dùng video/audio/log/telemetry khi chứng minh được giá trị thông tin bổ sung; nếu không, bỏ modality đó.
- Tránh paper thuần thuật toán/toán học hoặc “concat embeddings rồi phân loại”.


### 1.2 Ràng buộc thực thi


- Thời gian lập kế hoạch: khoảng **24 tuần / 6 tháng** (giả định). **Phải xác minh deadline chính thức EASE 2027**; không mặc định 24 tuần còn đủ.
- GPU cục bộ: **RTX 3050 6 GB**; ưu tiên CPU, mô hình nhỏ, feature engineering, XGBoost/LightGBM, pretrained encoder nhỏ. Không phụ thuộc huấn luyện foundation model hoặc API trả phí.
- **Không survey, không tuyển người tham gia, không thu MOS/ACR mới, không annotation thủ công quy mô lớn.**
- Ground truth phải khách quan: verified fault injection, test result, trace, commit/issue/fix được xác nhận, hoặc public labeled benchmark có provenance.
- **Không để paper phụ thuộc duy nhất vào việc multimodal AI thắng baseline.** Thiết kế outcome-neutral, có nhánh nếu multimodal thắng / ngang / thua.
- Không được cam kết “100% accepted”, “novelty tuyệt đối”, hay “đã có benchmark” nếu chưa kiểm chứng.


### 1.3 Trạng thái tri thức hiện tại


| Mục | Trạng thái | Ghi chú |
|---|---|---|
| Hướng WebRTC/video conferencing fault diagnosis | **Ý tưởng đã giải thích, chưa được chọn cuối cùng** | Đang là primary candidate để kiểm tra |
| Kiến trúc telemetry + video + audio + logs | **Thiết kế sơ bộ** | Cần thí nghiệm kiểm chứng từng modality |
| Ground truth từ fault injection | **Phương án khả thi về nguyên lý** | Chưa dựng testbed; chưa xác minh causal label |
| Dataset công khai đủ raw media + traces + fault labels | **CHƯA XÁC MINH** | Không được tự tuyên bố tồn tại |
| Novelty so với 2024–2026 | **CHƯA AUDIT** | Bắt buộc lập matrix claim vs closest prior art |
| EASE 2027 CFP/deadline | **CHƯA XÁC MINH** | Cần nguồn chính thức |
| Microservices RCA / issue localization / regression testing | **Ứng viên dự phòng** | Chưa xếp hạng dựa trên benchmark đã kiểm tra |
| Deep Research blueprint & contingency | **Đã yêu cầu thực hiện** | Chưa được coi là kết quả hoàn tất trong file này |


## 2. Primary candidate (tạm thời): WebRTC Fault Diagnosis


**Working title:** *Beyond Network Metrics: An Empirical Evaluation of Multimodal Root-Cause Diagnosis for WebRTC Video Conferencing Systems.*


**Vấn đề:** Một cuộc gọi WebRTC có thể bị freeze hình, giật tiếng, giảm FPS, tăng delay. Triệu chứng giống nhau có thể do mất gói, nghẽn băng thông, CPU overload, encoder/camera, hoặc lỗi kết nối. Cần hỗ trợ kỹ sư **phân biệt nguyên nhân khả dĩ, định vị thành phần và đưa ra bằng chứng**, thay vì chỉ báo “chất lượng cuộc gọi kém”.


**Đối tượng dùng:** kỹ sư phát triển ứng dụng họp trực tuyến, QA/reliability engineer, SRE/operator của hệ thống RTC.


**Workflow demo:** chạy cuộc gọi thử nghiệm → tiêm lỗi có kiểm soát → thu telemetry/log/video/audio theo thời gian → phát hiện degradation → xếp hạng nguyên nhân và bằng chứng → gợi ý hành động kỹ thuật → đối chiếu với oracle tiêm lỗi. Không cần xây clone Zoom/Meet.


### 2.1 Fault taxonomy dự kiến


- **Network:** bandwidth throttling, packet loss, jitter, latency/RTT tăng, congestion, burst loss.
- **Compute/encode:** CPU overload, encoder saturation, dropped frames, FPS collapse.
- **Device/media:** camera capture failure, audio dropout, track mute/stop (phải phân biệt intentional mute với lỗi).
- **Connection/signaling:** ICE failure/restart, disconnect/reconnect.
- **Controls:** normal/no-fault, benign fluctuations, quality adaptation bình thường.
- **Hard cases:** hai nguyên nhân cùng gây một triệu chứng; multi-fault; fault chồng lấp; injected fault không tạo degradation; degradation không đến từ injected fault.


**Không đồng nhất:** injected condition ≠ observed symptom ≠ causal root cause. Phải có nhãn riêng cho ba khái niệm.


### 2.2 Kiến trúc chức năng đề xuất


```text
[Scenario Orchestrator / Seed / Environment Manifest]
                  |
     +------------+-------------------+
     |                                |
[WebRTC Testbed]                [Fault Injector]
 browsers, synthetic media      netem / CPU / device
     |                                |
     +------------+-------------------+
                  |
          [Independent Oracle]
          injection event + verification
                  |
  +---------------+------------------------------+
  |               |              |               |
[getStats()]  [System/RTC Logs] [Video QoS]    [Audio QoS]
 RTT, loss,   CPU, ICE, codec,   FPS, freeze,   dropouts,
 jitter,      reconnect         frame changes  silence
 bitrate
  |               |              |               |
  +---------------+--------------+---------------+
                  |
       [Timestamp Alignment + QC]
                  |
        [Feature/Window Builder]
                  |
    +-------------+-------------------------+
    |             |                         |
[Rules]     [Tabular Baseline]    [Temporal/Fusion Models]
    |             |                         |
    +-------------+-------------------------+
                  |
       [Calibration + Abstention]
                  |
       [Ranked Diagnosis + Evidence]
                  |
     [Evaluation + Reproducible Report]
```


**Nguyên tắc kiến trúc:** giữ riêng raw data, derived features, injected-event metadata, labels và model inputs. **Injection metadata tuyệt đối không được vào features inference**.


### 2.3 Modalities — ưu tiên theo rủi ro


1. **Bắt buộc ban đầu:** WebRTC `RTCPeerConnection.getStats()` + browser/system/RTC logs.
2. **Ưu tiên thứ hai:** objective video-quality signals (FPS, freeze count/duration, frame timing); chỉ lưu raw video nếu có quyền, dung lượng và đồng bộ phù hợp.
3. **Chỉ thêm khi có lý do thực nghiệm:** objective audio features (dropout/silence/spectral indicators); không dùng MOS chủ quan.
4. **Không cố định multimodal:** nếu telemetry + logs đủ tốt, đóng góp có thể là phân tích *khi nào media signals có/không có ích*, nhưng phải có novelty và evidence độc lập.


**Gợi ý công nghệ (chưa chốt):** browser WebRTC sample hoặc testbed tối giản, Playwright/browser automation, getStats polling, Linux `tc netem` trong môi trường phù hợp, FFmpeg synthetic reference media, Python pandas/scikit-learn/XGBoost/LightGBM, Docker Compose, pytest.


### 2.4 Schema dữ liệu tối thiểu (đề xuất)


```json
{
  "run_id": "uuid",
  "session_id": "uuid",
  "scenario_id": "network_loss_burst",
  "environment_id": "browser_os_cpu_network_profile",
  "seed": 42,
  "browser": "chromium",
  "media_source_id": "synthetic_reference_v1",
  "window_start_ms": 12000,
  "window_end_ms": 15000,
  "telemetry": {
    "rtt_ms": null,
    "jitter_ms": null,
    "packet_loss_ratio": null,
    "available_bitrate_bps": null,
    "frames_per_second": null
  },
  "system": {
    "cpu_percent": null,
    "encoder_state": null,
    "ice_connection_state": null
  },
  "video_qos": {
    "freeze_duration_ms": null,
    "dropped_frame_ratio": null
  },
  "audio_qos": {
    "dropout_ratio": null
  },
  "missing_modality_mask": {
    "telemetry": false,
    "logs": false,
    "video": true,
    "audio": true
  }
}
```


**Nhãn/oracle lưu trong file riêng, KHÔNG gộp vào feature record:**


```json
{
  "run_id": "uuid",
  "fault_event_id": "uuid",
  "injection_type": "packet_loss",
  "injection_start_ms": 10000,
  "injection_end_ms": 20000,
  "requested_intensity": "configured value",
  "verified_intensity": "measured value",
  "verification_status": "verified|failed|ambiguous",
  "observed_degradation": "yes|no|unknown",
  "label_confidence": "high|medium|low",
  "oracle_evidence_paths": ["..."]
}
```


Các trường chỉ là **schema khởi đầu**, cần map chính xác với WebRTC Stats API và quy ước đo lường; không invent fields từ API. Mọi timestamp cần monotonic clock hoặc alignment được ghi rõ.


### 2.5 Ground truth và causal validity


- Orchestrator ghi **fault command**, nhưng oracle chỉ chấp nhận khi **đo được fault thực sự xảy ra** (ví dụ network impairment ở layer thích hợp, CPU utilization thực, ICE transition).
- Dữ liệu `fault_injected=true` **không đủ** để kết luận lỗi đó gây freeze; cần so sánh observed degradation, control, timing, và điều kiện can thiệp.
- Có normal/no-fault runs và *sham interventions* khi phù hợp.
- Multi-fault có thể là multi-label; không ép về một class duy nhất nếu không có quy tắc causal attribution đáng tin.
- Các case ambiguous phải được giữ/đánh dấu, không lặng lẽ xóa để tăng điểm.
- Test split theo **session / environment / fault configuration**, không random window split làm leakage.
- Đảm bảo browser version, codec, OS, hardware, source media, seeds và config được ghi manifest.


## 3. Câu hỏi nghiên cứu và đóng góp khả dĩ


**RQ0 — Data/label validity:** Có thể xây testbed tạo ra fault labels đáng tin và các cặp symptom-equivalent cases ở mức nào? Tỷ lệ verified injection, ambiguous labels, reproducibility giữa runs?


**RQ1 — Diagnostic capability:** Hệ thống phân biệt fault class/component/root-cause ranking tốt đến đâu so với rule-based, network-only, logs-only và tabular baselines?


**RQ2 — Modality utility:** Video/audio/log thêm giá trị nào, trong điều kiện nào, với chi phí và missingness ra sao? Báo cáo cả kết quả **ngang/thua**.


**RQ3 — Robustness/generalization:** Cross-browser, cross-machine, unseen network profile, unseen fault intensity, overlapping faults và out-of-distribution có làm suy giảm kết quả? Có thể abstain/calibrate không?


**RQ4 — Engineering usefulness:** Độ trễ chẩn đoán, mức độ bằng chứng có thể truy vết, độ chính xác localization, và trade-off performance/cost so với threshold-based monitoring. **Không dùng survey**; chỉ dùng objective engineering proxies.


**Đóng góp ứng viên (chưa được xác nhận novelty):**
1. Reproducible WebRTC fault-injection + oracle verification + aligned multi-source trace artifact.
2. Empirical evidence về **khi nào và vì sao** media-level features bổ sung cho network/system telemetry trong root-cause diagnosis.
3. Robustness/failure taxonomy, uncertainty-aware diagnosis, missing-modality evaluation và thực nghiệm cross-environment.


**Cấm claim khi chưa có bằng chứng:** “first-ever”, “state-of-the-art”, “causal diagnosis” nếu chỉ supervised classification, “real-world root causes” nếu chỉ synthetic injected faults.


## 4. Baselines, model candidates và evaluation


### 4.1 Baselines tối thiểu


- Threshold/rule-based monitoring (RTT, loss, jitter, FPS, CPU; tune trên validation).
- Majority/stratified dummy; simple logistic regression hoặc random forest.
- **XGBoost/LightGBM** trên telemetry + logs.
- Telemetry-only; logs-only; video-only; audio-only nếu modality tồn tại.
- Naive concatenation (early fusion).
- Late fusion (calibrated predictions), hoặc temporal alignment + gating.
- Missing-modality robustness baseline.
- Strongest prior-work baseline **chỉ chọn sau literature audit**.


### 4.2 Model candidates


- **A — Hierarchical diagnosis:** detect degradation → classify fault family → localize component → evidence.
- **B — Calibrated late fusion:** small experts per modality, calibrated aggregation, abstention on uncertainty/missingness.
- **C — Hybrid rules + ML:** rules/physical constraints để lọc impossible causes, ML rank remaining hypotheses.


Không xây cả ba trước khi có baseline và dataset sạch. Bắt đầu A hoặc C đơn giản; so sánh với B chỉ khi pilot cho thấy modality có tín hiệu.


### 4.3 Metrics và thống kê


- Fault class: macro-F1, balanced accuracy, per-class precision/recall; PR-AUC nếu hợp lệ.
- Ranking/localization: top-1/top-k accuracy, MRR (nếu nhãn rank được xác thực).
- Degradation detection: precision/recall, time-to-detect, false alarms per hour.
- Calibration: ECE/Brier, risk-coverage/abstention curve.
- Engineering: inference latency (p50/p95), memory/CPU/GPU footprint, collection overhead.
- Ground-truth quality: verified injection rate, label ambiguity rate, failed/partial injections.
- Report confidence intervals (bootstrap **clustered by session/environment**), paired comparisons, effect sizes, multiple-comparison control khi cần; >=3 seeds là gợi ý tối thiểu, không phải power analysis.
- Không chọn model dựa trên test split; pre-register protocol trước final test; lưu config và commit hash.


**Outcome-neutral:** Nếu multimodal thua, vẫn báo cáo trung thực, phân tích conditions/missingness/cost. Nhưng **negative result chỉ đủ sức thành paper nếu thiết kế và coverage đủ mạnh, novelty có thật**; nếu không, phải pivot.


## 5. Các đề tài dự phòng độc lập


**Backup 1 — Microservices Root-Cause Analysis (RCA):** dùng traces/metrics/logs của hệ thống microservices và fault injection hoặc public labeled benchmark; tập trung vào reliability engineering, component localization, robustness across topology. **Rủi ro:** literature RCA đã đông; nhãn/benchmark/cross-system validity chưa kiểm chứng. Không mặc định chọn.


**Backup 2 — Issue-to-Code Localization / Regression-Failure Diagnosis:** liên kết issue reports, CI/test failures, code changes và confirmed fixes để hỗ trợ kỹ sư định vị module/file gây lỗi; có thể dùng benchmark issue–fix công khai nếu license, provenance và temporal leakage hợp lệ. **Rủi ro:** mining GitHub có noise, issue–commit mapping có thể sai, novelty đã bị nhiều nghiên cứu chiếm. Không mặc định có benchmark đạt chuẩn.


**Backup 3 (nếu cần) — Regression Testing / Test Selection:** hỗ trợ chọn test có giá trị khi code thay đổi, dùng historical commits/test outcomes. Chỉ giữ nếu xác minh được oracle và strong baselines.


**Decision rule:** Trước W4 phải có candidate matrix với nguồn primary cho (i) dataset access/labels/license, (ii) closest 2024–2026 work, (iii) SE relevance, (iv) 6GB feasibility, (v) artifact/demo. Chọn primary dựa trên evidence, **không mặc định WebRTC thắng**.


## 6. Risk register, contingency tree, kill criteria


| Risk | Dấu hiệu/trigger đề xuất | Hành động |
|---|---|---|
| Không tái tạo được fault có oracle | Đến W4 vẫn không có ít nhất 3 fault families + controls với verification logs đáng tin | Dừng tăng model complexity; kiểm tra testbed 1 tuần; nếu vẫn thất bại pivot sang benchmark công khai của backup |
| Raw audio/video không khả dụng hoặc tốn kém | W6 media extraction không ổn định hoặc đồng bộ sai | Bỏ audio trước, giữ telemetry + logs + video objective metrics; không ép multimodal |
| Modality không thêm giá trị | W12 ablation + CI cho thấy hiệu ứng gần 0/âm trên các split quan trọng | Chuyển trọng tâm sang điều kiện thất bại/missingness nếu novelty đủ; nếu không pivot |
| Label leakage / confounding | Classifier dùng environment/injection artifacts để đoán thay vì symptom | Sửa protocol, rebuild split, loại leaked fields; không báo cáo điểm cũ như kết quả |
| OOD collapse | Cross-browser/machine/fault profile sụt mạnh | Report failure envelope, calibration/abstention; nếu không có generalizable contribution thì hạ claim/pivot |
| Real-bug replay thất bại | Không có real bug có thể tái lập | Không claim real-world generalization; báo cáo injected-only scope |
| Novelty bị prior work chiếm | Closest 2024–2026 work đã có cùng RQ, oracle, setup và results | Pivot **research question** hoặc **đề tài**, không rebrand model |
| 6GB GPU không đủ | OOM/training time vượt budget | Chuyển sang engineered features, tree models, frozen encoders, smaller windows |
| Lịch 24 tuần không khớp deadline | CFP chính thức ngắn hơn | Rút scope ngay; ưu tiên một RQ mạnh và reproducible artifact |
| Cả primary và multimodal đều không khả thi | W8 chưa có data + baseline + label audit tối thiểu | **Hard pivot** sang backup có public dataset được tải và chạy baseline thực sự; không cố cứu sunk cost |


**Worst-case rule:** Không “cứu paper” bằng claim không được chứng minh. Nếu cả 3 hướng không có verified labels + novelty + feasible protocol, dừng nộp EASE main track và xuất artifact/technical report trung thực.


**Tài sản tái sử dụng khi pivot:** repo scaffold, experiment registry, split/checksum tools, bootstrap stats, plotting, CI, Docker, logging, baseline/evaluation pipeline. **Không** giả vờ raw WebRTC data dùng được cho issue localization.


## 7. Go/no-go gates trong 24 tuần


| Mốc | Deliverable tối thiểu / điều kiện |
|---|---|
| **W2** | Repo chạy được; testbed WebRTC 2 endpoints; collector getStats + logs; ít nhất 10 runs với manifests; initial prior-art list |
| **W4** | Pilot normal + >=3 fault families; independent verification; novelty matrix sơ bộ; benchmark access check cho 2 backup |
| **W6** | Data schema v1, QC scripts, split strategy; đo tỷ lệ injection verified/ambiguous; chọn modalities giữ lại |
| **W8** | Baseline end-to-end trên held-out sessions; reproducible metrics; **hard pivot** nếu oracle hoặc baseline không tồn tại |
| **W12** | Full experimental design frozen; modality ablations; cross-condition pilot; thống kê sơ bộ |
| **W16** | Main runs, >=3 seeds nếu phù hợp; confidence intervals; cross-environment tests; failure analysis |
| **W20** | Paper draft, artifact audit, adversarial reviewer checklist, plots/tables từ script |
| **W24** | Submission-ready manuscript + public/private reproducibility package theo license và venue rules |


Các ngưỡng trên là **đề xuất quản trị rủi ro**, không phải dữ liệu nghiên cứu đã đo hay bảo đảm nộp đúng deadline.


## 8. Kế hoạch 14 ngày đầu cho Codex


### Ngày 1–2: Scaffolding, provenance, no leakage


- Tạo repo với `README.md`, `docs/research_contract.md`, `docs/assumptions.md`, `docs/literature_matrix.csv`, `docs/benchmark_audit.csv`, `docs/risk_register.md`.
- Thiết lập `pyproject.toml` hoặc `requirements.lock`, lint, pytest, GitHub Actions CI.
- Tạo config schema và `run_manifest.json` lưu seed, browser/OS/version, codec, host, CPU, network profile, source media checksum, commit hash, timestamps.
- Đặt policy: `data/raw` và `data/oracle` tách biệt; `data/features` không có trường injection labels.
- **Acceptance:** `pytest` pass, schema validates sample records, CI xanh, no secrets/raw media committed.


### Ngày 3–5: Minimal WebRTC call and collector


- Dùng WebRTC sample/testbed hợp pháp, 2 peers local/container, synthetic audio/video reference nếu được.
- Thu `getStats()` theo chu kỳ cố định; logs/ICE state; lưu timestamp, session id, codec/browser metadata.
- Xây parser normalize theo W3C WebRTC Stats API, xử lý missing fields và browser differences.
- **Acceptance:** >=10 clean sessions có manifest, stats rows không rỗng, monotonic timeline, data dictionary có unit và provenance.


### Ngày 6–8: Verified injection


- Tạo scenario runner với fault command + independent verification (network, CPU); chạy controls.
- Bắt đầu từ packet loss, bandwidth throttling, CPU load. Không thêm 10 fault types cùng lúc.
- **Acceptance:** có script tạo lại ít nhất 3 classes/conditions; verified vs requested intensity được ghi riêng; failed injection không bị gán label thành công.


### Ngày 9–11: Objective degradation and baseline


- Video QoS từ WebRTC stats hoặc reference comparison; tránh phụ thuộc chủ quan.
- Tạo feature windows với temporal alignment; session-level train/validation/test splits.
- Huấn luyện rule baseline + simple tabular baseline, không dùng oracle metadata.
- **Acceptance:** pipeline một lệnh tạo metrics JSON + confusion matrix; kiểm tra no-overlap giữa sessions trong splits.


### Ngày 12–14: Audit & decision memo


- Chạy ablation telemetry vs telemetry+logs; đo overhead.
- Điền ít nhất 5 closest related papers (ưu tiên 2024–2026), có DOI/URL, claim overlap, evaluation overlap và code/data availability **được kiểm tra**.
- Kiểm tra public dataset cho **hai backup độc lập**, tải sample/inspect schema/license nếu có.
- Viết `docs/go_no_go_W2.md`: các sự thật đã xác minh, điều chưa biết, risk/mitigation, quyết định tiếp tục/pivot.
- **Acceptance:** người khác có thể clone và tái tạo ít nhất một run và một baseline trên máy khác.


### Cấu trúc repo đề xuất


```text
ease-2027-research/
  README.md
  LICENSE
  CITATION.cff
  pyproject.toml
  configs/
    scenarios/
    experiments/
  docs/
    research_contract.md
    assumptions.md
    literature_matrix.csv
    benchmark_audit.csv
    risk_register.md
    data_dictionary.md
    go_no_go_W2.md
  schemas/
    run_manifest.schema.json
    feature_window.schema.json
    oracle_event.schema.json
  src/
    rtc_testbed/
    collectors/
    injectors/
    verification/
    features/
    baselines/
    models/
    evaluation/
  tests/
    test_schemas.py
    test_no_label_leakage.py
    test_split_integrity.py
    test_timestamp_alignment.py
  scripts/
    reproduce_pilot.sh
    run_baselines.sh
    audit_dataset.py
  data/
    README.md
    raw/.gitkeep
    oracle/.gitkeep
    features/.gitkeep
  artifacts/
    metrics/
    plots/
    manifests/
  .github/workflows/ci.yml
```


### CLI contract Codex nên triển khai (đây là giao diện mong muốn, chưa tồn tại)


```bash
python -m src.rtc_testbed.run --config configs/scenarios/normal.yaml
python -m src.rtc_testbed.run --config configs/scenarios/packet_loss.yaml
python -m src.verification.audit --manifest artifacts/manifests/latest.json
python -m src.features.build --config configs/experiments/pilot.yaml
python -m src.baselines.train --config configs/experiments/pilot.yaml
python -m src.evaluation.report --config configs/experiments/pilot.yaml
pytest -q
```


**Không giả định các command trên chạy ngay**; Codex phải tạo modules, configs và docs tương ứng, hoặc điều chỉnh CLI có lý do. Không yêu cầu `sudo tc` trên host nếu không có sandbox/netns an toàn.


## 9. Adversarial reviewer checklist


1. **“Đây chỉ là supervised fault classifier trên lỗi tự tiêm?”** → Cần oracle verification, symptom-equivalent scenarios, hard negatives, strong SE workflow và phân tích external validity.
2. **“Multimodal novelty đâu?”** → So sánh trực tiếp với 2024–2026 closest work; không claim novelty nếu chỉ early/late fusion phổ thông.
3. **“Có label leakage không?”** → Test tự động loại scenario IDs, injector timestamps, fault flags, filename hints; group split.
4. **“Synthetic media có đại diện call thật?”** → Báo cáo scope; nếu có media tự do bản quyền hoặc public traces thì đánh giá thêm; không thổi phồng.
5. **“Fault injection có thật sự gây lỗi?”** → Independent measured verification, controls, intervention timing, ambiguous labels.
6. **“Tại sao không dùng rules?”** → Rule-based baseline tune công bằng, đo accuracy/latency/overhead.
7. **“Model có chuyển sang browser/machine khác không?”** → Cross-environment tests, calibration/abstention, confidence intervals.
8. **“Cần audio không?”** → Ablation và cost/benefit; nếu không, bỏ.
9. **“Đóng góp SE hơn ML ở đâu?”** → Root-cause engineering task, diagnosis workflow, failure taxonomy, artifact reuse, actionable localization.
10. **“Reproducibility?”** → Licenses, data provenance, checksum, environment, scripts, split files, configs, seeds, logs, generated figures.


## 10. Artifact và paper checklist


**Artifact bắt buộc:**
- Source code + commit hashes, environment lockfiles, Docker/OS/browser versions.
- Config scenarios, fault injector, independent verification, control runs.
- Dataset manifest, schema, units, provenance, licenses, checksum, anonymization/privacy policy.
- Splits by session/environment, no-leakage tests, immutable test set.
- Baselines, model configs, seeds, resource monitoring.
- Evaluation scripts, raw per-run metrics, CI/bootstrap, ablation, failure cases.
- Reproduction README (1-command pilot nếu có thể), expected runtime and hardware.
- Figure/table generation scripts and traceability from each claim to experiment.


**Paper outline đề xuất:**
1. Introduction: engineering pain point + nontrivial ambiguity.
2. Related Work: closest 2024–2026 and novelty matrix.
3. Problem/Task/Oracle: definitions of fault, symptom, cause, component.
4. System & Data Collection: testbed, injection verification, privacy.
5. Study Design: RQs, baselines, splits, metrics, preregistration.
6. Results: RQ0 label validity; RQ1 diagnosis; RQ2 modality value; RQ3 robustness; RQ4 cost/engineering usefulness.
7. Failure Analysis / Threats to Validity.
8. Artifact and Conclusion.


## 11. Research verification queue (chưa thực hiện trong handoff này)


**P0 — trước khi chốt đề tài:**
- Official EASE 2027 Main Track CFP, page limit, deadline, artifact/open science requirements.
- 2024–2026 prior art: WebRTC QoE prediction, RTC anomaly detection, network/media fault diagnosis, multimodal RCA, causal fault localization.
- Public benchmarks: direct file access, schema, labels, raw media/traces, license, reproducibility, DOI and availability.
- Backup benchmarks: microservices RCA và issue-to-code/test failure; xác minh dataset thật sự có labels và được dùng hợp lệ.
- Minimal feasibility: getStats fields available per browser; objective audio/video degradation measures; hardware budget.


**Tài liệu kỹ thuật nên kiểm tra trực tiếp:**
- W3C WebRTC Statistics API: https://www.w3.org/TR/webrtc-stats/
- MDN RTCPeerConnection.getStats(): https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection/getStats
- WebRTC samples: https://webrtc.github.io/samples/
- Linux tc-netem manual: https://man7.org/linux/man-pages/man8/tc-netem.8.html
- Playwright: https://playwright.dev/


Các link trên là **điểm khởi đầu kỹ thuật**, không phải evidence novelty, benchmark availability hay EASE CFP.


## 12. Chỉ thị thực thi cho Codex


**Làm ngay:** đọc file này; tạo `docs/research_contract.md`; kiểm tra environment; dựng testbed + schema + collector + verification + baseline + CI. Ưu tiên reproducibility và label validity.


**Không làm ngay:** huấn luyện model lớn; tự chọn 4 modalities; viết claim SOTA; tạo dataset labels bằng cách copy injector config; thêm LLM vì “AI”; xây UI dashboard trước khi pipeline có data; giả định Deep Research đã xác nhận novelty.


**Trước mỗi milestone:** tạo decision memo với bốn cột **VERIFIED / ASSUMED / FAILED / NEXT TEST**, và cập nhật `risk_register.md`.


**Definition of Done cho nghiên cứu:** mọi claim có source hoặc experiment; mọi số liệu có script tái lập; không leak labels; negative findings được báo cáo; có hard-pivot path nếu primary không còn giá trị khoa học.


---


**Lưu ý cuối:** Đây là bản tổng hợp những gì **đã thảo luận**, cộng với các bước triển khai **được đề xuất** để Codex bắt đầu. Báo cáo Deep Research đầy đủ về architecture, novelty, datasets và backup plans đang được yêu cầu nhưng **không được coi là đã hoàn tất hoặc đã xác minh** trong tài liệu này. Sau khi nhận kết quả Deep Research, cập nhật lại decision matrix, nguồn primary, claim boundaries và go/no-go gates trước khi khóa hướng nghiên cứu.