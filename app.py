from flask import Flask, request, jsonify, render_template_string
import requests
import base64
import os

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"

CHAT_MODEL = "llama3.2:3b"
VISION_MODEL = "qwen2.5vl:3b"

SYSTEM_PROMPT = """
You are OVI, a helpful AI assistant.

Your purpose is to help people with real-life problems.

Rules:
- Give simple and practical answers.
- Keep answers clear and easy to understand.
- If the user speaks Telugu, reply in Telugu.
- If the user speaks Hindi, reply in Hindi.
- Otherwise reply in English.
- Be friendly and respectful.
- If an image is provided, carefully understand it and explain what is visible.
- If a document is provided, answer using the document content.
"""

HTML = """
<!DOCTYPE html>
<html>
<head>

<title>OVI - AI Assistant</title>

<style>

* {
    box-sizing: border-box;
}

:root {
    --bg: #ffffff;
    --sidebar: #f7f7f8;
    --text: #111111;
    --secondary: #777777;
    --border: #e5e5e5;
    --bubble: #f1f1f1;
    --user: #111111;
    --userText: #ffffff;
    --input: #ffffff;
    --hover: #e9e9ea;
    --accent: #111111;
}

body.dark {
    --bg: #18181b;
    --sidebar: #202023;
    --text: #f5f5f5;
    --secondary: #aaaaaa;
    --border: #353539;
    --bubble: #29292e;
    --user: #f5f5f5;
    --userText: #111111;
    --input: #242428;
    --hover: #303035;
    --accent: #ffffff;
}

body.purple {
    --bg: #faf8ff;
    --sidebar: #f1edff;
    --text: #181225;
    --secondary: #756b88;
    --border: #ddd4f5;
    --bubble: #eee8ff;
    --user: #6d4aff;
    --userText: #ffffff;
    --input: #ffffff;
    --hover: #e6ddff;
    --accent: #6d4aff;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    overflow: hidden;
    transition: background 0.2s, color 0.2s;
}

.app {
    display: flex;
    height: 100vh;
}

/* SIDEBAR */

.sidebar {
    width: 270px;
    background: var(--sidebar);
    border-right: 1px solid var(--border);
    padding: 18px;
    display: flex;
    flex-direction: column;
}

.logo {
    font-size: 25px;
    font-weight: bold;
    margin-bottom: 20px;
    padding-left: 5px;
}

.new-chat {
    border: 1px solid var(--border);
    background: var(--input);
    color: var(--text);
    border-radius: 10px;
    padding: 11px;
    font-size: 14px;
    cursor: pointer;
    margin-bottom: 25px;
}

.new-chat:hover {
    background: var(--hover);
}

.history-title {
    font-size: 12px;
    color: var(--secondary);
    font-weight: bold;
    margin: 0 5px 10px;
}

.history {
    overflow-y: auto;
    flex: 1;
}

.history-item {
    position: relative;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    margin-bottom: 4px;
    user-select: none;
}

.history-item:hover {
    background: var(--hover);
}

.history-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* DELETE */

.delete-menu {
    display: none;
    position: absolute;
    left: 10px;
    top: 38px;
    background: var(--input);
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    z-index: 100;
    overflow: hidden;
}

.delete-menu button {
    border: none;
    background: var(--input);
    padding: 9px 15px;
    cursor: pointer;
    font-size: 13px;
    color: #d11a2a;
}

.delete-menu button:hover {
    background: var(--hover);
}

/* MAIN */

.main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.topbar {
    height: 60px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 22px;
}

.top-title {
    font-size: 17px;
    font-weight: 600;
}

.settings {
    border: none;
    background: transparent;
    color: var(--text);
    font-size: 20px;
    cursor: pointer;
}

/* CHAT */

.chat-area {
    flex: 1;
    overflow-y: auto;
    padding: 35px 10%;
}

.welcome {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.welcome h1 {
    font-size: 30px;
    margin-bottom: 8px;
}

.welcome p {
    color: var(--secondary);
}

.message-row {
    display: flex;
    margin-bottom: 18px;
    width: 100%;
}

.user-row {
    justify-content: flex-end;
}

.bot-row {
    justify-content: flex-start;
}

.message {
    max-width: 70%;
    padding: 11px 15px;
    border-radius: 15px;
    font-size: 15px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.message.user {
    background: var(--user);
    color: var(--userText);
    border-bottom-right-radius: 4px;
}

.message.bot {
    background: var(--bubble);
    color: var(--text);
    border-bottom-left-radius: 4px;
}

/* IMAGE */

.chat-image {
    max-width: 300px;
    max-height: 300px;
    border-radius: 12px;
    display: block;
    margin-bottom: 8px;
}

/* THINKING */

.thinking {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 12px 15px;
    background: var(--bubble);
    border-radius: 15px;
    border-bottom-left-radius: 4px;
    width: fit-content;
}

.thinking span {
    width: 6px;
    height: 6px;
    background: var(--secondary);
    border-radius: 50%;
    display: block;
    animation: thinking 1.2s infinite;
}

.thinking span:nth-child(2) {
    animation-delay: .2s;
}

.thinking span:nth-child(3) {
    animation-delay: .4s;
}

@keyframes thinking {

    0%,60%,100% {
        opacity: .3;
        transform: translateY(0);
    }

    30% {
        opacity: 1;
        transform: translateY(-3px);
    }
}

/* INPUT */

.input-area {
    padding: 15px 10% 20px;
    border-top: 1px solid var(--border);
}

.input-box {
    display: flex;
    align-items: flex-end;
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 8px 10px;
    background: var(--input);
}

textarea {
    flex: 1;
    border: none;
    outline: none;
    resize: none;
    font-family: Arial;
    font-size: 15px;
    min-height: 35px;
    max-height: 120px;
    padding: 8px;
    background: transparent;
    color: var(--text);
}

textarea::placeholder {
    color: var(--secondary);
}

/* ATTACH */

.attach {
    position: relative;
}

.attach-button {
    border: none;
    background: transparent;
    color: var(--text);
    font-size: 21px;
    width: 38px;
    height: 38px;
    cursor: pointer;
}

.attach-menu {
    display: none;
    position: absolute;
    bottom: 48px;
    left: 0;
    background: var(--input);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: 0 5px 20px rgba(0,0,0,.15);
    overflow: hidden;
    z-index: 200;
}

.attach-menu button {
    display: block;
    width: 180px;
    padding: 12px;
    border: none;
    background: var(--input);
    color: var(--text);
    text-align: left;
    cursor: pointer;
}

.attach-menu button:hover {
    background: var(--hover);
}

/* PREVIEW */

.preview {
    display: none;
    margin-bottom: 8px;
    position: relative;
}

.preview img {
    width: 80px;
    height: 80px;
    object-fit: cover;
    border-radius: 10px;
}

.remove-file {
    position: absolute;
    top: -5px;
    left: 70px;
    border: none;
    background: #222;
    color: white;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    cursor: pointer;
}

/* SEND */

.send {
    border: none;
    background: var(--accent);
    color: var(--userText);
    width: 38px;
    height: 38px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 17px;
}

.send:disabled {
    opacity: .5;
}

/* MODAL */

.modal {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.4);
    align-items: center;
    justify-content: center;
    z-index: 500;
}

.modal-box {
    width: 360px;
    background: var(--input);
    color: var(--text);
    border-radius: 15px;
    padding: 25px;
    box-shadow: 0 10px 30px rgba(0,0,0,.25);
}

.close {
    float: right;
    border: none;
    background: transparent;
    color: var(--text);
    font-size: 22px;
    cursor: pointer;
}

.theme-title {
    margin-top: 25px;
    font-size: 14px;
    font-weight: bold;
}

.theme-buttons {
    display: flex;
    gap: 8px;
    margin-top: 10px;
}

.theme-buttons button {
    flex: 1;
    border: 1px solid var(--border);
    background: var(--input);
    color: var(--text);
    padding: 10px 5px;
    border-radius: 8px;
    cursor: pointer;
}

.theme-buttons button:hover {
    background: var(--hover);
}

/* MOBILE */

@media(max-width:700px) {

    .sidebar {
        width: 210px;
        padding: 12px;
    }

    .chat-area {
        padding: 25px 15px;
    }

    .input-area {
        padding: 10px 15px 15px;
    }

    .message {
        max-width: 85%;
    }

    .welcome h1 {
        font-size: 24px;
    }
}

</style>

</head>

<body>

<div class="app">

<aside class="sidebar">

    <div class="logo">
        OVI
    </div>

    <button class="new-chat" onclick="newChat()">
        + New Chat
    </button>

    <div class="history-title">
        CHAT HISTORY
    </div>

    <div class="history" id="historyList"></div>

</aside>


<main class="main">

<div class="topbar">

    <div class="top-title">
        OVI
    </div>

    <button class="settings" onclick="openSettings()">
        ⚙️
    </button>

</div>


<div class="chat-area" id="chatBox">

    <div class="welcome" id="welcome">

        <h1>Hello! I'm OVI 👋</h1>

        <p>
            AI that helps with real life.
        </p>

    </div>

</div>


<div class="input-area">

    <div id="preview" class="preview">

        <img id="previewImage">

        <button
            class="remove-file"
            onclick="removeAttachment()">
            ×
        </button>

    </div>


    <div class="input-box">

        <div class="attach">

            <button
                class="attach-button"
                onclick="toggleAttachMenu()">
                +
            </button>

            <div
                class="attach-menu"
                id="attachMenu">

                <button onclick="openCamera()">
                    📷 Camera
                </button>

                <button onclick="openPhoto()">
                    🖼️ Photo
                </button>

                <button onclick="openFile()">
                    📎 File
                </button>

            </div>

        </div>


        <textarea
            id="messageInput"
            placeholder="Message OVI..."
            rows="1"
            onkeydown="handleKey(event)">
        </textarea>


        <button
            class="send"
            id="sendButton"
            onclick="sendMessage()">
            ➤
        </button>

    </div>

</div>

</main>

</div>


<!-- CAMERA -->

<input
    type="file"
    id="cameraInput"
    accept="image/*"
    capture="environment"
    style="display:none"
    onchange="handleFile(this.files[0])">


<!-- PHOTO -->

<input
    type="file"
    id="photoInput"
    accept="image/*"
    style="display:none"
    onchange="handleFile(this.files[0])">


<!-- FILE -->

<input
    type="file"
    id="fileInput"
    accept=".pdf,.txt,.md,.doc,.docx"
    style="display:none"
    onchange="handleFile(this.files[0])">


<!-- SETTINGS -->

<div class="modal" id="settingsModal">

<div class="modal-box">

<button class="close" onclick="closeSettings()">
×
</button>

<h2>Settings</h2>

<p>
OVI is your AI assistant for real-life problems.
</p>

<div class="theme-title">
Theme
</div>

<div class="theme-buttons">

<button onclick="setTheme('light')">
☀️ Light
</button>

<button onclick="setTheme('dark')">
🌙 Dark
</button>

<button onclick="setTheme('purple')">
💜 Purple
</button>

</div>

</div>

</div>


<script>

let chats =
    JSON.parse(localStorage.getItem("oviChats")) || [];

let currentChatId = null;

let longPressTimer = null;

let selectedFile = null;


/* THEME */

function setTheme(theme) {

    document.body.classList.remove(
        "dark",
        "purple"
    );

    if (theme === "dark") {

        document.body.classList.add("dark");

    }

    if (theme === "purple") {

        document.body.classList.add("purple");

    }

    localStorage.setItem(
        "oviTheme",
        theme
    );

}


const savedTheme =
    localStorage.getItem("oviTheme") || "light";

setTheme(savedTheme);


/* CHAT STORAGE */

function saveChats() {

    localStorage.setItem(
        "oviChats",
        JSON.stringify(chats)
    );

}


/* CREATE CHAT */

function createChat() {

    const chat = {

        id: Date.now(),

        title: "New Chat",

        messages: []

    };

    chats.unshift(chat);

    currentChatId = chat.id;

    saveChats();

    renderHistory();

}


/* HISTORY */

function renderHistory() {

    const historyList =
        document.getElementById(
            "historyList"
        );

    historyList.innerHTML = "";


    chats.forEach(chat => {

        const item =
            document.createElement("div");

        item.className =
            "history-item";


        const name =
            document.createElement("div");

        name.className =
            "history-name";

        name.textContent =
            chat.title;


        const menu =
            document.createElement("div");

        menu.className =
            "delete-menu";


        const deleteButton =
            document.createElement("button");

        deleteButton.textContent =
            "Delete";


        deleteButton.onclick =
            function(event) {

                event.stopPropagation();

                deleteChat(chat.id);

            };


        menu.appendChild(deleteButton);

        item.appendChild(name);

        item.appendChild(menu);


        item.onclick =
            function() {

                closeAllMenus();

                openChat(chat.id);

            };


        item.oncontextmenu =
            function(event) {

                event.preventDefault();

                closeAllMenus();

                menu.style.display =
                    "block";

            };


        item.addEventListener(
            "touchstart",
            function() {

                longPressTimer =
                    setTimeout(
                        function() {

                            closeAllMenus();

                            menu.style.display =
                                "block";

                        },
                        600
                    );

            }
        );


        item.addEventListener(
            "touchend",
            function() {

                clearTimeout(
                    longPressTimer
                );

            }
        );


        item.addEventListener(
            "touchmove",
            function() {

                clearTimeout(
                    longPressTimer
                );

            }
        );


        historyList.appendChild(item);

    });

}


/* OPEN CHAT */

function openChat(id) {

    const chat =
        chats.find(
            c => c.id === id
        );

    if (!chat) return;

    currentChatId = id;

    const chatBox =
        document.getElementById(
            "chatBox"
        );

    chatBox.innerHTML = "";


    if (chat.messages.length === 0) {

        showWelcome();

        return;

    }


    chat.messages.forEach(message => {

        addMessage(
            message.text,
            message.type,
            message.image
        );

    });

}


/* DELETE */

function deleteChat(id) {

    chats =
        chats.filter(
            chat => chat.id !== id
        );

    saveChats();

    renderHistory();


    if (currentChatId === id) {

        currentChatId = null;

        showWelcome();

    }

}


/* WELCOME */

function showWelcome() {

    document.getElementById(
        "chatBox"
    ).innerHTML = `

        <div class="welcome" id="welcome">

            <h1>Hello! I'm OVI 👋</h1>

            <p>
                AI that helps with real life.
            </p>

        </div>

    `;

}


/* ADD MESSAGE */

function addMessage(
    text,
    type,
    image = null
) {

    const chatBox =
        document.getElementById(
            "chatBox"
        );


    const welcome =
        document.getElementById(
            "welcome"
        );

    if (welcome) {

        welcome.remove();

    }


    const row =
        document.createElement("div");

    row.className =
        type === "user"
        ? "message-row user-row"
        : "message-row bot-row";


    const bubble =
        document.createElement("div");

    bubble.className =
        "message " + type;


    if (image) {

        const img =
            document.createElement("img");

        img.src = image;

        img.className =
            "chat-image";

        bubble.appendChild(img);

    }


    if (text) {

        const textNode =
            document.createElement("div");

        textNode.textContent =
            text;

        bubble.appendChild(textNode);

    }


    row.appendChild(bubble);

    chatBox.appendChild(row);

    chatBox.scrollTop =
        chatBox.scrollHeight;

}


/* THINKING */

function showThinking() {

    const chatBox =
        document.getElementById(
            "chatBox"
        );


    const row =
        document.createElement("div");

    row.className =
        "message-row bot-row";

    row.id =
        "thinkingRow";


    const bubble =
        document.createElement("div");

    bubble.className =
        "thinking";


    bubble.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;


    row.appendChild(bubble);

    chatBox.appendChild(row);

    chatBox.scrollTop =
        chatBox.scrollHeight;

}


function removeThinking() {

    const thinking =
        document.getElementById(
            "thinkingRow"
        );

    if (thinking) {

        thinking.remove();

    }

}


/* SAVE MESSAGE */

function saveMessage(
    text,
    type,
    image = null
) {

    if (!currentChatId) {

        createChat();

    }


    const chat =
        chats.find(
            c => c.id === currentChatId
        );

    if (!chat) return;


    chat.messages.push({

        text: text,

        type: type,

        image: image

    });


    if (
        type === "user" &&
        chat.title === "New Chat"
    ) {

        chat.title =
            text
                ? text.substring(0, 30)
                : "Image Chat";

    }


    saveChats();

    renderHistory();

}


/* ATTACH MENU */

function toggleAttachMenu() {

    const menu =
        document.getElementById(
            "attachMenu"
        );

    menu.style.display =
        menu.style.display === "block"
        ? "none"
        : "block";

}


/* CAMERA */

function openCamera() {

    document.getElementById(
        "attachMenu"
    ).style.display = "none";

    document.getElementById(
        "cameraInput"
    ).click();

}


/* PHOTO */

function openPhoto() {

    document.getElementById(
        "attachMenu"
    ).style.display = "none";

    document.getElementById(
        "photoInput"
    ).click();

}


/* FILE */

function openFile() {

    document.getElementById(
        "attachMenu"
    ).style.display = "none";

    document.getElementById(
        "fileInput"
    ).click();

}


/* FILE SELECTED */

function handleFile(file) {

    if (!file) return;

    selectedFile = file;


    if (
        file.type.startsWith("image/")
    ) {

        const reader =
            new FileReader();


        reader.onload =
            function(event) {

                document.getElementById(
                    "previewImage"
                ).src =
                    event.target.result;

                document.getElementById(
                    "preview"
                ).style.display =
                    "block";

            };


        reader.readAsDataURL(file);

    }

}


/* REMOVE FILE */

function removeAttachment() {

    selectedFile = null;

    document.getElementById(
        "preview"
    ).style.display =
        "none";

    document.getElementById(
        "previewImage"
    ).src = "";

}


/* FILE TO BASE64 */

function fileToBase64(file) {

    return new Promise(
        (resolve, reject) => {

            const reader =
                new FileReader();

            reader.onload =
                () => resolve(
                    reader.result.split(",")[1]
                );

            reader.onerror =
                reject;

            reader.readAsDataURL(file);

        }
    );

}


/* SEND */

async function sendMessage() {

    const input =
        document.getElementById(
            "messageInput"
        );

    const button =
        document.getElementById(
            "sendButton"
        );


    const message =
        input.value.trim();


    if (!message && !selectedFile) {

        return;

    }


    if (!currentChatId) {

        createChat();

    }


    let imagePreview = null;


    if (
        selectedFile &&
        selectedFile.type.startsWith("image/")
    ) {

        imagePreview =
            await fileToBase64(
                selectedFile
            );

        imagePreview =
            "data:" +
            selectedFile.type +
            ";base64," +
            imagePreview;

    }


    /* USER */

    addMessage(
        message ||
        selectedFile.name,
        "user",
        imagePreview
    );


    saveMessage(
        message ||
        selectedFile.name,
        "user",
        imagePreview
    );


    input.value = "";

    button.disabled = true;

    button.textContent = "⏳";


    showThinking();


    try {

        let response;


        if (selectedFile) {

            const formData =
                new FormData();

            formData.append(
                "message",
                message
            );

            formData.append(
                "file",
                selectedFile
            );


            response =
                await fetch(
                    "/upload",
                    {
                        method: "POST",
                        body: formData
                    }
                );

        } else {

            response =
                await fetch(
                    "/chat",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                message:
                                    message
                            })
                    }
                );

        }


        const data =
            await response.json();


        removeThinking();


        const reply =
            data.reply ||
            "Sorry, I couldn't generate a response.";


        addMessage(
            reply,
            "bot"
        );


        saveMessage(
            reply,
            "bot"
        );


    } catch (error) {

        console.error(error);

        removeThinking();


        const errorMessage =
            "Something went wrong. Please make sure Ollama is running.";


        addMessage(
            errorMessage,
            "bot"
        );


        saveMessage(
            errorMessage,
            "bot"
        );

    }


    removeAttachment();

    button.disabled = false;

    button.textContent = "➤";

    input.focus();

}


/* ENTER */

function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();

    }

}


/* SETTINGS */

function openSettings() {

    document.getElementById(
        "settingsModal"
    ).style.display =
        "flex";

}


function closeSettings() {

    document.getElementById(
        "settingsModal"
    ).style.display =
        "none";

}


/* WINDOW */

window.onclick =
    function(event) {

        const modal =
            document.getElementById(
                "settingsModal"
            );


        if (event.target === modal) {

            closeSettings();

        }


        if (
            !event.target.closest(
                ".history-item"
            )
        ) {

            closeAllMenus();

        }


        if (
            !event.target.closest(
                ".attach"
            )
        ) {

            document.getElementById(
                "attachMenu"
            ).style.display =
                "none";

        }

    };


function closeAllMenus() {

    document
        .querySelectorAll(
            ".delete-menu"
        )
        .forEach(menu => {

            menu.style.display =
                "none";

        });

}


/* NEW CHAT */

function newChat() {

    currentChatId = null;

    showWelcome();

    document.getElementById(
        "messageInput"
    ).value = "";

    removeAttachment();

    document.getElementById(
        "messageInput"
    ).focus();

}


/* START */

renderHistory();

</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    if not data:
        return jsonify({
            "reply": "No message received."
        })

    message = data.get(
        "message",
        ""
    ).strip()

    if not message:
        return jsonify({
            "reply": "Please type a message."
        })

    prompt = f"""
{SYSTEM_PROMPT}

