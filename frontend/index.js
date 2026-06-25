

let serverWs = null; // Đổi tên ws thành serverWs để rõ ràng hơn
const clientWs = {}; // Dùng đối tượng để lưu trữ các kết nối client theo ID

// --- Hàm startServer (Đã cập nhật tên biến) ---
function startServer() {
    const log = document.getElementById("server-log"); // Đã cập nhật ID div log
    log.textContent += "\n[SERVER START] Connecting...\n";

    if (serverWs) {
        log.textContent += "\nSERVER ALREADY RUNNING\n";
        return;
    }

    const numround = document.getElementById("num_round").value;
    const local = document.getElementById("local").value;
    const lr = document.getElementById("lr").value;

    const params = new URLSearchParams({
        num_rounds: numround,
        lr: lr,
        local_epochs: local //
    }).toString();

    const websocketUrl = `ws://localhost:8000/ws/logs?${params}`;

    serverWs = new WebSocket(websocketUrl);

    serverWs.onmessage = (event) => {
        log.textContent += event.data + "\n";
        log.scrollTop = log.scrollHeight;
    };

    serverWs.onerror = () => {
        log.textContent += "[SERVER WebSocket ERROR]\n";
        serverWs = null;
    };

    serverWs.onclose = () => {
        log.textContent += "[SERVER WebSocket CLOSED]\n";
        serverWs = null
    };
}


// --- Hàm stopServer (Đã cập nhật tên biến) ---
function stopServer() {
    fetch("http://localhost:8000/stop-server", {
        method: "POST"
    })
        .then(res => res.json())
        .then(data => {
            const log = document.getElementById("server-log"); // Đã cập nhật ID div log
            log.textContent += `\n[SERVER STOP REQUEST] ${data.status}\n`;

            // nếu websocket còn mở thì đóng lại
            if (serverWs && serverWs.readyState === WebSocket.OPEN) {
                serverWs.close();
                serverWs = null
            }
        });
}

// ------------------------------------------------------------------
// --- HÀM MỚI: Khởi động Client và nhận Log qua WebSocket ---
// ------------------------------------------------------------------

function startClient(clientId) {
    // SỬA LỖI QUAN TRỌNG: Tạo ID DIV động từ clientId (ví dụ: client-log-1)
    const logDivId = `client-log-${clientId}`;
    const clientLogDiv = document.getElementById(logDivId);

    // Kiểm tra xem div có tồn tại không
    if (!clientLogDiv) {
        console.error(`Không tìm thấy div log với ID: ${logDivId}`);
        return;
    }

    clientLogDiv.textContent += `\n[CLIENT ${clientId} START]`

    // 1. Kiểm tra nếu Client này đã có kết nối đang mở
    if (clientWs[clientId] && clientWs[clientId].readyState === WebSocket.OPEN) {
        clientLogDiv.textContent += `[CLIENT ${clientId}] ALREADY RUNNING \n`;
        return;
    }

    // Đóng kết nối cũ nếu nó ở trạng thái khác
    if (clientWs[clientId]) {
        clientWs[clientId].close();
    }

    const seed = document.getElementById("seed").value;
    const endpoint = `ws://localhost:8000/ws/client/${clientId}/logs?seed=${seed}`;

    // 2. Tạo kết nối WebSocket mới
    const ws = new WebSocket(endpoint);
    clientWs[clientId] = ws; // Lưu kết nối vào đối tượng global

    // 3. Xử lý tin nhắn
    ws.onmessage = (event) => {
        // Hiển thị log
        clientLogDiv.textContent += `[C${clientId}] ${event.data}\n`;
        clientLogDiv.scrollTop = clientLogDiv.scrollHeight;
    };

    // 4. Xử lý lỗi
    ws.onerror = () => {
        clientLogDiv.textContent += `[CLIENT ${clientId} ERROR] Lỗi WebSocket (Kiểm tra backend đã chạy chưa).\n`;
    };

    // 5. Xử lý đóng kết nối
    ws.onclose = () => {
        clientLogDiv.textContent += `[CLIENT ${clientId} CLOSED] Kết nối đã đóng.\n`;
        delete clientWs[clientId];
    };
}

function stopClient(clientId) {
    const logDiv = document.getElementById(`client-log-${clientId}`);

    logDiv.textContent += `\n[SEND STOP REQUEST] Stopping client ${clientId}...\n`;

    fetch(`http://localhost:8000/stopClient/${clientId}`, {
        method: "POST"
    })
        .then(res => res.json())
        .then(data => {
            logDiv.textContent += `[CLIENT ${clientId} STOP] ${data.status}\n`;

            // Nếu WebSocket đang mở thì đóng
            if (clientWs[clientId] && clientWs[clientId].readyState === WebSocket.OPEN) {
                clientWs[clientId].close();
                delete clientWs[clientId];
            }
        })
        .catch(err => {
            console.error(err);
            logDiv.textContent += `[CLIENT ${clientId} ERROR] Không thể gửi request stop.\n`;
        });
}



