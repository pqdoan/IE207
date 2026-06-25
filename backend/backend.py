# backend.py
import asyncio
import threading
import subprocess
import sys
from queue import Queue, Empty
from fastapi import FastAPI, WebSocket, Query
from fastapi.responses import JSONResponse
from fastapi import Path
from typing import Dict
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import crud, models, schemas
from database import Base, engine, get_db
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # hoặc origin FE của bạn
    allow_credentials=True,
    allow_methods=["*"],      # QUAN TRỌNG: Cho phép OPTIONS
    allow_headers=["*"],
)

# Biến toàn cục giữ tiến trình server.py
server_process = None
process_lock = threading.Lock()  # để tránh race khi start/stop


@app.websocket("/ws/logs")
async def websocket_server_endpoint(websocket: WebSocket, num_rounds: int = Query(100), lr: float = Query(0.01), local_epochs: int = Query(1)):
    global server_process

    await websocket.accept()
    q = Queue()

    python_exe = sys.executable

    # Thread chạy server.py và đẩy log vào queue
    def run_server_and_stream():
        global server_process
        with process_lock:
            # nếu đã có process đang chạy thì không start lại
            if server_process and server_process.poll() is None:
                q.put("[SERVER_ALREADY_RUNNING]")
                return
            command = [python_exe, "server.py", "--num_rounds", str(num_rounds), "--lr", str(lr), "--local_epochs", str(local_epochs)]
            server_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

        # Đọc stdout của tiến trình
        try:
            for line in server_process.stdout:
                if line:
                    q.put(line.rstrip("\n"))
        except Exception:
            pass
        finally:
            q.put("[SERVER STOPPED]")

    # Start thread (daemon) để chạy server.py
    threading.Thread(target=run_server_and_stream, daemon=True).start()

    try:
        while True:
            try:
                # Không block vô hạn — timeout để loop có thể kiểm tra cancel
                line = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: q.get(timeout=0.2)
                )
            except Empty:
                # kiểm tra websocket vẫn mở, sau đó lặp lại
                await asyncio.sleep(0)  # yield control
                continue

            # gửi log cho client
            try:
                await websocket.send_text(line)
            except Exception:
                # client có thể đóng kết nối bất ngờ
                break

            if line == "[SERVER STOPPED]":
                break

    except asyncio.CancelledError:
        # WebSocket bị cancel (ví dụ reload or Ctrl+C) -> dọn dẹp process
        with process_lock:
            if server_process and server_process.poll() is None:
                try:
                    server_process.terminate()
                    server_process.wait(timeout=3)
                except Exception:
                    try:
                        server_process.kill()
                    except Exception:
                        pass
        raise
    finally:
        pass


@app.post("/stop-server")
async def stop_server():
    """HTTP endpoint để dừng server.py một cách an toàn"""
    global server_process
    with process_lock:
        if server_process and server_process.poll() is None:
            try:
                server_process.terminate()  # gửi SIGTERM (Windows: TerminateProcess)
                try:
                    server_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # không dừng -> kill cứng
                    server_process.kill()
                return JSONResponse({"status": "terminated"})
            except Exception as e:
                return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
        else:
            return JSONResponse({"status": "not running"})
        

# Khởi tạo các biến/lock/app nếu chưa có
process_lock = threading.Lock()
# Sử dụng Dict để lưu trữ các process theo client_id
running_processes: Dict[int, subprocess.Popen] = {} 

@app.websocket("/ws/client/{client_id}/logs")
async def websocket_client_endpoint(
    websocket: WebSocket, 
    client_id: int = Path(..., description="ID của client để chạy"),
    seed: int = Query(42)
):
    await websocket.accept()
    q = Queue()
    python_exe = sys.executable

    # Hàm chạy client.py với ID
    def run_client_and_stream(client_id: int):
        # Tạo key duy nhất cho process này
        process_key = client_id
        
        with process_lock:
            # 1. Kiểm tra nếu process với ID này đã chạy
            if process_key in running_processes and running_processes[process_key].poll() is None:
                q.put(f"[CLIENT_ID_{client_id}_ALREADY_RUNNING]")
                return
            
            # 2. Khởi tạo process mới
            process = subprocess.Popen(
                [python_exe, "client.py", str(client_id), str(seed)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            running_processes[process_key] = process # Lưu process vào Dict

        # Đọc stdout của tiến trình
        try:
            for line in process.stdout:
                if line:
                    q.put(line.rstrip("\n"))
        except Exception:
            pass
        finally:
            q.put(f"[CLIENT_ID_{client_id}_STOPPED]")
            # Dọn dẹp process khi nó dừng
            with process_lock:
                if process_key in running_processes:
                    del running_processes[process_key]

    # Start thread (daemon) để chạy client.py
    threading.Thread(target=run_client_and_stream, args=(client_id,), daemon=True).start()

    try:
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: q.get(timeout=0.2)
                )
            except Empty:
                await asyncio.sleep(0)
                continue

            try:
                await websocket.send_text(line)
            except Exception:
                break

            if line.endswith("_STOPPED]"):
                break

    except asyncio.CancelledError:
        # Xử lý khi WebSocket bị cancel: Kill tiến trình con
        with process_lock:
            process = running_processes.get(client_id)
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=3)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass
                finally:
                    # Dọn dẹp process
                    if client_id in running_processes:
                        del running_processes[client_id]
        raise
    finally:
        pass