User:
{message}

Answer the user clearly and helpfully.
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": CHAT_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )

        response.raise_for_status()

        result = response.json()

        return jsonify({
            "reply": result.get(
                "response",
                "I couldn't generate a response."
            )
        })

    except requests.exceptions.ConnectionError:

        return jsonify({
            "reply":
            "Ollama is not running. Please open Ollama."
        })

    except Exception as e:

        return jsonify({
            "reply":
            "Error: " + str(e)
        })


@app.route("/upload", methods=["POST"])
def upload():

    try:

        message = request.form.get(
            "message",
            ""
        ).strip()

        file = request.files.get("file")


        if not file:

            return jsonify({
                "reply": "No file received."
            })


        filename = file.filename or "file"

        file_bytes = file.read()

        content_type = file.content_type or ""


        # IMAGE

        if content_type.startswith("image/"):

            encoded = base64.b64encode(file_bytes).decode("utf-8")


            prompt = f"""
{SYSTEM_PROMPT}

The user uploaded an image named "{filename}".

User message:
{message if message else "Please analyze this image."}

Carefully examine the image and give a useful answer.
"""


            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": VISION_MODEL,
                    "prompt": prompt,
                    "images": [encoded],
                    "stream": False
                },
                timeout=300
            )


            response.raise_for_status()

            result = response.json()


            return jsonify({
                "reply":
                    result.get(
                        "response",
                        "I couldn't understand the image."
                    )
            })


        # TEXT FILES

        if (
            content_type.startswith("text/")
            or filename.lower().endswith(
                (".txt", ".md")
            )
        ):

            text = file_bytes.decode(
                "utf-8",
                errors="ignore"
            )

            prompt = f"""
{SYSTEM_PROMPT}

The user uploaded a document named "{filename}".

Document content:
{text[:30000]}

User question:
{message if message else "Please summarize and explain this document."}
"""

            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": CHAT_MODEL,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=300
            )

            response.raise_for_status()

            result = response.json()

            return jsonify({
                "reply":
                    result.get(
                        "response",
                        "I couldn't understand the document."
                    )
            })


        # PDF

        if filename.lower().endswith(".pdf"):

            try:

                from PyPDF2 import PdfReader

                temp_path = os.path.join(
                    os.getcwd(),
                    "_ovi_temp.pdf"
                )

                with open(
                    temp_path,
                    "wb"
                ) as f:

                    f.write(file_bytes)


                reader = PdfReader(temp_path)


                text = ""

                for page in reader.pages:

                    text += (
                        page.extract_text()
                        or ""
                    )


                os.remove(temp_path)


                prompt = f"""
{SYSTEM_PROMPT}

The user uploaded a PDF named "{filename}".

PDF content:
{text[:30000]}

User question:
{message if message else "Please summarize and explain this PDF."}
"""


                response = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": CHAT_MODEL,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=300
                )


                response.raise_for_status()

                result = response.json()


                return jsonify({
                    "reply":
                        result.get(
                            "response",
                            "I couldn't understand the PDF."
                        )
                })


            except ImportError:

                return jsonify({
                    "reply":
                    "PDF support needs PyPDF2. Run: pip install PyPDF2"
                })


        return jsonify({
            "reply":
            f"I received {filename}, but this file type is not supported yet."
        })


    except requests.exceptions.ConnectionError:

        return jsonify({
            "reply":
            "Ollama is not running. Please open Ollama."
        })


    except Exception as e:

        return jsonify({
            "reply":
            "Upload error: " + str(e)
        })


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )