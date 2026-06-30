# Plan viết báo cáo: Giải pháp dùng WiFi (thay 4G) khi thu thập dataset

> **Giao cho agent viết luận văn** (skill `write_chapter` / `latex_formatting`). Mục tiêu: viết một mục trình bày *giải pháp đảm bảo toàn vẹn dữ liệu khi thu dataset bằng cách chọn WiFi thay vì 4G*, theo đúng văn phong + cấu trúc luận văn.
> **Đọc trước:** `architecture/report.md` (cấu trúc chương, build, quy ước §7); DECISIONS **D-025** (toàn vẹn data — detect-and-discard) & **D-026** (điểm yếu A7680C + auto-detect); session report `session_report_2026-06-23_sisfall_data_collection.md` (quy trình thu verification dataset).
> **Phân vai (report.md §6):** đây là nội dung **Firmware/giải pháp đường truyền** → thuộc agent chính, KHÔNG đụng file model TinyML (`4_Ket_qua_thuc_nghiem.tex`).

## 1. Vị trí đặt (đã chọn — theo cấu trúc thực của báo cáo)

**CHÍNH — Chương 3** (`Chuong/3_Phuong_phap_de_xuat.tex`): thêm **1 `\section` mới** theo đúng mẫu 3 mục con **Bài toán → Giải pháp → Kết quả** mà các section khác trong Chương 3 đang dùng (vd "Phương Pháp Lấy Mẫu IMU... PCNT", "Đếm Bước Chân Gating..."). Tên đề xuất:
`\section{Giải Pháp Đảm Bảo Toàn Vẹn Dữ Liệu Thu Thập Qua Lựa Chọn Đường Truyền}` + `\label{sec:data_transport}`.
- Lý do: Chương 3 = "Phương pháp & giải pháp đề xuất", đã có sẵn khuôn Bài toán/Giải pháp/Kết quả cho các đóng góp firmware-tín hiệu tương tự → đây là nhà tự nhiên nhất, có "sức nặng giải pháp".

**PHỤ — chỉ trỏ tới, KHÔNG kể lại (chống trùng, report.md §6):**
- `Chuong/4_2_Thiet_ke.tex` mục **"Thiết kế giao thức truyền thông"** (dòng ~73): thêm **1 `\item`** mô tả ngắn *đường truyền kép (WiFi dev/thu thập + 4G production) và tự nhận diện module* → kèm `(xem Mục~\ref{sec:data_transport})`.
- `Chuong/5_Trien_khai_thuc_nghiem.tex` mục TinyML/dataset (§ quanh dòng 32-33, chỗ nói SisFall + thu dữ liệu thật): **1 câu** "tập dữ liệu xác minh thu trên thiết bị thật qua WiFi để bảo toàn tính liên tục (xem Mục~\ref{sec:data_transport})".

## 2. Nội dung 3 mục con (luận điểm + nguồn)

### 2.1 \subsection{Bài toán}
- Huấn luyện/kiểm thử mô hình HAR & phát hiện ngã cần **thu raw IMU 100Hz liên tục** từ thiết bị thật (chế độ \texttt{STATE\_STREAMING}). Dữ liệu phải **liên tục đúng tính nhân quả** — mất gói giữa luồng tạo **đứt quãng thời gian**, làm hỏng cửa sổ trượt và nhãn → mô hình học sai ở mối nối.
- Đường 4G qua module A7680C (PPPoS) **không phù hợp streaming tốc độ cao** vì hạn chế phần cứng (D-026): (i) UART 115200 baud **không có flow control RTS/CTS** → tràn bộ đệm khi burst → hỏng khung PPP/HDLC → mất byte/gói; (ii) đường vòng \texttt{ESP32→UART→PPP→modem→trạm} làm độ trễ dao động mạnh; (iii) băng thông/độ ổn định thấp hơn nhiều so với nhu cầu luồng liên tục.
- Nêu hệ quả: nếu cứ thu qua 4G, dataset rụng mẫu lả tả → vô dụng cho huấn luyện.

