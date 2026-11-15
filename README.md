# EASE2027 — diagnostic evidence and uncertainty

**Kế hoạch hiện tại (16/11 Bangkok):** [Hướng A → B, RQ và tiến độ](docs/directions_a_b_plan.md),
[prior-art audit mới](docs/directions_prior_art.md), [trạng thái](docs/research_progress.json).
19/19 live calls đã được kiểm chứng; novelty/main-study gate còn mở. Các mốc pilot bên dưới
là lịch sử, không thay thế kế hoạch hiện tại.

Repository nghiên cứu hướng tới EASE 2027 Main Research Track. Hướng WebRTC hiện là **ứng viên
đang kiểm chứng**. Artifact này triển khai pilot bằng cuộc gọi thật; chưa chứng minh novelty,
chẩn đoán nguyên nhân nhân quả, giá trị multimodal, hay mức độ sẵn sàng nộp bài.

Đọc [research contract](docs/research_contract.md), [protocol](docs/pilot_protocol.md) và
[decision memo](docs/go_no_go_W2.md) trước khi diễn giải số liệu. Bản
[handoff gốc](docs/EASE_2027_CODEX_HANDOFF.md) được giữ nguyên để truy vết yêu cầu.

Mốc hiện tại: **36 tests passed**, pilot **30 phiên / 720 mẫu / 180 windows**, và báo cáo được
tái tạo giống hệt trên split đã đóng băng. Chi tiết đo thực tế ở [pilot summary](docs/pilot_results.json).

Công việc tiếp theo đang thực hiện theo thứ tự: **CFP/deadline → novelty → oracle độc lập →
đa môi trường**. CFP đã xác minh: abstract **15/01/2027 AoE**, full paper **22/01/2027 AoE**.
Xem [CFP](docs/venue_verification.md), [novelty audit](docs/novelty_audit.md) và
[oracle measurement probes](docs/oracle_independence.md); novelty và oracle live-call vẫn chưa đạt gate.

## Chạy trong cloud environment

Yêu cầu: Python 3.11+ (đã kiểm tra 3.12), `uv`, Chromium và coturn. Pilot dùng CPU, không cần
GPU, API trả phí, webcam hay microphone. Các package Python được khóa trong `uv.lock`.

```bash
cd /workspace/EASE2027
bash scripts/setup_cloud.sh
EASE_RUN_BROWSER=1 uv run --frozen pytest -q
bash scripts/reproduce_pilot.sh data/local/my-new-pilot
```

Lệnh cuối thu 30 phiên (10 đối chứng, 10 tạm dừng nguồn hình, 10 đóng kết nối), audit dữ liệu,
tạo features, chia tập theo phiên và chạy baseline. Dùng **thư mục output mới, rỗng** cho mỗi
experiment; không ghi đè kết quả cũ. Chi phí dự kiến khoảng 4–5 phút trên cloud CPU hiện tại.
Đây là ba điều kiện ứng dụng, **chưa phải ba nhóm lỗi** theo gate W4.

Trong cloud, script cài coturn vào `/workspace/.local/ease-turn/root` từ gói Debian có xác minh
chữ ký/checksum, không cần `sudo`. Chromium giữ nguyên chính sách mạng của môi trường.
Mỗi phiên tự mở rồi đóng HTTP server và TURN/TCP relay chỉ trên loopback; relay chỉ cho phép
peer 127.0.0.1. Không cần dịch vụ chạy thường trực, không dùng TURN công cộng. Thông tin xác
thực relay được tạo tạm trong từng phiên, không lưu vào dữ liệu.

Trên máy Linux khác, cài coturn và Chromium bằng package manager của hệ điều hành, sau đó
`uv sync --frozen`. Nếu dùng Chromium của Playwright: `uv run --frozen playwright install --with-deps
chromium`. Có thể đặt `EASE_CHROMIUM_EXECUTABLE` hoặc `EASE_TURN_PREFIX` khi cần. Chưa xác minh
artifact trên máy thứ hai; CI được cấu hình nhưng chưa chạy trên GitHub trong phiên này.

## Các bước riêng lẻ

```bash
uv run --frozen ease-rtc collect --config configs/scenarios/normal.yaml \
  --output data/local/smoke --runs 1
uv run --frozen ease-rtc audit --dataset data/local/smoke
uv run --frozen ease-rtc features --dataset data/local/smoke

# Chỉ evaluate dataset đủ ba điều kiện, >=5 phiên đã được kiểm chứng/điều kiện.
uv run --frozen ease-rtc evaluate --dataset data/local/my-new-pilot
uv run --frozen python scripts/audit_sources.py
```

CLI dùng package `ease_rtc` thay cho đường dẫn `python -m src...` giả định trong handoff để
hỗ trợ cài đặt chuẩn bằng Python package. `python -m ease_rtc --help` cũng được hỗ trợ.

