# Bước 4 — cross-version pilot, chưa phải multi-machine validation

**Đã chạy:** 30 cuộc gọi mới, 15 với Chromium 156.0.8078.79 hệ thống và 15 với Chrome for Testing
159.0.8154.6 (Playwright pinned revision 1255). Mỗi nhóm gồm 5 normal, 5 capture_pause, 5 explicit
connection_close. Tổng 720 mẫu và 180 windows. Cả hai nhóm 15/15 completed/verified, zero ambiguous.

Đây là **hai cấu hình browser trên một host/OS**, khác cả version và distribution. Không gọi là
cross-machine, cross-OS, Firefox generalization hoặc isolated version effect. Firefox 159 tải được
nhưng launch thất bại với `Could not find profile folder`, kể cả khi TMPDIR chuyển sang workspace;
không đưa Firefox vào số môi trường đánh giá thành công.

## Protocol và chống leakage

- Kế hoạch/shuffle seed 20271115 ghi trước collection ở `data/local/transfer-v1/protocol.json`.
- Cả hai version chạy xen kẽ ngẫu nhiên, cùng source seeds 1042–1046 cân bằng theo condition;
  các seeds này khác 42–51 của tập training cũ. Đây là content/session shift có chủ đích.
- Fit imputer/scaler và model chỉ từ 18 source training sessions cũ. Rule thresholds chỉ tune
  trên 6 validation sessions cũ. Không dùng 6 source test sessions để train/tune; không tune target.
- Đánh giá toàn bộ fresh source/target sessions được oracle xác nhận; audit denominator giữ đủ runs.
- Tách session giữa mọi cohort, kiểm fingerprint source frozen split và từ chối target cùng version.
- Models/feature sets predefined; không chọn winner từ các kết quả mới.

## Macro-F1 quan sát được (15 sessions/cohort, exploratory)

| Model | Features | Fresh 156 | Fresh 159 |
|---|---|---:|---:|
| rules | telemetry_logs | 0.933 | 1.000 |
| dummy | telemetry | 0.167 | 0.167 |
| logistic_regression | telemetry | 0.568 | 0.933 |
| random_forest | telemetry | 0.733 | 0.634 |
| dummy | telemetry_logs | 0.167 | 0.167 |
| logistic_regression | telemetry_logs | 1.000 | 1.000 |
| random_forest | telemetry_logs | 1.000 | 1.000 |
| dummy | telemetry_logs_video | 0.167 | 0.167 |
| logistic_regression | telemetry_logs_video | 1.000 | 1.000 |
| random_forest | telemetry_logs_video | 1.000 | 1.000 |

Confusion matrices, balanced accuracy và 500-draw session bootstrap intervals nằm trong
[transfer_results.json](transfer_results.json); dự đoán từng phiên trong local metrics.json.

Fresh same-version telemetry LR giảm còn 0.568 mặc dù source pilot test trước đó đạt1.0.
Đây là dấu hiệu cần điều tra sampling/content/condition drift và sample size; không tự quy là
hiệu ứng browser. Logs giúp phân biệt explicit-close vốn là một ca dễ. Chưa có bằng chứng media
utility mới hay main-study generalization từ bảng này. Không retune trên các tập đã xem.

## Tái tạo

```bash
PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright uv run --frozen playwright install chromium
uv run --frozen python scripts/collect_transfer.py --source-browser /usr/bin/chromium \
  --target-browser /workspace/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome \
  --output data/local/new-transfer
uv run --frozen python -m ease_rtc.transfer --training data/local/pilot-v0.1 \
  --fresh-source data/local/new-transfer/source --target data/local/new-transfer/target \
  --output data/local/new-transfer/metrics.json
```

Không overwrite dữ liệu/kết quả cũ. Đường target revision được xác định từ uv.lock/Playwright
đã cài trong lần thử này; nếu đổi dependency/browser phải ghi lại version và tạo experiment mới.
Các baseline hiện cần dataset training đã được giữ trong workspace; fresh clone phải reproduce
pilot hoặc dùng artifact release đã audit. Chưa có public data archive hay kết quả trên máy thứ hai.

**Gate còn thiếu:** browser engine khác, máy/OS khác, network/compute fault classes với independent
oracle trong live calls; held-out intensity/configuration; protocol/power và stronger baselines.
Đánh giá này không nâng các application-condition labels thành causal root-cause labels.
