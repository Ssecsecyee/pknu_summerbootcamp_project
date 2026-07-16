// =====================================================
// 사용자 세션 / 현재 위치 / 이미지 파일 관리
// =====================================================
const sessionId = crypto.randomUUID();
let uploadedFile = null; 

let currentLat = sessionStorage.getItem("currentLat");
let currentLon = sessionStorage.getItem("currentLon");

if (currentLat !== null) currentLat = Number(currentLat);
if (currentLon !== null) currentLon = Number(currentLon);

console.log("저장된 사용자 위치:", currentLat, currentLon);

// =====================================================
// 시작 화면 → 챗봇
// =====================================================
function startChat() {
    document.getElementById("startScreen").style.display = "none";
    document.getElementById("chatScreen").style.display = "flex";
}

function goBack() {
    document.getElementById("chatScreen").style.display = "none";
    document.getElementById("startScreen").style.display = "flex";
    clearSelectedImage(); 
}

// =====================================================
// 💡 이미지 파일 선택 및 프리뷰 처리 
// =====================================================
function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        const file = files[0];
        
        if (file.type.startsWith("image/")) {
            uploadedFile = file;
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const previewImg = document.getElementById("imagePreview");
                const previewBox = document.getElementById("imagePreviewBox");
                
                if (previewImg && previewBox) {
                    previewImg.src = e.target.result;
                    // css의 none 속성을 확실하게 덮어쓰기 위해 setProperty 사용
                    previewBox.style.setProperty("display", "flex", "important"); 
                }
            };
            reader.readAsDataURL(file);
        } else {
            alert("❌ 이미지 파일(png, jpeg, jpg 등)만 선택할 수 있습니다.");
            clearSelectedImage();
        }
    }
}

// 이미지 취소 버튼 클릭 시 처리
function clearSelectedImage() {
    uploadedFile = null;
    const fileInput = document.getElementById("fileInput");
    if (fileInput) fileInput.value = ""; 
    
    const previewBox = document.getElementById("imagePreviewBox");
    const previewImg = document.getElementById("imagePreview");
    
    if (previewBox) previewBox.style.setProperty("display", "none", "important");
    if (previewImg) previewImg.src = "";
}

// =====================================================
// 사용자 위치 요청
// =====================================================
function getLocation() {
    if (!navigator.geolocation) {
        addBotMessage("❌ 현재 브라우저는 위치 정보를 지원하지 않습니다.");
        return;
    }
    addBotMessage("📍 현재 위치를 확인하고 있습니다...");
    navigator.geolocation.getCurrentPosition(
        searchNearby, locationError,
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
}

// =====================================================
// 위치 획득 성공 및 API 호출
// =====================================================
async function searchNearby(position) {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;

    currentLat = lat;
    currentLon = lon;
    sessionStorage.setItem("currentLat", currentLat);
    sessionStorage.setItem("currentLon", currentLon);

    try {
        const dangerResponse = await fetch("/danger/nearby", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lat: lat, lon: lon })
        });
        if (!dangerResponse.ok) throw new Error("위험구역 API 오류");
        const dangerData = await dangerResponse.json();
        showDanger(dangerData);

        const fishingResponse = await fetch("/fishing/nearby", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lat: lat, lon: lon })
        });
        if (!fishingResponse.ok) throw new Error("낚시터 API 오류");
        const fishingData = await fishingResponse.json();
        showFishing(fishingData);
    }
    catch (error) {
        console.error("주변 정보 검색 오류:", error);
        addBotMessage("❌ 주변 정보를 불러오는 중 오류가 발생했습니다.");
    }
}

function showDanger(data) {
    if (!data.danger) {
        addBotMessage(`✅ <strong>주변 위험구역을 확인했습니다.</strong><br><br>현재 위치 기준 <strong>500m 이내</strong>에 등록된 연안사고 위험구역이 없습니다.<br><br>안전에 유의하여 낚시를 즐겨주세요. 🌊`);
        return;
    }
    let message = `🚨 <strong>주변 위험구역을 확인했습니다.</strong><br><br>현재 위치 500m 이내에 <strong>위험구역 ${data.danger_count}곳</strong>이 있습니다.<br><br>`;
    data.danger_zones.forEach(zone => {
        message += `📍 <strong>${zone.장소명}</strong><br>현재 위치에서 약 <strong>${zone.거리_m}m</strong><br>장소 형태: ${zone.장소형태 || "정보 없음"}<br><br>`;
    });
    addBotMessage(message);
}

