// Logique Frontend pour Dwaya AI (دوايا) avec Carte Leaflet, TTS Haute Fidélité et Micro Universel

let currentLat = 33.5731; // Casablanca par défaut
let currentLng = -7.5898;
let map = null;
let markersLayer = null;
let userMarker = null;

// Initialisation de la carte Leaflet
function initMap() {
    map = L.map('pharmacy-map').setView([currentLat, currentLng], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);

    markersLayer = L.layerGroup().addTo(map);

    updateUserPositionMarker(currentLat, currentLng, "Position par défaut (Casablanca)");
}

// Mise à jour du marqueur de position de l'utilisateur
function updateUserPositionMarker(lat, lng, popupText = "Votre position") {
    if (!map) return;
    
    currentLat = lat;
    currentLng = lng;

    if (userMarker) {
        map.removeLayer(userMarker);
    }

    userMarker = L.circleMarker([lat, lng], {
        radius: 8,
        fillColor: "#2563eb", // Bleu vif
        color: "#ffffff",
        weight: 3,
        opacity: 1,
        fillOpacity: 1
    }).addTo(map).bindPopup(`<b>📍 ${popupText}</b>`);
}

// Mettre à jour les marqueurs des pharmacies sur la carte
function updateMapMarkers(pharmacies, centerLat, centerLng) {
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();

    // S'assurer que le marqueur utilisateur reste présent et visible
    updateUserPositionMarker(currentLat, currentLng, "Votre position");

    const bounds = L.latLngBounds([[currentLat, currentLng]]);

    pharmacies.forEach(p => {
        if (!p.lat || !p.lng) return;

        const isGarde = Boolean(p.garde);
        const markerColor = isGarde ? "#16a34a" : "#0d9488";

        const marker = L.circleMarker([p.lat, p.lng], {
            radius: isGarde ? 9 : 7,
            fillColor: markerColor,
            color: "#ffffff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.95
        });

        const popupContent = `
            <div style="font-size: 12px; line-height: 1.4;">
                <b style="color: ${markerColor};">${p.title}</b><br/>
                ${isGarde ? '<span style="background: #dcfce7; color: #166534; font-weight: bold; padding: 2px 4px; border-radius: 4px; font-size: 10px;">GARDE ACTIVE</span><br/>' : ''}
                ${p.address || p.ville}<br/>
                📞 ${p.phone || 'Non renseigné'}<br/>
                <span style="color: #64748b;">Distance: ${p.distance_km ? p.distance_km + ' km' : 'Proche'}</span><br/>
                <a href="https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}" target="_blank" style="color: #0284c7; text-decoration: underline; font-weight: 500;">Itinéraire GPS</a>
            </div>
        `;

        marker.bindPopup(popupContent);
        markersLayer.addLayer(marker);
        bounds.extend([p.lat, p.lng]);
    });

    if (pharmacies.length > 0) {
        map.fitBounds(bounds, { padding: [25, 25], maxZoom: 14 });
    }
}

// ----------------------------------------------------------------------------------
// Synthèse Vocale (TTS) Haute Qualité via l'API Backend gTTS
// ----------------------------------------------------------------------------------
let currentAudioPlayer = null;

async function playSpeechTTS(text) {
    if (!text || !text.trim()) return;

    if (currentAudioPlayer) {
        currentAudioPlayer.pause();
        currentAudioPlayer = null;
    }

    try {
        const response = await fetch('/api/audio/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) throw new Error("Erreur serveur TTS");

        const blob = await response.blob();
        const audioUrl = URL.createObjectURL(blob);
        currentAudioPlayer = new Audio(audioUrl);
        currentAudioPlayer.play();
    } catch (err) {
        console.warn("Fallback sur TTS navigateur :", err);
        // Fallback transparent
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const clean = text.replace(/[*_#`💡💊🔄📍🌙📞⚠️💰🚨]/g, '').trim();
            const utt = new SpeechSynthesisUtterance(clean);
            utt.lang = /[\u0600-\u06FF]/.test(clean) ? 'ar-XA' : 'fr-FR';
            window.speechSynthesis.speak(utt);
        }
    }
}

// Géolocalisation
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            currentLat = pos.coords.latitude;
            currentLng = pos.coords.longitude;
            document.getElementById('user-city').innerText = `GPS (${currentLat.toFixed(2)}, ${currentLng.toFixed(2)})`;
            updateUserPositionMarker(currentLat, currentLng, "Votre position GPS");
            if (map) {
                map.setView([currentLat, currentLng], 13);
            }
        },
        (err) => {
            console.log("Position par défaut (Casablanca).");
        },
        { enableHighAccuracy: true, timeout: 5000 }
    );
}

