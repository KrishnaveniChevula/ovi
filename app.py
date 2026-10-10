from flask import Flask, request, jsonify, render_template_string
from google import genai
import os
import tempfile

app = Flask(__name__)

# =========================================================
# GEMINI
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set.")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

MODEL = "gemini-3.5-flash-lite"

# =========================================================
# OVI SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are OVI, a helpful AI assistant designed to help people with real-life problems.

You can help with:
- Education
- Scholarships
- Government and civic information
- Farming
- Technology
- Careers
- Internships
- Documents
- Scam awareness
- General health information
- Accessibility
- Everyday questions

Rules:
1. Understand the user's problem first.
2. Give simple and practical answers.
3. If the user speaks Telugu, reply in Telugu.
4. If the user speaks Hindi, reply in Hindi.
5. If the user speaks English, reply in English.
6. Do not pretend to be a doctor, lawyer, or government officer.
7. For important information, tell the user to verify with an official source.
8. Never invent official information.
9. Be friendly and concise.
10. Give step-by-step instructions when useful.

FORMATTING RULES:
- Use clear, bold headings for main topics.
- Use bullet points for key information.
- Use numbered lists for step-by-step instructions.
- Include simple examples whenever useful.
- Keep paragraphs short and easy to understand.
- Bold important terms and key takeaways.
- Leave blank lines between sections.
- Use tables for comparisons when helpful.
- Avoid long paragraphs and unnecessary information.
- Respond in the user's language.
Answer the user's actual question directly and accurately.
Use simple language that beginners can understand.
Start with the direct answer, without unnecessary greetings.
Keep simple answers short and complex answers detailed.
Use headings, bullet points, and examples when useful.
For programming questions, provide correct code and briefly explain it.
Format Markdown and code blocks properly.
Do not invent facts. Clearly state when you are unsure.
Use the conversation history to understand follow-up questions.
Reply in the language the user uses.
"""

# =========================================================
# GEMINI TEXT
# =========================================================

def ask_gemini(prompt, uploaded_file=None):
    if not client:
        raise Exception(
            "Gemini API key is missing. Check your environment variable."
        )

    import time

    for attempt in range(3):
        try:
            contents = [SYSTEM_PROMPT, prompt]

            if uploaded_file is not None:
                contents.append(uploaded_file)

            response = client.models.generate_content(
                model=MODEL,
                contents=contents
            )

            answer = (response.text or "").strip()

            if not answer:
                raise Exception("Gemini returned an empty response.")

            return answer

        except Exception as e:
            error = str(e)
            print(f"Gemini attempt {attempt + 1}: {error}")

            temporary_error = any(
                code in error
                for code in [
                    "503",
                    "UNAVAILABLE",
                    "429",
                    "RESOURCE_EXHAUSTED",
                    "500",
                    "INTERNAL"
                ]
            )

            if temporary_error and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue

            if "503" in error or "UNAVAILABLE" in error:
                raise Exception(
                    "Gemini is busy right now. Please wait a minute "
                    "and try again."
                )

            if "429" in error or "RESOURCE_EXHAUSTED" in error:
                raise Exception(
                    "Gemini usage limit reached. Please try again later."
                )

            raise Exception(error)
    if not client:
        raise Exception("GEMINI_API_KEY is not configured.")

    if uploaded_file:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                SYSTEM_PROMPT,
                prompt,
                uploaded_file
            ]
        )
    else:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                SYSTEM_PROMPT,
                prompt
            ]
        )

    return (response.text or "").strip()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template_string(HTML)


# =========================================================
# CHAT
# =========================================================

@app.route("/chat", methods=["POST"])
def chat():

    try:
        data = request.get_json() or {}

        message = data.get("message", "").strip()

        if not message:
            return jsonify({
                "success": False,
                "error": "Please enter a message."
            })

        answer = ask_gemini(message)

        return jsonify({
            "success": True,
            "response": answer
        })

    except Exception as e:

        print("CHAT ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        })


# =========================================================
# VOICE
# =========================================================

@app.route("/voice", methods=["POST"])
def voice():

    temp_path = None

    try:

        if "audio" not in request.files:
            return jsonify({
                "success": False,
                "error": "No audio received."
            })

        audio = request.files["audio"]

        if not audio.filename:
            return jsonify({
                "success": False,
                "error": "No audio file."
            })

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp_file:

            temp_path = temp_file.name
            audio.save(temp_path)

        uploaded = client.files.upload(
            file=temp_path
        )

        answer = ask_gemini(
            """