const clientAcc = {
    client1: [],
    client2: [],
    client3: [],
    client4: []
};

const charts = {
    client1: null,
    client2: null,
    client3: null,
    client4: null
};

const wsClients = {}; // giữ WebSocket cho từng client

function connectToWsClient(clientId) {
    if (wsClients[clientId]) {
        wsClients[clientId].close();
    }

    wsClients[clientId] = new WebSocket(`ws://localhost:8000/ws/client${clientId}/acc`);

    wsClients[clientId].onmessage = (event) => {
        const data = JSON.parse(event.data); // server gửi **chỉ mảng client đó**

        clientAcc[`client${clientId}`] = []; // reset
        data.forEach(item => {
            clientAcc[`client${clientId}`].push([item.round, item.acc]);
        });

        drawChart(clientId);
    };

    wsClients[clientId].onerror = () => console.log(`WS error client${clientId}`);
    wsClients[clientId].onclose = () => console.log(`WS closed client${clientId}`);
}

function drawChart(clientId) {
    const ctx = document.getElementById(`lossChart-${clientId}`).getContext('2d');

    if (charts[`client${clientId}`]) {
        charts[`client${clientId}`].destroy();
    }

    const labels = clientAcc[`client${clientId}`].map(item => `Round ${item[0]}`);
    const dataPoints = clientAcc[`client${clientId}`].map(item => item[1]);

    charts[`client${clientId}`] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `Accuracy Client ${clientId}`,
                data: dataPoints,
                borderColor: 'rgb(0, 102, 255)',
                backgroundColor: 'rgba(0, 102, 255, 0.2)',
                borderWidth: 2,
                tension: 0.4,
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { title: { display: true, text: 'Round' } },
                y: { title: { display: true, text: 'Accuracy (%)' }, beginAtZero: true, suggestedMax: 100 }
            }
        }
    });
}

document.getElementById("find1").addEventListener("click", async () => {
    const payload = {
        num_rounds: Number(document.getElementById("num_round1").value),
        local_epochs: Number(document.getElementById("local1").value),
        lr: Number(document.getElementById("lr1").value),   // sửa learning_rate -> lr
        seed: Number(document.getElementById("seed1").value)
    };

    console.log(payload);

    const res = await fetch("http://127.0.0.1:8000/sessions/find", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const sessions = await res.json();
    console.log(sessions)

    const select = document.getElementById("select1");
    select.innerHTML = "";

    sessions.forEach(s => {
        const op = document.createElement("option");
        op.value = s.session_id;
        op.textContent = `Session ${s.session_id}`;
        select.appendChild(op);
    });
});

const compareCharts = {
    cp1: null,
    cp2: null,
    cp3: null,
    cp4: null,
    cp5: null, 
    cp6: null,
    cp7: null,
    cp8: null
};

function drawCompareChart(clientData, canvasId) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const clientId = clientData[0].client_id;
    const sessionId = clientData[0].session_id;

    // Hủy biểu đồ cũ nếu có
    if (compareCharts[canvasId]) {
        compareCharts[canvasId].destroy();
    }

    const roundLabels = clientData.map(d => d.round_number);
    const accuracyData = clientData.map(d => d.accuracy);

    compareCharts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: roundLabels,
            datasets: [{
                label: `Session ${sessionId} - Client ${clientId}`,
                data: accuracyData,
                // Tạo màu ngẫu nhiên cho biểu đồ
                borderColor: '#' + Math.floor(Math.random() * 16777215).toString(16),
                borderWidth: 2,
                tension: 0.3,
                fill: false,
                pointRadius: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Round Number' } },
                y: { title: { display: true, text: 'Accuracy' }, beginAtZero: true, suggestedMax: 1 }
            },
            plugins: {
                title: {
                    display: true,
                    text: `Client ${clientId} Accuracy`
                }
            }
        }
    });
}

