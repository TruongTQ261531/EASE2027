# Kế hoạch A → B và tiêu chí hoàn thành

Quyết định theo yêu cầu người dùng, 16/11/2026 (Asia/Bangkok): **A là hướng chính;
B là kiểm chứng phương pháp bổ trợ**. Được phép triển khai và xuất bản từng mốc trên GitHub.
Đây là lựa chọn ưu tiên nghiên cứu, chưa phải kết luận novelty hoặc bảo đảm được EASE nhận.
CFP đã xác minh: abstract 15/01/2027 AoE; full paper 22/01/2027 AoE.

## Câu hỏi nghiên cứu có thể kiểm tra

**A1 — Giới hạn bằng chứng:** Trong testbed WebRTC có điều kiện được đo riêng, những cặp
điều kiện nào gây nhầm lẫn khi chỉ quan sát phía nhận? Thêm lịch sử trước sự kiện, telemetry
và biến đổi hình ảnh phía nhận giúp phân biệt đến đâu, với chi phí gì?

Phân biệt ba mức kết luận: (i) cùng giá trị FPS hoặc cùng bucket chỉ chứng minh va chạm của
biểu diễn đó; (ii) baseline phân loại kém là khó phân biệt thực nghiệm; (iii) bất khả định danh
đòi hỏi mô hình/giả thiết quan sát và chứng minh hai phân phối quan sát tương đương. Không
suy (iii) từ (i)/(ii), không dùng test không có ý nghĩa thống kê để tuyên bố tương đương.
Benign static hiện giữ tĩnh suốt cuộc gọi; source freeze có chuyển động trước/sau. Lịch sử
có thể phân biệt hai thiết kế hiện tại, nên đây chưa phải cặp tương đương đầy đủ.

**A2 — Quyết định có từ chối:** Với rủi ro sai được định nghĩa trước, một bộ phân loại dùng
CPU có thể trả lời bao nhiêu phiên và từ chối bao nhiêu phiên? Rủi ro, coverage, bỏ sót lỗi,
false alarm trên controls và chi phí quan sát thay đổi thế nào khi đổi môi trường/cường độ?
Confidence của model không tự là xác suất đúng; coverage của prediction set không đồng
nghĩa kiểm soát lỗi trong các dự đoán singleton. Không chuyển bảo đảm cùng phân phối sang
host/browser mới nếu chưa kiểm chứng giả thiết.

**B1 — Độ hợp lệ của nhãn:** Việc dùng yêu cầu tiêm lỗi thay cho điều kiện đo được làm thay
đổi mẫu đủ điều kiện, nhãn và kết luận đánh giá như thế nào? Tách thí nghiệm paired scoring
(giữ nguyên prediction, đổi chính sách nhãn) khỏi paired retraining (đổi nhãn train, giữ split,
model và đánh giá bằng reference độc lập). Không coi injection thất bại là nhãn normal.

Người hưởng lợi dự kiến: kỹ sư QA/reliability của ứng dụng RTC. Đóng góp dự kiến là bằng
chứng về khi nào nên thu thêm thông tin hoặc không tự động chẩn đoán, cùng protocol đánh giá
có thể tái lập. Không đề xuất thuật toán abstention mới, không đo hiệu quả làm việc của người
dùng khi chưa có nghiên cứu người dùng. Xem [prior art](directions_prior_art.md).

## Thứ tự thực hiện và đầu ra kiểm tra được

