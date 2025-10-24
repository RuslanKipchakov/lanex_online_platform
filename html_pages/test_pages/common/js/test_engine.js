// =======================
// ✅ Telegram WebApp Integration (clean version)
// =======================
function initializeTelegramWebApp() {
  const tg = window.Telegram?.WebApp;

  if (!tg) {
    createFallbackTelegramField();
    return;
  }

  const userFromUnsafe = tg.initDataUnsafe?.user;
  const userFromInitData = tg.initData?.user;
  const user = userFromUnsafe || userFromInitData;

  if (user?.id) {
    setTelegramUserData(user.id);

    // Автоподстановка имени пользователя
    const usernameInput = document.getElementById('username');
    if (usernameInput && !usernameInput.value.trim()) {
      const userName = user.username || user.first_name || `user_${user.id}`;
      usernameInput.value = userName;
    }
  } else {
    createFallbackTelegramField();
  }
}

function setTelegramUserData(telegramId) {
  let telegramIdField = document.getElementById('telegram-id');

  if (!telegramIdField) {
    telegramIdField = document.createElement('input');
    telegramIdField.type = 'hidden';
    telegramIdField.id = 'telegram-id';
    telegramIdField.name = 'telegram_id';

    const form = document.getElementById('testForm') || document.querySelector('form');
    if (form) {
      form.appendChild(telegramIdField);
    } else {
      const submitBtn = document.querySelector('button[type="submit"], #submit-test');
      if (submitBtn) {
        submitBtn.parentNode.insertBefore(telegramIdField, submitBtn);
      } else {
        document.body.appendChild(telegramIdField);
      }
    }
  }

  telegramIdField.value = telegramId;
}

function createFallbackTelegramField() {
  let telegramIdField = document.getElementById('telegram-id');
  if (!telegramIdField) {
    telegramIdField = document.createElement('input');
    telegramIdField.type = 'hidden';
    telegramIdField.id = 'telegram-id';
    telegramIdField.name = 'telegram_id';
    telegramIdField.value = '';
    document.body.appendChild(telegramIdField);
  }
}

// =======================
// 🔙 Кнопка "Назад" — простая интеграция
// =======================
function initializeBackButton() {
  const tg = window.Telegram?.WebApp;
  const backBtn = document.getElementById("back-button");
  if (!backBtn) return;

  backBtn.addEventListener("click", (e) => {
    e.preventDefault();

    // 🟢 Если открыто внутри Telegram WebApp
    if (tg && typeof tg.close === "function") {
      tg.close();
      return;
    }

    // 🧩 Если страница открыта в браузере — fallback
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = "../../index.html";
    }
  });
}

// Инициализация при загрузке DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initializeTelegramWebApp();
    initializeBackButton();
  });
} else {
  initializeTelegramWebApp();
  initializeBackButton();
}


// =======================
// ⚙️ Основная логика test_engine.js
// =======================

const DEFAULT_OPTIONS = {
  endpoint: "/api/check_test",
  submitButtonIds: ["submit-test", "btn-check", "submit", "check"],
  resultContainerIds: ["final-message", "final-result", "result"],
  taskSelector: '[id^="task"]'
};

export function initTest(level, taskData = {}, options = {}) {
  const cfg = { ...DEFAULT_OPTIONS, ...options };
  const state = { level, taskData, cfg, lastPayload: null, lastResult: null };
  attachButtonHandlers(state);
  return state;
}

