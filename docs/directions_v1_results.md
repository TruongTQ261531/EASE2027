# A1 — Diagnostic uncertainty: kết quả feasibility v1

**Đã chạy; chưa có bằng chứng kiểm soát rủi ro triển khai.** 19 cuộc gọi cũ: train 5, calibration 5,
evaluation cùng host 5, host khác 4. Mỗi tập development chỉ có một content seed. Toàn bộ dữ liệu
đã được xem mô tả trước khi chọn A/B; đây là phân tích hồi cứu, không phải xác nhận prospective mới.

Config được commit trước khi chạy ở `68ed478`; code/config/dependencies được khóa và đẩy ở
`7fe02c2`. Không sửa source/data/lock collection v1. Cả 19 phiên vẫn vượt audit.

## Bằng chứng quan sát

Biểu diễn FPS hiện tại với buckets cố định `<1`, `1–<10`, `>=10` tạo ra:

| Bucket FPS | Phiên | Điều kiện theo reference | Sai tối thiểu trên chính bảng này nếu mỗi bucket chỉ trả một nhãn |
|---|---:|---|---:|
| <1 | 8 | {'normal': 4, 'source_freeze': 4} | 4 |
| 1–<10 | 4 | {'compute_contention': 4} | 0 |
| >=10 | 7 | {'network_loss': 3, 'normal': 4} | 3 |

Đây là va chạm của **một biểu diễn FPS thô trên dữ liệu đã có**, không phải lower bound lỗi
quần thể, không chứng minh mọi telemetry/history đều bất khả định danh. Bốn source-freeze và
bốn benign-static cùng nằm bucket thấp; ba measured-network-loss nằm cùng bucket cao với bốn
moving controls. Không diễn giải FPS cao là không có packet loss hoặc không có mọi dạng degradation.

## Always-predict và ngưỡng chọn từ calibration

Bảng ghi `số chấp nhận / số sai trong số chấp nhận`; cột bắt buộc dự đoán ghi `số đúng / tổng`.
Không gộp hai tập để báo transfer effect: cloud thiếu network-loss, support class khác và seed300
được dùng chung giữa hai host. Không chọn model/ngưỡng mới sau khi xem bảng này.

| View | Model | Bắt buộc, cùng host | Bắt buộc, host khác | Chấp nhận/sai, cùng host | Chấp nhận/sai, host khác |
|---|---|---:|---:|---:|---:|
| fps_current | dummy | 2/5 | 2/4 | 0/0 | 0/0 |
| fps_current | logistic_regression | 2/5 | 1/4 | 0/0 | 0/0 |
| fps_current | random_forest | 3/5 | 3/4 | 1/0 | 1/0 |
| receiver_current | dummy | 2/5 | 2/4 | 0/0 | 0/0 |
| receiver_current | logistic_regression | 3/5 | 1/4 | 0/0 | 0/0 |
| receiver_current | random_forest | 3/5 | 3/4 | 0/0 | 0/0 |
| receiver_history | dummy | 2/5 | 2/4 | 0/0 | 0/0 |
| receiver_history | logistic_regression | 3/5 | 2/4 | 3/1 | 2/0 |
| receiver_history | random_forest | 4/5 | 3/4 | 1/0 | 1/0 |

Với LR + receiver history, ngưỡng 0.5 không có lỗi calibration trong các ca chấp nhận nhưng
trên evaluation cùng host chấp nhận 3/5 và sai 1/3. Đây là một counterexample hữu hạn cho việc
coi “calibration không lỗi” là bảo đảm, chưa phải ước lượng rủi ro triển khai. RF + history đúng 4/5
khi ép dự đoán, nhưng selective policy chỉ chấp nhận 1/5; không che phần bị từ chối bằng accuracy.

**Gate upper-bound: 0/9 cấu hình có ngưỡng đủ bằng chứng.** Dùng upper bound Clopper–Pearson
một phía, alpha 0.05 chia 225 checks, yêu cầu risk<=10% ở từng stratum. Mỗi stratum calibration
chỉ một phiên: ngay cả 0 lỗi, bound khoảng 99.978%; stratum không có accepted sample có bound 1.
Cả hai tập evaluation bị từ chối toàn bộ bởi gate này. Selective risk=**null**, không phải 0%.
Các bounds chỉ minh họa yêu cầu mẫu dưới giả thiết i.i.d. trong strata; giả thiết và deployment
population chưa được xác lập, cũng không áp bảo đảm từ source sang cloud.

Planning với 0 lỗi: policy cố định cần 29 accepted độc lập cho bound 95%<=10%, 59 cho <=5%.
Với 225 checks cần 80/164 accepted mỗi stratum tương ứng; chưa gồm train/test, dependency,
nonzero errors hoặc coverage. Không coi đó là power analysis hoàn chỉnh.

## Chi phí và tái lập

Đo trên cloud: 0.562 s cho analysis sau import, peak RSS 118.4 MiB
(gồm imports), 9 lần fit, model n_jobs=1, không GPU. Không bao gồm browser collection, setup,
whole-machine RAM hoặc dự báo main-study cost. Một lần chạy, không phải benchmark nhiều lần.

```bash
uv run --frozen python lab/freeze_plan.py
uv run --frozen python scripts/diagnostic_analysis.py --output /tmp/ease-directions-new
```

Output phải là thư mục mới. [JSON đầy đủ](../data/analyses/directions-v1/diagnostic_results.json)
gồm input audits, mỗi candidate threshold, confusion matrices, probabilities, per-class/control
counts, Brier và risk–coverage giữ nguyên ties; [CSV](../data/analyses/directions-v1/summary.csv)
để đọc nhanh; [runtime](../data/analyses/directions-v1/runtime.json). Không báo ECE từ vài mẫu như
đã được hiệu chuẩn, không bootstrap các windows như phiên độc lập.

**B0 đã hoàn thành:** [provenance audit trên 77 attempts](oracle_validity_v1_results.md). Tiếp theo A2/B1 pilot v2 có matched benign pause,
severity và checks không chọn theo request type. Novelty, valid reference và đa môi trường còn mở.

Tái lập: chạy lại từ output mới cho JSON diagnostic giống từng byte. Validation: 76 tests
local passed, 3 browser tests skipped local; [GitHub CI trên code 7fe02c2](https://github.com/TruongTQ261531/EASE2027/actions/runs/43750287058)
đã thành công với browser tests bật. Collector freeze vẫn hợp lệ.

Fresh tracked checkout 807d888 cũng tái lập mọi giá trị khoa học/input hashes; chỉ metadata
`provenance.code_commit` khác 7fe02c2 do commits tài liệu. Xem [verification record](directions_verification.json).