| Mốc | Đầu ra | Tiêu chí xong | Trạng thái khi lập kế hoạch |
|---|---|---|---|
| A0 | RQ, matrix prior art, claim boundaries | Đọc methods nguồn gần; ghi phần chưa đọc, điểm trùng và quyết định | Hoàn thành rà soát có giới hạn; novelty gate còn mở |
| A1 | Analysis v1 trên dữ liệu cũ | Khóa input/config; train seed100, chọn ngưỡng seed200; không tune seed300; tái lập được | Tiếp theo |
| A2 | Protocol v2 và pilot đối chứng khó | Benign pause có cùng onset/duration; nhiều severity; missing observations; oracle đo trước/sau; chi phí thực đo | Chưa chạy |
| A3 | Main-study freeze | Novelty đủ rõ; labels/QC; cỡ mẫu/precision và ngân sách; splits mới trước khi thu test | Chưa đạt |
| A4 | Thí nghiệm và kết luận | Baselines, ablations, controls, uncertainty, failures; host/engine/userland khác có bằng chứng | Chưa chạy |
| B0 | Audit nhãn hiện có | Đếm toàn bộ attempts, verified, unknown; chỉ rõ request-conditioned verifier | Sau A1 |
| B1 | Pilot kiểm tra độ hợp lệ | Lệnh no-op/delayed/partial và sensor failure trong lab; independent checks mọi nhóm; ambiguous/multiple vẫn giữ | Chưa chạy |
| B2 | Paired label-policy study | Định lượng bias trên reference đã đánh giá độ tin cậy; không lấy label agreement tự tham chiếu làm ground truth | Chưa chạy |

## Analysis v1: chạy ngay, phạm vi hẹp

- Dữ liệu: 19 phiên sealed live-frozen-v1. Đã xem mô tả nên toàn bộ phân tích này là
  **retrospective feasibility**, không biến thành test xác nhận mới. Không sửa lock/source v1.
- Mỗi cuộc gọi một hàng; features lấy cửa sổ cố định 4–6s; lịch sử 1–3s. Không chọn cửa sổ
  theo actual injection/oracle timestamps. Đây là bài toán offline đã căn lịch, chưa phải phát
  hiện online hay chẩn đoán sớm. Source/OS oracle và thời điểm tiêm không vào model.
- Ba views: FPS; 9 receiver features hiện tại; 9 features hiện tại + 9 trước đó. Models cố định:
  dummy, logistic regression, random forest. Không tăng model complexity để cứu kết quả.
- So sánh always-predict, always-abstain, ngưỡng confidence chọn trên validation và gate dùng
  upper bound nhị thức một phía. Grid 5 ngưỡng × 3 model × 3 view × 5 strata = 225 kiểm tra;
  Bonferroni kiểm soát việc chọn giữa các candidates nếu giả thiết lấy mẫu hợp lệ.
- Strata: ba điều kiện lỗi + moving control + static control. Mỗi stratum chỉ có một phiên
  calibration; toàn bộ calibration chỉ có một content seed. Bounds là kiểm tra tính khả thi,
  **không cấp chứng nhận rủi ro triển khai**. Không có ngưỡng đủ bằng chứng thì từ chối toàn bộ;
  selective risk khi coverage=0 phải là null, không phải 0% lỗi.
- Báo cáo full confusion, per-class/per-control coverage và lỗi, Brier, empirical risk–coverage
  theo cả nhóm confidence bằng nhau; không fit calibrator/ECE claim từ 5 phiên validation.
- B0 đọc toàn bộ 77 attempts đã công bố, tách debugging và frozen cohorts. Nhãn verified hiện
  copy loại được yêu cầu sau khi check tương ứng pass; agreement không ước lượng oracle accuracy.

## Protocol v2/main study: điều kiện trước khi thu số lượng lớn

1. Controls ghép cặp theo content/schedule, intentional pause/recovery, benign static/adaptation;
   nhiều mức network/compute/media và severity giữ ngoài train. Không gọi “intent” là quan sát
   đo trực tiếp được. Phải có trace/cấu hình kiểm tra semantics của controls.
2. Observer chỉ đo; evaluator chạy các checks độc lập cho mọi nhóm mà không nhận request type.
   Request được join sau khi chốt measured state. Có thể trả nhiều điều kiện/unknown; sensor
   mất số đo khác với chứng minh không có lỗi. Chia sẻ process/clock/screen capture vẫn là hạn chế.
3. Không dùng tất cả phiên chung host/seed như các lần lặp môi trường độc lập. Split theo content,
   session, severity, configuration; calibration mới và holdout mới. Thiết kế randomized blocks;
   bootstrap theo block khi có phiên ghép cặp. Không tăng n bằng số cửa sổ.
4. Baselines: symptom rule, dummy, LR/RF; confidence threshold, margin/entropy rejection;
   risk-control baseline theo prior art. Conformal set là comparator nếu triển khai đúng mục tiêu,
   không thay selective-risk guarantee. Domino chỉ thành executable baseline nếu task/data phù hợp;
   hiện chưa chạy và không giả vờ đã so sánh hiệu năng với Domino.
5. Environment matrix cần thực chạy: host thứ hai có netem, engine ngoài Chromium, OS userland
   khác. Hiện có hai host/kernel nhưng cùng Debian12/Chromium159; Firefox ICE failed được giữ.
   Không coi một container mới là máy mới; không gộp ảnh hưởng engine và OS thành hiệu ứng nhân quả.
6. Định trước primary endpoint: selective error và coverage đồng thời, controls false-positive
   rate, class-wise abstention/missed-fault rates. Risk target 10%, confidence 95%, minimum useful
   coverage 50% là **mục tiêu thiết kế nội bộ**, chưa được kỹ sư thực tế xác nhận. Báo sensitivity
   tại risk 5/10/20%; không chọn mức đẹp sau khi nhìn test. Negative finding vẫn là kết quả.
7. Cỡ mẫu dựa trên precision, không chỉ số vòng lặp. Với 0 lỗi, một policy cố định cần ít nhất
   29 accepted độc lập để upper bound 95% <=10%, 59 cho <=5%. Với family 225 và 5 strata:
   cần tối thiểu 80/165 accepted **mỗi stratum**, tương ứng 400/825 tổng, trong trường hợp lý
   tưởng 0 lỗi. Đây là lower bound calibration, chưa phải power analysis, chưa gồm train/test,
   không bảo đảm 50% coverage. Thu thêm bao nhiêu phải dựa trên pilot v2 và thiết kế dependency.
8. CPU-first. Đo wall time/RSS, browser collection và dung lượng thật; chạy batches có stop rule
   trước ngân sách lớn. Không cần GPU/heavy training cho RQ hiện tại. Local Linux có netem giúp
   external validation; chuyển máy không tự khắc phục thiết kế thí nghiệm.

## Tiến độ nội bộ (không phải cam kết kết quả)

| Hạn | Việc tuần tự | Quyết định khi chưa đạt |
|---|---|---|
| 16–18/11 | A0 → A1 → B0, commit và push từng mốc | Công bố cả kết quả không đủ bằng chứng |
| 19–22/11 | Đóng closest-work gaps, chốt contribution A và vai trò B | Thu hẹp claim; không tự pivot khi chưa có quyết định có bằng chứng |
| 23–29/11 | Pilot v2, blind checks, hard controls, engine/host feasibility | Ghi failure; điều chỉnh phiên bản protocol trước main freeze |
| 30/11–06/12 | Precision/resource review, khóa protocol/splits/main seeds mới | Chưa đạt thì không gọi main study |
| 07–20/12 | Main A; B paired study sau khi reference đủ tin cậy | Báo denominator, failures và missingness đúng |
| 21–27/12 | Replication, failure analysis, robustness, artifact audit | Giới hạn kết luận theo môi trường thật đã chạy |
| 28/12–12/01 | Viết paper, claim→evidence, anonymized supplement | Không dùng named GitHub repo làm anonymous supplement |
| 15/01 và 22/01 AoE | Abstract và full paper theo CFP | Chỉ nộp claim có bằng chứng, không hứa acceptance |

Mỗi mốc cần code/config, input hashes, kết quả gồm cả failure, lệnh tái lập, giới hạn và Git commit.
Trạng thái máy đọc ở [research_progress.json](research_progress.json); không dùng các trang lịch sử
để suy rằng gate hiện tại đã đạt. Dữ liệu bên thứ ba chỉ lưu URL/hash/reading notes khi chưa rõ quyền.