function collectAnswersFromDOM() {
  const answers = {};
  const taskBlocks = Array.from(document.querySelectorAll(DEFAULT_OPTIONS.taskSelector));

  taskBlocks.forEach(task => {
    const taskId = task.id || task.dataset.taskId;
    if (!taskId) return;
    answers[taskId] = {};

    const radios = Array.from(task.querySelectorAll('input[type="radio"]'));
    const radioNames = Array.from(new Set(radios.map(r => r.name).filter(Boolean)));
    radioNames.forEach(name => {
      const checked = task.querySelector(`input[type="radio"][name="${escapeCssSelector(name)}"]:checked`);
      const qnum = extractQnumFromNameOrElement(name, checked);
      answers[taskId][String(qnum)] = checked ? checked.value : "";
    });

    const checkboxes = Array.from(task.querySelectorAll('input[type="checkbox"]'));
    const checkboxNames = Array.from(new Set(checkboxes.map(c => c.name).filter(Boolean)));
    checkboxNames.forEach(name => {
      const checked = Array.from(task.querySelectorAll(`input[type="checkbox"][name="${escapeCssSelector(name)}"]:checked`)).map(i => i.value);
      const qnum = extractQnumFromNameOrElement(name);
      answers[taskId][String(qnum)] = checked;
    });

    const otherSelectors = 'textarea, select, input[type="text"], input[type="number"], input[type="email"], input[type="hidden"], input[type="tel"], input[type="url"]';
    const otherInputs = Array.from(task.querySelectorAll(otherSelectors));

    otherInputs.forEach((el, index) => {
      const qnumAttr = findQnumFromAncestor(el);
      const qnum = qnumAttr || extractQnumFromNameOrElement(el.name) || (index + 1);
      answers[taskId][String(qnum)] = (el.value || "").trim();
    });

    const questionBlocks = Array.from(task.querySelectorAll('.question'));
    questionBlocks.forEach((qb, idx) => {
      const qnum = qb.dataset.qnum || idx + 1;
      if (!(String(qnum) in answers[taskId])) {
        const checkedRadio = qb.querySelector('input[type="radio"]:checked');
        if (checkedRadio) answers[taskId][String(qnum)] = checkedRadio.value;
        else {
          const checkedCheckboxes = Array.from(qb.querySelectorAll('input[type="checkbox"]:checked')).map(i => i.value);
          if (checkedCheckboxes.length) answers[taskId][String(qnum)] = checkedCheckboxes;
          else {
            const ta = qb.querySelector('textarea');
            if (ta) answers[taskId][String(qnum)] = (ta.value || "").trim();
            else answers[taskId][String(qnum)] = "";
          }
        }
      }
    });
  });
  return answers;
}

