function initializeTelegramWebApp() {
  const tg = window.Telegram?.WebApp;

  if (!tg) {
    createFallbackTelegramField();
    return;
  }

  const user = tg.initDataUnsafe?.user || tg.initData?.user;

  if (!user?.id) {
    createFallbackTelegramField();
    return;
  }

  setTelegramUserData(user.id);

  const usernameInput = document.getElementById('username');

  if (usernameInput && !usernameInput.value.trim()) {
    usernameInput.value =
      user.username ||
      user.first_name ||
      `user_${user.id}`;
  }
}

function setTelegramUserData(telegramId) {
  let field = document.getElementById('telegram-id');

  if (!field) {
    field = document.createElement('input');
    field.type = 'hidden';
    field.id = 'telegram-id';
    field.name = 'telegram_id';

    const form = document.getElementById('testForm') || document.querySelector('form');

    if (form) {
      form.append(field);
    } else {
      const submitButton = document.querySelector('button[type="submit"], #submit-test');

      if (submitButton?.parentNode) {
        submitButton.parentNode.insertBefore(field, submitButton);
      } else {
        document.body.append(field);
      }
    }
  }

  field.value = telegramId;
}

function createFallbackTelegramField() {
  if (document.getElementById('telegram-id')) return;

  const field = document.createElement('input');
  field.type = 'hidden';
  field.id = 'telegram-id';
  field.name = 'telegram_id';
  field.value = '';

  document.body.append(field);
}

function initializeBackButton() {
  const tg = window.Telegram?.WebApp;
  const backBtn = document.getElementById('back-button');

  if (!backBtn || typeof tg?.close !== 'function') return;

  backBtn.addEventListener('click', (e) => {
    e.preventDefault();
    tg.close();
  });
}

function initPage() {
  initializeTelegramWebApp();
  initializeBackButton();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPage);
} else {
  initPage();
}

const DEFAULT_OPTIONS = {
  endpoint: '/api/check_test',
  submitButtonIds: ['submit-test', 'btn-check', 'submit', 'check'],
  resultContainerIds: ['final-message', 'final-result', 'result'],
  taskSelector: '[id^="task"]'
};

function showLoader() {
  const loader = document.getElementById('loader');
  if (loader) loader.classList.add('active');
}

function hideLoader() {
  const loader = document.getElementById('loader');
  if (loader) loader.classList.remove('active');
}

export function initTest(level, taskData = {}, options = {}) {
  const cfg = { ...DEFAULT_OPTIONS, ...options };

  const state = {
    level,
    taskData,
    cfg,
    lastPayload: null,
    lastResult: null
  };

  attachButtonHandlers(state);

  return state;
}

function collectAnswersFromDOM() {
  const answers = {};
  const tasks = Array.from(document.querySelectorAll(DEFAULT_OPTIONS.taskSelector));

  tasks.forEach((task) => {
    const taskId = task.id || task.dataset.taskId;
    if (!taskId) return;

    answers[taskId] = {};

    // ===== Радио-кнопки =====
    const radios = Array.from(task.querySelectorAll('input[type="radio"]'));
    const radioNames = Array.from(new Set(radios.map(r => r.name).filter(Boolean)));

    radioNames.forEach((name) => {
      const checked = task.querySelector(
        `input[type="radio"][name="${escapeCssSelector(name)}"]:checked`
      );

      const qnum = extractQnumFromNameOrElement(name, checked);
      answers[taskId][String(qnum)] = checked ? checked.value : '';
    });

    // ===== Чекбоксы =====
    const checkboxes = Array.from(task.querySelectorAll('input[type="checkbox"]'));
    const checkboxNames = Array.from(new Set(checkboxes.map(c => c.name).filter(Boolean)));

    checkboxNames.forEach((name) => {
      const checked = Array.from(
        task.querySelectorAll(
          `input[type="checkbox"][name="${escapeCssSelector(name)}"]:checked`
        )
      ).map(i => i.value);

      const qnum = extractQnumFromNameOrElement(name);
      answers[taskId][String(qnum)] = checked;
    });

    // ===== Остальные поля =====
    const otherSelectors = `
      textarea,
      select,
      input[type="text"],
      input[type="number"],
      input[type="email"],
      input[type="hidden"],
      input[type="tel"],
      input[type="url"]
    `;

    const otherInputs = Array.from(task.querySelectorAll(otherSelectors));

    otherInputs.forEach((el, index) => {
      const qnumAttr = findQnumFromAncestor(el);
      const qnum =
        qnumAttr ||
        extractQnumFromNameOrElement(el.name) ||
        (index + 1);

      answers[taskId][String(qnum)] = (el.value || '').trim();
    });

    // ===== Фолбэк через .question =====
    const questionBlocks = Array.from(task.querySelectorAll('.question'));

    questionBlocks.forEach((qb, index) => {
      const qnum = qb.dataset.qnum || index + 1;

      if (String(qnum) in answers[taskId]) return;

      const checkedRadio = qb.querySelector('input[type="radio"]:checked');
      if (checkedRadio) {
        answers[taskId][String(qnum)] = checkedRadio.value;
        return;
      }

      const checkedCheckboxes = Array.from(
        qb.querySelectorAll('input[type="checkbox"]:checked')
      ).map(i => i.value);

      if (checkedCheckboxes.length) {
        answers[taskId][String(qnum)] = checkedCheckboxes;
        return;
      }

      const textarea = qb.querySelector('textarea');

      if (textarea) {
        answers[taskId][String(qnum)] = (textarea.value || '').trim();
      } else {
        answers[taskId][String(qnum)] = '';
      }
    });
  });

  return answers;
}