### 2.2 \subsection{Giải pháp}
- **Tách đôi đường truyền theo ngữ cảnh:** dùng **WiFi cho pha thu thập dữ liệu** (TCP/IP qua MAC nội bộ, kiểm soát luồng chặt ở tầng vật lý, băng thông dư thừa, độ trễ thấp) — phù hợp luồng 100Hz liên tục; giữ **4G cho vận hành thực địa** (chỉ telemetry nhẹ + cảnh báo ngã, tải thấp khớp PPPoS).
- **Tự động nhận diện đường truyền (runtime)** để một firmware chạy cả hai ngữ cảnh, không cần biên dịch lại: khi khởi động, firmware **lắng nghe hoạt động trên bus UART** nối module (\texttt{UART\_BREAK}/\texttt{UART\_DATA}); có module → đi 4G, bus im → tự chuyển WiFi (D-026). Nêu nguyên tắc "phát hiện bằng hoạt động sớm của bus, không bằng phản hồi AT muộn".
- **(Bổ trợ) tự kiểm chứng tính liên tục:** phía thu (FE/BE) kiểm tra timestamp/đếm gói (`ts`, `cnt`) để phát hiện và loại bỏ trial có lỗ thủng, đảm bảo dataset xuất ra liên tục bất kể đường truyền (D-025). Trình bày ngắn — chi tiết FE thuộc backend/web.
- Có thể chèn **sơ đồ khối** đường truyền kép + nhánh auto-detect (TikZ vẽ trực tiếp được, report.md §4).

### 2.3 \subsection{Kết quả}
- Thu được **tập dữ liệu xác minh (verification dataset)** định dạng chuẩn SisFall, liên tục, không mất mẫu, phục vụ đánh giá mô hình \texttt{v30\_optimize} (liên kết tới mục dataset Chương 5).
- Auto-detect hoạt động: ngữ cảnh không gắn module → tự vào WiFi nhanh (**dẫn số đo thật từ log: ~11 giây**, so với ~40 giây của cơ chế dò cũ — CHỈ dùng số đã đo, xem §4).
- Nêu **định hướng phát triển:** bổ sung hardware flow control (RTS/CTS) để 4G có thể kham streaming trong tương lai (đồng nhất với mục "định hướng" của các section khác Chương 3).

## 3. Hình / Bảng đề xuất (tùy chọn, theo report.md §7.3–7.4)
- **Bảng so sánh WiFi vs 4G(PPPoS) cho luồng streaming**: các tiêu chí flow control, độ trễ điển hình, băng thông, độ tin cậy gói — bảng tối giản, `\hline` ngang, caption TRÊN, có trích dẫn + bình luận trong text. **Không bịa số**: chỉ điền số có nguồn (đo/log) hoặc để định tính (cao/thấp) nếu chưa đo.
- **Sơ đồ khối đường truyền kép + auto-detect** (TikZ): nguồn → nhánh sniff bus → 4G / WiFi. Đối chiếu `plans/report_missing_figures_plan.md` xem đã có slot chưa; nếu vẽ mới thì thêm vào danh sách đó.
- Mọi hình/bảng phải được `\ref` + giải thích trong thân bài.

## 4. Quy ước & ràng buộc (report.md §7)
- Tiếng Việt học thuật; **mỗi đoạn một ý**; câu ngắn, không từ cảm xúc ("tuyệt vời", "cực mạnh"...).
- `\texttt{}` cho định danh code (`STATE\_STREAMING`, `svc\_network`, `AT+...`, `UART\_BREAK`).
- **KHÔNG bịa số.** Số được phép dùng: **~11s / ~40s** (đo từ log boot thực), tần số 100Hz, baud 115200 — đều có nguồn. Các con số độ trễ 4G nếu chưa tự đo thì **để định tính** ("dao động lớn") hoặc ghi rõ là ước lượng tham khảo, KHÔNG ghi như số đo của hệ thống.
- Liệt kê inline (i)(ii)(iii) khi ngắn; đơn vị SI; thuật ngữ viết tắt lần đầu mở ngoặc tiếng Anh.
- **Chống trùng lặp:** toàn bộ lập luận "tại sao 4G yếu / vì sao WiFi" sống ở Mục~\ref{sec:data_transport}; 4_2 và 5.x chỉ 1 câu + `\ref`.

## 5. Glossary (nếu chưa có, thêm vào `Tu_viet_tat.tex` — report.md §3)
Kiểm tra & bổ sung nếu thiếu: **PPPoS**, **HDLC**, **RTS/CTS** (flow control), **ADL** (đã có?), **HAR**. Định nghĩa `\newglossaryentry{...}{type=\acronymtype, name={...}, description={Nghĩa VN (English)}}`. Thân bài KHÔNG cần `\gls{}`.

## 6. Verify (bắt buộc trước khi coi là xong)
1. `pdflatex -interaction=nonstopmode -halt-on-error 20225198_VuManhHung.tex` ở `Do_an_tot_nghiep_Vu_Manh_Hung/` → `EXIT=0` (qua mọi TikZ/figure). Chạy **2 lượt** nếu thêm glossary/ref.
2. Nếu có hình TikZ: rasterize trang chứa section mới (rungs → PNG) để mắt thường xác nhận sơ đồ hiện đúng, rồi **xóa ảnh debug**.
3. Kiểm `\ref{sec:data_transport}` ở 4_2 & 5.x resolve (không "??").
4. Nếu sửa preamble (thêm package) → nhớ đẩy luôn `20225198_VuManhHung.tex` lên Overleaf (report.md §5).

## 7. Nguồn tham chiếu khi viết
- DECISIONS: **D-025** (toàn vẹn data, detect-and-discard bằng timestamp), **D-026** (điểm yếu A7680C + auto-detect bus UART).
- `session_report_2026-06-23_sisfall_data_collection.md` (quy trình thu verification dataset, định dạng SisFall, luồng start_stream → buffer → .txt).
- Code đối chiếu (nếu cần trích cơ chế): `firmware/components/svc_network/svc_network.c` (sniff bus), `svc_imu/imu_service.c` (STREAMING chỉ Kalman+batch).
- Số đo thật: log boot (no-module → WiFi ~11s; cơ chế cũ ~40s).

---

## 8. CHỐT FRAMING & TRẠNG THÁI FILE (đọc trước khi implement)

**Framing đã chốt (deadline — viết theo đúng đây):**
- **SisFall = nguồn HUẤN LUYỆN.** **Dữ liệu cá nhân (thu trên thiết bị thật, qua WiFi) = KIỂM THỬ/ĐÁNH GIÁ.**
- Việc **thu đầy đủ dataset cá nhân là BƯỚC TRIỂN KHAI TIẾP THEO** (chưa hoàn tất) → mục Kết quả viết theo hướng "đã dựng sẵn quy trình/pipeline thu qua WiFi", KHÔNG khẳng định đã thu xong nhiều đối tượng.
- Cơ chế auto-detect đường truyền **đã hiện thực & đo thật** (~11s) → phần này khẳng định chắc.

**Trạng thái file hiện tại (đừng làm trùng):**
- `Tu_viet_tat.tex`: **đã thêm sẵn** entry `hdlc` (HDLC) — KHÔNG thêm lại. PPPoS/LTE/UART/MQTT/TLS/RSSI đã có sẵn.
- `Chuong/3_Phuong_phap_de_xuat.tex`, `Chuong/4_2_Thiet_ke.tex`, `Chuong/5_Trien_khai_thuc_nghiem.tex`: **CHƯA chèn gì** (bản gốc) → cần chèn theo §8.1–8.3 dưới.

### 8.1 — Chèn vào `Chuong/3_Phuong_phap_de_xuat.tex`
**Anchor:** ngay TRƯỚC dòng cuối `\end{document}` (sau section "Đếm Bước Chân... Gating"). Chèn nguyên khối:

