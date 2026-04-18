const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
  ? 'http://127.0.0.1:8000'
  : 'http://127.0.0.1:8000';

const chatBox = document.getElementById('chatBox');
const userInput = document.getElementById('userInput');
const chatForm = document.getElementById('chatForm');
const statusPill = document.getElementById('statusPill');
const supportPanel = document.getElementById('supportPanel');
const promptButtons = document.querySelectorAll('.prompt-chip');

const sessionId = sessionStorage.getItem('mindbridge_session_id') || crypto.randomUUID();
sessionStorage.setItem('mindbridge_session_id', sessionId);

let conversation = [];

promptButtons.forEach((button) => {
  button.addEventListener('click', () => {
    userInput.value = button.dataset.prompt || '';
    userInput.focus();
  });
});

chatForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;

  addMessage(text, 'user');
  conversation.push({ role: 'user', content: text });
  userInput.value = '';
  setStatus('Thinking...', '');
  toggleInput(false);
  clearSupportPanel();

  const typingId = addTypingIndicator();

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        session_id: sessionId,
        history: conversation.slice(-8)
      })
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }

    const data = await response.json();
    removeTypingIndicator(typingId);

    addMessage(data.reply, 'bot');
    conversation.push({ role: 'assistant', content: data.reply });

    renderSupportPanel(data.resources || [], null, data.next_steps || []);
    setStatus('Listening', '');

  } catch (error) {
    removeTypingIndicator(typingId);
    addMessage(
      'I am having trouble reaching the support service right now. Please try again in a moment. If this feels urgent, contact Samaritans on 116 123 or NHS 111.',
      'system'
    );
    setStatus('Offline', '');
  } finally {
    toggleInput(true);
    userInput.focus();
  }
});

function addMessage(text, sender) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}`;

  if (sender === 'bot') {
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    meta.textContent = 'MindBridge';
    messageDiv.appendChild(meta);
  }

  const paragraph = document.createElement('p');
  paragraph.textContent = text;
  messageDiv.appendChild(paragraph);
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function addTypingIndicator() {
  const wrapper = document.createElement('div');
  const id = `typing-${Date.now()}`;
  wrapper.id = id;
  wrapper.className = 'message bot';
  wrapper.innerHTML = `
    <div class="message-meta">MindBridge</div>
    <div class="typing-indicator" aria-label="Assistant is typing">
      <span></span><span></span><span></span>
    </div>
  `;
  chatBox.appendChild(wrapper);
  chatBox.scrollTop = chatBox.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const node = document.getElementById(id);
  if (node) node.remove();
}

function renderSupportPanel(resources, riskLevel, nextSteps) {
  const cards = [];

  if (nextSteps.length) {
    cards.push(`
      <article class="resource-card">
        <h4>Suggested next step</h4>
        <p>${escapeHtml(nextSteps.join(' '))}</p>
      </article>
    `);
  }

  resources.forEach((resource) => {
    cards.push(`
      <article class="resource-card">
        <h4>${escapeHtml(resource.name)}</h4>
        <p>${escapeHtml(resource.description)}</p>
        <p><strong>${escapeHtml(resource.contact_label)}:</strong> ${escapeHtml(resource.contact_value)}</p>
        ${resource.url ? `<a href="${resource.url}" target="_blank" rel="noopener noreferrer">Visit resource</a>` : ''}
      </article>
    `);
  });

  if (!cards.length) {
    supportPanel.classList.remove('active');
    supportPanel.innerHTML = '';
    return;
  }

  supportPanel.innerHTML = cards.join('');
  supportPanel.classList.add('active');
  supportPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function clearSupportPanel() {
  supportPanel.classList.remove('active');
  supportPanel.innerHTML = '';
}

function toggleInput(enabled) {
  userInput.disabled = !enabled;
  document.getElementById('sendBtn').disabled = !enabled;
}

function setStatus(text, level) {
  statusPill.textContent = text;
  statusPill.className = 'status-pill';
}

function capitalise(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function escapeHtml(text) {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

document.addEventListener("DOMContentLoaded", () => {
  const consentModal = document.getElementById("consentModal");
  const agreeBtn = document.getElementById("agreeBtn");

  if (!localStorage.getItem("mindbridge_consent")) {
    consentModal.style.display = "flex";
  }

  agreeBtn?.addEventListener("click", () => {
    localStorage.setItem("mindbridge_consent", "true");
    consentModal.style.display = "none";
  });
});