const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const voiceBtn = document.getElementById('voice-btn');

const speechTexts = {};

function appendMessage(sender, htmlContent, isUser = false, rawTextToSpeak = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `flex items-start space-x-3 ${isUser ? 'justify-end' : ''}`;
    
    if (isUser) {
        msgDiv.innerHTML = `
            <div class="bg-teal-600 text-white rounded-2xl rounded-tr-none p-3.5 max-w-lg shadow-sm text-sm">
                ${htmlContent}
            </div>
            <div class="w-8 h-8 rounded-full bg-slate-300 text-slate-700 flex items-center justify-center flex-shrink-0 text-sm shadow">
                <i class="fa-solid fa-user"></i>
            </div>
        `;
    } else {
        const speechId = 'speech-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
        if (rawTextToSpeak) {
            speechTexts[speechId] = rawTextToSpeak;
        }

        const audioBtn = rawTextToSpeak ? `
            <button onclick="playStoredSpeech('${speechId}')" class="text-slate-400 hover:text-teal-600 p-1 float-right" title="Écouter la voix naturelle">
                <i class="fa-solid fa-volume-high text-xs"></i>
            </button>
        ` : '';

        msgDiv.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-teal-600 text-white flex items-center justify-center flex-shrink-0 text-sm shadow">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="bg-slate-100 text-slate-800 rounded-2xl rounded-tl-none p-3.5 max-w-lg shadow-sm text-sm space-y-2">
                ${audioBtn}
                ${htmlContent}
            </div>
        `;
    }

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function playStoredSpeech(speechId) {
    const text = speechTexts[speechId];
    if (text) {
        playSpeechTTS(text);
    }
}

function updateInspector(data) {
    const intentBox = document.getElementById('inspector-intent');
    const intentColors = {
        'check_availability': 'text-blue-700',
        'ask_price_reimbursement': 'text-emerald-700',
        'find_alternatives': 'text-purple-700',
        'ask_posology_usage': 'text-amber-700',
        'ask_side_effects_safety': 'text-red-700'
    };
    const color = intentColors[data.intent] || 'text-slate-700';
    intentBox.innerHTML = `
        <span class="font-mono font-bold ${color}">${data.intent}</span>
        <span class="bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">${Math.round(data.confidence * 100)}%</span>
    `;

    const entBox = document.getElementById('inspector-entities');
    const ents = data.entities || {};
    let entHtml = '';
    if (ents.medication) entHtml += `<div><span class="text-slate-400">Marque:</span> <span class="bg-teal-100 text-teal-800 px-1.5 py-0.5 rounded font-bold">${ents.medication}</span></div>`;
    if (ents.dosage_val) entHtml += `<div><span class="text-slate-400">Dosage:</span> <span class="bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">${ents.dosage_val} ${ents.dosage_unit || ''}</span></div>`;
    if (ents.galenic_form) entHtml += `<div><span class="text-slate-400">Forme:</span> <span class="bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded">${ents.galenic_form}</span></div>`;
    if (ents.location) entHtml += `<div><span class="text-slate-400">Ville:</span> <span class="bg-indigo-100 text-indigo-800 px-1.5 py-0.5 rounded font-bold">📍 ${ents.location}</span></div>`;
    entBox.innerHTML = entHtml || '<p class="text-slate-400 italic">Aucune entité extraite</p>';

    const drugBox = document.getElementById('inspector-drug');
    if (data.matched_drug) {
        const d = data.matched_drug;
        drugBox.innerHTML = `
            <div class="font-bold text-teal-900">${d.nom}</div>
            <div class="text-[11px] text-slate-500">CIP: ${d.code} | DCI: ${d.dci}</div>
            <div class="flex justify-between pt-1 font-semibold text-emerald-700">
                <span>PPV: ${d.ppv.toFixed(2)} DH</span>
                <span class="text-slate-500">${d.princeps_generique} (${d.taux_remboursement})</span>
            </div>
        `;
    } else {
        drugBox.innerHTML = '<p class="text-slate-400 italic">Aucun médicament apparié</p>';
    }

    if (data.pharmacies && data.pharmacies.length > 0) {
        const first = data.pharmacies[0];
        updateMapMarkers(data.pharmacies, first.lat, first.lng);
    }
}

let attachedImageFile = null;

async function sendMessage(text) {
    const hasImage = Boolean(attachedImageFile);
    const trimmedText = text ? text.trim() : '';

    if (!trimmedText && !hasImage) return;

    // 1. Affichage du message côté utilisateur
    let userDisplayHtml = '';
    if (hasImage) {
        const tempImgUrl = URL.createObjectURL(attachedImageFile);
        userDisplayHtml = `
            <div class="space-y-1.5">
                <img src="${tempImgUrl}" class="max-w-[200px] max-h-[130px] rounded-lg border border-slate-200 shadow-sm object-cover" alt="Boîte envoyée" />
                ${trimmedText ? `<p>${trimmedText}</p>` : '<p class="text-xs text-slate-500 italic">📷 Identification de cette boîte de médicament...</p>'}
            </div>
        `;
    } else {
        userDisplayHtml = `<p>${trimmedText}</p>`;
    }

    appendMessage('user', userDisplayHtml, true);
    userInput.value = '';

    // Réinitialiser la barre de prévisualisation
    const imageToSend = attachedImageFile;
    clearAttachedImage();

    // 2. Indicateur de chargement
    const loadingId = 'loading-' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.id = loadingId;
    loadingDiv.className = 'flex items-start space-x-3';
    loadingDiv.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-teal-600 text-white flex items-center justify-center flex-shrink-0 text-sm shadow animate-pulse">
            <i class="fa-solid fa-spinner fa-spin"></i>
        </div>
        <div class="bg-slate-100 text-slate-500 rounded-2xl rounded-tl-none p-3 max-w-xs shadow-sm text-xs italic">
            ${hasImage ? 'Analyse multimodale Gemini & vision CNOPS...' : 'Analyse NLU & recherche dans le référentiel CNOPS...'}
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        let response;
        if (hasImage) {
            // Envoi multipart/form-data
            const formData = new FormData();
            formData.append('message', trimmedText || 'Peux-tu analyser cette boîte de médicament et m\'expliquer ce que c\'est en Darija ?');
            formData.append('image', imageToSend, imageToSend.name || 'medication.jpg');
            if (currentLat) formData.append('lat', currentLat);
            if (currentLng) formData.append('lng', currentLng);

            response = await fetch('/api/chat/multimodal', {
                method: 'POST',
                body: formData
            });
        } else {
            // Envoi JSON classique
            response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: trimmedText,
                    lat: currentLat,
                    lng: currentLng
                })
            });
        }

        const data = await response.json();
        document.getElementById(loadingId)?.remove();

        updateInspector(data);

        // Header du message assistant (avec badge modèle LLM si actif)
        let modelBadge = '';
        if (data.is_llm) {
            modelBadge = `<span class="bg-indigo-100 text-indigo-800 border border-indigo-200 px-2 py-0.5 rounded-full text-[10px] font-bold inline-flex items-center"><i class="fa-solid fa-sparkles text-indigo-500 mr-1"></i>Gemini Flash (Darija)</span>`;
        }

        let replyHtml = `
            ${modelBadge ? `<div class="mb-1.5 flex justify-end">${modelBadge}</div>` : ''}
            <div class="text-sm leading-relaxed">${formatMarkdownText(data.reply_text)}</div>
        `;

        if (data.matched_drug) {
            const d = data.matched_drug;
            replyHtml += `
                <div class="mt-2.5 p-3 bg-white border border-teal-200 rounded-xl shadow-xs text-xs">
                    <div class="flex justify-between items-start font-bold text-slate-800">
                        <span>💊 ${d.nom}</span>
                        <span class="text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200 font-mono">${d.ppv.toFixed(2)} DH</span>
                    </div>
                    <div class="text-slate-500 mt-1">DCI : <strong>${d.dci}</strong> (${d.dosage} ${d.unite_dosage || ''})</div>
                    <div class="text-slate-500">Forme : ${d.forme} ${d.presentation ? '- ' + d.presentation : ''}</div>
                    <div class="mt-1.5 flex items-center space-x-2 text-[11px] text-slate-600">
                        <span class="bg-slate-100 px-1.5 py-0.5 rounded font-medium">${d.princeps_generique}</span>
                        <span class="text-emerald-700">Remboursement CNOPS/AMO: ${d.taux_remboursement}</span>
                    </div>
                </div>
            `;
        }

        if (data.alternatives && data.alternatives.length > 0) {
            replyHtml += `<div class="mt-2.5 font-semibold text-xs text-purple-800">🔄 Alternatives & Génériques moins chers au Maroc :</div><div class="space-y-1.5 mt-1">`;
            data.alternatives.slice(0, 3).forEach(alt => {
                replyHtml += `
                    <div class="p-2 bg-purple-50 border border-purple-200 rounded-lg text-xs flex justify-between items-center">
                        <div>
                            <span class="font-bold text-purple-900">${alt.nom}</span>
                            <span class="text-slate-500 text-[11px] block">${alt.forme} - ${alt.presentation || ''}</span>
                        </div>
                        <span class="font-bold text-purple-800 font-mono">${alt.ppv.toFixed(2)} DH</span>
                    </div>
                `;
            });
            replyHtml += `</div>`;
        }

        if (data.pharmacies && data.pharmacies.length > 0) {
            replyHtml += `<div class="mt-2.5 font-semibold text-xs text-blue-900">📍 Pharmacies à proximité (Gardes & Actions Directes) :</div><div class="space-y-2 mt-1">`;
            data.pharmacies.slice(0, 3).forEach(p => {
                const isGarde = Boolean(p.is_garde || p.garde);
                replyHtml += `
                    <div class="p-2.5 bg-white border ${isGarde ? 'border-emerald-300 ring-1 ring-emerald-200' : 'border-slate-200'} rounded-lg text-xs shadow-2xs">
                        <div class="flex justify-between items-center">
                            <span class="font-bold text-slate-800">${p.name || p.title}</span>
                            ${isGarde ? '<span class="bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.5 rounded text-[10px]"><i class="fa-solid fa-moon mr-1"></i>GARDE ACTIVE</span>' : ''}
                        </div>
                        <div class="text-slate-500 text-[11px] mt-0.5">${p.address || p.city || p.ville || ''}</div>
                        <div class="flex items-center space-x-2 mt-1 text-[11px] text-slate-500">
                            <span><i class="fa-solid fa-phone text-slate-400 mr-1"></i>${p.phone || 'Non renseigné'}</span>
                            <span class="font-mono text-teal-700 font-medium">📍 ${p.distance_km ? p.distance_km + ' km' : 'Proche'}</span>
                        </div>
                        <div class="mt-2 pt-1.5 border-t border-slate-100 flex items-center gap-1.5">
                            ${p.phone_url ? `<a href="${p.phone_url}" class="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-[11px] font-medium flex items-center transition shadow-2xs"><i class="fa-solid fa-phone mr-1"></i>Appeler</a>` : ''}
                            ${p.whatsapp_url ? `<a href="${p.whatsapp_url}" target="_blank" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-medium flex items-center transition shadow-2xs"><i class="fa-brands fa-whatsapp mr-1"></i>WhatsApp</a>` : ''}
                            ${p.maps_url ? `<a href="${p.maps_url}" target="_blank" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 rounded text-[11px] font-medium flex items-center transition"><i class="fa-solid fa-diamond-turn-right mr-1"></i>Itinéraire</a>` : ''}
                        </div>
                    </div>
                `;
            });
            replyHtml += `</div>`;
        }

        if (data.safety_alert) {
            replyHtml = `
                <div class="p-3 bg-red-100 border-l-4 border-red-600 rounded text-red-800 text-xs font-semibold">
                    <i class="fa-solid fa-triangle-exclamation mr-1 text-base"></i> ${data.safety_alert}
                </div>
            `;
        }

        appendMessage('assistant', replyHtml, false, data.reply_text);

    } catch (err) {
        document.getElementById(loadingId)?.remove();
        appendMessage('assistant', `<span class="text-red-500 font-semibold">Erreur de connexion au serveur backend : ${err.message}</span>`, false);
    }
}

function formatMarkdownText(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '<br/><br/>')
        .replace(/\n/g, '<br/>');
}

function clearAttachedImage() {
    attachedImageFile = null;
    const previewBar = document.getElementById('attached-preview-bar');
    if (previewBar) previewBar.classList.add('hidden');
    const cameraInput = document.getElementById('camera-input');
    if (cameraInput) cameraInput.value = '';
}

function sendQuickMessage(text) {
    userInput.value = text;
    sendMessage(text);
}

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage(userInput.value);
});

// ----------------------------------------------------------------------------------
// Enregistrement Micro Universel via MediaRecorder (Compatible Tous Navigateurs)
// ----------------------------------------------------------------------------------
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

async function setupUniversalAudioRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        voiceBtn.style.display = 'none';
        return;
    }

    voiceBtn.addEventListener('click', async () => {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    // Stopper tous les flux micro
                    stream.getTracks().forEach(track => track.stop());

                    // Envoi vers le serveur backend pour transcription
                    userInput.placeholder = "⏳ Transcription vocale en cours...";
                    const formData = new FormData();
                    formData.append('file', audioBlob, 'voice_record.webm');

                    try {
                        const res = await fetch('/api/audio/transcribe', {
                            method: 'POST',
                            body: formData
                        });
                        const resData = await res.json();
                        if (resData.text && resData.text.trim()) {
                            userInput.value = resData.text;
                            sendMessage(resData.text);
                        } else {
                            alert("Aucune parole détectée avec certitude. Veuillez réessayer ou taper votre message.");
                        }
                    } catch (err) {
                        console.error("Erreur de transcription :", err);
                        alert("Erreur lors de la transcription vocale.");
                    } finally {
                        userInput.placeholder = "Écrivez votre message en Darija, Arabizi ou Français...";
                    }
                };

                mediaRecorder.start();
                isRecording = true;
                voiceBtn.classList.remove('text-slate-500');
                voiceBtn.classList.add('text-red-600', 'bg-red-50', 'animate-pulse');
                userInput.placeholder = "🔴 Enregistrement en cours... Cliquez à nouveau sur le micro pour valider.";
            } catch (err) {
                console.error("Erreur accès micro :", err);
                alert("Accès au microphone refusé ou non disponible. Veuillez vérifier les autorisations du navigateur.");
            }
        } else {
            // Arrêter l'enregistrement
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
            isRecording = false;
            voiceBtn.classList.remove('text-red-600', 'bg-red-50', 'animate-pulse');
            voiceBtn.classList.add('text-slate-500');
        }
    });
}

// ----------------------------------------------------------------------------------
// Module Vision & OCR (Challenge #2) — Scan de Boîte de Médicaments
// ----------------------------------------------------------------------------------

function setupCameraAndVision() {
    const cameraBtn = document.getElementById('camera-btn');
    const cameraInput = document.getElementById('camera-input');
    const cancelAttachBtn = document.getElementById('cancel-attach-btn');
    const attachedPreviewBar = document.getElementById('attached-preview-bar');
    const attachedThumb = document.getElementById('attached-thumb');

    if (!cameraBtn || !cameraInput) return;

    cameraBtn.addEventListener('click', () => {
        cameraInput.click();
    });

    if (cancelAttachBtn) {
        cancelAttachBtn.addEventListener('click', () => {
            clearAttachedImage();
        });
    }

    cameraInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        attachedImageFile = file;
        if (attachedThumb && attachedPreviewBar) {
            attachedThumb.src = URL.createObjectURL(file);
            attachedPreviewBar.classList.remove('hidden');
        }
        userInput.placeholder = "Posez une question sur cette boîte (ou appuyez sur Entrée)...";
        userInput.focus();
    });
}

async function uploadAndScanMedicationBox(file, hintTokens = null) {
    if (!file) return;

    // 1. Lire la miniature de l'image pour l'afficher côté utilisateur
    const reader = new FileReader();
    reader.onload = async (e) => {
        const imgUrl = e.target.result;
        const userHtml = `
            <div class="space-y-1.5">
                <p class="font-medium">📷 Photo de boîte envoyée :</p>
                <img src="${imgUrl}" class="max-w-[220px] max-h-[140px] rounded-lg border border-slate-200 shadow-sm object-cover" alt="Boîte envoyée" />
            </div>
        `;
        appendMessage('user', userHtml, true);

        // Indicateur de chargement
        const loadingId = 'loading-vision-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'flex items-start space-x-3';
        loadingDiv.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-teal-600 text-white flex items-center justify-center flex-shrink-0 text-sm shadow">
                <i class="fa-solid fa-camera animate-spin"></i>
            </div>
            <div class="bg-slate-100 rounded-2xl rounded-tl-none p-3.5 max-w-lg shadow-sm text-sm text-slate-500">
                <i class="fa-solid fa-circle-notch fa-spin mr-2 text-teal-600"></i> Traitement Vision, CLAHE, OCR bilingue et matching CNOPS en cours...
            </div>
        `;
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        const formData = new FormData();
        formData.append('image', file, file.name || 'medication_box.jpg');
        if (hintTokens) {
            formData.append('hint_tokens', hintTokens);
        }

        try {
            const res = await fetch('/vision/recognize', {
                method: 'POST',
                body: formData
            });

            document.getElementById(loadingId)?.remove();

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || "Erreur lors de l'analyse optique de l'image.");
            }

            const data = await res.json();
            renderVisionScanResponse(data);

        } catch (err) {
            document.getElementById(loadingId)?.remove();
            appendMessage('assistant', `<span class="text-red-500 font-semibold"><i class="fa-solid fa-triangle-exclamation mr-1"></i> Erreur Vision : ${err.message}</span>`, false);
        }
    };
    reader.readAsDataURL(file);
}

