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


    try {

        // 위험구역 API

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


        // 낚시터 API

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

        console.error(error);


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
// 사용자 메시지 전송
// =====================================================

function sendMessage() {

    const input =
        document.getElementById("messageInput");


    const message =
        input.value.trim();


    if (!message) {

        return;
    }


    addUserMessage(message);


    input.value = "";


    setTimeout(() => {

        addBotMessage(`

            🤖 AI 챗봇 기능을 준비 중입니다.

            <br><br>

            현재는 위치 기반
            위험구역 확인과
            주변 낚시터 추천 기능을
            이용할 수 있습니다.

        `);

    }, 500);
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
// 자동 스크롤
// =====================================================

function scrollBottom() {

    const chatArea =
        document.getElementById("chatArea");


    chatArea.scrollTop =
        chatArea.scrollHeight;
}