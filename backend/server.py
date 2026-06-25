import flwr as fl
from flwr.server.strategy import FedAvg
from task import SimpleCNN, ImprovedCNN
import argparse
import requests
import torch
import time, os

class SaveModelStrategy(FedAvg):
    def __init__(self, model, num_rounds, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.num_rounds = num_rounds

    def aggregate_fit(self, server_round, results, failures):
        aggregated, metrics = super().aggregate_fit(server_round, results, failures)

        if server_round == self.num_rounds:
            if aggregated is not None:
                ndarrays = fl.common.parameters_to_ndarrays(aggregated)
                keys = list(self.model.state_dict().keys())

                new_state_dict = {
                    k: torch.tensor(ndarrays[i]) for i, k in enumerate(keys)
                }
                self.model.load_state_dict(new_state_dict)
                os.makedirs("C:/trained_models", exist_ok=True)
                torch.save(self.model.state_dict(), f"C:/trained_models/final_model_{int(time.time())}.pth")

        return aggregated, metrics



# Khởi tạo mô hình toàn cục
model = SimpleCNN()
initial_parameters = fl.common.ndarrays_to_parameters(
    [val.cpu().numpy() for _, val in model.state_dict().items()]
)

if __name__ == "__main__":
    # 1. Định nghĩa và đọc đối số dòng lệnh
    parser = argparse.ArgumentParser(description="Flower Server.")
    
    # Thêm tham số num_rounds
    parser.add_argument(
        "--num_rounds",
        type=int,
        default=100,
        help="Số vòng huấn luyện (mặc định: 100)",
    )
    
    # 👈 Thêm tham số learning rate (lr)
    parser.add_argument(
        "--lr",
        type=float, # Dùng float vì lr là số thực
        default=0.01, # Giá trị mặc định
        help="Tốc độ học (Learning Rate) cho client (mặc định: 0.01)",
    )

    parser.add_argument(
        "--local_epochs",
        type=int,
        default=1, # Giá trị mặc định
    )
    
    args = parser.parse_args()
    
    # Lấy giá trị num_rounds
    num_rounds = args.num_rounds
    
    # 👈 Lấy giá trị lr và gán vào biến toàn cục
    global_lr = args.lr

    local_epochs = args.local_epochs

    def fit_config(server_round: int):
        return {
            "server_round": server_round,
            "local_epochs": local_epochs,
            # Sử dụng biến GLOBAL_LR đã được thiết lập
            "lr": global_lr, 
        }
    
    print(f"[SERVER] Starting with config:", flush=True)
    print(f"  - num_rounds = {num_rounds}", flush=True)
    print(f"  - lr = {global_lr}", flush=True)
    print(f"  - local_epochs = {local_epochs}", flush=True)

    try:
        response = requests.post(
            "http://localhost:8000/sessions/",
            json={
                "num_rounds": num_rounds,
                "lr": global_lr,
                "local_epochs": local_epochs
            },
            timeout=5
        )
        if response.status_code in [200, 201]:
            session_data = response.json()
            print(f"[SERVER] Created session in DB: {session_data}")
            session_id = session_data["id"]  # lưu lại để client submit
        else:
            print(f"[SERVER] Failed to create session: {response.text}")
            session_id = None
    except Exception as e:
        print(f"[SERVER] Error calling backend API: {e}")
        session_id = None

    def evaluate_config(server_round: int):
        return {
            "server_round": server_round,
            "session_id": session_id
        }
    
    strategy = SaveModelStrategy(
        model=model,
        num_rounds=num_rounds,
        initial_parameters=initial_parameters,
        min_available_clients=2,
        min_fit_clients=2,
        min_evaluate_clients=2,
        on_fit_config_fn=fit_config,
        on_evaluate_config_fn=evaluate_config,
    )
    # 2. Khởi động server
    fl.server.start_server(
        server_address="localhost:8080",
        config=fl.server.ServerConfig(num_rounds=num_rounds), 
        strategy=strategy
    )