@app.post("/stopClient/{client_id}")
async def stopClient(client_id: int = Path(..., description="ID của client để chạy")):
    with process_lock:
        process = running_processes.get(client_id)

        if process and process.poll() is None:
            try:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()

                del running_processes[client_id]   # ⚠️ Quan trọng
                return JSONResponse({"status": "terminated"})

            except Exception as e:
                return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

        else:
            return JSONResponse({"status": "not running"})


accclient = {"client1": [], "client2": [], "client3": [], "client4": []}
wsclientacc = {"client1": None, "client2": None, "client3": None, "client4": None,}

@app.post("/client/metric")
async def recieve(data: dict):
    global accclient, wsclientacc
    client_id = f"client{data.get('client_id')}"  # client gửi kèm ID
    if client_id in accclient:
        accclient[client_id].append(data)

    # Nếu WebSocket đang kết nối thì gửi dữ liệu
    ws = wsclientacc.get(client_id)
    if ws is not None:
        try:
            await ws.send_text(json.dumps(accclient[client_id]))
        except:
            wsclientacc[client_id] = None  # reset nếu WS đóng

    return {"status": "ok"}


@app.websocket("/ws/{client_id}/acc")
async def sendacc(websocket: WebSocket, client_id: str):
    global wsclientacc
    if client_id not in wsclientacc:
        await websocket.close()
        return

    await websocket.accept()
    wsclientacc[client_id] = websocket
    print(f"WebSocket {client_id} connected")

    try:
        while True:
            await websocket.receive_text()  # giữ kết nối
    except:
        wsclientacc[client_id] = None
        print(f"WebSocket {client_id} disconnected")

@app.post("/sessions/", response_model=schemas.TrainingSessionOut)
def create_training_session(session: schemas.TrainingSessionCreate, db: Session = Depends(get_db)):
    """
    Tạo session mới
    """
    return crud.create_session(db, session)

@app.post("/client/submit")
def create_client_submit(submit: schemas.ClientSubmitCreate, db: Session = Depends(get_db)):
    db_item = crud.create_submit(db, submit)
    return {
        "id": db_item.id,
        "session_id": db_item.session_id,
        "client_id": db_item.client_id,
        "round_number": db_item.round_number,
        "accuracy": db_item.accuracy,
        "seed": db_item.seed,
        "timestamp": db_item.timestamp.isoformat()  # convert datetime -> str
    }

@app.post("/sessions/find")
def find_sessions(payload: schemas.SessionFindRequest, db: Session = Depends(get_db)):

    sessions = crud.find_sessions_by_params(
        db=db,
        num_rounds=payload.num_rounds,
        local_epochs=payload.local_epochs,
        lr=payload.lr,
        seed=payload.seed,
    )
    print(sessions)
    return [{"session_id": s.id} for s in sessions]

@app.get("/sessions/{session_id}/submits")
def get_session_submits(session_id: int, db: Session = Depends(get_db)):
    submits = crud.get_submits_by_session(db=db, session_id=session_id)
    # Trả về dữ liệu dưới dạng list các đối tượng ClientSubmitOut
    return [schemas.ClientSubmitOut.from_orm(s) for s in submits]

@app.post("/count-submit/{client_id}")
def count_submit_client(
    client_id: int = Path(..., description="ID của client để chạy"),
    db: Session = Depends(get_db)
):
    count, last = crud.count_and_last_submit(db, client_id)

    return {
        "count": count,
        "last_submit": last.timestamp.isoformat() if last else None
    }

