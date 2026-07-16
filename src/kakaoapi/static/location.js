// =====================================================
// 사용자 세션 / 현재 위치
// =====================================================

const sessionId = crypto.randomUUID();


// sessionStorage에 저장된 위치 불러오기

let currentLat = sessionStorage.getItem("currentLat");

let currentLon = sessionStorage.getItem("currentLon");


// 저장된 문자열을 숫자로 변환

if (currentLat !== null) {

    currentLat = Number(currentLat);

}


if (currentLon !== null) {

    currentLon = Number(currentLon);

}


console.log(
    "저장된 사용자 위치:",
    currentLat,
    currentLon
);

// =====================================================
// 시작 화면 → 챗봇
// =====================================================

function startChat() {

    document.getElementById("startScreen").style.display = "none";

    document.getElementById("chatScreen").style.display = "flex";
}


// =====================================================
// 뒤로가기
// =====================================================

function goBack() {

    document.getElementById("chatScreen").style.display = "none";

    document.getElementById("startScreen").style.display = "flex";
}


// =====================================================
// 사용자 위치 요청
// =====================================================

function getLocation() {

    if (!navigator.geolocation) {

        addBotMessage(
            "❌ 현재 브라우저는 위치 정보를 지원하지 않습니다."
        );

        return;
    }


    addBotMessage(
        "📍 현재 위치를 확인하고 있습니다..."
    );


    navigator.geolocation.getCurrentPosition(

        searchNearby,

        locationError,

        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        }

    );
}


// =====================================================
// 위치 획득 성공
// =====================================================

async function searchNearby(position) {

    const lat = position.coords.latitude;

    const lon = position.coords.longitude;


    // =================================================
    // 현재 사용자 위치 저장
    // =================================================

    currentLat = lat;

    currentLon = lon;


    // 브라우저 세션에 위치 저장

    sessionStorage.setItem(
        "currentLat",
        currentLat
    );

    sessionStorage.setItem(
        "currentLon",
        currentLon
    );


    console.log(
        "현재 위치 저장 완료:",
        currentLat,
        currentLon
    );


    try {

        // =================================================
        // 위험구역 API
        // =================================================

        const dangerResponse = await fetch(

            "/danger/nearby",

            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    lat: lat,
                    lon: lon
                })
            }

        );


        if (!dangerResponse.ok) {

            throw new Error(
                "위험구역 API 오류"
            );
        }


        const dangerData =
            await dangerResponse.json();


        showDanger(dangerData);


        // =================================================
        // 낚시터 API
        // =================================================

        const fishingResponse = await fetch(

            "/fishing/nearby",

            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    lat: lat,
                    lon: lon
                })
            }

        );


        if (!fishingResponse.ok) {

            throw new Error(
                "낚시터 API 오류"
            );
        }


        const fishingData =
            await fishingResponse.json();


        showFishing(fishingData);

    }

    catch (error) {

        console.error(
            "주변 정보 검색 오류:",
            error
        );


        addBotMessage(
            "❌ 주변 정보를 불러오는 중 오류가 발생했습니다."
        );

    }
}


// =====================================================
// 위험구역 결과
// =====================================================

function showDanger(data) {

    if (!data.danger) {

        addBotMessage(`

            ✅ <strong>주변 위험구역을 확인했습니다.</strong>

            <br><br>

            현재 위치 기준
            <strong>500m 이내</strong>에 등록된
            연안사고 위험구역이 없습니다.

            <br><br>

            안전에 유의하여 낚시를 즐겨주세요. 🌊

        `);

        return;
    }


    let message = `

        🚨 <strong>주변 위험구역을 확인했습니다.</strong>

        <br><br>

        현재 위치 500m 이내에

        <strong>
            위험구역 ${data.danger_count}곳
        </strong>

        이 있습니다.

        <br><br>

    `;


    data.danger_zones.forEach(zone => {

        message += `

            📍 <strong>${zone.장소명}</strong>

            <br>

            현재 위치에서 약
            <strong>${zone.거리_m}m</strong>

            <br>

            장소 형태:
            ${zone.장소형태 || "정보 없음"}

            <br><br>

        `;

    });


    addBotMessage(message);
}