function showFishing(data) {
    if (!data.fishing_spots || data.fishing_spots.length === 0) {
        addBotMessage(`🎣 <strong>주변 낚시터 검색 결과</strong><br><br>현재 위치 10km 이내에 등록된 낚시터가 없습니다.`);
        return;
    }
    let message = `🎣 <strong>주변 낚시터를 찾았습니다.</strong><br><br>현재 위치 10km 이내의 가까운 낚시터를 안내해 드릴게요.<br><br>`;
    data.fishing_spots.forEach((spot, index) => {
        message += `<strong>${index + 1}. ${spot.낚시터명}</strong><br>📍 거리: ${spot.거리_km}km<br>${spot.주소 || ""}<br><br>`;
    });
    addBotMessage(message);
}

// 위치 에러
function locationError(error) {
    let message = "❌ 위치 정보를 가져오는 중 오류가 발생했습니다.";
    if (error.code === 1) message = "❌ 위치 권한이 거부되었습니다.<br>브라우저 위치 권한을 허용해 주세요.";
    if (error.code === 2) message = "❌ 현재 위치를 확인할 수 없습니다.";
    if (error.code === 3) message = "❌ 위치 확인 시간이 초과되었습니다.<br>다시 시도해 주세요.";
    addBotMessage(message);
}

// =====================================================
// AI 챗봇 메시지 전송 (화면 출력 기능 개선)
// =====================================================
async function sendMessage() {
    const input = document.getElementById("messageInput");
    let message = input.value.trim();

    if (!message && !uploadedFile) return;
    if (!message && uploadedFile) message = "";

    // 업로드할 파일이 존재하면 채팅창 말풍선 내부 렌더링용 임시 주소 발급
    let localImageUrl = null;
    if (uploadedFile) {
        localImageUrl = URL.createObjectURL(uploadedFile);
    }

    // 메세지와 로컬 이미지 주소를 함께 넘겨 화면에 동시 출력
    addUserMessage(message, localImageUrl);
    input.value = "";
    loadSavedLocation();
    
    const loadingRow = addLoadingMessage();
    let imagePathOnServer = null;

    try {
        if (uploadedFile) {
            const formData = new FormData();
            formData.append("file", uploadedFile);

            const uploadResponse = await fetch("/api/upload-image", {
                method: "POST", body: formData
            });

            if (!uploadResponse.ok) throw new Error("이미지 서버 업로드 실패");

            const uploadData = await uploadResponse.json();
            if (uploadData.status === "success") {
                imagePathOnServer = uploadData.image_path; 
            } else {
                throw new Error(uploadData.message || "이미지 저장 실패");
            }
        }
    } catch (uploadError) {
        console.error("이미지 사전 처리 실패:", uploadError);
        if (loadingRow && loadingRow.isConnected) loadingRow.remove();
        addBotMessage("❌ 물고기 사진 업로드 중 오류가 생겼습니다.");
        clearSelectedImage();
        return;
    }

    clearSelectedImage();
    
    // 이미지가 업로드된 경우, 에이전트(LLM)가 확실하게 인지하도록 프롬프트를 조립하여 주입합니다.
    let finalMessage = message;
    if (imagePathOnServer) {
        finalMessage = `${message}\n\n[시스템 알림: 사용자가 물고기 사진을 성공적으로 첨부했습니다. 반드시 제공된 비전 모델(YOLO) 가중치를 이용해 서버 내부의 해당 사진을 분석하여 사용자가 올린 물고기 어종을 판별하고 결과를 안내하세요.]`;
    }

    await requestChat(finalMessage, loadingRow, false, imagePathOnServer);
}

function loadSavedLocation() {
    const savedLat = sessionStorage.getItem("currentLat");
    const savedLon = sessionStorage.getItem("currentLon");
    currentLat = savedLat !== null ? Number(savedLat) : null;
    currentLon = savedLon !== null ? Number(savedLon) : null;
}

