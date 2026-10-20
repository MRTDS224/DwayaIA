// Logique Frontend pour Saydalia Bot avec Carte Leaflet et Synthèse Vocale (TTS)

let currentLat = 33.5731; // Casablanca par défaut
let currentLng = -7.5898;
let map = null;
let markersLayer = null;

// Initialisation de la carte Leaflet
function initMap() {
    map = L.map('pharmacy-map').setView([currentLat, currentLng], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);

    markersLayer = L.layerGroup().addTo(map);

    // Marqueur de l'utilisateur
    L.circleMarker([currentLat, currentLng], {
        radius: 7,
        fillColor: "#0284c7",
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.9
    }).addTo(map).bindPopup("<b>Votre position</b>");
}

// Mettre à jour les marqueurs des pharmacies sur la carte
function updateMapMarkers(pharmacies, centerLat, centerLng) {
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();

    if (centerLat && centerLng) {
        map.setView([centerLat, centerLng], 13);
    }

    pharmacies.forEach(p => {
        if (!p.lat || !p.lng) return;

        const isGarde = Boolean(p.garde);
        const markerColor = isGarde ? "#16a34a" : "#0d9488"; // Vert si garde, Teal sinon

        const marker = L.circleMarker([p.lat, p.lng], {
            radius: isGarde ? 9 : 7,
            fillColor: markerColor,
            color: "#ffffff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
        });

        const popupContent = `
            <div style="font-size: 12px; line-height: 1.4;">
                <b style="color: ${markerColor};">${p.title}</b><br/>
                ${isGarde ? '<span style="background: #dcfce7; color: #166534; font-weight: bold; padding: 2px 4px; border-radius: 4px; font-size: 10px;">GARDE 24H</span><br/>' : ''}
                ${p.address || p.ville}<br/>
                📞 ${p.phone || 'Non renseigné'}<br/>
                <a href="https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}" target="_blank" style="color: #0284c7; text-decoration: underline; font-weight: 500;">Ouvrir dans Google Maps</a>
            </div>
        `;

        marker.bindPopup(popupContent);
        markersLayer.addLayer(marker);
    });
}

// Fonction de Synthèse Vocale (Text-To-Speech)
function speakText(text) {
    if (!('speechSynthesis' in window)) {
        alert("La synthèse vocale n'est pas supportée par votre navigateur.");
        return;
    }

    window.speechSynthesis.cancel(); // Arrêter toute lecture précédente

    // Nettoyer le texte du markdown
    const cleanText = text
        .replace(/[*_#`]/g, '')
        .replace(/💡|💊|🔄|📍|🌙|📞|⚠️/g, '')
        .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Détecter si le texte contient principalement de l'arabe
    const isArabic = /[\u0600-\u06FF]/.test(cleanText);
    utterance.lang = isArabic ? 'ar-XA' : 'fr-FR';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    window.speechSynthesis.speak(utterance);
}

// Géolocalisation Utilisateur
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            currentLat = pos.coords.latitude;
            currentLng = pos.coords.longitude;
            document.getElementById('user-city').innerText = `GPS (${currentLat.toFixed(2)}, ${currentLng.toFixed(2)})`;
            if (map) {
                map.setView([currentLat, currentLng], 13);
            }
        },
        () => {
            console.log("Géolocalisation par défaut (Casablanca).");
        }
    );
}

const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const voiceBtn = document.getElementById('voice-btn');

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
        const audioBtn = rawTextToSpeak ? `
            <button onclick="speakText('${encodeURIComponent(rawTextToSpeak)}')" class="text-slate-400 hover:text-teal-600 p-1 float-right" title="Écouter la réponse vocale">
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

function updateInspector(data) {
    // 1. Intention
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

    // 2. Entités
    const entBox = document.getElementById('inspector-entities');
    const ents = data.entities || {};
    let entHtml = '';
    if (ents.medication) entHtml += `<div><span class="text-slate-400">Marque:</span> <span class="bg-teal-100 text-teal-800 px-1.5 py-0.5 rounded">${ents.medication}</span></div>`;
    if (ents.dosage_val) entHtml += `<div><span class="text-slate-400">Dosage:</span> <span class="bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">${ents.dosage_val} ${ents.dosage_unit || ''}</span></div>`;
    if (ents.galenic_form) entHtml += `<div><span class="text-slate-400">Forme:</span> <span class="bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded">${ents.galenic_form}</span></div>`;
    if (ents.location) entHtml += `<div><span class="text-slate-400">Ville:</span> <span class="bg-indigo-100 text-indigo-800 px-1.5 py-0.5 rounded">${ents.location}</span></div>`;
    entBox.innerHTML = entHtml || '<p class="text-slate-400 italic">Aucune entité extraite</p>';

    // 3. Médicament CNOPS
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

    // 4. Mettre à jour la carte avec les pharmacies retournées
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
                            ${isGarde ? '<span class="bg-green-100 text-green-800 font-bold px-1.5 py-0.5 rounded text-[10px]"><i class="fa-solid fa-moon mr-1"></i>GARDE 24H</span>' : ''}
                        </div>
                        <div class="text-slate-500 text-[11px] mt-0.5">${p.address || p.ville}</div>
                        <div class="flex justify-between items-center mt-1 text-[11px] text-slate-600">
                            <span><i class="fa-solid fa-phone text-slate-400 mr-1"></i>${p.phone || 'Non renseigné'}</span>
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

// Reconnaissance vocale (SpeechRecognition)
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRec();
    recognition.lang = 'ar-MA';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
        voiceBtn.classList.add('text-red-600', 'animate-pulse');
        userInput.placeholder = "Écoute en cours... Parlez en Darija ou Français...";
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        sendMessage(transcript);
    };

    recognition.onerror = () => {
        voiceBtn.classList.remove('text-red-600', 'animate-pulse');
        userInput.placeholder = "Écrivez votre message en Darija, Arabizi ou Français...";
    };

    recognition.onend = () => {
        voiceBtn.classList.remove('text-red-600', 'animate-pulse');
        userInput.placeholder = "Écrivez votre message en Darija, Arabizi ou Français...";
    };

    voiceBtn.addEventListener('click', () => {
        try {
            recognition.start();
        } catch (e) {
            recognition.stop();
        }
    });
}

// Initialiser la carte au chargement du DOM
window.addEventListener('DOMContentLoaded', () => {
    initMap();
});
