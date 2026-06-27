# Federated Learning - Phát hiện mã độc

## 1. Giới thiệu đề tài

Dự án triển khai **Federated Learning** (học liên kết) bằng **Flower framework** để **phát hiện/phân loại mã độc** dựa trên ảnh byteplot của các họ malware (bộ dữ liệu kiểu Malimg). Mỗi client huấn luyện một mô hình CNN trên dữ liệu cục bộ của mình, rồi gửi cập nhật trọng số về server để tổng hợp (FedAvg) thành một mô hình chung — **không cần chia sẻ dữ liệu gốc**.

Hệ thống bao gồm:

- **Server huấn luyện trung tâm** (Flower, cổng 8080) tổng hợp mô hình bằng `FedAvg`.
- **Nhiều client độc lập**, mỗi client có dữ liệu mã độc riêng.
- **Backend API** (FastAPI, cổng 8000): điều khiển server/client qua WebSocket, stream log, lưu session và kết quả submit vào cơ sở dữ liệu.
- **Giao diện web** (HTML/CSS/JS + Chart.js): điều khiển training, theo dõi log và biểu đồ accuracy theo từng round, so sánh các session.

## 2. Cấu trúc thư mục

```
IE207/
├── backend/                # API FastAPI + server/client Flower + DB + logic train
│   ├── backend.py          # FastAPI app (WebSocket, REST API)
│   ├── start_backend.py    # Script khởi động backend (uvicorn)
│   ├── server.py           # Flower server (FedAvg)
│   ├── client.py           # Flower client
│   ├── task.py             # Mô hình CNN + load dữ liệu + train/test
│   ├── database.py         # Kết nối MySQL, tự fallback SQLite
│   ├── models.py           # Bảng DB (SQLAlchemy)
│   ├── crud.py             # Truy vấn DB
│   ├── schemas.py          # Pydantic schema
│   └── trained_models/     # Mô hình cuối được lưu sau khi train xong (tự tạo)
├── frontend/               # Giao diện web
│   ├── index.html
│   ├── index.css
│   └── index.js
├── client1/ ... client4/   # Dữ liệu ảnh mã độc cho từng client (mỗi họ malware = 1 thư mục con)
├── requirements.txt
├── run_demo.sh             # Script chạy nhanh toàn bộ demo (Linux/macOS)
└── README.md
```

## 3. Yêu cầu hệ thống

- **Python 3.9+** (đã kiểm thử trên Python 3.12)
- **pip** và **venv** (xem mục 4 nếu máy chưa có)
- Trình duyệt web hiện đại (Chrome, Edge, Firefox)
- (Tùy chọn) MySQL — nếu không có, hệ thống tự dùng SQLite

## 4. Cài đặt môi trường Python

> Trên một số bản Debian/Ubuntu, Python hệ thống **không có sẵn `pip` và `venv`**. Nếu lệnh `python3 -m venv` báo lỗi `ensurepip is not available` hoặc `No module named pip`, hãy làm theo mục 4.0 trước.

### 4.0. (Chỉ khi cần) Cài pip và venv

Cách 1 — dùng apt (cần quyền sudo):

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip
```

Cách 2 — không có quyền sudo (bootstrap vào thư mục người dùng):

```bash
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python3 /tmp/get-pip.py --user --break-system-packages
python3 -m pip install --user --break-system-packages virtualenv
```

### 4.1. Tạo môi trường ảo

**Linux / macOS:**

```bash
cd /home/doanpq/ie207ie/IE207
python3 -m venv .venv        # hoặc: python3 -m virtualenv .venv (nếu dùng cách 2 ở trên)
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
cd <đường_dẫn>\IE207
python -m venv .venv
.venv\Scripts\activate
```

### 4.2. Cài đặt các package

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> **Lưu ý về PyTorch:** mặc định pip có thể tải bản GPU/CUDA rất nặng. Nếu máy **không có GPU NVIDIA** (hoặc muốn nhẹ và nhanh), hãy cài bản **CPU**:
>
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
> pip install fastapi "uvicorn[standard]" sqlalchemy pymysql flwr requests pillow websockets
> ```

## 5. Các package chính

| Package | Vai trò |
|---|---|
| `flwr` | Federated Learning framework |
| `torch`, `torchvision` | Mô hình CNN, xử lý ảnh |
| `fastapi`, `uvicorn` | Backend API + WebSocket |
| `sqlalchemy`, `pymysql` | ORM + driver MySQL (fallback SQLite) |
| `requests` | Client/server gọi API backend |
| `pillow` | Đọc ảnh |
| `websockets` | Hỗ trợ WebSocket cho uvicorn |

## 6. Chạy chương trình

### Cách A — Chạy nhanh bằng script (Linux/macOS)

Chạy toàn bộ demo (backend + server + 2 client) chỉ với 1 lệnh:

```bash
cd /home/doanpq/ie207ie/IE207
source .venv/bin/activate
ROUNDS=2 SEED=42 ./run_demo.sh
```

Script tự bật backend → Flower server → 2 client, in log và lưu mô hình vào `backend/trained_models/`. Đổi `ROUNDS=10` để train nhiều vòng hơn.

### Cách B — Chạy thủ công qua giao diện web

**Bước 1 — Khởi động backend** (terminal 1):