```latex
% -----------------------------------------------------------------------

\section{Giải Pháp Đảm Bảo Toàn Vẹn Dữ Liệu Thu Thập Qua Lựa Chọn Đường Truyền}
\label{sec:data_transport}

\subsection{Bài toán}

Chiến lược dữ liệu của đồ án phân tách rõ hai nguồn: bộ dữ liệu công khai SisFall dùng để \textit{huấn luyện} mô hình, còn một bộ \textbf{dữ liệu cá nhân} thu trực tiếp từ thiết bị đeo thật dùng để \textit{kiểm thử và đánh giá}. Việc đánh giá trên dữ liệu thu bằng chính phần cứng và quy trình tiền xử lý của hệ thống là cần thiết, bởi SisFall được thu trong điều kiện cảm biến và bố trí khác, không phản ánh đầy đủ đặc trưng tín hiệu mà mô hình gặp khi vận hành thực tế.

Để xây dựng bộ dữ liệu cá nhân, thiết bị phải truyền luồng dữ liệu IMU thô tần số 100~Hz một cách liên tục về máy chủ (chế độ \texttt{STATE\_STREAMING}). Yêu cầu cốt lõi của dữ liệu huấn luyện và đánh giá là tính \textbf{liên tục theo thời gian}: mỗi cửa sổ trượt $200 \times 6$ phải gồm các mẫu kề nhau đúng theo trục thời gian. Khi một gói dữ liệu (batch) bị mất giữa luồng, chuỗi mẫu bị đứt quãng --- hai đoạn tín hiệu không liền mạch bị ghép thành một cửa sổ, tạo ra bản ghi sai lệch về mặt vật lý và làm nhiễu nhãn của bộ dữ liệu.

Tuyến truyền 4G LTE qua module A7680C (giao thức PPPoS) không đáp ứng được yêu cầu luồng liên tục tốc độ cao này do các hạn chế phần cứng cố hữu. Thứ nhất, đường UART nối giữa vi điều khiển và module hoạt động ở tốc độ 115200~baud nhưng \textbf{không có điều khiển luồng phần cứng} (hai chân RTS/CTS không được nối). Khi lưu lượng tăng đột biến, bộ đệm UART bị tràn, gây mất byte và làm hỏng khung dữ liệu của giao thức PPP/HDLC. Thứ hai, đường dữ liệu đi vòng qua nhiều tầng (\texttt{ESP32 $\rightarrow$ UART $\rightarrow$ PPP $\rightarrow$ modem $\rightarrow$ trạm phát}) khiến độ trễ dao động lớn và băng thông thực tế thấp. Hệ quả là dữ liệu thu qua 4G rụng mẫu rải rác và mất giá trị cho huấn luyện hay đánh giá.

\subsection{Giải pháp}

Đồ án giải quyết bằng cách \textbf{tách đôi đường truyền theo ngữ cảnh sử dụng}, thay vì ép một tuyến duy nhất phục vụ hai nhu cầu trái ngược. Pha thu thập dữ liệu sử dụng WiFi: vi điều khiển ESP32-S3 giao tiếp trực tiếp qua ngăn xếp TCP/IP gắn liền địa chỉ MAC nội bộ, kiểm soát luồng chặt ở tầng vật lý nên không mất byte, với băng thông và độ trễ dư thừa so với mức 100~Hz của luồng IMU. Pha vận hành thực địa giữ nguyên 4G LTE, nơi tải truyền thông rất nhẹ --- gói viễn trắc định kỳ và cảnh báo té ngã tức thời --- hoàn toàn phù hợp với năng lực của PPPoS. Bảng~\ref{tab:wifi_vs_4g} đối chiếu hai tuyến theo các tiêu chí quyết định cho bài toán streaming.

\begin{table}[H]
\centering
\caption{Đối chiếu hai tuyến truyền cho bài toán thu luồng dữ liệu IMU 100~Hz liên tục.}
\label{tab:wifi_vs_4g}
\begin{tabular}{lll}
\hline
\textbf{Tiêu chí} & \textbf{WiFi (STA)} & \textbf{4G LTE (PPPoS, A7680C)} \\
\hline
Điều khiển luồng phần cứng & Có (tầng MAC nội bộ) & Không (thiếu RTS/CTS) \\
Mất byte/khung khi tải cao & Không & Có (tràn UART, hỏng khung PPP) \\
Băng thông khả dụng & Cao, dư thừa & Thấp \\
Độ trễ & Thấp, ổn định & Dao động lớn \\
Phù hợp streaming 100~Hz liên tục & Phù hợp & Không phù hợp \\
\hline
\end{tabular}
\end{table}

Để một bản firmware duy nhất phục vụ cả hai ngữ cảnh mà không cần biên dịch lại, hệ thống \textbf{tự động nhận diện đường truyền} ngay khi khởi động. Cơ chế nhận diện dựa trên \textit{hoạt động sớm của bus UART}, thay vì chờ phản hồi lệnh AT --- vốn đến muộn do module 4G cần hàng chục giây để khởi động xong. Firmware lắng nghe các sự kiện báo hiệu trên bus (\texttt{UART\_BREAK}, \texttt{UART\_DATA}): nếu phát hiện hoạt động bền vững, hệ thống xác nhận có module và đi tuyến PPPoS; nếu bus im lặng tuyệt đối trong cửa sổ quan sát, hệ thống kết luận không có module và tự chuyển sang khởi tạo WiFi. Hình~\ref{fig:transport_autodetect} mô tả luồng quyết định này.

\begin{figure}[H]
\centering
\begin{tikzpicture}[
    node distance = 0.7cm,
    every node/.style = {font=\small},
    proc/.style = {draw, rounded corners=5pt, text width=5.4cm,
                   minimum height=0.85cm, align=center, fill=white},
    dec/.style  = {draw, diamond, aspect=2.2, inner sep=1pt,
                   text width=2.6cm, align=center, fill=blue!6},
    res/.style  = {draw, rounded corners=5pt, text width=3.4cm,
                   minimum height=0.9cm, align=center, fill=gray!15},
    lbl/.style  = {font=\footnotesize},
    arr/.style  = {-{Latex[length=2.2mm, width=1.8mm]}, thick},
]
\node[proc] (boot) {Khởi động dịch vụ mạng\\(\texttt{svc\_network})};
\node[proc, below=0.5cm of boot] (sniff)
    {Lắng nghe bus UART trong cửa sổ quan sát\\(\texttt{UART\_BREAK} / \texttt{UART\_DATA})};
\node[dec, below=0.75cm of sniff] (q) {Bus có hoạt động?};
\node[res, below=2.4cm of q, xshift=-3.4cm] (cell)
    {Tuyến 4G LTE (PPPoS)\\vận hành thực địa};
\node[res, below=2.4cm of q, xshift=+3.4cm] (wifi)
    {Tuyến WiFi\\thu thập dữ liệu};

\draw[arr] (boot) -- (sniff);
\draw[arr] (sniff) -- (q);
\draw[arr] (q.south west) -- node[lbl, left, pos=0.6] {Có (module 4G)} (cell.north);
\draw[arr] (q.south east) -- node[lbl, right, pos=0.6] {Không (bus im)} (wifi.north);
\end{tikzpicture}
\caption{Luồng tự nhận diện đường truyền theo hoạt động bus UART --- D-026.}
\label{fig:transport_autodetect}
\end{figure}

Bên cạnh đó, ở phía thu (máy chủ và giao diện web), hệ thống \textbf{tự kiểm chứng tính liên tục} của dữ liệu bằng cách đối sánh nhãn thời gian và số lượng mẫu đính kèm mỗi gói: nếu phát hiện khoảng trống bất thường giữa hai gói liên tiếp, phiên thu tương ứng bị đánh dấu lỗi và loại bỏ thay vì âm thầm sinh ra một tệp dữ liệu hỏng. Cơ chế này bảo đảm bộ dữ liệu xuất ra luôn liên tục, không phụ thuộc vào đường truyền.

\subsection{Kết quả và Định hướng phát triển}

Cơ chế tự nhận diện đường truyền đã được hiện thực và kiểm chứng trên phần cứng thực tế. Trong trường hợp thiết bị không gắn module 4G, firmware nhận ra bus UART im lặng và chuyển sang WiFi trong khoảng 11~giây, so với khoảng 40~giây của cơ chế dò bằng lệnh AT trước đó. Phần lớn thời gian tiết kiệm đến từ việc loại bỏ thao tác thoát chế độ dữ liệu (\texttt{+++}) vốn chờ phản hồi vô ích khi không có module.

Về chiến lược dữ liệu, đồ án sử dụng SisFall làm nguồn huấn luyện chính (trình bày tại Chương~5) và thiết lập sẵn quy trình thu bộ dữ liệu cá nhân qua WiFi để phục vụ đánh giá mô hình trong điều kiện vận hành thực. Bộ dữ liệu cá nhân được thu và gán nhãn theo đúng định dạng SisFall nhằm tái sử dụng trực tiếp quy trình tiền xử lý và đánh giá đã xây dựng. Việc thu thập đầy đủ bộ dữ liệu cá nhân trên nhiều đối tượng là bước triển khai tiếp theo của đồ án.

Về định hướng phát triển, việc bổ sung điều khiển luồng phần cứng --- nối hai chân RTS/CTS giữa vi điều khiển và module --- sẽ nâng độ tin cậy của tuyến 4G đủ để kham cả luồng streaming, từ đó hợp nhất hai tuyến truyền và cho phép thu thập dữ liệu thực địa từ xa mà không cần WiFi cục bộ.
```

