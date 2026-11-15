# Bước 3 — oracle độc lập: measurement probes, chưa đạt WebRTC gate

**Thực thi:** `uv run --frozen python -m ease_rtc.oracle_probes --output data/local/<new-probes>`.
18 phép thử: 3 seeds × 3 nhóm × sham/intervention. Kết quả đo thật tại
[oracle_probe_results.json](oracle_probe_results.json); raw request/measurement và checksum ở
`data/local/oracle-probes-v1/`. Cả 18 kiểm tra đạt tiêu chí heuristic, không có failed/ambiguous.

| Nhóm | Can thiệp | Đo từ đường quan sát riêng | Ranh giới |
|---|---|---|---|
| Network | Relay UDP loopback bỏ 20/60 packet theo sequence với seeded schedule | Socket receiver đếm sequence nhận được, không đọc drop schedule | Chỉ loss trong probe; không phải impairment đường RTP/browser hoặc mất gói ngoài lab |
| Compute | Worker process tính liên tục thay cho sleep | psutil đọc OS process CPU time, PID và creation time | Chứng minh worker load, không chứng minh CPU saturation, encoder overload hay degradation của browser |
| Media | FFmpeg tạo file frozen thay cho moving fixture | Decoder FFmpeg riêng lấy decoded-frame hashes; checksum file | Chứng minh nội dung file đứng hình, không chứng minh camera/capture fault trong live call |

Đường đo không suy outcome từ request; request và measurement tách file. Verifier từ chối thiếu
bằng chứng, báo failed khi sham có effect hoặc khi intervention không có effect. Trường
`causal_root_cause` luôn `unestablished`. Các probe/threshold này chỉ là validation của bộ đo;
không tạo training labels cho `ease-rtc` classifier. Receiver/injector UDP chạy thread riêng
cùng process: independence ở đường đo, **không phải** độc lập về toàn bộ failure domain.

## Chưa hoàn tất

Pilot WebRTC cũ vẫn dùng observer cùng testbed, không đạt oracle causal độc lập. Container không
có effective capabilities và không tạo được user/net namespace; không chạy tc trên shared host.
Public Internet access không cấp NET_ADMIN. Không đổi camera freeze thành network fault hoặc
worker load thành encoder overload để đủ số nhóm lỗi.

Để đạt gate cần một lab cô lập: sender/receiver tách process/namespace, riêng scope qdisc;
independent packet capture/counters, CPU accounting của renderer/encoder thực và capture/decoded
frame observer ngoài code injector. Đồng bộ clock với bounded skew; measure before/during/after,
recovery, controls, benign static content, injected-no-degradation và degradation-without-injection.
Có xác minh condition vẫn không tự chứng minh causal attribution; cần matched controls và thời gian.

Mỗi evidence record phải có session/run, sensor identity, clock/alignment, requested interval riêng,
measured interval/intensity, coverage, checksums, failed/ambiguous status và limitation. Không cho
sensor/request metadata vào model features. Main-study gate cần >=3 fault families **plus** controls
trên cuộc gọi thật và report verification denominator; 18 probe trials không đáp ứng thay.

**Status: PARTIAL.** Đã có phép thử đo độc lập thực thi và tests chống successful-by-request;
chưa đủ điều kiện chốt nghiên cứu chính. Tiếp tục portability của artifact là kiểm tra kỹ thuật
hữu ích, không cấp causal labels hay tuyên bố gate này đã qua.

Lưu ý về lặp: seed chỉ thay đổi drop schedule của UDP probe. Compute và media là các lần lặp
độc lập của cùng cấu hình, không phải ba stochastic model seeds hay power analysis.

## Live-call integration update

The earlier probe-only state above is historical. A new isolated container harness now runs real
calls with separate sender/receiver browser processes and a separate OS sensor. The GitHub pilot
`data/releases/live-pilot/ci-43722157644` contains five verified Chromium calls: kernel-measured
packet loss, sender-process-tree CPU contention, source screenshot freeze, moving sham and benign
static control. Five Firefox failures remain in the same denominator. This is evidence of three
bounded measured fault families on live calls, not independently established causal attribution.
Cloud's missing qdisc kinds are recorded in live_cloud_capabilities.json; cloud live calls verify
compute/media and controls, with network measurement explicitly unavailable. Read live_protocol_v1.md
for the prospective freeze. Pixel observation shares the orchestrator failure domain; do not call
this a fully external hardware oracle or a complete main-study validity result.
