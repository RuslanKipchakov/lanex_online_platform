/**
 * Универсальный движок теста для страниц уровней (starter, ...).
 *
 * API:
 *   import { initTest } from "/common/js/test_engine.js";
 *   initTest("starter", { task1: task1Data, task2: task2Data, ... }, { endpoint: "/api/check_test" });
 *
 * Движок НЕ отвечает за рендер заданий — рендер оставляем в level/js/render_task*.js
 * Он только: собирает ответы, отправляет на сервер (или проверяет локально), отображает результат.
 */

const DEFAULT_OPTIONS = {
  endpoint: "/api/check_test", // URL для проверки (можно переопределить)
  submitButtonIds: ["submit-test", "btn-check", "submit", "check"], // try for common ids
  backButtonIds: ["btn-back", "cancelBtn", "btn-cancel", "back"],
  okButtonId: "btn-ok",
  resultContainerIds: ["final-message", "final-result", "result"],
  taskSelector: '[id^="task"]' // селектор для поиска блоков task1, task2, ...
};

/**
 * Инициализация теста.
 * level: строка уровня, например "starter"
 * taskData: объект { task1: [...], task2: [...], ... } — используется для локальной проверки при отсутствии сервера
 * options: переопределяет DEFAULT_OPTIONS
 */
export function initTest(level, taskData = {}, options = {}) {
  const cfg = { ...DEFAULT_OPTIONS, ...options };
  const state = {
    level,
    taskData,
    cfg,
    lastPayload: null,
    lastResult: null
  };

  // пробуем найти и навесить обработчики на кнопки
  attachButtonHandlers(state);

  // удобный глобальный хелпер для inline onclick="goBack()"
  window.goBack = () => closeTestPage();

  return state; // возвращаем состояние на случай отладки
}

/* -------------------------
   Сбор ответов со страницы
   ------------------------- */

/**
 * Собирает ответы со страницы в структуру:
 * {
 *   task1: { "1": "C", "2": "", ... },
 *   task2: { "1": "B", ... },
 *   taskN: { ... }
 * }
 *
 * Правила извлечения номера вопроса:
 * 1) если ближайший .question имеет data-qnum — используем его
 * 2) иначе, пытаемся распарсить цифры из имени input/textarea (например t1q7 → 7)
 * 3) иначе — назначаем порядковый номер внутри найденных вопросов
 */
function collectAnswersFromDOM() {
  const answers = {};
  const taskBlocks = Array.from(document.querySelectorAll(DEFAULT_OPTIONS.taskSelector));

  taskBlocks.forEach(task => {
    const taskId = task.id || task.dataset.taskId;
    if (!taskId) return;
    answers[taskId] = {};

    // 1) radio groups — собираем по группам (name)
    const radios = Array.from(task.querySelectorAll('input[type="radio"]'));
    const radioNames = Array.from(new Set(radios.map(r => r.name).filter(Boolean)));
    radioNames.forEach(name => {
      const checked = task.querySelector(`input[type="radio"][name="${escapeCssSelector(name)}"]:checked`);
      const qnum = extractQnumFromNameOrElement(name, checked);
      answers[taskId][String(qnum)] = checked ? checked.value : "";
    });

    // 2) checkboxes — собираем массив значений (если используются)
    const checkboxes = Array.from(task.querySelectorAll('input[type="checkbox"]'));
    const checkboxNames = Array.from(new Set(checkboxes.map(c => c.name).filter(Boolean)));
    checkboxNames.forEach(name => {
      const checked = Array.from(task.querySelectorAll(`input[type="checkbox"][name="${escapeCssSelector(name)}"]:checked`)).map(i => i.value);
      const qnum = extractQnumFromNameOrElement(name);
      answers[taskId][String(qnum)] = checked; // массив (может быть пустым)
    });

    // 3) текстовые поля, textarea, select, input[type=text|number|email|hidden]
    const otherSelectors = 'textarea, select, input[type="text"], input[type="number"], input[type="email"], input[type="hidden"], input[type="tel"], input[type="url"]';
    const otherInputs = Array.from(task.querySelectorAll(otherSelectors));

    otherInputs.forEach((el, index) => {
      // если элемент внутри .question с data-qnum — берём его
      const qnumAttr = findQnumFromAncestor(el);
      const qnum = qnumAttr || extractQnumFromNameOrElement(el.name) || (index + 1);
      answers[taskId][String(qnum)] = (el.value || "").trim();
    });

    // 4) как дополнительный шаг — если в answers[taskId] нет номеров для некоторых вопросов,
    //    попробуем пройти по .question (порядок) и гарантировать, что все вопросы имеют ключи.
    const questionBlocks = Array.from(task.querySelectorAll('.question'));
    questionBlocks.forEach((qb, idx) => {
      const qnum = qb.dataset.qnum || idx + 1;
      if (!(String(qnum) in answers[taskId])) {
        // пробуем найти выбранный input внутри qb (радио/чек/textarea)
        const checkedRadio = qb.querySelector('input[type="radio"]:checked');
        if (checkedRadio) answers[taskId][String(qnum)] = checkedRadio.value;
        else {
          const checkedCheckboxes = Array.from(qb.querySelectorAll('input[type="checkbox"]:checked')).map(i => i.value);
          if (checkedCheckboxes.length) answers[taskId][String(qnum)] = checkedCheckboxes;
          else {
            const ta = qb.querySelector('textarea');
            if (ta) answers[taskId][String(qnum)] = (ta.value || "").trim();
            else {
              // оставляем пустую строку — пользователь не ответил
              answers[taskId][String(qnum)] = "";
            }
          }
        }
      }
    });
  });
  return answers;
}