### 8.2 — Chèn vào `Chuong/4_2_Thiet_ke.tex`
**Anchor:** trong mục "Thiết kế giao thức truyền thông", thêm `\item` này NGAY TRƯỚC `\end{itemize}` (sau item "Lớp Cấu hình từ xa"):

```latex
    \item \textbf{Lớp đường truyền vật lý kép (Dual-transport):} Thiết bị hỗ trợ hai tuyến truyền theo ngữ cảnh sử dụng --- WiFi cho pha thu thập dữ liệu cần luồng IMU liên tục, và 4G LTE (PPPoS) cho vận hành thực địa --- và tự động nhận diện tuyến phù hợp ngay khi khởi động. Cơ sở lý thuyết và cơ chế nhận diện được trình bày tại Mục~\ref{sec:data_transport}.
```

### 8.3 — Chèn vào `Chuong/5_Trien_khai_thuc_nghiem.tex`
**Anchor:** mục `\subsection{Huấn luyện và triển khai mô hình học máy (TinyML)}`, ngay sau câu giới thiệu SisFall ("...đảm bảo tính đa dạng và độ tin cậy cao."). Sửa phẫu thuật: thêm câu sau vào CUỐI đoạn đó (edit unique, đừng viết lại cả đoạn vì đoạn này thuộc agent model):

```latex
 Bên cạnh nguồn huấn luyện công khai này, đồ án thiết lập một bộ \textit{dữ liệu cá nhân} thu trực tiếp từ thiết bị đeo thật để \textit{kiểm thử và đánh giá} mô hình trong điều kiện vận hành thực; quá trình thu được thực hiện qua WiFi nhằm bảo toàn tính liên tục của tín hiệu (xem Mục~\ref{sec:data_transport}).
```

### 8.4 — Verify
1. `pdflatex -interaction=nonstopmode -halt-on-error 20225198_VuManhHung.tex` (thư mục `Do_an_tot_nghiep_Vu_Manh_Hung/`) → `EXIT=0`. Chạy **2 lượt** (glossary HDLC + `\ref`).
2. Rasterize trang chứa Hình~\ref{fig:transport_autodetect} (rungs → PNG) xem sơ đồ diamond hiện đúng; xóa ảnh debug.
3. Kiểm `\ref{sec:data_transport}` ở 4_2 & 5 không ra "??".
4. Nếu build Overleaf qua `ols`: đẩy 4 file đã đổi (`Tu_viet_tat.tex`, `3_...`, `4_2_...`, `5_...`); không đụng preamble nên không cần đẩy file chính trừ khi cần.