document.getElementById("find1").addEventListener("click", async () => {
    const payload = {
        num_rounds: Number(document.getElementById("num_round1").value),
        local_epochs: Number(document.getElementById("local1").value),
        lr: Number(document.getElementById("lr1").value),
        seed: Number(document.getElementById("seed1").value)
    };

    console.log("[Find1] Payload:", payload);

    const res = await fetch("http://127.0.0.1:8000/sessions/find", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const sessions = await res.json();
    console.log("[Find1] Sessions found:", sessions);

    const select = document.getElementById("select1");
    select.innerHTML = "";
    select.disabled = (sessions.length === 0); // Vô hiệu hóa nếu không có kết quả

    sessions.forEach(s => {
        const op = document.createElement("option");
        op.value = s.session_id;
        op.textContent = `Session ${s.session_id}`;
        select.appendChild(op);
    });
});

document.getElementById("active1").addEventListener("click", async () => {
    const select = document.getElementById("select1");
    const sessionId = select.value;
    
    if (!sessionId) {
        console.error("Vui lòng chọn một Session ID cho Object 1.");
        return;
    }

    console.log(`[Object1 Active] Lấy dữ liệu cho Session ID: ${sessionId}`);

    // 2. Gọi API backend
    const res = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}/submits`);
    
    if (!res.ok) {
        console.error("Lỗi khi fetch dữ liệu submit Object 1:", await res.text());
        return;
    }
    
    const submits = await res.json();
    
    // 3. Nhóm dữ liệu theo client_id
    const groupedData = submits.reduce((acc, submit) => {
        const clientId = submit.client_id;
        if (!acc[clientId]) {
            acc[clientId] = [];
        }
        acc[clientId].push(submit);
        return acc;
    }, {});
    
    // 4. Vẽ biểu đồ cho tối đa 4 client (cp1, cp2, cp3, cp4)
    const clientIds = Object.keys(groupedData).sort((a, b) => a - b);
    const canvasIds = ["cp1", "cp2", "cp3", "cp4"];

    clientIds.forEach((clientId, index) => {
        if (index < canvasIds.length) {
            drawCompareChart(groupedData[clientId], canvasIds[index]);
        }
    });

    // 5. Xóa biểu đồ ở các canvas còn lại nếu có ít hơn 4 client
    for (let i = clientIds.length; i < canvasIds.length; i++) {
        const canvasId = canvasIds[i];
         if (compareCharts[canvasId]) {
            compareCharts[canvasId].destroy();
            compareCharts[canvasId] = null;
        }
    }
});


// ------------------------------------------------------------------
// --- LOGIC CHO OBJECT 2 ---
// ------------------------------------------------------------------

document.getElementById("find2").addEventListener("click", async () => {
    // Lấy giá trị từ các trường nhập liệu của Object2
    const payload = {
        num_rounds: Number(document.getElementById("num_round2").value),
        local_epochs: Number(document.getElementById("local2").value),
        lr: Number(document.getElementById("lr2").value),
        seed: Number(document.getElementById("seed2").value)
    };

    console.log("[Find2] Payload:", payload);

    const res = await fetch("http://127.0.0.1:8000/sessions/find", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const sessions = await res.json();
    console.log("[Find2] Sessions found:", sessions);

    // Đổ kết quả vào select box của Object2 (ID: select2)
    const select = document.getElementById("select2");
    select.innerHTML = "";
    select.disabled = (sessions.length === 0); // Vô hiệu hóa nếu không có kết quả

    sessions.forEach(s => {
        const op = document.createElement("option");
        op.value = s.session_id;
        op.textContent = `Session ${s.session_id}`;
        select.appendChild(op);
    });
});

document.getElementById("active2").addEventListener("click", async () => {
    const select = document.getElementById("select2");
    const sessionId = select.value;
    
    if (!sessionId) {
        console.error("Vui lòng chọn một Session ID cho Object 2.");
        return;
    }

    console.log(`[Object2 Active] Lấy dữ liệu cho Session ID: ${sessionId}`);

    // 2. Gọi API backend
    const res = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}/submits`);
    
    if (!res.ok) {
        console.error("Lỗi khi fetch dữ liệu submit Object 2:", await res.text());
        return;
    }
    
    const submits = await res.json();
    
    // 3. Nhóm dữ liệu theo client_id
    const groupedData = submits.reduce((acc, submit) => {
        const clientId = submit.client_id;
        if (!acc[clientId]) {
            acc[clientId] = [];
        }
        acc[clientId].push(submit);
        return acc;
    }, {});
    
    // 4. Vẽ biểu đồ cho tối đa 4 client (cp5, cp6, cp7, cp8)
    const clientIds = Object.keys(groupedData).sort((a, b) => a - b);
    const canvasIds = ["cp5", "cp6", "cp7", "cp8"];

    clientIds.forEach((clientId, index) => {
        if (index < canvasIds.length) {
            drawCompareChart(groupedData[clientId], canvasIds[index]);
        }
    });

    // 5. Xóa biểu đồ ở các canvas còn lại nếu có ít hơn 4 client
    for (let i = clientIds.length; i < canvasIds.length; i++) {
        const canvasId = canvasIds[i];
         if (compareCharts[canvasId]) {
            compareCharts[canvasId].destroy();
            compareCharts[canvasId] = null;
        }
    }
});

function countSubmit(id) {
    const logDiv = document.getElementById(`count-${id}`);
    const time = document.getElementById(`last-${id}`);

    fetch(`http://localhost:8000/count-submit/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(data => {
        logDiv.textContent = data.count;
        time.textContent = data.last_submit;
    })
    .catch(err => {
        logDiv.textContent = `Error: ${err}`;
    });
}