/* -------------------------
   Отправка на сервер / fallback
   ------------------------- */

/**
 * Отправляет payload на сервер (cfg.endpoint).
 * Если успешный ответ — возвращает JSON.
 * Если ошибка/timeout/не отвечает — бросает.
 */
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

/**
 * Локальная проверка (fallback) по taskData, чтобы можно было протестировать страницу без сервера.
 * Формирует результат в том же формате / совместимом с backend check_test_results:
 *
 * { task1: { "1": "correct", "2": "incorrect", "score": "5/10" }, task2: "open", total: "xx.x%" }
 */
function localCheckAnswers(answers, taskData) {
  const result = {};
  const totalFractions = [];

  for (const [taskId, dataArray] of Object.entries(taskData || {})) {
    // если dataArray не массив — пропускаем как open
    if (!Array.isArray(dataArray) || dataArray.length === 0) {
      result[taskId] = "open";
      continue;
    }

    // определяем, закрыто ли задание: есть ли у элемента поле 'correct'
    const first = dataArray[0];
    const isClosed = typeof first === "object" && first !== null && ('correct' in first);

    if (!isClosed) {
      result[taskId] = "open";
      continue;
    }

    // закрытая задача — сравниваем
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

  // итог (усреднение по таскам, как делает твой бекенд)
  if (totalFractions.length) {
    const avg = totalFractions.reduce((a, b) => a + b, 0) / totalFractions.length;
    result["total"] = `${(avg * 100).toFixed(1)}%`;
  } else {
    result["total"] = "0%";
  }

  return result;
}

/* -------------------------
   Обработка результата и UI
   ------------------------- */

/**
 * Обрабатывает результат (от сервера или локального чекера) и меняет страницу:
 * - для закрытых вопросов добавляет .correct-block / .incorrect-block на соответствующие .question
 * - для задач, помеченных как "open" — заменяет контент на сообщение "Это задание проверит учитель."
 * - блокирует все инпуты
 * - прячет кнопки "назад" и "проверить", показывает кнопку "ОК"
 * - отображает итоговый блок (переменные id)
 */
function applyResultToPage(result, cfg) {
  // Пройти по всем найденным task-блокам (task1, task2...)
  const taskBlocks = Array.from(document.querySelectorAll(cfg.taskSelector));

  taskBlocks.forEach(task => {
    const taskId = task.id;
    if (!taskId) return;

    const taskRes = result[taskId];

    // Если сервер прислал string "open" — заменим содержимое блока
    if (taskRes === "open") {
      replaceTaskWithOpenMessage(task);
      return;
    }

    // Если нет результата — ничего делать не будем
    if (!taskRes || typeof taskRes !== "object") return;

    // Подробные результаты: ожидаем пары "1": "correct"/"incorrect" и "score"
    // пройдём по всем .question внутри task и поставим класс по data-qnum / порядку
    const qBlocks = Array.from(task.querySelectorAll('.question'));
    qBlocks.forEach((qb, idx) => {
      // определяем номер вопроса
      const qnum = qb.dataset.qnum || String(idx + 1);
      const status = taskRes[String(qnum)];

      // удаляем старые классы, если есть
      qb.classList.remove("correct-block", "incorrect-block");

      if (status === "correct") qb.classList.add("correct-block");
      else if (status === "incorrect") qb.classList.add("incorrect-block");
      // если status == undefined → возможно открытый вопрос или не найден — оставим без подсветки
    });

    // если сервер вернул score — покажем его внизу блока
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

  // Итог — разные id результата, попробуем найдти один из них
  displayTotalResult(result, cfg);

  // Блокируем все инпуты, textarea и select
  disableAllInputs();

  // Скрываем кнопки назад/проверить и показываем OK
  toggleButtonsAfterCheck(cfg);
}

/* -------------------------
   Малые помощники UI
   ------------------------- */

/** Заменяет содержимое task-блока сообщением о ручной проверке */
function replaceTaskWithOpenMessage(taskBlock) {
  taskBlock.innerHTML = `
    <div class="question open-task-message" style="padding:15px;">
      <p><strong>Это задание проверит преподаватель.</strong></p>
      <p>Ответы будут проверены вручную; вы получите результат позже.</p>
    </div>
  `;
}

///** Блокируем все input/textarea/select на странице */
//function disableAllInputs() {
//  const all = Array.from(document.querySelectorAll('input, textarea, select, button'));
//  all.forEach(el => {
//    // Не блокируем кнопку ОК (ее мы хотим оставить активной)
//    if (el.id === DEFAULT_OPTIONS.okButtonId) return;
//    // Для кнопок оставляем их видимыми, но disable
//    if (el.tagName.toLowerCase() === 'button') {
//      el.disabled = true;
//    } else {
//      el.disabled = true;
//      el.setAttribute('aria-disabled', 'true');
//    }
//  });
//}

function disableAllInputs() {
  const all = Array.from(document.querySelectorAll('input, textarea, select'));
  all.forEach(el => {
    el.disabled = true;
    el.setAttribute('aria-disabled', 'true');
  });
}


/** Показывает итоговый текст (попытается поместить в найденный контейнер или создаст новый) */
function displayTotalResult(result, cfg) {
  const containerId = cfg.resultContainerIds.find(id => document.getElementById(id));
  let container = containerId ? document.getElementById(containerId) : null;

  if (!container) {
    // создаём подвал в контейнере .container или после форм
    const root = document.querySelector('.container') || document.body;
    container = document.createElement('div');
    container.id = cfg.resultContainerIds[0];
    container.className = 'total-score';
    root.appendChild(container);
  }

  // собираем общий текст: если result.total есть — используем; иначе собираем суммы
  const total = result.total || result['total'] || '';
  let html = `<h2>Спасибо за прохождение теста!</h2>`;
  if (total) {
    html += `<p><strong>Итог: </strong> ${total}</p>`;
  }

  // дополнительно: можно показать per-task score если есть
  for (const [taskId, taskRes] of Object.entries(result)) {
    if (taskId === 'total') continue;
    if (typeof taskRes === 'object' && taskRes.score) {
      html += `<p><strong>${taskId}:</strong> ${taskRes.score}</p>`;
    }
  }

  // Кнопка ОК (если еще нет)
  html += `<div style="margin-top:12px;"><button id="${DEFAULT_OPTIONS.okButtonId}">ОК</button></div>`;
  container.innerHTML = html;

  // навесим закрытие на кнопку OK
  const okBtn = document.getElementById(DEFAULT_OPTIONS.okButtonId);
  if (okBtn) okBtn.addEventListener('click', closeTestPage);
}

/** Скрывает кнопки проверки/назад и показывает кнопку ОК */
function toggleButtonsAfterCheck(cfg) {
  // спрячем все известные кнопки submit/check/back
  cfg.submitButtonIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
  cfg.backButtonIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });

  // если кнопка OK существует — покажем, иначе будет создана в result-контейнере
  const ok = document.getElementById(cfg.okButtonId);
  if (ok) ok.style.display = 'inline-block';
}

/* -------------------------
   Обработчики кнопок / привязки
   ------------------------- */

/**
 * Пробует найти submit/back кнопки и навесить обработчики.
 * submit вызывает сбор и отправку.
 * back — закрытие страницы (возврат в бот).
 */
function attachButtonHandlers(state) {
  const cfg = state.cfg;

  // Найти submit кнопку по списку возможных id или по data-атрибуту
  let submitBtn = null;
  for (const id of cfg.submitButtonIds) {
    const el = document.getElementById(id);
    if (el) { submitBtn = el; break; }
  }
  // fallback — первый button внутри .buttons с type != button? (try multiple heuristics)
  if (!submitBtn) {
    submitBtn = document.querySelector('.buttons button[type="button"], .buttons button[type="submit"], .buttons button');
  }

  if (submitBtn) {
    submitBtn.addEventListener('click', async (ev) => {
      ev.preventDefault();
      // соберём и отправим
      await onSubmitClicked(state);
    });
  }

  // back buttons — возможные id
  for (const id of cfg.backButtonIds) {
    const b = document.getElementById(id);
    if (b) b.addEventListener('click', (ev) => { ev.preventDefault(); closeTestPage(); });
  }
}

/**
 * Главный обработчик submit: собирает ответы, пытается отправить на сервер,
 * при ошибке — делает локальную проверку, затем применяет результат к странице.
 */
async function onSubmitClicked(state) {
  const cfg = state.cfg;
  const level = state.level;
  const taskData = state.taskData;

  // 1) соберём ответы из DOM
  const answers = collectAnswersFromDOM();
  state.lastPayload = { level, answers };

  // Подтверждение — можно показывать confirm, но оставим невмешивающимся (если нужно — включим)
  if (!confirm("Вы уверены, что хотите отправить тест на проверку?")) return;

  // 2) попытаемся отправить на сервер
  let result = null;
  try {
    result = await postToServer(state.lastPayload, cfg);
    state.lastResult = result;
  } catch (err) {
    console.warn("Не удалось отправить на сервер, выполняю локальную проверку. Причина:", err);
    // локальная проверка
    result = localCheckAnswers(answers, taskData);
    state.lastResult = result;
  }

  // 3) применяем результат к странице (подсветки, сообщения, кнопки)
  applyResultToPage(result, cfg);
}

/* -------------------------
   Утилиты
   ------------------------- */

/** Безопасно экранирует имя для использования в querySelector (CSS escape) */
function escapeCssSelector(s) {
  if (!s) return s;
  return s.replace(/([ #.;?+*~\[\]:!^$()=<>|\\/])/g, '\\$1');
}

/** Пытаемся получить номер вопроса из имени groupName или элемента (например "t1q7" -> 7) */
function extractQnumFromNameOrElement(nameOrElement, maybeCheckedEl=null) {
  if (!nameOrElement && maybeCheckedEl) nameOrElement = maybeCheckedEl.name || "";

  if (typeof nameOrElement === "string") {
    // ищем pattern q{digits}
    const matchQ = nameOrElement.match(/q(\d+)/i);
    if (matchQ) return matchQ[1];
    // ищем любые цифры
    const anyDigit = nameOrElement.match(/(\d+)/);
    if (anyDigit) return anyDigit[1];
    return nameOrElement; // fallback — возвращаем как есть
  }
  return "";
}

/** Ищем ближайший ancestor .question и берем data-qnum (если есть) */
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

/** Закрывает WebApp (Telegram) или окно (fallback) */
function closeTestPage() {
  try {
    if (window.Telegram && window.Telegram.WebApp && typeof window.Telegram.WebApp.close === 'function') {
      window.Telegram.WebApp.close();
      return;
    }
  } catch (e) {
    // ignore
  }
  // fallback
  try { window.close(); } catch (err) { console.warn("Не удалось закрыть окно автоматически."); }
}