function renderVisionScanResponse(data) {
    let statusBadge = '';
    let scoreColor = 'teal';

    if (data.status === 'validated') {
        statusBadge = `<span class="bg-emerald-100 text-emerald-800 border border-emerald-300 px-2 py-0.5 rounded-full text-xs font-bold"><i class="fa-solid fa-check-circle mr-1"></i> Identifié avec Certitude</span>`;
        scoreColor = 'emerald';
    } else if (data.status === 'ambiguous') {
        statusBadge = `<span class="bg-amber-100 text-amber-800 border border-amber-300 px-2 py-0.5 rounded-full text-xs font-bold"><i class="fa-solid fa-triangle-exclamation mr-1"></i> Validation Requise</span>`;
        scoreColor = 'amber';
    } else {
        statusBadge = `<span class="bg-red-100 text-red-800 border border-red-300 px-2 py-0.5 rounded-full text-xs font-bold"><i class="fa-solid fa-times-circle mr-1"></i> Rejet Optique (< 0.60)</span>`;
        scoreColor = 'red';
    }

    let replyHtml = `
        <div class="space-y-3">
            <div class="flex items-center justify-between border-b border-slate-200 pb-2">
                <span class="font-bold text-slate-800 text-sm"><i class="fa-solid fa-microchip text-teal-600 mr-1.5"></i> Reconnaissance Visuelle (Challenge #2)</span>
                ${statusBadge}
            </div>

            <!-- Score composite -->
            <div class="bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs">
                <div class="flex justify-between items-center mb-1">
                    <span class="font-semibold text-slate-700">Score de Confiance Composite :</span>
                    <span class="font-bold text-${scoreColor}-600">${(data.composite_score * 100).toFixed(0)}%</span>
                </div>
                <div class="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                    <div class="bg-teal-600 h-2 rounded-full" style="width: ${Math.min(100, data.composite_score * 100)}%"></div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>Conf. OCR : ${(data.conf_ocr * 100).toFixed(0)}%</span>
                    <span>Similarité CNOPS : ${(data.sim_matching * 100).toFixed(0)}%</span>
                    <span>Redressement : ${data.skew_angle}°</span>
                </div>
            </div>

            <p class="text-sm text-slate-700">${data.message}</p>
    `;

    // Si médicament identifié
    if (data.matched_drug) {
        const drug = data.matched_drug;
        replyHtml += `
            <div class="bg-white border-2 border-teal-500 rounded-xl p-3.5 shadow-sm space-y-2">
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="font-bold text-slate-900 text-sm">${drug.nom}</h4>
                        <p class="text-xs text-slate-500">DCI : <span class="font-semibold text-slate-700">${drug.dci || 'Non spécifiée'}</span></p>
                    </div>
                    <span class="bg-teal-50 text-teal-800 font-bold px-2.5 py-1 rounded-lg text-sm border border-teal-200">
                        ${drug.ppv.toFixed(2)} MAD
                    </span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-xs text-slate-600 pt-1">
                    <div><span class="text-slate-400">Dosage :</span> ${drug.dosage || 'N/A'}</div>
                    <div><span class="text-slate-400">Forme :</span> ${drug.forme || 'N/A'}</div>
                    <div><span class="text-slate-400">Type :</span> ${drug.is_generique ? 'Générique' : 'Princeps'}</div>
                    <div><span class="text-slate-400">Code CIP :</span> <code class="bg-slate-100 px-1 py-0.5 rounded">${drug.cip}</code></div>
                </div>

                <div class="pt-2 border-t border-slate-100 flex space-x-2">
                    <button onclick="sendQuickMessage('Trouver pharmacie pour ${drug.nom}')" class="flex-1 bg-teal-600 hover:bg-teal-700 text-white text-xs font-medium py-1.5 px-3 rounded-lg transition text-center shadow-sm">
                        📍 Trouver en pharmacie
                    </button>
                    <button onclick="sendQuickMessage('Générique f blast ${drug.nom}')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium py-1.5 px-3 rounded-lg transition">
                        🔄 Génériques
                    </button>
                </div>
            </div>
        `;
    }

    // Alternatives génériques
    if (data.generics && data.generics.length > 0) {
        replyHtml += `
            <div class="pt-1">
                <span class="text-xs font-bold text-slate-700 block mb-1.5">💡 Génériques équivalents plus économiques :</span>
                <div class="space-y-1.5">
        `;
        data.generics.forEach(g => {
            replyHtml += `
                <div class="bg-emerald-50 border border-emerald-200 rounded-lg p-2 flex justify-between items-center text-xs">
                    <div>
                        <span class="font-bold text-emerald-900">${g.nom}</span>
                        <span class="text-emerald-700 text-[11px] block">${g.dosage} - ${g.forme}</span>
                    </div>
                    <div class="text-right">
                        <span class="font-bold text-emerald-800">${g.ppv.toFixed(2)} MAD</span>
                        ${g.savings_mad > 0 ? `<span class="block text-[10px] text-emerald-600 font-semibold">-${g.savings_mad.toFixed(2)} MAD</span>` : ''}
                    </div>
                </div>
            `;
        });
        replyHtml += `</div></div>`;
    }

    // Avertissement réglementaire
    replyHtml += `
            <div class="pt-2 border-t border-slate-100 text-[10px] text-slate-400 leading-tight">
                <i class="fa-solid fa-shield-halved text-amber-500 mr-1"></i> ${data.disclaimer}
            </div>
        </div>
    `;

    appendMessage('assistant', replyHtml, false, data.message);

    // Mettre à jour l'inspecteur NLU & Vision
    updateVisionInspector(data);
}

