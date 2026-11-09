
document.addEventListener("DOMContentLoaded", function () {
    const chatContainer = document.getElementById("chat-container");
    const messagesContainer = document.getElementById("messages");
    const messageForm = document.getElementById("message-form");
    const messageInput = document.getElementById("message-input");
    const chatStatus = document.getElementById("chat-status");

    if (!chatContainer || !messagesContainer || !messageForm) {
        return;
    }

    const recipientId = Number(chatContainer.dataset.userId);
    window.currentUserId = Number(chatContainer.dataset.currentUserId);

    // Connect to the Flask-SocketIO server
    const socket = io();

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function displayMessage(data) {
        const wrapper = document.createElement("div");
        wrapper.className = "mb-3";

        const alignment = document.createElement("div");
        alignment.className =
            "d-flex " +
            (Number(data.sender_id) === Number(window.currentUserId)
                ? "justify-content-end"
                : "justify-content-start");

        const bubble = document.createElement("div");
        bubble.style.maxWidth = "75%";
        bubble.style.padding = "10px 14px";
        bubble.style.borderRadius = "12px";
        bubble.style.background =
            Number(data.sender_id) === Number(window.currentUserId)
                ? "#dbeafe"
                : "#ffffff";

        const messageText = document.createElement("div");
        messageText.style.whiteSpace = "pre-wrap";
        messageText.style.overflowWrap = "anywhere";

        // textContent prevents HTML/script injection
        messageText.textContent = data.message;

        const timestamp = document.createElement("small");
        timestamp.className = "text-muted";
        timestamp.textContent = data.created_at;

        bubble.appendChild(messageText);
        bubble.appendChild(timestamp);
        alignment.appendChild(bubble);
        wrapper.appendChild(alignment);
        messagesContainer.appendChild(wrapper);

        scrollToBottom();
    }

    socket.on("connect", function () {
        chatStatus.textContent = "Connected";

        socket.emit("join_chat", {
            user_id: recipientId
        });
    });

    socket.on("disconnect", function () {
        chatStatus.textContent = "Disconnected. Reconnecting...";
    });

    socket.on("connect_error", function () {
        chatStatus.textContent = "Connection error. Please refresh the page.";
    });

    socket.on("receive_message", function (data) {
        displayMessage(data);
    });

    messageForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const message = messageInput.value.trim();

        if (!message) {
            return;
        }

        socket.emit("send_message", {
            recipient_id: recipientId,
            message: message
        });

        messageInput.value = "";
        messageInput.focus();
    });

    scrollToBottom();
});