// =====================================================
// 낚시터 결과
// =====================================================

function showFishing(data) {

    if (
        !data.fishing_spots ||
        data.fishing_spots.length === 0
    ) {

        addBotMessage(`

            🎣 <strong>주변 낚시터 검색 결과</strong>

            <br><br>

            현재 위치 10km 이내에
            등록된 낚시터가 없습니다.

        `);

        return;
    }


    let message = `

        🎣 <strong>주변 낚시터를 찾았습니다.</strong>

        <br><br>

        현재 위치 10km 이내의
        가까운 낚시터를 안내해 드릴게요.

        <br><br>

    `;


    data.fishing_spots.forEach(

        (spot, index) => {

            message += `

                <strong>
                    ${index + 1}. ${spot.낚시터명}
                </strong>

                <br>

                📍 거리:
                ${spot.거리_km}km

                <br>

                ${spot.주소 || ""}

                <br><br>

            `;

        }

    );


    addBotMessage(message);
}


// =====================================================
// 위치 오류
// =====================================================

function locationError(error) {

    let message;


    switch (error.code) {

        case 1:

            message =
                "❌ 위치 권한이 거부되었습니다.<br>브라우저 위치 권한을 허용해 주세요.";

            break;


        case 2:

            message =
                "❌ 현재 위치를 확인할 수 없습니다.";

            break;


        case 3:

            message =
                "❌ 위치 확인 시간이 초과되었습니다.<br>다시 시도해 주세요.";

            break;


        default:

            message =
                "❌ 위치 정보를 가져오는 중 오류가 발생했습니다.";

    }


    addBotMessage(message);


    console.error(
        "위치 오류:",
        error
    );
}


// =====================================================
// AI 챗봇 메시지 전송
// =====================================================

async function sendMessage() {

    const input =
        document.getElementById("messageInput");


    const message =
        input.value.trim();


    if (!message) {

        return;

    }


    // =================================================
    // 사용자 메시지 출력
    // =================================================

    addUserMessage(message);


    // =================================================
    // 입력창 초기화
    // =================================================

    input.value = "";


    // =================================================
    // 저장된 위치 불러오기
    // =================================================

    loadSavedLocation();


    // =================================================
    // AI 응답 대기 메시지
    // =================================================

    const loadingRow =
        addLoadingMessage();


    // =================================================
    // Chat API 요청
    // =================================================

    await requestChat(
        message,
        loadingRow,
        false
    );

}


// =====================================================
// 저장된 위치 불러오기
// =====================================================

function loadSavedLocation() {

    const savedLat =
        sessionStorage.getItem(
            "currentLat"
        );


    const savedLon =
        sessionStorage.getItem(
            "currentLon"
        );


    currentLat =
        savedLat !== null
            ? Number(savedLat)
            : null;


    currentLon =
        savedLon !== null
            ? Number(savedLon)
            : null;


    console.log(
        "저장된 위치:",
        currentLat,
        currentLon
    );

}


// =====================================================
// Chat API 요청
// =====================================================