Listen to this audio and transcribe exactly what the user said.

Return ONLY the transcription.
Do not explain it.
Do not answer the question.
""",
            uploaded
        )

        return jsonify({
            "success": True,
            "text": answer
        })

    except Exception as e:

        print("VOICE ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        })

    finally:

        if temp_path:

            try:
                os.remove(temp_path)
            except Exception:
                pass


# =========================================================
# FILE UPLOAD
# =========================================================

@app.route("/upload", methods=["POST"])
def upload():

    temp_path = None

    try:

        if "file" not in request.files:
            return jsonify({
                "success": False,
                "error": "No file selected."
            })

        file = request.files["file"]

        if not file.filename:
            return jsonify({
                "success": False,
                "error": "No file selected."
            })

        filename = file.filename

        extension = os.path.splitext(
            filename
        )[1].lower()

        # =================================================
        # IMAGE
        # =================================================

        if extension in [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ]:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension
            ) as temp_file:

                temp_path = temp_file.name
                file.save(temp_path)

            uploaded = client.files.upload(
                file=temp_path
            )

            answer = ask_gemini(
                """
Analyze this uploaded image.

If it contains text, read the important information.

If it is a document, explain the important information.

If it contains something the user may need help understanding,
explain it clearly.

If something is unclear, say that instead of guessing.
""",
                uploaded
            )

            return jsonify({
                "success": True,
                "filename": filename,
                "response": answer
            })


        # =================================================
        # PDF
        # =================================================

        if extension == ".pdf":

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as temp_file:

                temp_path = temp_file.name
                file.save(temp_path)

            uploaded = client.files.upload(
                file=temp_path
            )

            answer = ask_gemini(
                """
Analyze this PDF document.

Explain the important information clearly.

If useful, provide:
- Summary
- Important points
- Dates
- Requirements
- Instructions
- Actions the user should take

Do not invent information that is not present in the document.
""",
                uploaded
            )

            return jsonify({
                "success": True,
                "filename": filename,
                "response": answer
            })


        # =================================================
        # TEXT FILES
        # =================================================

        if extension in [
            ".txt",
            ".md",
            ".csv"
        ]:

            content = file.read().decode(
                "utf-8",
                errors="ignore"
            )

            content = content[:50000]

            answer = ask_gemini(
                f"""
The user uploaded this file:

Filename:
{filename}

File content:
{content}