function updateVisionInspector(data) {
    const insp = document.getElementById('inspector-vision');
    if (!insp) return;

    const roi = data.roi_box || {};
    insp.innerHTML = `
        <div class="space-y-1.5 text-[11px]">
            <div class="flex justify-between items-center">
                <span class="text-slate-500 font-semibold">Statut :</span>
                <span class="font-mono font-bold ${data.status === 'validated' ? 'text-emerald-600' : (data.status === 'ambiguous' ? 'text-amber-600' : 'text-red-600')}">${data.status.toUpperCase()}</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-slate-500">Score Composite :</span>
                <span class="font-mono font-bold text-teal-700">${(data.composite_score * 100).toFixed(0)}%</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-slate-500">RoI Détectée :</span>
                <span class="font-mono text-slate-600">[${roi.x || 0}, ${roi.y || 0}, ${roi.w || 0}x${roi.h || 0}]</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-slate-500">Angle Deskew :</span>
                <span class="font-mono text-slate-600">${data.skew_angle || 0}°</span>
            </div>
            ${data.extracted_text?.fr ? `
                <div class="pt-1 border-t border-slate-200">
                    <span class="text-slate-500 block">Texte OCR FR :</span>
                    <span class="font-mono text-slate-700 block truncate">${data.extracted_text.fr}</span>
                </div>
            ` : ''}
            ${data.extracted_text?.ar ? `
                <div class="pt-1 border-t border-slate-200">
                    <span class="text-slate-500 block">Texte OCR Arabe :</span>
                    <span class="font-mono text-slate-700 block truncate" dir="rtl">${data.extracted_text.ar}</span>
                </div>
            ` : ''}
        </div>
    `;
}