async function requestChat(
    message,
    loadingRow,
    isRetry
) {

    try {

        console.log(
            "챗봇 전달 위치:",
            currentLat,
            currentLon
        );


        const response = await fetch(

            "/chat",

            {

                method: "POST",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify({

                    session_id: sessionId,

                    message: message,

                    lat: currentLat,

                    lon: currentLon,

                    image_path: null

                })

            }

        );


        if (!response.ok) {

            throw new Error(
                `챗봇 API 오류: ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "챗봇 응답:",
            data
        );


        // =================================================
        // 현재 위치가 필요한 경우
        // =================================================

        if (
            data.status === "location_required" &&
            !isRetry
        ) {

            addBotMessage(

                "📍 주변 정보를 확인하기 위해 현재 위치를 확인하고 있습니다..."

            );


            try {

                const position =
                    await getCurrentPositionAsync();


                currentLat =
                    position.coords.latitude;


                currentLon =
                    position.coords.longitude;


                // =========================================
                // 현재 위치 세션 저장
                // =========================================

                sessionStorage.setItem(
                    "currentLat",
                    currentLat
                );


                sessionStorage.setItem(
                    "currentLon",
                    currentLon
                );


                console.log(
                    "현재 위치 저장 완료:",
                    currentLat,
                    currentLon
                );


                // =========================================
                // 위치 포함하여 같은 질문 재전송
                // =========================================

                await requestChat(
                    message,
                    loadingRow,
                    true
                );


                return;

            }

            catch (error) {

                console.error(
                    "위치 조회 오류:",
                    error
                );


                if (
                    loadingRow &&
                    loadingRow.isConnected
                ) {

                    loadingRow.remove();

                }


                locationError(
                    error
                );


                return;

            }

        }


        // =================================================
        // 로딩 메시지 삭제
        // =================================================

        if (
            loadingRow &&
            loadingRow.isConnected
        ) {

            loadingRow.remove();

        }


        // =================================================
        // AI 답변 출력
        // =================================================

        addBotMessage(

            formatBotMessage(
                data.answer
            )

        );


        // =================================================
        // 개발 확인용 로그
        // =================================================

        console.log(
            "질문 분류:",
            data.category
        );


        console.log(
            "AI 답변:",
            data.answer
        );

    }

    catch (error) {

        console.error(
            "챗봇 오류:",
            error
        );


        // =================================================
        // 로딩 메시지 삭제
        // =================================================

        if (
            loadingRow &&
            loadingRow.isConnected
        ) {

            loadingRow.remove();

        }


        addBotMessage(

            "❌ AI 챗봇 응답을 불러오는 중 오류가 발생했습니다."

        );

    }

}


// =====================================================
// GPS Promise 처리
// =====================================================

function getCurrentPositionAsync() {

    return new Promise(

        (resolve, reject) => {

            if (!navigator.geolocation) {

                reject({

                    code: 2,

                    message:
                        "현재 브라우저는 위치 정보를 지원하지 않습니다."

                });


                return;

            }


            navigator.geolocation.getCurrentPosition(

                resolve,

                reject,

                {

                    enableHighAccuracy: true,

                    timeout: 15000,

                    maximumAge: 0

                }

            );

        }

    );

}


// =====================================================
// Enter 전송
// =====================================================

function handleEnter(event) {

    if (event.key === "Enter") {

        sendMessage();

    }

}


// =====================================================
// Enter 전송
// =====================================================

function handleEnter(event) {

    if (event.key === "Enter") {

        sendMessage();

    }
}


// =====================================================
// 봇 말풍선 생성
// =====================================================

function addBotMessage(message) {

    const chatArea =
        document.getElementById("chatArea");


    const row =
        document.createElement("div");


    row.className =
        "message-row bot-row";


    row.innerHTML = `

        <div class="bot-icon">
            🤖
        </div>

        <div class="message bot-message">

            ${message}

        </div>

    `;


    chatArea.appendChild(row);


    scrollBottom();
}


// =====================================================
// 사용자 말풍선 생성
// =====================================================

function addUserMessage(message) {

    const chatArea =
        document.getElementById("chatArea");


    const row =
        document.createElement("div");


    row.className =
        "message-row user-row";


    const messageDiv =
        document.createElement("div");


    messageDiv.className =
        "message user-message";


    messageDiv.textContent =
        message;


    row.appendChild(messageDiv);


    chatArea.appendChild(row);


    scrollBottom();
}


// =====================================================
// AI 응답 대기 메시지
// =====================================================

function addLoadingMessage() {

    const chatArea =
        document.getElementById("chatArea");


    const row =
        document.createElement("div");


    row.className =
        "message-row bot-row";


    row.innerHTML = `

        <div class="bot-icon">
            🤖
        </div>

        <div class="message bot-message">

            답변을 생성하고 있습니다...

        </div>

    `;


    chatArea.appendChild(row);


    scrollBottom();


    return row;
}


// =====================================================
// AI 답변 형식 처리
// =====================================================

function formatBotMessage(message) {

    if (!message) {

        return "AI 답변을 불러올 수 없습니다.";

    }


    return message
        .replace(/\n/g, "<br>");

}


// =====================================================
// 자동 스크롤
// =====================================================

function scrollBottom() {

    const chatArea =
        document.getElementById("chatArea");


    chatArea.scrollTop =
        chatArea.scrollHeight;
}