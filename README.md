# EASE2027 — diagnostic evidence and uncertainty

Nghiên cứu thực nghiệm hướng tới EASE 2027 Main Research Track. **A: diagnostic identifiability
và uncertainty** là hướng chính; **B: independent-oracle validity** là phần kiểm chứng bổ trợ.
[Kế hoạch, RQ và tiến độ](docs/directions_a_b_plan.md) ghi từng mốc và điều kiện hoàn thành.
Novelty và main-study readiness chưa đạt; không có bảo đảm acceptance hoặc causal diagnosis.

CFP đã xác minh: abstract **15/01/2027 AoE**, full paper **22/01/2027 AoE**;
[nguồn và yêu cầu](docs/venue_verification.md). Bản handoff là kế hoạch đầu vào, không phải
bằng chứng các giả thuyết nghiên cứu đã đúng.

## Kết quả hiện tại — 16/11/2026 Bangkok

- **A0:** đối chiếu selective prediction, diagnosability, oracle và direct WebRTC work; đã đọc
  methods của Transport-Aware QoE từ full PDF. [Prior art](docs/directions_prior_art.md) ghi
  rõ phần đã đọc và còn thiếu. Không coi abstention/oracle là ý tưởng mới.
- **A1:** phân tích hồi cứu 19 cuộc gọi đã sealed,9 tổ hợp model/view chạy CPU. FPS có va chạm
  giữa fault/control; không phương án nào đủ bằng chứng đạt risk gate. [Kết quả](docs/directions_v1_results.md).
- **B0:** audit 77 attempts (bao gồm19 cuộc gọi trên), 32 verified, 45 failed. Agreement của
  verifier phụ thuộc request không đo oracle accuracy. [Kết quả và giới hạn](docs/oracle_validity_v1_results.md).
- Hạ tầng đã đo ba nhóm điều kiện trong live calls, có controls, checksum, failed attempts và
  hai host/kernel. Cùng Debian12/Chromium159; Firefox ICE và distinct-userland gates còn mở.
  [Collection v1](docs/live_frozen_v1_results.md) là prospective feasibility; phân tích A/B sau
  khi đã xem dữ liệu là retrospective. Hai phạm vi này khác nhau.

## Kết quả lưu ở đâu?

| Nội dung | Đường dẫn |
|---|---|
| Trạng thái và claim→evidence | [research_progress.json](docs/research_progress.json), [claim_evidence.md](docs/claim_evidence.md) |
| Prior art, URLs, reading scope, hashes | [directions_prior_art.md](docs/directions_prior_art.md), [sources](docs/directions_sources.json) |
| Config/analysis lock | [configs/analysis](configs/analysis/) |
| Per-model predictions, risk/coverage, oracle audit, runtime | [data/analyses/directions-v1](data/analyses/directions-v1/) |
| Sanitized observations, including failures | [data/releases](data/releases/README.md) |
| Collector/lab and analysis code | [src/ease_rtc](src/ease_rtc/), [lab](lab/README.md), [scripts](scripts/) |
| Kế hoạch gốc và giới hạn nghiên cứu | [handoff](docs/EASE_2027_CODEX_HANDOFF.md), [contract](docs/research_contract.md) |

Mỗi milestone hoàn thành được commit/push lên GitHub theo AGENTS.md. Originals nằm trong
`data/local/`; third-party PDFs trong `artifacts/local/` chỉ lưu local, công bố URL/hash/notes.
Named development repository chưa phải anonymous supplement hoặc long-term DOI archive.

## Tái lập phân tích CPU

Tại root repository, dùng Python>=3.11 và uv. Các lệnh dùng output mới, không ghi đè dữ liệu cũ.
Không cần browser/GPU để phân tích bộ dữ liệu đã công bố.

```bash
uv sync --frozen
uv run --frozen python lab/freeze_plan.py
uv run --frozen python scripts/diagnostic_analysis.py --output /tmp/ease-directions-new
uv run --frozen python scripts/oracle_validity_audit.py --output /tmp/ease-oracle-new.json
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen pytest -q
```

Local: 76 tests passed, 3 browser tests skipped. [CI trên analysis code](https://github.com/TruongTQ261531/EASE2027/actions/runs/43750287058)
thành công với browser tests bật. Diagnostic JSON tái lập giống từng byte; collector freeze còn
hợp lệ. Training+analysis đo khoảng 0.56s sau imports, process peak RSS 118MiB, không GPU;
đây không phải chi phí main-study/browser collection.

Muốn thu **pilot mới**, đọc [lab guide](lab/README.md), [live protocol](docs/live_protocol_v1.md)
và [next steps](docs/next_steps.md). Cloud thiếu kernel netem; không chạy tc trên host dùng chung.
Không chỉnh source/protocol v1 đã khóa để thu thí nghiệm v2. Browser integration checks cần
Chromium/coturn và `EASE_RUN_BROWSER=1`; setup cloud: `bash scripts/setup_cloud.sh`.
