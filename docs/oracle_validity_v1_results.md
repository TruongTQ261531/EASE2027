# B0 — Audit nguồn nhãn, không phải oracle accuracy

**77 attempts đã được kiểm tra: 32 verified, 45 execution failures, 0 ambiguous.** Đây là tổng kế
các vòng debugging cộng frozen collection, không phải mẫu i.i.d. để ước lượng failure rate.
Các phiên thất bại nằm trong mẫu số và không được cấp nhãn normal hay fault để train.

| Cohort | Attempts | Verified | Không có reference đủ điều kiện | Request khác verified label |
|---|---:|---:|---:|---:|
| live-frozen-v1/ci-43723089658 | 15 | 15 | 0 | 0 |
| live-frozen-v1/cloud | 4 | 4 | 0 | 0 |
| live-pilot/ci-43722157644 | 10 | 5 | 5 | 0 |
| live-pilot/cloud-attempt-v1 | 8 | 0 | 8 | 0 |
| live-pilot/cloud-attempt-v2 | 8 | 0 | 8 | 0 |
| live-pilot/cloud-attempt-v3 | 8 | 0 | 8 | 0 |
| live-pilot/cloud-attempt-v4 | 8 | 0 | 8 | 0 |
| live-pilot/cloud-attempt-v5 | 8 | 4 | 4 | 0 |
| live-pilot/cloud-attempt-v6 | 8 | 4 | 4 | 0 |

**0/32 label disagreements không chứng minh oracle đúng 100%.** Trong `verify_live`, request type
chọn phép kiểm tra; nếu pass, verified_condition được gán lại chính type đó. Vì vậy agreement
là tính chất của thiết kế verifier, không phải đánh giá bằng một bộ nhận diện ground truth khác.
OS observer có đường đo riêng; source screenshots dùng API khác với injection flags nhưng vẫn
chung orchestrator. Checksum đảm bảo truy vết dữ liệu, không xác nhận causal truth.

45 attempts còn lại sẽ có nhãn **không được hỗ trợ** nếu luôn dùng request làm nhãn. Không
gọi 45 đó là 45 nhãn sai đã biết hoặc 45 false positives: không có reference đủ điều kiện và đa số
lỗi xảy ra trước khi cuộc gọi/tiêm lỗi hoạt động. Không có nhóm completed-but-ambiguous trong
dữ liệu này để đo bias do tiêm một phần/no-op trong cuộc gọi đang hoạt động.

Hiện chưa có ước lượng ảnh hưởng lên false positives, false negatives, calibration hay model
ranking; các trường này là null trong report. Không tạo nhãn ngẫu nhiên rồi báo là lỗi đo thật.

## Thiết kế B1 tiếp theo

1. Observer ghi packet/process/media measurements; evaluator kiểm tra **mọi measured state**
   mà không nhận requested condition. Tách `measured_state` (loss/high CPU/no source motion)
   khỏi `intended_intervention` và `application_semantics` (intentional pause). Source không
   đổi pixels tự nó không phân biệt intentional pause với faulty freeze. Trả multiple/unknown
   khi cần; không ép blind checks thành một causal label.
2. Trong lab cô lập, chạy matched sham, đúng đường tiêm, no-op/delayed/partial và sensor outage;
   giữ log thời điểm/thực thi riêng. Chứng minh reference coverage/sensitivity bằng các cases
   có cả kiểm tra đo thứ hai, controls và recovery trước khi gọi reference là ground truth.
3. Với predictions cố định, paired-score theo request labels và measured reference trên cùng
   eligible cases; phần missing/unknown báo riêng, sensitivity bounds thay vì gán normal.
4. Paired-retraining là experiment khác: giữ split/preprocessing/hyperparameters và reference
   evaluation, chỉ thay chính sách nhãn training. Các policy giữ nguyên mô hình/samples nếu muốn
   tách label effect khỏi selection effect; báo cả fixed-intersection và eligible-coverage views.

Không sửa dữ liệu/collector v1. B1 cần version 2 và thí nghiệm mới; audit này chỉ hoàn thành B0.

```bash
uv run --frozen python lab/freeze_plan.py
uv run --frozen python scripts/oracle_validity_audit.py --output /tmp/ease-oracle-audit-new.json
```

[Kết quả từng attempt](../data/analyses/directions-v1/oracle_validity_results.json),
[A1](directions_v1_results.md), [kế hoạch/tiến độ](directions_a_b_plan.md).

Oracle JSON tái lập giống từng byte từ tracked checkout 807d888; xem [verification record](directions_verification.json).