async function postToServer(payload, cfg, timeoutMs = 8000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  const res = await fetch(cfg.endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal: controller.signal,
    body: JSON.stringify(payload)
  }).finally(() => clearTimeout(id));

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Server returned ${res.status} ${res.statusText} ${text}`);
  }
  return res.json();
}

function localCheckAnswers(answers, taskData) {
  const result = {};
  const totalFractions = [];

  for (const [taskId, dataArray] of Object.entries(taskData || {})) {
    if (!Array.isArray(dataArray) || dataArray.length === 0) {
      result[taskId] = "open";
      continue;
    }

    const first = dataArray[0];
    const isClosed = typeof first === "object" && first !== null && ('correct' in first);

    if (!isClosed) {
      result[taskId] = "open";
      continue;
    }

    const taskResult = {};
    let score = 0;
    const total = dataArray.length;

    for (let i = 0; i < total; i++) {
      const qnum = String(i + 1);
      const correct = String(dataArray[i].correct).trim();
      const userAnsForTask = (answers[taskId] && answers[taskId][qnum]) || "";
      const user = String(userAnsForTask).trim();
      if (user && user === correct) {
        taskResult[qnum] = "correct";
        score++;
      } else {
        taskResult[qnum] = "incorrect";
      }
    }

    taskResult["score"] = `${score}/${total}`;
    result[taskId] = taskResult;
    totalFractions.push(score / total);
  }

  if (totalFractions.length) {
    const avg = totalFractions.reduce((a, b) => a + b, 0) / totalFractions.length;
    result["total"] = `${(avg * 100).toFixed(1)}%`;
  } else {
    result["total"] = "0%";
  }

  return result;
}

function applyResultToPage(result, cfg) {
  const taskBlocks = Array.from(document.querySelectorAll(cfg.taskSelector));

  taskBlocks.forEach(task => {
    const taskId = task.id;
    if (!taskId) return;

    const taskRes = result[taskId];

    if (taskRes === "open") {
      replaceTaskWithOpenMessage(task);
      return;
    }

    if (!taskRes || typeof taskRes !== "object") return;

    const qBlocks = Array.from(task.querySelectorAll('.question'));
    qBlocks.forEach((qb, idx) => {
      const qnum = qb.dataset.qnum || String(idx + 1);
      const status = taskRes[String(qnum)];
      qb.classList.remove("correct-block", "incorrect-block");
      if (status === "correct") qb.classList.add("correct-block");
      else if (status === "incorrect") qb.classList.add("incorrect-block");
    });

    if (taskRes.score) {
      let scoreNode = task.querySelector('.task-score');
      if (!scoreNode) {
        scoreNode = document.createElement('div');
        scoreNode.className = 'task-score';
        task.appendChild(scoreNode);
      }
      scoreNode.textContent = `Баллы: ${taskRes.score}`;
    }
  });

  displayTotalResult(result, cfg);
  disableAllInputs();
  hideSubmitButton(cfg);
}

function replaceTaskWithOpenMessage(taskBlock) {
  taskBlock.innerHTML = `
    <div class="question open-task-message" style="padding:15px;">
      <p><strong>Это задание проверит преподаватель.</strong></p>
      <p>Ответы будут проверены вручную; вы получите результат позже.</p>
    </div>
  `;
}

function disableAllInputs() {
  const all = Array.from(document.querySelectorAll('input, textarea, select'));
  all.forEach(el => {
    el.disabled = true;
    el.setAttribute('aria-disabled', 'true');
  });
}

function displayTotalResult(result, cfg) {
  const containerId = cfg.resultContainerIds.find(id => document.getElementById(id));
  let container = containerId ? document.getElementById(containerId) : null;

  if (!container) {
    const root = document.querySelector('.container') || document.body;
    container = document.createElement('div');
    container.id = cfg.resultContainerIds[0];
    container.className = 'total-score';
    root.appendChild(container);
  }

  const total = result.total || result['total'] || '';
  let html = `<h2>Спасибо за прохождение теста!</h2>`;
  if (total) {
    html += `<p><strong>Итог: </strong> ${total}</p>`;
  }

  for (const [taskId, taskRes] of Object.entries(result)) {
    if (taskId === 'total') continue;
    if (typeof taskRes === 'object' && taskRes.score) {
      html += `<p><strong>${taskId}:</strong> ${taskRes.score}</p>`;
    }
  }

  container.innerHTML = html;
}

function hideSubmitButton(cfg) {
  cfg.submitButtonIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
}

function attachButtonHandlers(state) {
  const cfg = state.cfg;

  let submitBtn = null;
  for (const id of cfg.submitButtonIds) {
    const el = document.getElementById(id);
    if (el) { submitBtn = el; break; }
  }
  if (!submitBtn) {
    submitBtn = document.querySelector('.buttons button[type="button"], .buttons button[type="submit"], .buttons button');
  }

  if (submitBtn) {
    submitBtn.addEventListener('click', async (ev) => {
      ev.preventDefault();
      await onSubmitClicked(state);
    });
  }
}

async function onSubmitClicked(state) {
  const cfg = state.cfg;
  const level = state.level;
  const taskData = state.taskData;

  const answers = collectAnswersFromDOM();
  const usernameInput = document.getElementById("username");
  const username = usernameInput ? usernameInput.value.trim() : "";

  const telegramIdInput = document.getElementById("telegram-id");
  const telegram_id = telegramIdInput ? parseInt(telegramIdInput.value, 10) : null;

  state.lastPayload = { username, level, telegram_id, answers };

  let result = null;
  try {
    result = await postToServer(state.lastPayload, cfg);
  } catch {
    result = localCheckAnswers(answers, taskData);
    result = { status: "ok", result };
  }

  state.lastResult = result;

  if (!result || !result.status) {
    alert("Ошибка: сервер не вернул статус. Попробуйте позже.");
    return;
  }

  if (result.status === "empty_form") {
    showEmptyFormWarning();
    return;
  }

  if (result.status !== "ok") {
    alert(`Ошибка при обработке теста: ${result.status}`);
    return;
  }

  const oldWarning = document.getElementById("empty-warning");
  if (oldWarning) oldWarning.remove();

  applyResultToPage(result.result || {}, cfg);
}

function escapeCssSelector(s) {
  if (!s) return s;
  return s.replace(/([ #.;?+*~\[\]:!^$()=<>|\\/])/g, '\\$1');
}

function extractQnumFromNameOrElement(nameOrElement, maybeCheckedEl=null) {
  if (!nameOrElement && maybeCheckedEl) nameOrElement = maybeCheckedEl.name || "";

  if (typeof nameOrElement === "string") {
    const matchQ = nameOrElement.match(/q(\d+)/i);
    if (matchQ) return matchQ[1];
    const anyDigit = nameOrElement.match(/(\d+)/);
    if (anyDigit) return anyDigit[1];
    return nameOrElement;
  }
  return "";
}

function findQnumFromAncestor(el) {
  let cur = el;
  while (cur && cur !== document.body) {
    if (cur.classList && cur.classList.contains('question')) {
      if (cur.dataset && cur.dataset.qnum) return cur.dataset.qnum;
    }
    cur = cur.parentElement;
  }
  return null;
}

function showEmptyFormWarning() {
  const existing = document.getElementById("empty-warning");
  if (existing) existing.remove();

  const msg = document.createElement("div");
  msg.id = "empty-warning";
  msg.className = "empty-warning";
  msg.innerHTML = `
    <p><strong>⚠️ Ваш тест не был отправлен.</strong></p>
    <p>Вы не заполнили ни одного ответа, поэтому результат не сохраняется.</p>
    <p>Пожалуйста, ответьте хотя бы на один вопрос и попробуйте снова.</p>
  `;

  const container = document.querySelector('.container') || document.body;
  container.appendChild(msg);
}