async function postToServer(payload, cfg, timeoutMs = 8000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(cfg.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal
    });

    if (!response.ok) {
      const text = await response.text().catch(() => '');
      throw new Error(`Server returned ${response.status} ${response.statusText} ${text}`);
    }

    return response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

function localCheckAnswers(answers, taskData) {
  const result = {};
  const totalFractions = [];

  for (const [taskId, dataArray] of Object.entries(taskData || {})) {
    if (!Array.isArray(dataArray) || dataArray.length === 0) {
      result[taskId] = 'open';
      continue;
    }

    const first = dataArray[0];
    const isClosed = typeof first === 'object' && first !== null && 'correct' in first;

    if (!isClosed) {
      result[taskId] = 'open';
      continue;
    }

    const taskResult = {};
    let score = 0;
    const total = dataArray.length;

    for (let i = 0; i < total; i++) {
      const qnum = String(i + 1);
      const correct = String(dataArray[i].correct).trim();
      const userAns = (answers[taskId]?.[qnum] || '').trim();

      if (userAns && userAns === correct) {
        taskResult[qnum] = 'correct';
        score++;
      } else {
        taskResult[qnum] = 'incorrect';
      }
    }

    taskResult.score = `${score}/${total}`;
    result[taskId] = taskResult;
    totalFractions.push(score / total);
  }

  result.total = totalFractions.length
    ? `${((totalFractions.reduce((a, b) => a + b, 0) / totalFractions.length) * 100).toFixed(1)}%`
    : '0%';

  return result;
}

