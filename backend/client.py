

import sys
import torch
import flwr as fl
from task import SimpleCNN, ImprovedCNN, load_data, train as train_fn, test as test_fn
import requests

class FlowerClient(fl.client.NumPyClient):
    def __init__(self, partition_id, randomseed):
        self.partition_id = partition_id
        self.model = SimpleCNN()
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.trainloader, self.valloader = load_data(partition_id, randomseed)
        self.randomseed = randomseed

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters):
        state_dict = dict(zip(self.model.state_dict().keys(), [torch.tensor(p) for p in parameters]))
        self.model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        train_fn(
            self.model,
            self.trainloader,
            epochs=int(config.get("local_epochs", 1)),
            lr=float(config.get("lr", 0.011)),
            device=self.device,
        )
        return self.get_parameters(config), len(self.trainloader.dataset), {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, acc = test_fn(self.model, self.valloader, self.device)
        round_num = config.get("server_round", "Unknown")
        session_id = config.get("session_id")
        seed = self.randomseed

        print(f"[Client {self.partition_id}] Random Seed: {seed} Round {round_num} - Evaluation - Loss: {loss:.4f}, Accuracy: {acc:.2f}%", flush=True)

        # Gửi thông tin cũ (chỉ acc)
        if self.partition_id in [1,2,3,4]:
            try:
                requests.post(
                    "http://localhost:8000/client/metric",
                    json={
                        "client_id": self.partition_id,
                        "round": round_num,
                        "acc": float(acc)
                    },
                    timeout=5
                )
            except Exception as e:
                print("[Client] Failed to POST acc:", e)

            # Gửi thêm thông tin đầy đủ vào endpoint lưu ClientSubmit
            if session_id is not None:
                try:
                    requests.post(
                        "http://localhost:8000/client/submit",
                        json={
                            "session_id": session_id,
                            "client_id": self.partition_id,
                            "round_number": round_num,
                            "accuracy": float(acc),
                            "seed": seed
                        },
                        timeout=5
                    )
                except Exception as e:
                    print("[Client] Failed to POST full submit:", e)

        return float(loss), len(self.valloader.dataset), {"accuracy": float(acc)}



if __name__ == "__main__":
    partition_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    randomseed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    fl.client.start_numpy_client(server_address="localhost:8080", client=FlowerClient(partition_id, randomseed))