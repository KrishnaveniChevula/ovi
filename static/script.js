let pendingImage = null;


// =========================
// ESCAPE TEXT
// =========================

function escapeHTML(text) {

    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

}



// =========================
// FORMAT OVI RESPONSE
// =========================

function formatAIResponse(text) {

    text = escapeHTML(text);


    // Bold

    text = text.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );


    // Headings

    text = text.replace(
        /^### (.*)$/gm,
        "<h3>$1</h3>"
    );


    text = text.replace(
        /^## (.*)$/gm,
        "<h2>$1</h2>"
    );


    text = text.replace(
        /^# (.*)$/gm,
        "<h1>$1</h1>"
    );


    // Bullet points

    text = text.replace(
        /^\s*[-*]\s+(.*)$/gm,
        "• $1"
    );


    // Numbered points

    text = text.replace(
        /^\s*(\d+)\.\s+(.*)$/gm,
        "<strong>$1.</strong> $2"
    );


    // New lines

    text = text.replace(
        /\n/g,
        "<br>"
    );


    return text;

}



// =========================
// THINKING
// =========================

function showThinking() {

    let chat = document.querySelector("#chat");


    chat.innerHTML += `

        <div
            class="ai-message"
            id="thinking"
        >

            <span class="dot"></span>

            <span class="dot"></span>

            <span class="dot"></span>

        </div>

    `;


    chat.scrollTop =
        chat.scrollHeight;

}


function removeThinking() {

    document
        .querySelector("#thinking")
        ?.remove();

}



// =========================
// SEND MESSAGE
// =========================

async function sendMessage() {

    let input =
        document.querySelector("#messageInput");

    let message =
        input.value.trim();

    let chat =
        document.querySelector("#chat");



    // =====================
    // IMAGE + QUESTION
    // =====================

    if (pendingImage) {


        if (!message) {

            message =
                "Explain this image simply.";

        }


        // User bubble

        chat.innerHTML += `

            <div class="user-message">

                ${escapeHTML(message)}

            </div>

        `;


        input.value = "";


        showThinking();


        let formData =
            new FormData();


        formData.append(
            "image",
            pendingImage
        );


        formData.append(
            "message",
            message
        );


        try {


            let response =
                await fetch(
                    "/vision",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            let data =
                await response.json();


            removeThinking();


            chat.innerHTML += `

                <div class="ai-message">

                    ${formatAIResponse(
                        data.reply
                    )}

                </div>

            `;


            chat.scrollTop =
                chat.scrollHeight;


        }

        catch {


            removeThinking();


            chat.innerHTML += `

                <div class="ai-message">

                    Sorry, I couldn't
                    understand the image.

                </div>

            `;

        }


        pendingImage = null;

        return;

    }



    // =====================
    // NORMAL CHAT
    // =====================

    if (!message) return;


    // User bubble

    chat.innerHTML += `

        <div class="user-message">

            ${escapeHTML(message)}

        </div>

    `;


    input.value = "";


    showThinking();


    try {


        let response =
            await fetch(
                "/chat",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        message:
                            message

                    })

                }
            );


        let data =
            await response.json();


        removeThinking();


        chat.innerHTML += `

            <div class="ai-message">

                ${formatAIResponse(
                    data.reply
                )}

            </div>

        `;


        chat.scrollTop =
            chat.scrollHeight;


    }

    catch {


        removeThinking();


        chat.innerHTML += `

            <div class="ai-message">

                Sorry, something went wrong.
                Please try again.

            </div>

        `;

    }

}



// =========================
// ENTER KEY
// =========================

document
    .querySelector("#messageInput")
    .addEventListener(
        "keypress",
        function(event) {

            if (event.key === "Enter") {

                sendMessage();

            }

        }
    );



// =========================
// SUGGESTIONS
// =========================

function useSuggestion(text) {

    let input =
        document.querySelector(
            "#messageInput"
        );


    input.value = text;


    sendMessage();

}



// =========================
// IMAGE UPLOAD
// =========================

document
    .querySelectorAll(
        ".icon-button input"
    )
    .forEach(
        input => {


            input.addEventListener(
                "change",
                function() {


                    if (!this.files.length)
                        return;


                    let file =
                        this.files[0];


                    if (
                        !file.type
                            .startsWith("image/")
                    ) {

                        return;

                    }


                    pendingImage =
                        file;


                    let chat =
                        document.querySelector(
                            "#chat"
                        );


                    let reader =
                        new FileReader();


                    reader.onload =
                        function(e) {


                            chat.innerHTML += `

                                <div
                                    class="user-message"
                                >

                                    <img
                                        src="${e.target.result}"
                                        class="uploaded-image"
                                    >

                                </div>

                            `;


                            chat.scrollTop =
                                chat.scrollHeight;

                        };


                    reader.readAsDataURL(
                        file
                    );

                }

            );

        }
    );



// =========================
// CLEAR CHAT
// =========================

function clearChat() {

    pendingImage = null;


    document
        .querySelector("#chat")
        .innerHTML = `

            <div class="ai-message">

                <strong>
                    Hi! I'm OVI.
                </strong>

                <br>

                Tell me what's going on,
                and I'll help you figure out
                what to do next.

            </div>

        `;

}