# Việc tiếp theo — 16/11/2026 Bangkok

Đã hoàn thành A0 (audit có giới hạn), A1 (phân tích hồi cứu) và B0 (audit nguồn nhãn).
Xem [kế hoạch A→B](directions_a_b_plan.md), [A1](directions_v1_results.md),
[B0](oracle_validity_v1_results.md). Không có main-study/novelty claim được thông qua.

1. **A2: thiết kế và pilot protocol v2.** Thêm intentional pause có cùng onset/duration/recovery
   với freeze, nhiều mức severity và quan sát thiếu. Cố định window/observation budget, content
   và randomized blocks trước khi chạy. Data mới, version mới; v1 vẫn giữ nguyên.
2. **B1 hỗ trợ A2:** evaluator đọc measurements để kiểm tra loss/high CPU/source motion cho
   mọi nhóm, không nhận requested type. Join request sau; tách measured state khỏi intention
   và causal attribution. No-op/delayed/partial và sensor outage cần được thử trên cuộc gọi thật.
   Nhiều trạng thái đồng thời hoặc thiếu bằng chứng phải trả multiple/unknown.
3. **Đóng novelty gate trước 22/11:** đọc phần còn thiếu của WebRTC-QoE, Wi-Fi QoE, Machination,
   oracle survey; citation chase Domino và software diagnostic uncertainty; so sánh task/oracle/
   splits/artifact. Đóng góp phải hơn generic “RCA+abstention” đã có prior art. Nếu chỉ có easy
   FPS counterexamples, thu hẹp claim; không tuyên bố fundamental non-identifiability.
4. **Portability feasibility trước 29/11:** sửa Firefox ICE, chạy engine khác thật, distinct OS
   userland, host thứ hai có netem. Giữ failures. Chưa có máy/môi trường phù hợp thì báo chính xác
   thiếu coverage; local Linux/Docker có thể giúp, GPU không phải yêu cầu hiện tại.
5. **Freeze main protocol trước 06/12 nếu gates đạt:** precision/resource budget sau pilot v2,
   fresh train/calibration/test seeds và held-out configs; primary risk/coverage, controls,
   class-wise abstention, strong baselines, paired-label analyses. Không dùng19 phiên cũ làm
   confirmatory holdout mới. Không đồng nhất minimum sample bound với power calculation.

Main runs 07–20/12, replication 21–27/12, manuscript 28/12–12/01 là **mốc nội bộ có điều kiện**.
Official CFP: abstract 15/01/2027 AoE, full 22/01/2027 AoE. Không đánh đổi bằng chứng để giữ lịch.
Tất cả milestone đã xong tiếp tục commit/push; bài chưa được nộp, môi trường không được publish lại.
