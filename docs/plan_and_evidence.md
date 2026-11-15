# Kế hoạch trong handoff và kết quả kiểm chứng khác nhau thế nào?

File Markdown ban đầu đã có kế hoạch: chọn ứng viên WebRTC để kiểm tra, dựng testbed, oracle,
controls, baseline, split và go/no-go gates. Nó đồng thời ghi rõ WebRTC **chưa được chọn cuối cùng**,
novelty **chưa audit**, và không được biến giả thuyết thành claim. Vì vậy việc đọc prior art để chốt
RQ hoặc pivot là một bước của kế hoạch, không có nghĩa là trước đó chưa có kế hoạch.

Theo yêu cầu hiện tại, project tiếp tục triển khai live-call oracle và protocol/dataset; không
thực hiện pivot đề tài trong milestone này. Novely gate vẫn được báo cáo riêng và chưa mặc định
đạt chỉ vì code chạy. Protocol feasibility có thể được cố định để thu dữ liệu đáng tin trong lúc
RQ/main-study protocol vẫn cần được kiểm chứng. Xem live_protocol_v1.md và frozen_plan_v1.json.

Bước live-call đã chuyển từ probe rời sang can thiệp trên cuộc gọi thật, với separate OS observer,
source-pixel observation, matched before/during/after và controls. Causal attribution vẫn giữ là
unestablished. Ba điều kiện đo được không phải chứng minh mọi root cause trong hệ thống thực.

Hai host/kernel đã được dùng: cloud kernel6.18 và GitHub runner kernel7.0-azure, cùng image Debian12.
Firefox ICE failure được giữ trong dữ liệu; không đổi tên cross-host thành cross-browser/cross-OS.
Final main-study protocol cần đủ scope, novelty, sample size và validation trước khi tuyên bố nộp EASE.
