// Logique Frontend pour Saydalia Bot

let currentLat = null;
let currentLng = null;

// Tenter de récupérer la géolocalisation de l'utilisateur
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            currentLat = pos.coords.latitude;
            currentLng = pos.coords.longitude;
            document.getElementById('user-city').innerText = `GPS (${currentLat.toFixed(2)}, ${currentLng.toFixed(2)})`;
        },
        () => {
            console.log("Géolocalisation refusée ou indisponible. Ville par défaut utilisée.");
        }
    );
}

const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const voiceBtn = document.getElementById('voice-btn');

function appendMessage(sender, htmlContent, isUser = false) {
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
        msgDiv.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-teal-600 text-white flex items-center justify-center flex-shrink-0 text-sm shadow">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="bg-slate-100 text-slate-800 rounded-2xl rounded-tl-none p-3.5 max-w-lg shadow-sm text-sm space-y-2">
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

    // 4. Pharmacies
    const pharmBox = document.getElementById('inspector-pharmacy');
    if (data.pharmacies && data.pharmacies.length > 0) {
        pharmBox.innerHTML = `
            <div class="font-bold text-slate-800">${data.pharmacies.length} officines identifiées</div>
            <div class="text-[11px] text-slate-500">Garde active: ${data.pharmacies.filter(p => p.garde).length}</div>
        `;
    } else {
        pharmBox.innerHTML = '<p class="text-slate-400 italic">Aucune officine requêtée</p>';
    }
}

async function sendMessage(text) {
    if (!text || !text.trim()) return;

    appendMessage('user', text, true);
    userInput.value = '';

    // Loader temporaire
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

        // Mettre à jour l'inspecteur NLU
        updateInspector(data);

        // Formater le message assistant
        let replyHtml = `<p>${data.reply_text}</p>`;

        // Si médicament identifié
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

        // Si alternatives / génériques trouvés
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

        // Si pharmacies de garde ou proches
        if (data.pharmacies && data.pharmacies.length > 0) {
            replyHtml += `<div class="mt-2 font-semibold text-xs text-blue-800">📍 Officines à proximité :</div><div class="space-y-1.5 mt-1">`;
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
                            <span class="text-slate-400 font-mono">${p.distance_km < 900 ? p.distance_km + ' km' : p.ville}</span>
                        </div>
                    </div>
                `;
            });
            replyHtml += `</div>`;
        }

        // Alerte d'urgence vitale
        if (data.safety_alert) {
            replyHtml = `
                <div class="p-3 bg-red-100 border-l-4 border-red-600 rounded text-red-800 text-xs font-semibold">
                    <i class="fa-solid fa-triangle-exclamation mr-1 text-base"></i> ${data.safety_alert}
                </div>
            `;
        }

        appendMessage('assistant', replyHtml, false);

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

// Reconnaissance vocale navigateur (Web Speech API)
let recognition = null;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRec();
    recognition.lang = 'ar-MA'; // ou 'fr-FR'
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
} else {
    voiceBtn.addEventListener('click', () => {
        alert("La reconnaissance vocale directe n'est pas supportée par votre navigateur. Vous pouvez saisir votre requête au clavier.");
    });
}