Explain the important information clearly.
"""
            )

            return jsonify({
                "success": True,
                "filename": filename,
                "response": answer
            })


        return jsonify({
            "success": False,
            "error": "This file type is not supported."
        })

    except Exception as e:

        print("UPLOAD ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        })

    finally:

        if temp_path:

            try:
                os.remove(temp_path)
            except Exception:
                pass


# =========================================================
# HTML
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0">

<title>OVI</title>

<style>

* {
    box-sizing: border-box;
}

:root {
    --bg: #ffffff;
    --sidebar: #f7f7f8;
    --text: #171717;
    --muted: #777;
    --border: #e5e5e5;
    --hover: #eeeeee;
    --bubble: #f1f1f1;
    --accent: #111111;
}

body.dark {
    --bg: #181818;
    --sidebar: #202020;
    --text: #f5f5f5;
    --muted: #aaa;
    --border: #333;
    --hover: #2c2c2c;
    --bubble: #292929;
    --accent: #ffffff;
}

body.purple {
    --bg: #faf8ff;
    --sidebar: #f1edff;
    --text: #201735;
    --muted: #776b91;
    --border: #ddd4f4;
    --hover: #e9e2fa;
    --bubble: #eee8fb;
    --accent: #6d4aff;
}

body {
    margin: 0;
    height: 100vh;
    overflow: hidden;
    font-family: Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
}

.app {
    display: flex;
    height: 100vh;
}

.sidebar {
    width: 260px;
    background: var(--sidebar);
    border-right: 1px solid var(--border);
    padding: 16px;
    display: flex;
    flex-direction: column;
}

.logo {
    font-size: 25px;
    font-weight: bold;
    margin-bottom: 20px;
}

.new-chat {
    width: 100%;
    padding: 11px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--bg);
    color: var(--text);
    cursor: pointer;
}

.history-title {
    margin-top: 20px;
    margin-bottom: 8px;
    font-size: 11px;
    color: var(--muted);
}

.history {
    overflow-y: auto;
}

.history-item {
    padding: 10px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.history-item:hover {
    background: var(--hover);
}

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
    padding: 0 18px;
}

.top-title {
    font-weight: bold;
}

.settings-button {
    border: none;
    background: transparent;
    color: var(--text);
    font-size: 20px;
    cursor: pointer;
}

.chat {
    flex: 1;
    overflow-y: auto;
    padding: 25px;
}

.welcome {
    text-align: center;
    margin-top: 18vh;
}

.welcome h1 {
    font-size: 34px;
}

.welcome p {
    color: var(--muted);
}

.message-row {
    display: flex;
    margin-bottom: 18px;
}

.message-row.user {
    justify-content: flex-end;
}

.message-row.ovi {
    justify-content: flex-start;
}

.message {
    max-width: 75%;
    padding: 11px 15px;
    border-radius: 15px;
    line-height: 1.5;
    white-space: pre-wrap;
}

.user .message {
    background: var(--accent);
    color: var(--bg);
    border-bottom-right-radius: 5px;
}

.ovi .message {
    background: var(--bubble);
    border-bottom-left-radius: 5px;
}

.thinking {
    display: flex;
    gap: 5px;
}

.dot {
    width: 6px;
    height: 6px;
    background: var(--muted);
    border-radius: 50%;
    animation: blink 1s infinite;
}

.dot:nth-child(2) {
    animation-delay: .2s;
}

.dot:nth-child(3) {
    animation-delay: .4s;
}

@keyframes blink {
    0%,100% {
        opacity: .2;
    }

    50% {
        opacity: 1;
    }
}

.input-area {
    padding: 12px 20px 18px;
}

.input-box {
    max-width: 900px;
    margin: auto;
    border: 1px solid var(--border);
    border-radius: 18px;
    display: flex;
    align-items: flex-end;
    padding: 7px;
}

textarea {
    flex: 1;
    resize: none;
    border: none;
    outline: none;
    background: transparent;
    color: var(--text);
    padding: 10px;
    font-family: inherit;
    font-size: 15px;
}

.action-button,
.voice-button {
    width: 38px;
    height: 38px;
    border: none;
    border-radius: 50%;
    background: transparent;
    color: var(--text);
    cursor: pointer;
    font-size: 18px;
}

.action-button:hover,
.voice-button:hover {
    background: var(--hover);
}

.voice-button.recording {
    background: #e53935;
    color: white;
}

.send {
    width: 38px;
    height: 38px;
    border: none;
    border-radius: 50%;
    background: var(--accent);
    color: var(--bg);
    cursor: pointer;
    font-size: 18px;
}

.preview {
    max-width: 900px;
    margin: auto;
    padding: 5px;
    color: var(--muted);
    font-size: 13px;
    display: none;
}

.attach-menu {
    position: fixed;
    bottom: 75px;
    left: 20px;
    display: none;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 6px;
}

.attach-menu button {
    display: block;
    width: 150px;
    padding: 10px;
    border: none;
    background: transparent;
    color: var(--text);
    text-align: left;
    cursor: pointer;
}

.attach-menu button:hover {
    background: var(--hover);
}

.modal {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.45);
    display: none;
    align-items: center;
    justify-content: center;
}

.modal-box {
    background: var(--bg);
    padding: 22px;
    width: 320px;
    border-radius: 16px;
}

.theme-button,
.close-modal {
    width: 100%;
    padding: 10px;
    margin-top: 7px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg);
    color: var(--text);
    cursor: pointer;
}

@media(max-width:700px) {

    .sidebar {
        display: none;
    }

    .chat {
        padding: 15px;
    }

    .message {
        max-width: 88%;
    }
}

/* OVI MOBILE LAYOUT FIX */
@media screen and (max-width: 700px) {
    html,
    body {
        width: 100%;
        max-width: 100%;
        overflow-x: hidden;
    }

    .app,
    .main,
    .chat {
        box-sizing: border-box;
        max-width: 100%;
        min-width: 0;
    }

    .chat {
        padding: 12px;
    }

    .message {
        max-width: 90%;
        overflow-wrap: anywhere;
    }

    .input-area,
    .input-box {
        box-sizing: border-box;
        width: 100%;
        max-width: 100%;
        min-width: 0;
    }

    textarea,
    input {
        box-sizing: border-box;
        max-width: 100%;
        min-width: 0;
        font-size: 16px;
    }

    button {
        max-width: 100%;
    }

    img,
    video,
    canvas {
        max-width: 100%;
        height: auto;
    }
}

/* Mobile chat history drawer */
.history-toggle {
    display: none;
}

@media screen and (max-width: 700px) {
    .history-toggle {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 8px 10px;
        border: 1px solid var(--border);
        border-radius: 8px;
        background: var(--bg);
        color: var(--text);
        cursor: pointer;
        flex-shrink: 0;
    }

    .sidebar.mobile-open {
        display: flex !important;
        position: fixed;
        top: 0;
        left: 0;
        bottom: 0;
        width: min(280px, 85vw);
        height: 100vh;
        height: 100dvh;
        box-sizing: border-box;
        overflow-y: auto;
        z-index: 1000;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.2);
    }

    .topbar {
        gap: 10px;
    }
}
.message h1,
.message h2,
.message h3,
.message h4,
.message h5,
.message h6 {
    font-weight: 700;
}


/* OVI answers: no bubble or background */
.message.ovi,
.message.assistant,
.message.bot {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    border-radius: 0 !important;
    max-width: 100% !important;
}

/* OVI answers without a bubble */
.ovi-answer {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    border-radius: 0 !important;
    max-width: 100% !important;
    width: 100%;
    color: inherit;
}

/* Keep formatted answers readable */
.ovi-answer p {
    margin: 0 0 12px;
}

.ovi-answer h1,
.ovi-answer h2,
.ovi-answer h3,
.ovi-answer h4 {
    font-weight: 700;
    margin: 16px 0 8px;
}
</style>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify/dist/purify.min.js"></script>
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

<div class="history" id="history"></div>

</aside>

<main class="main">

<div class="topbar">

<div class="top-title">
<button
    class="history-toggle"
    onclick="toggleHistory()"
    aria-label="Open chat history">
    ☰ History
</button>
OVI
</div>

<button class="settings-button" onclick="openSettings()">
⚙
</button>

</div>

<div class="chat" id="chat">

<div class="welcome" id="welcome">

<h1>
Hi, I'm OVI
</h1>

<p>
AI that helps with real life.
</p>

</div>

</div>

<div class="input-area">

<div class="preview" id="preview"></div>

<div class="input-box">

<button class="action-button" onclick="toggleAttach()">
+
</button>

<textarea
id="messageInput"
placeholder="Message OVI..."
rows="1"
onkeydown="handleKey(event)">
</textarea>

<button
class="voice-button"
id="voiceButton"
onclick="toggleVoice()">
🎤
</button>

<button
class="send"
onclick="sendMessage()">
➤
</button>

</div>

</div>

</main>

</div>

<div class="attach-menu" id="attachMenu">

<button onclick="choosePhoto()">
🖼️ Photo
</button>

<button onclick="chooseCamera()">
📷 Camera
</button>

<button onclick="chooseFile()">
📄 File
</button>

</div>

<input
type="file"
id="fileInput"
hidden
accept=".txt,.md,.csv,.pdf">

<input
type="file"
id="imageInput"
hidden
accept="image/*">

<input
type="file"
id="cameraInput"
hidden
accept="image/*"
capture="environment">

<div class="modal" id="settingsModal">

<div class="modal-box">

<h2>
Settings
</h2>

<button class="theme-button" onclick="setTheme('light')">
☀ Light
</button>

<button class="theme-button" onclick="setTheme('dark')">
🌙 Dark
</button>

<button class="theme-button" onclick="setTheme('purple')">
💜 Purple
</button>

<button class="close-modal" onclick="closeSettings()">
Close
</button>

</div>

</div>

<script>

let selectedFile = null;

let mediaRecorder = null;

let audioChunks = [];

let isRecording = false;

let conversations =
JSON.parse(
localStorage.getItem("oviHistory") || "[]"
);

let currentMessages = [];


// =========================================================
// HISTORY
// =========================================================

function saveHistory() {

    localStorage.setItem(
        "oviHistory",
        JSON.stringify(conversations)
    );

    renderHistory();
}

function renderHistory() {

    const history =
        document.getElementById("history");

    history.innerHTML = "";

    conversations.forEach(
        (conversation, index) => {

            const item =
                document.createElement("div");

            item.className = "history-item";

            item.textContent =
                conversation.title;

            item.onclick =
                function() {
                    loadConversation(index);
                };

            item.oncontextmenu = function(event) {
    event.preventDefault();

    // Remove any existing context menu
    document.querySelectorAll(".context-menu").forEach(menu => menu.remove());

    const menu = document.createElement("div");
    menu.className = "context-menu";
    menu.textContent = "🗑️ Delete";

    menu.style.cssText = `
        position: fixed;
        left: ${event.clientX}px;
        top: ${event.clientY}px;
        background: #222;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        cursor: pointer;
        z-index: 9999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    `;

    menu.onclick = function() {
        conversations.splice(index, 1);
        saveHistory();
        menu.remove();
        newChat();
    };

    document.body.appendChild(menu);

    // Close the menu when clicking elsewhere
    setTimeout(() => {
        document.addEventListener("click", function closeMenu() {
            menu.remove();
            document.removeEventListener("click", closeMenu);
        }, { once: true });
    }, 0);
};

history.appendChild(item);
        }
    );
}

function loadConversation(index) {

    currentMessages =
        conversations[index].messages || [];

    const chat =
        document.getElementById("chat");

    chat.innerHTML = "";

    currentMessages.forEach(
        message => {

            addMessage(
                message.text,
                message.sender,
                false
            );

        }
    );
}


function addMessage(text, sender, save = true) {
    const welcome = document.getElementById("welcome");

    if (welcome) {
        welcome.remove();
    }

    const row = document.createElement("div");
    row.className = "message-row " + sender;

    const bubble = document.createElement("div");
    bubble.className =
    (sender === "ovi" || sender === "assistant" || sender === "bot")
        ? "message ovi-answer"
        : "message";

    // Render OVI responses as formatted Markdown
    if (sender === "ovi" || sender === "assistant" || sender === "bot") {
        if (
            typeof marked !== "undefined" &&
            typeof DOMPurify !== "undefined"
        ) {
            bubble.innerHTML = DOMPurify.sanitize(
                marked.parse(text)
            );
        } else {
            bubble.textContent = text;
            console.error("Markdown libraries are not loaded.");
        }
    } else {
        // Keep user messages as plain text
        bubble.textContent = text;
    }

    row.appendChild(bubble);

    const chat = document.getElementById("chat");
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;

    if (save) {
        currentMessages.push({
            sender: sender,
            text: text
        });
    }
}


// =========================================================
// THINKING
// =========================================================

function showThinking() {

    const row =
        document.createElement("div");

    row.id = "thinking";

    row.className =
        "message-row ovi";

    row.innerHTML = `

        <div class="message thinking">

            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>

        </div>

    `;

    document
        .getElementById("chat")
        .appendChild(row);
}

function removeThinking() {

    const element =
        document.getElementById("thinking");

    if(element) {
        element.remove();
    }
}


// =========================================================
// CHAT
// =========================================================

async function sendMessage() {

    const input =
        document.getElementById("messageInput");

    const message =
        input.value.trim();

    if(!message && !selectedFile) {
        return;
    }

    if(message) {

        addMessage(
            message,
            "user"
        );

    }

    input.value = "";

    if(selectedFile) {

        await uploadFile();

        selectedFile = null;

        document.getElementById(
            "preview"
        ).style.display = "none";

        return;
    }

    showThinking();

    try {

        const response =
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
                            message: message
                        })
                }
            );

        const data =
            await response.json();

        removeThinking();

        if(data.success) {

            addMessage(
                data.response,
                "ovi"
            );

        } else {

            addMessage(
                "Error: " + data.error,
                "ovi"
            );

        }

    } catch(error) {

        removeThinking();

        addMessage(
            "Could not connect to OVI.",
            "ovi"
        );
    }

    if(
        currentMessages.length > 0 &&
        currentMessages.length <= 2
    ) {

        saveCurrentChat();

        currentMessages = [];
    }
}


// =========================================================
// VOICE
// =========================================================

async function toggleVoice() {

    if(isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {

    try {

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        audioChunks = [];

        mediaRecorder =
            new MediaRecorder(stream);

        mediaRecorder.ondataavailable =
            function(event) {

                if(event.data.size > 0) {

                    audioChunks.push(
                        event.data
                    );

                }
            };

        mediaRecorder.onstop =
            async function() {

                stream
                    .getTracks()
                    .forEach(
                        track =>
                            track.stop()
                    );

                const audioBlob =
                    new Blob(
                        audioChunks,
                        {
                            type: "audio/webm"
                        }
                    );

                await sendAudio(audioBlob);
            };

        mediaRecorder.start();

        isRecording = true;

        const button =
            document.getElementById(
                "voiceButton"
            );

        button.classList.add("recording");

        button.textContent = "⏹️";

    } catch(error) {

        alert(
            "Microphone permission is required for OVI voice input."
        );

        console.log(error);
    }
}

function stopRecording() {

    if(
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {

        mediaRecorder.stop();
    }

    isRecording = false;

    const button =
        document.getElementById(
            "voiceButton"
        );

    button.classList.remove("recording");

    button.textContent = "🎤";
}

async function sendAudio(audioBlob) {

    const button =
        document.getElementById(
            "voiceButton"
        );

    button.textContent = "⏳";

    const formData =
        new FormData();

    formData.append(
        "audio",
        audioBlob,
        "voice.webm"
    );

    try {

        const response =
            await fetch(
                "/voice",
                {
                    method: "POST",
                    body: formData
                }
            );

        const data =
            await response.json();

        if(data.success) {

            const input =
                document.getElementById(
                    "messageInput"
                );

            input.value =
                data.text;

            input.focus();

        } else {

            alert(
                "Voice error: " +
                data.error
            );
        }

    } catch(error) {

        alert(
            "Could not process your voice."
        );

        console.log(error);
    }

    button.textContent = "🎤";
}


// =========================================================
// ATTACHMENTS
// =========================================================

function toggleAttach() {

    const menu =
        document.getElementById(
            "attachMenu"
        );

    menu.style.display =
        menu.style.display === "block"
        ? "none"
        : "block";
}

function chooseFile() {

    document.getElementById(
        "fileInput"
    ).click();

    toggleAttach();
}

function choosePhoto() {

    document.getElementById(
        "imageInput"
    ).click();

    toggleAttach();
}

function chooseCamera() {

    document.getElementById(
        "cameraInput"
    ).click();

    toggleAttach();
}

function showPreview(name) {

    const preview =
        document.getElementById(
            "preview"
        );

    preview.textContent =
        "Selected: " + name;

    preview.style.display =
        "block";
}


// =========================================================
// FILE INPUTS
// =========================================================

document.getElementById(
    "fileInput"
).onchange =
function(event) {

    if(event.target.files.length) {

        selectedFile =
            event.target.files[0];

        showPreview(
            selectedFile.name
        );
    }
};

document.getElementById(
    "imageInput"
).onchange =
function(event) {

    if(event.target.files.length) {

        selectedFile =
            event.target.files[0];

        showPreview(
            selectedFile.name
        );
    }
};

document.getElementById(
    "cameraInput"
).onchange =
function(event) {

    if(event.target.files.length) {

        selectedFile =
            event.target.files[0];

        showPreview(
            selectedFile.name
        );
    }
};


// =========================================================
// UPLOAD
// =========================================================

async function uploadFile() {

    showThinking();

    const formData =
        new FormData();

    formData.append(
        "file",
        selectedFile
    );

    try {

        const response =
            await fetch(
                "/upload",
                {
                    method: "POST",
                    body: formData
                }
            );

        const data =
            await response.json();

        removeThinking();

        if(data.success) {

            addMessage(
                data.response,
                "ovi"
            );

        } else {

            addMessage(
                data.error,
                "ovi"
            );
        }

    } catch(error) {

        removeThinking();

        addMessage(
            "File processing failed.",
            "ovi"
        );
    }
}


// =========================================================
// KEYBOARD
// =========================================================

function handleKey(event) {

    if(
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();
    }
}


// =========================================================
// SETTINGS
// =========================================================

function openSettings() {

    document.getElementById(
        "settingsModal"
    ).style.display = "flex";
}

function closeSettings() {

    document.getElementById(
        "settingsModal"
    ).style.display = "none";
}

function setTheme(theme) {

    document.body.className = "";

    if(theme !== "light") {

        document.body.classList.add(
            theme
        );
    }

    localStorage.setItem(
        "oviTheme",
        theme
    );

    closeSettings();
}


// =========================================================
// START
// =========================================================

const savedTheme =
    localStorage.getItem(
        "oviTheme"
    );

if(savedTheme) {
    setTheme(savedTheme);
}

renderHistory();

function toggleHistory() {
    const sidebar = document.querySelector(".sidebar");

    if (sidebar) {
        sidebar.classList.toggle("mobile-open");
    }
}

function closeHistory() {
    const sidebar = document.querySelector(".sidebar");

    if (sidebar) {
        sidebar.classList.remove("mobile-open");
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const history = document.getElementById("history");

    if (history) {
        history.addEventListener("click", function (event) {
            if (event.target.closest(".history-item")) {
                closeHistory();
            }
        });
    }
});


</script>

</body>
</html>
"""


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )