document.addEventListener("DOMContentLoaded", () => {
    const voiceSelect = document.getElementById("voice-select");
    const textInput = document.getElementById("text-input");
    const saveMp3Checkbox = document.getElementById("save-mp3");
    const filenameInput = document.getElementById("filename");
    const convertBtn = document.getElementById("convert-btn");
    const statusDiv = document.getElementById("status");
    const audioDownloadDiv = document.getElementById("audio-download");
    const downloadLink = document.getElementById("download-link");

    // Fetch available voices
    fetch("/get_voices")
        .then(response => response.json())
        .then(voices => {
            voices.forEach(voice => {
                const option = document.createElement("option");
                option.value = voice.index;
                option.textContent = `${voice.name} (${voice.gender})`;
                voiceSelect.appendChild(option);
            });
        })
        .catch(error => {
            statusDiv.textContent = "Error loading voices.";
            console.error(error);
        });

    // Enable/disable filename input based on checkbox
    saveMp3Checkbox.addEventListener("change", () => {
        filenameInput.disabled = !saveMp3Checkbox.checked;
        if (!saveMp3Checkbox.checked) {
            filenameInput.value = "output.mp3";
        }
    });

    // Convert text to speech
    convertBtn.addEventListener("click", () => {
        const text = textInput.value.trim();
        if (!text) {
            statusDiv.textContent = "Please enter some text.";
            return;
        }

        const voiceIndex = parseInt(voiceSelect.value);
        const saveToFile = saveMp3Checkbox.checked;
        const filename = filenameInput.value || "output.mp3";

        statusDiv.textContent = "Converting...";
        audioDownloadDiv.style.display = "none";

        fetch("/convert", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text,
                voice_index: voiceIndex >= 0 ? voiceIndex : null,
                save_to_file: saveToFile,
                filename
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                statusDiv.textContent = "Conversion successful!";
                if (data.audio_url) {
                    audioDownloadDiv.style.display = "block";
                    downloadLink.href = data.audio_url;
                    downloadLink.textContent = `Download ${filename}`;
                }
            } else {
                statusDiv.textContent = `Error: ${data.message}`;
            }
        })
        .catch(error => {
            statusDiv.textContent = "Error during conversion.";
            console.error(error);
        });
    });
});