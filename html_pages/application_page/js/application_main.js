// ==================== Telegram WebApp Integration ====================
function initializeTelegramWebApp() {
  const tg = window.Telegram?.WebApp;
  if (!tg) return; // Telegram SDK не найден — пропускаем

  const user = tg.initDataUnsafe?.user || tg.initData?.user;
  if (user?.id) {
    const idField = document.getElementById("telegram_id");
    if (idField) idField.value = user.id;
  }

  // Разворачиваем окно
  if (typeof tg.expand === "function") tg.expand();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeTelegramWebApp);
} else {
  initializeTelegramWebApp();
}

document.addEventListener("DOMContentLoaded", () => {
  const tg = window.Telegram?.WebApp;
  if (tg && typeof tg.expand === "function") tg.expand();

  const form = document.getElementById("applicationForm");
  const submitBtn = document.getElementById("submitBtn");
  const cancelBtn = document.getElementById("cancelBtn");
  const modal = document.getElementById("successModal");
  const okBtn = document.getElementById("okBtn");
  const scheduleGrid = document.querySelector(".schedule-grid");

  // ==================== Получаем параметры URL ====================
  const urlParams = new URLSearchParams(window.location.search);
  const editId = urlParams.get("edit_id"); // <-- определяем режим

  // ==================== Генерация сетки расписания ====================
  if (scheduleGrid) {
    const days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];
    const hours = Array.from({ length: 13 }, (_, i) => i + 8); // 08:00–20:00

    scheduleGrid.innerHTML = "";

    // Заголовки дней
    days.forEach(day => {
      const dayDiv = document.createElement("div");
      dayDiv.className = "day-header";
      dayDiv.textContent = day;
      scheduleGrid.appendChild(dayDiv);
    });

    // Сетка по времени
    hours.forEach(hour => {
      const timeLabel = `${hour.toString().padStart(2, "0")}:00`;
      days.forEach(day => {
        const label = document.createElement("label");
        label.className = "time-slot";

        const input = document.createElement("input");
        input.type = "checkbox";
        input.name = "schedule";
        input.value = timeLabel;
        input.dataset.day = day;

        label.appendChild(input);
        label.appendChild(document.createTextNode(timeLabel));
        scheduleGrid.appendChild(label);
      });
    });
  }

  // ==================== Валидация формы ====================
  function validatePhone(phone) {
    const regex = /^\+998\s?\d{2}\s?\d{3}-?\d{2}-?\d{2}$/;
    return regex.test(phone.trim()) || /^\+998\d{9}$/.test(phone.trim());
  }

  function validateForm() {
    let valid = true;

    const name = document.getElementById("applicant_name")?.value.trim() || "";
    if (name.length < 2) valid = false;

    const phone = document.getElementById("phone_number")?.value.trim() || "";
    if (!validatePhone(phone)) valid = false;

    const ageVal = document.getElementById("applicant_age")?.value;
    const age = ageVal ? Number(ageVal) : null;
    if (!age || age < 6 || age > 99) valid = false;

    if (form.querySelectorAll("input[name='preferred_class_format']:checked").length === 0) valid = false;
    if (form.querySelectorAll("input[name='preferred_study_mode']:checked").length === 0) valid = false;
    if (!form.querySelector("input[name='level']:checked")) valid = false;
    if (form.querySelectorAll("input[name='schedule']:checked").length === 0) valid = false;

    submitBtn.disabled = !valid;
  }

  form.addEventListener("input", validateForm);
  form.addEventListener("change", validateForm);

  // ==================== Загрузка существующей заявки ====================
  if (editId) {
    loadExistingApplication(editId);
  }

  async function loadExistingApplication(id) {
    try {
      const res = await fetch(`/api/applications/${id}`);
      if (!res.ok) throw new Error("Ошибка при получении заявки");
      const data = await res.json();

      // === Автозаполнение полей ===
      document.getElementById("applicant_name").value = data.applicant_name || "";
      document.getElementById("phone_number").value = data.phone_number || "";
      document.getElementById("applicant_age").value = data.applicant_age || "";

      data.preferred_class_format?.forEach(val => {
        const el = form.querySelector(`input[name="preferred_class_format"][value="${val}"]`);
        if (el) el.checked = true;
      });

      data.preferred_study_mode?.forEach(val => {
        const el = form.querySelector(`input[name="preferred_study_mode"][value="${val}"]`);
        if (el) el.checked = true;
      });

      if (data.level) {
        const levelEl = form.querySelector(`input[name="level"][value="${data.level}"]`);
        if (levelEl) levelEl.checked = true;
      }

      if (data.reference_source) {
        const refEl = form.querySelector(`select[name="reference_source"]`);
        if (refEl) refEl.value = data.reference_source;
      }

      data.previous_experience?.forEach(val => {
        const el = form.querySelector(`input[name="previous_experience"][value="${val}"]`);
        if (el) el.checked = true;
      });

      const ieltsEl = form.querySelector(`input[name="need_ielts"][value="${data.need_ielts}"]`);
      if (ieltsEl) ieltsEl.checked = true;

      const lanexEl = form.querySelector(`input[name="studied_at_lanex"][value="${data.studied_at_lanex}"]`);
      if (lanexEl) lanexEl.checked = true;

      if (Array.isArray(data.possible_scheduling)) {
        data.possible_scheduling.forEach(slot => {
          const day = slot.day;
          slot.times?.forEach(time => {
            const input = form.querySelector(`input[name="schedule"][data-day="${day}"][value="${time}"]`);
            if (input) input.checked = true;
          });
        });
      }

      document.getElementById("telegram_id").value = data.telegram_id || "";
      submitBtn.textContent = "💾 Обновить заявку";
      validateForm();

    } catch (err) {
      console.error("Ошибка при загрузке заявки:", err);
      alert("Не удалось загрузить данные заявки. Попробуйте позже.");
    }
  }

  // ==================== Кнопка Назад ====================
  cancelBtn.addEventListener("click", () => {
    if (tg && typeof tg.close === "function") tg.close();
    else window.close();
  });

  // ==================== Отправка формы ====================
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (submitBtn.disabled) return;

    const fd = new FormData(form);
    const checkedSlots = Array.from(form.querySelectorAll('input[name="schedule"]:checked'));
    const grouped = {};
    checkedSlots.forEach(el => {
      const day = el.dataset.day;
      const time = el.value;
      if (!grouped[day]) grouped[day] = [];
      grouped[day].push(time);
    });
    const possible_scheduling = Object.entries(grouped).map(([day, times]) => ({ day, times }));

    const payload = {
      applicant_name: fd.get("applicant_name"),
      phone_number: fd.get("phone_number"),
      applicant_age: Number(fd.get("applicant_age")),
      preferred_class_format: fd.getAll("preferred_class_format"),
      preferred_study_mode: fd.getAll("preferred_study_mode"),
      level: fd.get("level") || null,
      possible_scheduling,
      reference_source: fd.get("reference_source") || null,
      need_ielts: fd.get("need_ielts") === "true",
      studied_at_lanex: fd.get("studied_at_lanex") === "true",
      previous_experience: fd.getAll("previous_experience"),
      telegram_id: Number(fd.get("telegram_id")) || null,
    };

    await submitForm(payload);
  });

  // ==================== Отправка данных (POST/PUT) ====================
  async function submitForm(payload) {
    const url = editId
      ? `/api/applications/${editId}`   // режим редактирования
      : `/api/applications`;            // режим новой заявки

    const method = editId ? "PUT" : "POST";

    try {
      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await response.json().catch(() => null);

      if (response.ok) {
        if (modal) modal.style.display = "flex";
        form.reset();
        submitBtn.disabled = true;
      } else {
        console.error("Server returned error:", response.status, result);
        alert("❌ Ошибка: " + (result?.detail || response.statusText || "Попробуйте позже"));
      }

      console.log(result);
    } catch (err) {
      console.error("Fetch error:", err);
      alert("⚠️ Не удалось связаться с сервером");
    }
  }

  // ==================== Модальное окно ====================
  if (okBtn) okBtn.addEventListener("click", () => {
    if (modal) modal.style.display = "none";
    if (tg && typeof tg.close === "function") tg.close();
    else window.close();
  });

  // ==================== Инициализация ====================
  validateForm();
});
