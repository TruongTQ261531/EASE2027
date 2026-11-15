# Targeted prior-art audit cho A/B — 16/11/2026 Bangkok

**Quyết định: triển khai A như một empirical study về giới hạn bằng chứng và abstention;
B bổ trợ về validity. Novelty vẫn chưa xác lập.** Các kỹ thuật chính đều có prior art.
Không dùng claim “first uncertainty-aware RCA”, “first independent oracle”, hay “new abstention”.

Sáu truy vấn OpenAlex, tối đa sáu kết quả/truy vấn; sau đó lấy full text từ publisher/PMLR/
arXiv. Một số kết quả không liên quan (ví dụ blockchain oracle) bị loại. Đây là tìm kiếm có
giới hạn, không systematic review và không chứng minh không có bài trùng. Query URLs, danh sách
discovery, HTTP status, timestamp và SHA256 ở [source manifest](directions_sources.json).
Full PDFs chỉ ở artifacts/local/directions-a-b, không phân phối lại. Chỉ các phần chỉ rõ dưới
đây đã được đọc; không đánh dấu tất cả tài liệu là đã đọc toàn văn từ đầu đến cuối.

| Nguồn | Phần đọc và overlap | Hệ quả cho project |
|---|---|---|
| Geifman & El-Yaniv, [Selective Classification for Deep Neural Networks](https://arxiv.org/abs/1705.08500), 2017 | §§2–3: selective risk/coverage, confidence thresholds, binomial risk bound, multiple checks, giả thiết i.i.d. | Abstention và risk–coverage không mới; dùng như baseline, không đồng nhất confidence với correctness |
| Geifman & El-Yaniv, [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a.html), 2019 | Architecture/coverage calibration và Table1: reject option học chung, coverage thực có thể lệch mục tiêu | Không cần train neural net để tạo novelty; phân biệt target coverage và coverage quan sát |
| Angelopoulos et al., [Learn then Test](https://arxiv.org/abs/2110.01052), bản 03/10/2022 | §§1.1–2.3: calibration độc lập, fixed candidate family, FWER, có thể không tìm được policy đạt risk | Freeze candidate grid; xử lý selection multiplicity; không có candidate hợp lệ thì báo không đủ chứng cứ |
| Provan, [A Realization-Theoretic Foundation for Fault Diagnosis, with Diagnosability Equivalence Predictions](https://doi.org/10.4230/OASIcs.DX.2026.1), 2026 | Abstract, §§3.2,5.2–5.4: separability, confusable classes, structural witnesses trong formal model | Identifiability không phải ý tưởng mới. Bucket FPS va chạm chỉ là witness cho biểu diễn đó; không chứng minh tương đương toàn bộ WebRTC observations |
| Gupta, [Cost-Aware Abstention for LLM-Based IT Ticket Classification](https://arxiv.org/abs/2610.31657), 2026 | §§II–III: LR/RF baselines, held-out calibration, confidence/margin/entropy, cost sensitivity; preprint ghi accepted ICTAI | SE-adjacent abstention cũng có prior art. Không cần LLM; không claim engineering utility từ chi phí giả định |
| Duru et al., [Evidence Gated Root Cause Diagnosis for Fintech Microservices under Telemetry Loss](https://doi.org/10.58175/gjarr.2026.4.4.0091), 2026 | §§2–4: Gaussian simulated incidents, confidence/evidence gating, risk/coverage, mismatch, shared-seed dependence; artifact chưa chạy | Overlap trực tiếp với generic “RCA + evidence + abstention”. Khác biệt khả dĩ phải là measured live-call observational limits và cross-environment evidence, không chỉ gating hoặc hashes |
| Gurses et al., [Transport-Aware QoE Modeling for WebRTC](https://doi.org/10.1007/s10922-026-10076-z), 2026 | **Full PDF lấy được lần này**; §§4–5.1, Tables1/4/5: Google Meet/Chrome104–106,118 logs, freezeCount target, RF/MLP,80/20 split và10-fold CV | Task là symptom regression, không verified cause/selective diagnosis. Session grouping không được mô tả trong đoạn split đã đọc; chưa kiểm tra artifact nên không cáo buộc leakage. Bật QUIC setting không tự chứng minh đường media cụ thể; không mượn protocol claim này cho project |
| Hazimeh et al., [Magma: A Ground-Truth Fuzzing Benchmark](https://arxiv.org/abs/2009.01120), 2020 | §4.2–4.3: instrumentation/canary, tách reached/triggered/detected; chưa replay benchmark | Phân biệt injected/measured/observed không mới. B phải đo ảnh hưởng thực trên đánh giá, không chỉ xây oracle |
| Cotroneo et al., [Fault Injection Analytics](https://arxiv.org/abs/2010.00331), 2020 preprint, DOI10.1109/TDSC.2020.3025289 | Introduction/§2: distributed traces, probabilistic model để tách benign nondeterminism khỏi failure, cost của fault injection | Fault injection analytics và benign variation đã có prior work; cần controls/sampling hợp lý, không tuyên bố một class label là failure mode đã biết |
| Barr et al., [The Oracle Problem in Software Testing: A Survey](https://doi.org/10.1109/TSE.2014.2372785) | Metadata OpenAlex; UCL landing403; chưa đọc full methods | Lead cần đọc tiếp, chưa dùng nội dung không đọc làm bằng chứng |
| [Domino](https://arxiv.org/abs/2505.14540), 2025 | Selected setup/method sections đã đọc ở milestone trước; [audit cũ](novelty_audit.md) | Closest cross-layer WebRTC RCA comparator, chưa chạy artifact. Không lặp lại đóng góp cross-layer RCA |

Đọc được transport-aware đã đóng **access gap của một bài**, không có nghĩa toàn bộ novelty gate
đã đóng. WebRTC-QoE, Wi-Fi QoE, Machination vẫn cần full-method/artifact review; follow citations
của Domino, diagnosability và selective diagnosis trong software systems trước 22/11. Các nguồn
2026 mới cũng chưa được tái lập độc lập; số liệu của tác giả không phải kết quả project.

## Contribution candidate và phép thử bác bỏ

- Một dataset/protocol về **bounded measured conditions**, matched benign symptoms, missing
  observations và transfer, kèm các trường hợp hệ thống nên từ chối. Artifact tự nó chưa đủ novelty.
- Bằng chứng thực nghiệm về giá trị của từng observation budget: snapshot so với lịch sử receiver,
  controls khó và unknown/multiple states. Nếu chỉ easy controls phân biệt được bằng lịch sử,
  bỏ claim inherent non-identifiability; báo chính xác thiếu sót của FPS-only diagnosis.
- Đánh giá risk/coverage và ảnh hưởng của nhãn request-based. Nếu không đủ accepted calibration
  hoặc assumptions không có cơ sở, không tuyên bố controlled confidence. Nếu request/measurement
  không khác trên các ca có reference, không bịa label-bias effect; báo chưa nhận diện được hiệu ứng.

**Gate:** GO cho phân tích/pilot có thể tái sử dụng; NO-GO cho novelty/acceptance claim hay thu
main-study quy mô lớn trước khi contribution được phân biệt và reference được kiểm tra.