```bash
cd /home/doanpq/ie207ie/IE207/backend
source ../.venv/bin/activate
python start_backend.py
```

Backend chạy tại `http://127.0.0.1:8000`. Giữ terminal này mở.

**Bước 2 — Mở giao diện web.** Khuyến nghị chạy một web server tĩnh (terminal 2) để tránh trình duyệt chặn file local:

```bash
cd /home/doanpq/ie207ie/IE207/frontend
python3 -m http.server 5500
```

Rồi mở trình duyệt vào `http://localhost:5500`. (Có thể mở thẳng `frontend/index.html` nhưng nên dùng cách trên.)

**Bước 3 — Điều khiển training trên web** (xem mục 7).

## 7. Hướng dẫn sử dụng giao diện

### Điều khiển huấn luyện

1. Nhập tham số: **Num Round**, **Local Epochs**, **Learning rate**, **Random seed**.
2. Nhấn **Start Server** để khởi động Flower server.
3. Nhấn **Start Client 1/2/3/4**. **Bắt buộc chạy ít nhất 2 client** vì server cấu hình `min_fit_clients = 2`; nếu chỉ có 1 client, training sẽ **không bắt đầu** mà chờ đủ client.
4. Nhấn **View Client X** để xem biểu đồ accuracy của client đó theo từng round.

### Theo dõi log

- **Server Log**: log từ Flower server.
- **Client Log**: log riêng của từng client.

### So sánh session

- Nhập tham số ở **Session A** hoặc **Session B** → nhấn **Find** để tìm session phù hợp.
- Chọn session trong danh sách rồi nhấn **Active** để xem biểu đồ so sánh.

### Đếm submit

- Nhấn **Count** ở từng card client để xem tổng số submit và thời gian submit gần nhất.

## 8. Cấu hình nâng cao (biến môi trường, tùy chọn)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `HOST` / `PORT` | `127.0.0.1` / `8000` | Địa chỉ backend (đặt trước `start_backend.py`) |
| `DB_BACKEND` | `mysql` | Mặc định dùng MySQL. Đặt `sqlite` để chạy tạm bằng SQLite |
| `DB_USER` | `root` | User MySQL |
| `DB_PASS` | *(rỗng)* | Mật khẩu MySQL |
| `DB_HOST` / `DB_PORT` | `127.0.0.1` / `3306` | Địa chỉ MySQL server |
| `DB_NAME` | `IE207` | Tên database (tự tạo nếu chưa có) |
| `MODEL_DIR` | `backend/trained_models` | Thư mục lưu mô hình cuối |

Ví dụ chạy backend trỏ tới MySQL với user/mật khẩu riêng:

```bash
DB_USER=ie207 DB_PASS=ie207pass python start_backend.py
```

Ví dụ chạy tạm bằng SQLite (không cần MySQL):

```bash
DB_BACKEND=sqlite python start_backend.py
```

## 9. Lưu ý quan trọng

- Hệ thống **mặc định dùng MySQL**. Database (`IE207`) sẽ được **tự động tạo nếu chưa tồn tại**; bạn chỉ cần đảm bảo MySQL server đang chạy và thông tin đăng nhập đúng (xem mục 8). Nếu không kết nối được, backend sẽ **báo lỗi rõ ràng và dừng** (không tự chuyển sang SQLite). Muốn chạy tạm không cần MySQL thì đặt `DB_BACKEND=sqlite`.
- Đảm bảo các thư mục dữ liệu `client1/ ... client4/` nằm đúng vị trí (ngang cấp với `backend/`), vì `task.py` đọc theo đường dẫn tương đối `../client1`...
- Các cảnh báo `DEPRECATED FEATURE` của Flower (`start_server`, `start_numpy_client`) là **bình thường** với phiên bản mới, chương trình vẫn chạy đúng.
- Mô hình cuối được lưu tại `backend/trained_models/final_model_*.pth` sau round cuối.

## 10. Khắc phục sự cố thường gặp

### `ModuleNotFoundError`

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### `ensurepip is not available` / `No module named pip`

Xem mục **4.0** để cài `python3-venv` / `pip`.

### Chữ tiếng Việt trên web bị lỗi (ví dụ `Quáº£n lÃ½`)

Lỗi encoding do thiếu khai báo charset. File `frontend/index.html` đã có `<meta charset="UTF-8">`; chỉ cần tải lại trang (`Ctrl + Shift + R`).

### Port 8000 hoặc 8080 đang được dùng

```bash
# Linux/macOS
lsof -t -i:8000 | xargs -r kill
lsof -t -i:8080 | xargs -r kill
```

### Training không bắt đầu sau khi Start Server

Kiểm tra đã **Start đủ ít nhất 2 client** chưa (yêu cầu `min_fit_clients = 2`).

### Không thấy giao diện cập nhật

- Kiểm tra backend đã chạy chưa (`http://127.0.0.1:8000`).
- Mở/refresh frontend **sau khi** backend đã sẵn sàng.

## 11. Kết luận

Đây là dự án demo Federated Learning ứng dụng vào **phát hiện mã độc**: nhiều client cùng huấn luyện một mô hình chung mà không chia sẻ dữ liệu gốc. Hệ thống có thể mở rộng cho các bài toán phân loại/nhận diện mẫu và học máy phân tán khác.
