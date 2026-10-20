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

async function sendMessage(text) {
    if (!text || !text.trim()) return;

    appendMessage('user', text, true);
    userInput.value = '';

    const loadingId = 'loading-' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.id = loadingId;
    loadingDiv.className = 'flex items-start space-x-3';
    loadingDiv.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-teal-600 text-white flex items-center justify-center flex-shrink-0 text-sm shadow animate-pulse">
            <i class="fa-solid fa-spinner fa-spin"></i>
        </div>
        <div class="bg-slate-100 text-slate-500 rounded-2xl rounded-tl-none p-3 max-w-xs shadow-sm text-xs italic">
            Analyse NLU & recherche dans le référentiel CNOPS...
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                lat: currentLat,
                lng: currentLng
            })
        });

        const data = await response.json();
        document.getElementById(loadingId)?.remove();

        updateInspector(data);

        let replyHtml = `<p>${data.reply_text}</p>`;

        if (data.matched_drug) {
            const d = data.matched_drug;
            replyHtml += `
                <div class="mt-2 p-2.5 bg-white border border-teal-200 rounded-xl shadow-xs text-xs">
                    <div class="flex justify-between items-start font-bold text-slate-800">
                        <span>💊 ${d.nom}</span>
                        <span class="text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">${d.ppv.toFixed(2)} DH</span>
                    </div>
                    <div class="text-slate-500 mt-1">DCI : <strong>${d.dci}</strong> (${d.dosage} ${d.unite_dosage || ''})</div>
                    <div class="text-slate-500">Forme : ${d.forme} - ${d.presentation}</div>
                    <div class="mt-1 flex items-center space-x-2 text-[11px] text-slate-600">
                        <span class="bg-slate-100 px-1.5 py-0.5 rounded">${d.princeps_generique}</span>
                        <span class="text-emerald-700">Remboursement CNOPS/AMO: ${d.taux_remboursement}</span>
                    </div>
                </div>
            `;
        }

        if (data.alternatives && data.alternatives.length > 0) {
            replyHtml += `<div class="mt-2 font-semibold text-xs text-purple-800">🔄 Génériques équivalents disponibles :</div><div class="space-y-1 mt-1">`;
            data.alternatives.slice(0, 3).forEach(alt => {
                replyHtml += `
                    <div class="p-2 bg-purple-50 border border-purple-200 rounded-lg text-xs flex justify-between items-center">
                        <div>
                            <span class="font-bold text-purple-900">${alt.nom}</span>
                            <span class="text-slate-500 text-[11px] block">${alt.forme} - ${alt.presentation}</span>
                        </div>
                        <span class="font-bold text-purple-800">${alt.ppv.toFixed(2)} DH</span>
                    </div>
                `;
            });
            replyHtml += `</div>`;
        }

        if (data.pharmacies && data.pharmacies.length > 0) {
            replyHtml += `<div class="mt-2 font-semibold text-xs text-blue-800">📍 Officines à proximité (visibles sur la carte) :</div><div class="space-y-1.5 mt-1">`;
            data.pharmacies.slice(0, 3).forEach(p => {
                const isGarde = Boolean(p.garde);
                replyHtml += `
                    <div class="p-2.5 bg-white border ${isGarde ? 'border-green-300 ring-1 ring-green-200' : 'border-slate-200'} rounded-lg text-xs">
                        <div class="flex justify-between items-center">
                            <span class="font-bold text-slate-800">${p.title}</span>
                            ${isGarde ? '<span class="bg-green-100 text-green-800 font-bold px-1.5 py-0.5 rounded text-[10px]"><i class="fa-solid fa-moon mr-1"></i>GARDE ACTIVE</span>' : ''}
                        </div>
                        <div class="text-slate-500 text-[11px] mt-0.5">${p.address || p.ville}</div>
                        <div class="flex justify-between items-center mt-1 text-[11px] text-slate-600">
                            <span><i class="fa-solid fa-phone text-slate-400 mr-1"></i>${p.phone || 'Non renseigné'}</span>
                            <span class="text-slate-500 font-mono">${p.distance_km ? p.distance_km + ' km' : p.ville}</span>
                            <a href="https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}" target="_blank" class="text-teal-600 hover:underline">
                                <i class="fa-solid fa-diamond-turn-right mr-1"></i>Itinéraire
                            </a>
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

// Initialisation au chargement
window.addEventListener('DOMContentLoaded', () => {
    initMap();
    setupUniversalAudioRecording();
});
