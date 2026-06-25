# Federated Learning Demo

## 1. Giới thiệu đề tài

Dự án này triển khai một mô hình demo về Federated Learning (học tập phân tán) với các client riêng biệt, trong đó mỗi client huấn luyện một mô hình trên dữ liệu cục bộ của mình rồi gửi các cập nhật về server để tổng hợp thành một mô hình chung.

Mục tiêu chính của dự án là minh họa cách hoạt động của Federated Learning trong môi trường phân tán, bao gồm:

- Khởi động một server huấn luyện trung tâm
- Chạy nhiều client độc lập
- Theo dõi tiến trình huấn luyện qua log và biểu đồ
- Lưu trữ session và kết quả submit của từng client
- So sánh các session training trên giao diện web

> Dự án hiện tại là một demo giáo dục/ứng dụng minh họa, không phải một hệ thống phát hiện mã độc chuyên nghiệp. Nếu dữ liệu đầu vào được thay bằng các mẫu liên quan đến malware/threat, hệ thống này có thể được mở rộng cho mục đích phân loại và phát hiện mẫu độc hại.

## 2. Cấu trúc thư mục

- backend/: chứa API FastAPI, server Flower, client Flower, cơ sở dữ liệu và logic huấn luyện
- frontend/: giao diện web để điều khiển và theo dõi quá trình training
- client1/, client2/, client3/, client4/: dữ liệu hình ảnh dùng cho từng client

## 3. Yêu cầu hệ thống

- Python 3.9 trở lên
- pip
- Git (tùy chọn)
- Trình duyệt web hiện đại (Chrome, Edge, Firefox)

## 4. Cài đặt môi trường Python

### Bước 1: Tạo môi trường ảo

Trên Windows:

```bash
cd D:\python\IE207\do_an\Federated_Learning
python -m venv .venv
.venv\Scripts\activate
```

### Bước 2: Cài đặt các package cần thiết

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Các package và thư viện cần thiết

Dự án sử dụng các thư viện sau:

- fastapi
- uvicorn
- sqlalchemy
- pymysql
- flwr
- torch
- torchvision
- requests
- pillow

Nếu bạn gặp lỗi khi cài torch/torchvision, hãy dùng bản phù hợp với hệ thống của bạn từ trang chính thức của PyTorch.

## 6. Chạy chương trình

### Bước 1: Khởi động backend

```bash
cd backend
python start_backend.py
```

Backend sẽ chạy ở địa chỉ:

- http://127.0.0.1:8000

### Bước 2: Mở frontend

Bạn có thể mở file:

```text
frontend/index.html
```

Nếu trình duyệt chặn việc load file local, hãy dùng một công cụ như VS Code Live Server hoặc một máy chủ tĩnh đơn giản.

## 7. Hướng dẫn sử dụng giao diện

### Điều khiển huấn luyện

- Nhấn Start Server để khởi động server
- Chọn số vòng huấn luyện, số epoch, learning rate và seed
- Nhấn Start Client 1/2/3/4 để chạy từng client
- Nhấn View Client X để xem biểu đồ accuracy của client đó

### Theo dõi log

- Server Log: hiển thị log từ server
- Client Log: hiển thị log từ từng client

### So sánh session

- Nhập các tham số ở Session A hoặc Session B
- Nhấn Find để tìm session phù hợp
- Chọn session và nhấn Active để xem biểu đồ so sánh

### Đếm submit

- Nhấn Count ở từng card client để xem tổng số submit và thời gian submit gần nhất

## 8. Lưu ý quan trọng

- Dự án có thể tự động dùng SQLite nếu MySQL không sẵn sàng.
- Khi chạy backend, hãy đảm bảo thư mục dữ liệu client1/..../client4 nằm ở đúng vị trí tương đối với backend.
- Nếu gặp lỗi "port already in use", hãy đóng tiến trình đang dùng cổng 8000 hoặc 8080.

## 9. Khắc phục sự cố thường gặp

### ModuleNotFoundError

```bash
pip install -r requirements.txt
```

### Port 8000 hoặc 8080 đang được dùng

- Tắt tiến trình cũ
- Hoặc đổi cổng trong cấu hình

### Không thấy giao diện cập nhật

- Kiểm tra backend đã chạy chưa
- Mở frontend sau khi backend đã sẵn sàng

## 10. Kết luận

Đây là một dự án demo về Federated Learning, giúp bạn hiểu cách nhiều client có thể huấn luyện một mô hình chung mà không cần chia sẻ dữ liệu gốc. Dự án có thể được mở rộng cho nhiều ứng dụng khác nhau, bao gồm phân loại dữ liệu, nhận diện mẫu hoặc các bài toán học máy phân tán khác.
