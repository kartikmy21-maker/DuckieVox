function runTest() {
    const command = "create a folder";
    
    fetch('/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json())
    .then(data => {
        const chatBox = document.getElementById('chat-window'); // ✅ FIXED

        chatBox.innerHTML += `<div class="bubble user-bubble">${command}</div>`;
        chatBox.innerHTML += `<div class="bubble duckie-bubble">🦆 ${data.message}</div>`;

        chatBox.scrollTop = chatBox.scrollHeight; // auto scroll
    });

    // This checks every 1000ms (1 second) if the wake word was heard
    setInterval(function() {
        fetch('/check-wake-word')
        .then(res => res.json())
        .then(data => {
            if (data.awake) {
                // Trigger the visual UI and start the full command logic
                startListening(); 
            }
        });
    }, 1000);
}