// Fonction de démo en 1-clic pour le professeur
async function triggerSamplePhotoScan() {
    // Créer une image simulée sur un canvas HTML5 avec le packaging bilingue d'Augmentin
    const canvas = document.createElement('canvas');
    canvas.width = 600;
    canvas.height = 380;
    const ctx = canvas.getContext('2d');

    // Fond blanc avec liseré pharmaceutique
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#ffffff';
    ctx.strokeStyle = '#0d9488';
    ctx.lineWidth = 6;
    ctx.fillRect(40, 30, 520, 320);
    ctx.strokeRect(40, 30, 520, 320);

    // Bandeau couleur marque
    ctx.fillStyle = '#2563eb';
    ctx.fillRect(40, 30, 520, 65);

    // Titre de marque
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 32px sans-serif';
    ctx.fillText('AUGMENTIN 1g / 125mg', 60, 75);

    // Inscription en Arabe
    ctx.fillStyle = '#0f172a';
    ctx.font = 'bold 24px sans-serif';
    ctx.fillText('أوغمنتين 1 غرام', 380, 140);

    // Dosage & Forme
    ctx.fillStyle = '#dc2626';
    ctx.font = 'bold 22px sans-serif';
    ctx.fillText('Amoxicilline / Acide clavulanique', 60, 140);

    ctx.fillStyle = '#475569';
    ctx.font = '16px sans-serif';
    ctx.fillText('Poudre pour suspension buvable en sachet-dose', 60, 180);
    ctx.fillText('Boîte de 12 sachets - Voie orale', 60, 210);

    // Code CIP et fabricant
    ctx.fillStyle = '#94a3b8';
    ctx.font = '12px monospace';
    ctx.fillText('CIP: 3274241 | GSK GlaxoSmithKline', 60, 310);

    canvas.toBlob(async (blob) => {
        if (!blob) return;
        const fakeFile = new File([blob], 'boite_augmentin_1g.jpg', { type: 'image/jpeg' });
        await uploadAndScanMedicationBox(fakeFile, "AUGMENTIN, 1G, POUDRE");
    }, 'image/jpeg');
}

// Initialisation au chargement
window.addEventListener('DOMContentLoaded', () => {
    initMap();
    setupUniversalAudioRecording();
    setupCameraAndVision();
});
