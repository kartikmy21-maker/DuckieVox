// 🧪 TEST FUNCTION (optional)
function runTest() {
    const command = "create a folder";

    const chatBox = document.getElementById('chat-window');

    // show user input
    chatBox.innerHTML += `<div class="bubble user-bubble">${command}</div>`;

    fetch('/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json())
    .then(data => {
        chatBox.innerHTML += `<div class="bubble duckie-bubble">🦆 ${data.message}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    });
}


// 🎤 VOICE FUNCTION (MAIN FEATURE)
async function startVoice() {
    const win = document.getElementById('chat-window');

    win.innerHTML += `<div class="bubble duckie-bubble">🎤 Listening...</div>`;
    win.scrollTop = win.scrollHeight;

    try {
        const res = await fetch('/voice', {
            method: 'POST'
        });

        const data = await res.json();

        if (data.status === "success") {
            win.innerHTML += `<div class="bubble user-bubble">${data.command}</div>`;
            win.innerHTML += `<div class="bubble duckie-bubble">🦆 ${data.message}</div>`;
        } else {
            win.innerHTML += `<div class="bubble duckie-bubble">❌ ${data.message}</div>`;
        }

    } catch (err) {
        win.innerHTML += `<div class="bubble duckie-bubble">❌ Voice error</div>`;
    }

    win.scrollTop = win.scrollHeight;
}


// 🔁 OPTIONAL: WAKE WORD CHECK (ADVANCED - USE LATER)
function startWakeWordListener() {
    setInterval(function () {
        fetch('/check-wake-word')
            .then(res => res.json())
            .then(data => {
                if (data.awake) {
                    startVoice();
                }
            });
    }, 1000);
}