## Kết quả và ranh giới dữ liệu

- `reports/audit.json`: checksum, timeline, replay oracle, số phiên verified/ambiguous/failed.
- `reports/splits.json`: tập train/validation/test theo session, đóng băng cùng fingerprint dataset.
- `reports/metrics.json`: rules, dummy, logistic regression, random forest; ba tập feature;
  confusion matrices, dự đoán từng phiên, calibration và bootstrap theo session.
- `reports/report.md`: bảng kết quả sinh từ script, luôn ghi rõ feasibility-only.
- [Data dictionary](docs/data_dictionary.md) ghi nguồn API, đơn vị và quy tắc missing/counter reset.

Oracle, lịch tiêm lỗi, source observer và manifests được tách khỏi features. Ma trận mô hình chỉ
nhận whitelist số đo. Requested intervention ≠ verified condition ≠ observed degradation ≠
causal root cause. Cột causal root cause luôn là `unestablished` trong pilot này. Phiên thất bại
vẫn được giữ trong audit và không được cấp training label.

Dữ liệu thu thật và outputs nằm trong `data/local/`, `artifacts/local/`, được Git-ignore.
Không commit raw media, credentials hoặc metadata mạng nội bộ. Trước public release cần audit
privacy/license và đóng gói dataset riêng; xem [data/README](data/README.md).

## Kiểm chứng và công việc tiếp theo

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
EASE_RUN_BROWSER=1 uv run --frozen pytest -q
```

`pytest` không bật biến trên sẽ bỏ qua 3 browser tests, vì vậy không đủ xác nhận cuộc gọi thật.
Test bao gồm schema, đơn vị đo, missing/reset counters, timeline, chống leakage, group split,
oracle không thành công giả, bootstrap theo session, và sửa dữ liệu làm checksum thất bại.

Ưu tiên tiếp: xác minh CFP/deadline; rà soát closest WebRTC work 2024–2026; xây network/CPU
interventions có đo độc lập trong lab cô lập; bổ sung hard negatives và cross-environment runs.
Không chạy `tc` trên host dùng chung. Theo dõi [roadmap](docs/roadmap.md),
[risk register](docs/risk_register.md), [candidate decision](docs/candidate_decision.md),
[literature matrix](docs/literature_matrix.csv) và [benchmark audit](docs/benchmark_audit.csv).

## Cập nhật sau xác minh CFP và portability

[Trạng thái từng bước](docs/research_progress.json): CFP đã xác minh; novelty audit ban đầu có
overlap trực tiếp và chưa chốt novelty; 18 oracle measurement probes đã chạy nhưng chưa thay
được live-call oracle; thêm 30 calls trên Chromium 156/159 cùng host. Xem
[cross-version results](docs/cross_environment.md). 47 tests pass, bao gồm 3 browser tests.

```bash
uv run --frozen python -m ease_rtc.oracle_probes --output data/local/new-oracle-probes
```

Probe network/compute/media yêu cầu FFmpeg và chỉ xác nhận phép đo riêng, không cấp causal labels.
Không thay đổi/publish cấu hình môi trường trong đợt kiểm chứng này.

## GitHub delivery và kết quả đã lưu

Kết quả đã hoàn thành được commit/push theo từng milestone (AGENTS.md). Xem
[bước tiếp theo và bản đồ lưu trữ](docs/next_steps.md). Bộ dữ liệu tổng hợp đã loại định danh mạng
được lưu ở [data/releases](data/releases/README.md), gồm per-session metrics và cả exploratory
failures. Bản gốc giữ trong data/local/; PDF bên thứ ba không được đưa vào repo.

## Live-call oracle và protocol feasibility v1

Xem [giải thích kế hoạch và bằng chứng](docs/plan_and_evidence.md),
[protocol đã cố định](docs/live_protocol_v1.md), và [hướng dẫn lab](lab/README.md).
Lab tiêm lỗi trong namespace container riêng, với bộ đo OS riêng và kiểm tra source pixels.
Dữ liệu pilot thành công lẫn thất bại được giữ tại data/releases/live-pilot/; bộ prospective
được lưu tại data/releases/live-frozen-v1/. Đây là các mốc feasibility, chưa phải kết luận causal
RCA, novelty hay study đã đủ sức nộp hội nghị. Các giới hạn Firefox và kernel đều được báo cáo.

Mốc prospective v1 đã hoàn tất: **19/19 live calls** vượt audit trên hai host/kernel; protocol và
dataset khóa checksum. Xem [kết quả và giới hạn](docs/live_frozen_v1_results.md). CI live-lab đã
chạy thành công; Firefox/OS-userland coverage và final-study gate vẫn chưa đạt.
