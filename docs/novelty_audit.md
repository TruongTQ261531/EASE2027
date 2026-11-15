# Bước 2 — novelty audit ban đầu, 15/11/2026

**Cập nhật 16/11 Bangkok:** người dùng chọn A (identifiability/uncertainty) ưu tiên1 và B
(oracle validity) ưu tiên2. [Audit mới](directions_prior_art.md) đã lấy được và đọc methods
full PDF của Transport-Aware QoE, cùng selective prediction/diagnosability/oracle prior art.
Mô tả access failure dưới đây là lịch sử lần truy cập đầu; novelty vẫn chưa được xác lập.

**Kết luận: novelty chưa được xác lập. Không chốt paper quanh “multimodal WebRTC RCA”.**
Phát hiện overlap đủ rõ để bác bỏ việc coi testbed/getStats/fusion là novelty mặc định.
Đây là audit có giới hạn truy cập, không phải systematic literature review đã hoàn tất.

## Cách tìm và mức bằng chứng

Truy vấn OpenAlex: WebRTC diagnosis, WebRTC QoE, video conferencing troubleshooting,
video conferencing root cause, WebRTC testing, real-time communication anomaly detection.
Tìm 2020–15/11/2026 để không bỏ các nền tảng cũ; ưu tiên 2024–2026. Crossref dùng đối chiếu
DOI/metadata. Kết quả và query URL lưu tại `artifacts/local/research-audit/openalex/*.json`,
`crossref/*.json`, `papers/*.metadata.json`; checksum trong research_source_manifest.json.

Crossref broad search trả nhiều kết quả không liên quan và hai truy vấn 429; Google không trả
nội dung usable, DuckDuckGo challenge, Bing nhiều kết quả lạc đề. Không coi các kết quả này là
search coverage. OpenAlex là nguồn discovery/abstract thứ cấp; phải đọc full text hoặc kiểm tra
publisher/author copy để nâng mức bằng chứng. Metadata ngày Machination mâu thuẫn (13/10 ở
OpenAlex, 14/11 ở Crossref); chỉ dùng năm 2026 và giữ xung đột, không kết luận priority theo ngày.

| Công trình | Evidence đã đọc | Overlap cụ thể | Điều chưa xác minh |
|---|---|---|---|
| **Automated, Cross-Layer Root Cause Analysis of 5G Video-Conferencing Quality Degradation** (2025), DOI 10.1145/3730567.3764434, [author preprint](https://arxiv.org/abs/2505.14540) | Full PDF: abstract, §§1–5, measurement setup và causal-chain method | Domino dùng cross-layer measurements và causal graph để trace QoE impairments; 24 chains theo tác giả. Direct overlap với “WebRTC RCA + evidence” | Không chạy code/dataset; không tự nhận số liệu tác giả là số đo của project; paper preprint không đồng nhất bản ACM cuối |
| **Transport-Aware QoE Modeling for WebRTC: Predicting Playback Freezes with Machine Learning** (2026), [DOI](https://doi.org/10.1007/s10922-026-10076-z) | Crossref abstract + metadata, OpenAlex abstract; publisher PDF/HTML 429 | Client stats, RF/MLP, freeze labels, transport-dependent predictors; overlap telemetry baseline và robustness | Chưa đọc methods/splits/full data; không suy ra paper có lỗi transport hoặc leakage từ abstract |
| **WebRTC-QoE: A dataset of QoE assessment of subjective scores, network impairments, and facial & speech features** (2024), [DOI](https://doi.org/10.1016/j.comnet.2024.110356) | Bibliographic metadata; author repository PDF 403 | Multisource WebRTC QoE/dataset topic overlap; title alone không chứng minh cùng oracle/RQ | Chưa có full text, file dữ liệu, license hoặc xác nhận causal labels; không coi là benchmark phù hợp sẵn |
| **Advancing WebRTC QoE Assessment with Machine Learning in Real-World Wi-Fi Scenarios** (2024), [DOI](https://doi.org/10.1109/MeditCom61057.2024.10621275) | Abstract qua OpenAlex + Crossref bibliographic record | Link-layer metrics → perceived QoE, ML/SHAP; “telemetry ML + explanations” đã có prior art | Chưa đọc split/label procedure/code/license |
| **Machination: An Application-Agnostic Framework for Black-Box WebRTC Testing** (2026), [DOI](https://doi.org/10.1145/3847192.3847355) | Abstract OpenAlex + Crossref metadata; ACM PDF 403 | Generic WebRTC test framework không mới tự thân; abstract tập trung security/privacy | Full-text fault model, portability và artifact chưa đọc. ArXiv search trả bài không đúng: loại, không trích như nguồn |
| **Estimating QoE from Encrypted Video Conferencing Traffic** (2025), [full text](https://www.mdpi.com/1424-8220/25/4/1009), DOI 10.3390/s25041009 | Full PDF: abstract, setup/features, models và evaluation sections | Zoom traffic features + classic ML/DNN; targets FPS/resolution/NIQE; overlap objective QoE prediction | Không phải cùng root-cause task; không có causal localization ground truth được project kiểm chứng |
| **QoE Metrics for Interactivity in Video Conferencing Applications: Definition and Evaluation Methodology** (2024), DOI 10.1145/3625468.3647622 | OpenAlex abstract; ACM full text 403 | Objective interactivity metrics và scalable evaluation; engineering proxy không tự là novelty | Chưa đọc full methods; không tái dùng metric như đã validated cho pilot của project |

## Quyết định về claim

- **Không dùng:** first WebRTC RCA; first multimodal RTC diagnosis; novelty của concat/late fusion;
  freeze prediction from getStats; “causal root cause” từ class tiêm lỗi; “benchmark có sẵn” khi
  chưa inspect nhãn/license. Cross-layer evidence đã có direct prior work mạnh.
- **Ứng viên RQ cần kiểm tra tiếp:** điều kiện nào các nguyên nhân tạo triệu chứng tương đương
  không thể phân biệt từ telemetry; oracle đo độc lập thay đổi đánh giá đến đâu; chẩn đoán từ chối
  khi thiếu chứng cứ có transfer được giữa browser/configuration không. Đây là đề xuất, không
  phải novelty đã chứng minh. Cần so sánh methods/results toàn văn trực tiếp trước topic lock.
- **Baseline implication:** Domino phải được xem xét ở cấp task/evidence, nhưng cần trace 5G và
  graph phù hợp; không gắn nhãn baseline đã chạy. RF/MLP, rules, telemetry-only là bắt buộc hữu ích.
- **GO:** phép thử oracle và portability có thể tái sử dụng khi pivot. **NO-GO:** tăng độ phức tạp
  model hoặc freeze claim/title trước khi full-text và independent-oracle gates được đáp ứng.

## Next tests cho novelty gate (hạn nội bộ 22/11/2026)

1. Lấy author/publisher full text của transport-aware, dataset, Wi-Fi và Machination theo access
   hợp lệ; đọc task/labels/splits/evaluation/artifact, không suy từ abstract.
2. Theo backward/forward citations của Domino và tìm software testing/diagnostic identifiability.
3. Kiểm tra label provenance/license của dataset, chạy baseline phù hợp trên sample thật.
4. Chốt một RQ khác biệt bằng matrix claim→evidence; nếu không đủ, pivot RQ/topic theo contract.

Việc chuyển sang kiểm tra kỹ thuật oracle dưới đây là công việc feasibility được phép, không phải
khẳng định gate novelty đã đạt. Bốn bước giữ thứ tự thực hiện và trạng thái riêng.