// =====================================================
// Chat API 요청
// =====================================================
async function requestChat(message, loadingRow, isRetry, imagePath = null) {
    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: sessionId, 
                message: message, 
                lat: currentLat, 
                lon: currentLon, 
                image_path: imagePath 
            })
        });

        if (!response.ok) throw new Error(`챗봇 API 오류: ${response.status}`);
        const data = await response.json();

        if (data.status === "location_required" && !isRetry) {
            addBotMessage("📍 주변 정보를 확인하기 위해 현재 위치를 확인하고 있습니다...");
            try {
                const position = await getCurrentPositionAsync();
                currentLat = position.coords.latitude;
                currentLon = position.coords.longitude;
                sessionStorage.setItem("currentLat", currentLat);
                sessionStorage.setItem("currentLon", currentLon);

                await requestChat(message, loadingRow, true, imagePath);
                return;
            } catch (error) {
                if (loadingRow && loadingRow.isConnected) loadingRow.remove();
                locationError(error);
                return;
            }
        }

        if (loadingRow && loadingRow.isConnected) loadingRow.remove();
        
        // 💡 [수정]: 타이핑 효과 함수(addBotMessage) 내부에서 자체 포맷팅을 하므로 원본 데이터를 그대로 넘겨줍니다.
        addBotMessage(data.answer);

    } catch (error) {
        console.error("챗봇 오류:", error);
        if (loadingRow && loadingRow.isConnected) loadingRow.remove();
        addBotMessage("❌ AI 챗봇 응답을 불러오는 중 오류가 발생했습니다.");
    }
}

function getCurrentPositionAsync() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject({ code: 2, message: "현재 브라우저는 위치 정보를 지원하지 않습니다." });
            return;
        }
        navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true, timeout: 15000, maximumAge: 0
        });
    });
}

function handleEnter(event) {
    if (event.key === "Enter") sendMessage();
}

// =====================================================
// UI 렌더링 헬퍼 함수 (💡 실시간 타이핑 효과 적용)
// =====================================================
function addBotMessage(message) {
    const chatArea = document.getElementById("chatArea");
    const row = document.createElement("div");
    row.className = "message-row bot-row";
    row.innerHTML = `<div class="bot-icon">🤖</div><div class="message bot-message"></div>`;
    chatArea.appendChild(row);
    
    const messageContainer = row.querySelector(".bot-message");
    
    // 마크다운 형태의 줄바꿈 문자 처리를 위해 포맷팅 적용
    const formattedMessage = formatBotMessage(message);
    
    // HTML 내부 태그들(<strong>, <br> 등)이 쪼개져 출력되어 화면이 깨지는 현상을 막기 위한 가상 DOM 토큰화 작업
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = formattedMessage;
    
    const tokens = [];
    let i = 0;
    while (i < tempDiv.innerHTML.length) {
        if (tempDiv.innerHTML[i] === '<') {
            let tag = "";
            while (i < tempDiv.innerHTML.length && tempDiv.innerHTML[i] !== '>') {
                tag += tempDiv.innerHTML[i];
                i++;
            }
            tag += '>';
            i++;
            tokens.push(tag); // 태그는 통째로 하나의 토큰으로 묶어 한 번에 렌더링
        } else {
            tokens.push(tempDiv.innerHTML[i]); // 일반 글자는 한 글자씩 분할
            i++;
        }
    }

    let tokenIndex = 0;
    const typingSpeed = 20; // 💡 출력 속도 조절 (밀리초 단위, 작을수록 빨라짐)

    function typeWriter() {
        if (tokenIndex < tokens.length) {
            messageContainer.innerHTML += tokens[tokenIndex];
            tokenIndex++;
            scrollBottom();
            setTimeout(typeWriter, typingSpeed);
        }
    }
    
    typeWriter();
}

// 사용자가 보낸 이미지 표시 기능
function addUserMessage(message, imageUrl = null) {
    const chatArea = document.getElementById("chatArea");
    const row = document.createElement("div");
    row.className = "message-row user-row";
    
    let imageHtml = "";
    if (imageUrl) {
        imageHtml = `<img src="${imageUrl}" style="max-width: 200px; max-height: 200px; border-radius: 10px; margin-bottom: 8px; display: block; border: 1px solid #dee2e6;">`;
    }

    row.innerHTML = `<div class="message user-message">${imageHtml}${message}</div>`;
    chatArea.appendChild(row);
    scrollBottom();
}

function addLoadingMessage() {
    const chatArea = document.getElementById("chatArea");
    const row = document.createElement("div");
    row.className = "message-row bot-row";
    row.innerHTML = `<div class="bot-icon">🤖</div><div class="message bot-message">답변을 생성하고 있습니다...</div>`;
    chatArea.appendChild(row);
    scrollBottom();
    return row;
}

function formatBotMessage(message) {
    if (!message) return "AI 답변을 불러올 수 없습니다.";
    // 이미 <br> 태그가 적용되어 있는 경우가 아니라면 개행문자를 치환합니다.
    if (!message.includes("<br>")) {
        return message.replace(/\n/g, "<br>");
    }
    return message;
}

function scrollBottom() {
    const chatArea = document.getElementById("chatArea");
    chatArea.scrollTop = chatArea.scrollHeight;
}