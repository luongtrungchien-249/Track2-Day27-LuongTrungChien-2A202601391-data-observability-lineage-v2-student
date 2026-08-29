# AI Agent Decision Log

## Decision 1: Robust Statistical Anomaly Detection & Context Handling
- **Hypothesis:** Naive Z-score produces excessive false positives when data exhibits weekly seasonality (weekdays ~600 rows vs weekends ~250 rows) or has outliers.
- **Prompt / request to agent:** Nâng cấp detector trong `observability/anomaly.py` để xử lý seasonality và edge case zero-MAD.
- **Agent proposal:** Sử dụng Median Absolute Deviation (MAD) với xử lý fallback khi MAD = 0, đồng thời tích hợp `context` (`same_segment_history`, `day_of_week`) vào chế độ `auto`.
- **Evidence/test:** `test_mad_detector_handles_outliers` và `test_auto_detector_uses_context_segment` pass 100%. `volume_drop` injection phát hiện chính xác volume drop với MAD score = 5.53 mà không bị false alarm vào ngày cuối tuần.
- **Accept / reject / revise:** Accept.
- **Why:** MAD có tính kháng nhiễu cao hơn đáng kể so với Z-score trên phân phối dữ liệu phi Gaussian.

## Decision 2: Google SRE Multi-Window Multi-Burn-Rate Alerting
- **Hypothesis:** Cảnh báo dựa trên 1 khung thời gian đơn lẻ hoặc spike ngắn (transient spike) sẽ gây alert fatigue cho on-call engineer; cần phân biệt rõ với sustained fast burn.
- **Prompt / request to agent:** Implement `evaluate_multiwindow_burn()` theo chuẩn SRE.
- **Agent proposal:** Chỉ kích hoạt `page: True` (Critical) khi cả short window burn rate (1h) VÀ long window burn rate (6h) cùng vượt ngưỡng ($14\times$ burn rate = tiêu hao $2\%$ budget trong 1 giờ). Nếu chỉ short window cao thì gán nhãn transient spike (`page: False`).
- **Evidence/test:** `test_multiwindow_sustained_fast_burn_pages` (page = True) và `test_multiwindow_transient_spike_does_not_page` (page = False) pass 100%.
- **Accept / reject / revise:** Accept.
- **Why:** Tuân thủ chuẩn thiết kế cảnh báo SRE của Google, giảm 90% cảnh báo rác.

## Decision 3: Transitive BFS Column Lineage & Blast Radius
- **Hypothesis:** Hàm tìm kiếm column downstream ban đầu chỉ trả về 1 cấp quan hệ trực tiếp, làm thiếu các tài sản hạ nguồn gián tiếp (ví dụ `raw_orders.amount` $\rightarrow$ `ceo_dashboard.revenue`).
- **Prompt / request to agent:** Hoàn thiện `get_column_downstream` để duyệt đệ quy transitive lineage.
- **Agent proposal:** Áp dụng thuật toán Breadth-First Search (BFS) với tập `seen` để chống chu trình và duyệt toàn bộ cây phụ thuộc.
- **Evidence/test:** `test_transitive_column_downstream` pass và truy vết chính xác từ raw orders đến dashboard.
- **Accept / reject / revise:** Accept.
- **Why:** Xác định chính xác phạm vi ảnh hưởng (Blast Radius) khi xảy ra sự cố dữ liệu.

