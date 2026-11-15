# Claim → evidence → giới hạn

Cập nhật 16/11/2026 Bangkok. Chỉ các claim ở đúng phạm vi dưới đây có bằng chứng.

| Claim có thể viết | Bằng chứng | Không được suy rộng thành |
|---|---|---|
| Main-track deadline hiện công bố 22/01/2027 AoE | venue_verification.md, official CFP links | Rank edition đã independently audited hoặc chắc chắn được nhận |
| Ba điều kiện network/compute/media được đo trong live-call lab, có controls | live_frozen_v1_results.md, sealed releases, CI 43723089658 | Mọi root cause thực tế đã được xác minh; measured condition là QoE degradation |
| FPS bucket giống nhau chứa cả source-freeze/static và network-loss/moving-control | directions_v1_results.md, diagnostic_results.json | Mọi receiver feature hoặc lịch sử đều không thể phân biệt; Bayes-error lower bound |
| Ngưỡng không lỗi trên calibration có thể sai trên evaluation | LR+history: accepted 3, wrong 1 ở source evaluation | Đã ước lượng chính xác deployment risk từ 3 accepted samples |
| Risk-bound gate không tìm được policy đạt target trên pilot này | 9 cấu hình, 225 checks, 1 calibration session/stratum | Từ chối hết nghĩa 0% selective risk, hoặc thuật toán đã đạt controlled confidence |
| 77 attempts được giữ; 32 verified, 45 failed | oracle_validity_v1_results.md, per-attempt audit | 45 proven wrong labels hoặc failure-rate estimate i.i.d. |
| Request/verified labels đồng ý 32/32 vì verifier có điều kiện theo request | lab_sensors.verify_live, oracle_validity_results.json | Oracle accuracy 100% hoặc độc lập về causal truth |
| Collection chạy trên hai host/kernel | manifests/platforms và live results | Cross-engine, distinct OS userland hoặc isolated host causal effect |
| Phương pháp A/B có prior art rõ ràng | directions_prior_art.md, URLs/hashes/section notes | Novelty đã chốt, first/SOTA hoặc paper đã đạt chuẩn nộp |
| Phân tích nhỏ hiện chạy CPU khoảng 0.56 s, peak RSS 118 MiB | data/analyses/directions-v1/runtime.json | Main-study collection rẻ như vậy, hoặc cần train GPU model |

Tiếp theo cần evidence cho matched difficult controls, blind measured states, reference reliability,
precision và fresh holdouts; xem next_steps.md. Kết quả âm/không đủ chứng cứ vẫn được công bố.