function applyResultToPage(result, cfg) {
  const taskBlocks = Array.from(document.querySelectorAll(cfg.taskSelector));

  taskBlocks.forEach((task) => {
    const taskId = task.id;
    if (!taskId) return;

    const taskRes = result[taskId];

    if (taskRes === 'open') {
      replaceTaskWithOpenMessage(task);
      return;
    }

    if (!taskRes || typeof taskRes !== 'object') return;

    // ===== Проставляем классы для вопросов =====
    const qBlocks = Array.from(task.querySelectorAll('.question'));

    qBlocks.forEach((qb, idx) => {
      const qnum = qb.dataset.qnum || String(idx + 1);
      const status = taskRes[String(qnum)];

      qb.classList.remove('correct-block', 'incorrect-block');

      if (status === 'correct') qb.classList.add('correct-block');
      else if (status === 'incorrect') qb.classList.add('incorrect-block');
    });

    // ===== Проставляем баллы =====
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
  const title = taskBlock.querySelector('h2');
  taskBlock.innerHTML = '';

  if (title) {
    taskBlock.appendChild(title);
  }

  const message = document.createElement('div');
  message.className = 'question open-task-message';
  message.style.padding = '15px';
  message.innerHTML = `
    <p><strong>Это задание проверит преподаватель.</strong></p>
    <p>Ответы будут проверены вручную; вы получите результат позже.</p>
  `;

  taskBlock.appendChild(message);
}

function disableAllInputs() {
  const inputs = Array.from(document.querySelectorAll('input, textarea, select'));

  inputs.forEach((el) => {
    el.disabled = true;
    el.setAttribute('aria-disabled', 'true');
  });
}

function displayTotalResult(result, cfg) {
  let containerId = cfg.resultContainerIds.find((id) => document.getElementById(id));
  let container = containerId ? document.getElementById(containerId) : null;

  if (!container) {
    const root = document.querySelector('.container') || document.body;
    container = document.createElement('div');
    container.id = cfg.resultContainerIds[0];
    container.className = 'total-score';
    root.appendChild(container);
  }

  const total = result.total || result['total'] || '';
  const numericTotal = parseFloat(total);

  let levelClass = '';
  if (!isNaN(numericTotal)) {
    levelClass = numericTotal >= 70 ? 'level-confirmed' : 'level-not-confirmed';
  }

  let html = `
    <h2>Спасибо за прохождение теста!</h2>
    <p class="note">
      Уровень считается подтвержденным, если ваш итоговый результат составляет не менее <b>70%</b>.
    </p>
  `;

  if (total) {
    html += `<p class="final-score ${levelClass}"><strong>Итог:</strong> ${total}</p>`;
  }

  for (const [taskId, taskRes] of Object.entries(result)) {
    if (taskId === 'total') continue;
    if (typeof taskRes === 'object' && taskRes.score) {
      html += `<p><strong>${taskId}:</strong> ${taskRes.score}</p>`;
    }
  }

  container.innerHTML = html;

  // ===== Размещаем результат перед кнопкой "Назад", если она есть =====
  const backBtn = document.getElementById('back-button');
  if (backBtn?.parentNode) {
    backBtn.parentNode.insertBefore(container, backBtn);
  } else {
    const buttonsBlock = document.querySelector('.buttons');
    if (buttonsBlock) buttonsBlock.insertAdjacentElement('afterend', container);
  }

  // ===== Делаем кнопку "Отправить" неактивной =====
  const submitBtn = document.getElementById('submit-test');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.classList.add('disabled-btn');
  }
}

function hideSubmitButton(cfg) {
  cfg.submitButtonIds.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
}

function attachButtonHandlers(state) {
  const cfg = state.cfg;
  let submitBtn = null;

  // ===== Ищем кнопку по ID из cfg =====
  for (const id of cfg.submitButtonIds) {
    const el = document.getElementById(id);
    if (el) {
      submitBtn = el;
      break;
    }
  }

  // ===== Фолбэк: ищем кнопку в блоке .buttons =====
  if (!submitBtn) {
    submitBtn = document.querySelector(
      '.buttons button[type="button"], .buttons button[type="submit"], .buttons button'
    );
  }

  // ===== Привязываем обработчик клика =====
  if (submitBtn) {
    submitBtn.addEventListener('click', async (ev) => {
      ev.preventDefault();
      await onSubmitClicked(state);
    });
  }
}

async function onSubmitClicked(state) {
  const { cfg, level, taskData } = state;

  showLoader();

  const answers = collectAnswersFromDOM();
  const usernameInput = document.getElementById('username');
  const username = usernameInput ? usernameInput.value.trim() : '';

  const telegramIdInput = document.getElementById('telegram-id');
  const telegram_id = telegramIdInput ? parseInt(telegramIdInput.value, 10) : null;

  state.lastPayload = { username, level, telegram_id, answers };

  let result = null;
  try {
    result = await postToServer(state.lastPayload, cfg);
  } catch {
    result = localCheckAnswers(answers, taskData);
    result = { status: 'ok', result };
  } finally {
    hideLoader();
  }

  state.lastResult = result;

  if (!result || !result.status) {
    alert('Ошибка: сервер не вернул статус. Попробуйте позже.');
    return;
  }

  if (result.status === 'empty_form') {
    showEmptyFormWarning();
    return;
  }

  if (result.status !== 'ok') {
    alert(`Ошибка при обработке теста: ${result.status}`);
    return;
  }

  const oldWarning = document.getElementById('empty-warning');
  if (oldWarning) oldWarning.remove();

  applyResultToPage(result.result || {}, cfg);
}

function escapeCssSelector(s) {
  if (!s) return s;
  return s.replace(/([ #.;?+*~\[\]:!^$()=<>|\\/])/g, '\\$1');
}

function extractQnumFromNameOrElement(nameOrElement, maybeCheckedEl = null) {
  if (!nameOrElement && maybeCheckedEl) nameOrElement = maybeCheckedEl.name || '';

  if (typeof nameOrElement === 'string') {
    const matchQ = nameOrElement.match(/q(\d+)/i);
    if (matchQ) return matchQ[1];

    const anyDigit = nameOrElement.match(/(\d+)/);
    if (anyDigit) return anyDigit[1];

    return nameOrElement;
  }

  return '';
}

function findQnumFromAncestor(el) {
  let cur = el;

  while (cur && cur !== document.body) {
    if (cur.classList?.contains('question') && cur.dataset?.qnum) {
      return cur.dataset.qnum;
    }
    cur = cur.parentElement;
  }

  return null;
}

function showEmptyFormWarning() {
  const existing = document.getElementById('empty-warning');
  if (existing) existing.remove();

  const msg = document.createElement('div');
  msg.id = 'empty-warning';
  msg.className = 'empty-warning';
  msg.innerHTML = `
    <p><strong>⚠️ Ваш тест не был отправлен.</strong></p>
    <p>Вы не заполнили ни одного ответа, поэтому результат не сохраняется.</p>
    <p>Пожалуйста, ответьте хотя бы на один вопрос и попробуйте снова.</p>
  `;

  const container = document.querySelector('.container') || document.body;
  container.appendChild(msg);
}



