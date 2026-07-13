// HTML에서 필요한 요소들 가져오기
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const introScreen = document.getElementById('introScreen');
const chatScreen = document.getElementById('chatScreen');

// 🛠️ 화면 전환 기능 추가
function startChat() {
    introScreen.style.display = 'none';
    chatScreen.style.display = 'flex';
    scrollToBottom();
}

function goBack() {
    introScreen.style.display = 'flex';
    chatScreen.style.display = 'none';
}

// 메시지 전송 함수 (일반 텍스트 입력)
function sendMessage() {
    const messageText = chatInput.value.trim();
    if (messageText === '') return;

    appendUserMessage(messageText);
    chatInput.value = '';
    scrollToBottom();

    // 1초 뒤 자동 응답
    setTimeout(() => {
        botReply(messageText);
    }, 1000);
}

// 유저 말풍선 공통 추가 함수
function appendUserMessage(text) {
    const userRow = document.createElement('div');
    userRow.className = 'message-row user-row';
    userRow.innerHTML = `<div class="user-bubble">${text}</div>`;
    chatMessages.appendChild(userRow);
    scrollToBottom();
}

// 🤖 텍스트 기반 챗봇 기본 응답 함수
function botReply(userMessage) {
    const botRow = document.createElement('div');
    botRow.className = 'message-row bot-row';
    
    let replyText = `"${userMessage}"에 대한 정보를 찾고 있습니다. 정확한 분석을 원하시면 우측 상단 📍 버튼으로 위치를 공유해 주세요!`;
    if(userMessage.includes('안녕')) {
        replyText = "반가워요! 안전한 낚시 활동을 위해 현재 위치 주변의 연안사고 위험구역을 알려드릴게요.";
    }

    botRow.innerHTML = `
        <div class="bot-avatar">
            <span class="material-symbols-outlined">smart_toy</span>
        </div>
        <div class="bot-bubble">${replyText}</div>
    `;
    
    chatMessages.appendChild(botRow);
    scrollToBottom();
}

// 🛠️ 디벨롭 포인트: HTML5 Geolocation API 호출 함수
function askLocation() {
    if (navigator.geolocation) {
        // 시스템 알림 봇 띄우기
        appendBotSystemMessage("📡 실시간 GPS 위성 신호를 탐색 중입니다...");
        
        const gpsOptions = {
            enableHighAccuracy: true, // 정확도 최우선 (방파제/갯바위 필수)
            timeout: 7000,
            maximumAge: 0
        };
        
        navigator.geolocation.getCurrentPosition(onGpsSuccess, onGpsError, gpsOptions);
    } else {
        appendBotSystemMessage("❌ 회원님의 브라우저는 위치 서비스를 지원하지 않습니다.");
    }
}

// 📍 GPS 수신 성공 시 동작
function onGpsSuccess(position) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    
    // 사용자가 내 위치를 보낸 것처럼 말풍선 추가
    appendUserMessage(`📍 내 현재 위치 전송<br>(위도: ${lat.toFixed(4)}, 경도: ${lon.toFixed(4)})`);
    
    // 파이썬 백엔드로 비동기 전송 시도
    sendLocationToPython(lon, lat);
}

// 🌐 파이썬 백엔드 API 서버와 실시간 통신 연동 파트
function sendLocationToPython(lon, lat) {
    // 파이썬 FastAPI/Flask 분석 서버 경로 (구축 예정 주소)
    const backendApiUrl = "http://localhost:8000/analyze";
    
    fetch(backendApiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ longitude: lon, latitude: lat })
    })
    .then(response => response.json())
    .then(data => {
        // [성공] 파이썬 공간분석 결과(FishingSafetyService)를 챗봇 대화창에 바인딩
        appendBotLongReply(data.reply);
    })
    .catch(error => {
        console.warn("백엔드 서버가 켜져 있지 않아 가상 분석 결과를 출력합니다.");
        
        // 💡 [테스트 모드] 서버 연결 전 프론트 자체 가상 연산 시뮬레이터
        setTimeout(() => {
            let mockReply = "";
            // 감천항 좌표 시뮬레이션 예시 (아까 만든 파이썬 결과와 매핑)
            if (lon >= 129.00 && lon <= 129.01) {
                mockReply = `🚨 <b>[위험 경고] 회원님 근처 500m 이내에 사고 구역이 존재합니다!</b><br>
                             📍 인접 위험지점: '감천-1 방파제' (약 45.2m 거리)<br>
                             ⚠️ 이곳은 추락 및 익사 사고가 빈번한 연안사고 위험구역이오니 낚시를 즉시 중단하시거나 안전구역으로 이동해 주세요.`;
            } else {
                mockReply = `🍏 <b>[분석 완료] 현재 위치 주변 1km 이내에 안전 위험구역이 없습니다.</b><br>
                             🎣 쾌적하고 안전한 낚시가 가능합니다! 안전을 위해 구명조끼는 상시 착용해 주시기 바랍니다.`;
            }
            appendBotLongReply(mockReply);
        }, 1200);
    });
}

// GPS 수신 실패(오류) 시 처리
function onGpsError(error) {
    let errorMsg = "위치 정보를 가져오지 못했습니다.";
    if (error.code === error.PERMISSION_DENIED) {
        errorMsg = "❌ 위치 권한 승인이 거부되었습니다. 주소창 왼쪽 자물쇠 아이콘을 눌러 위치 권한을 허용해 주세요.";
    } else if (error.code === error.TIMEOUT) {
        errorMsg = "❌ GPS 연결 시간이 초과되었습니다. 신호가 좋은 곳에서 다시 시도해 주세요.";
    }
    appendBotSystemMessage(errorMsg);
}

// 챗봇 시스템 멘트용 전용 함수
function appendBotSystemMessage(text) {
    const botRow = document.createElement('div');
    botRow.className = 'message-row bot-row';
    botRow.innerHTML = `
        <div class="bot-avatar"><span class="material-symbols-outlined">info</span></div>
        <div class="bot-bubble" style="background-color: #fff4f4; color: #d9383a;">${text}</div>
    `;
    chatMessages.appendChild(botRow);
    scrollToBottom();
}

// 챗봇 장문/HTML 안내 메시지 출력 함수
function appendBotLongReply(htmlContent) {
    const botRow = document.createElement('div');
    botRow.className = 'message-row bot-row';
    botRow.innerHTML = `
        <div class="bot-avatar"><span class="material-symbols-outlined">smart_toy</span></div>
        <div class="bot-bubble" style="line-height: 1.5;">${htmlContent}</div>
    `;
    chatMessages.appendChild(botRow);
    scrollToBottom();
}

// 스크롤 자동 하단 이동 함수
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 이벤트 리스너 연결
sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') sendMessage();
});