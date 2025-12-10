// ==================== Telegram WebApp Integration ====================
function initializeTelegramWebApp() {
  const tg = window.Telegram?.WebApp;
  if (!tg) return;

  const user = tg.initDataUnsafe?.user || tg.initData?.user;
  if (user?.id) {
    const idField = document.getElementById("telegram_id");
    if (idField) idField.value = user.id;
  }

  if (typeof tg.expand === "function") tg.expand();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeTelegramWebApp);
} else {
  initializeTelegramWebApp();
}

document.addEventListener("DOMContentLoaded", () => {
  const tg = window.Telegram?.WebApp;

  const form = document.getElementById("applicationForm");
  const submitBtn = document.getElementById("submitBtn");
  const cancelBtn = document.getElementById("cancelBtn");

  const modal = document.getElementById("successModal");
  const okBtn = document.getElementById("okBtn");

  const scheduleGrid = document.querySelector(".schedule-grid");

  const urlParams = new URLSearchParams(window.location.search);
  const editId = urlParams.get("edit_id");

  // ==================== Генерация сетки расписания ====================

  if (scheduleGrid) {
    const days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];
    const hours = Array.from({ length: 13 }, (_, i) => i + 8); // 08:00–20:00

    scheduleGrid.innerHTML = "";

    // Заголовки дней
    days.forEach((day) => {
      const dayDiv = document.createElement("div");
      dayDiv.className = "day-header";
      dayDiv.textContent = day;
      scheduleGrid.appendChild(dayDiv);
    });

    // Тайм-слоты
    hours.forEach((hour) => {
      const timeLabel = `${hour.toString().padStart(2, "0")}:00`;

      days.forEach((day) => {
        const label = document.createElement("label");
        label.className = "time-slot";

        const input = document.createElement("input");
        input.type = "checkbox";
        input.name = "schedule";
        input.value = timeLabel;
        input.dataset.day = day;

        label.append(input, document.createTextNode(timeLabel));
        scheduleGrid.appendChild(label);
      });
    });
  }

  // ==================== Валидация формы ====================

  function validateForm() {
    let valid = true;

    // Очищаем старые ошибки
    document.querySelectorAll(".error-message").forEach((el) => (el.textContent = ""));
    document.querySelectorAll(".invalid").forEach((el) => el.classList.remove("invalid"));

    // --- Имя ---
    const name = document.getElementById("applicant_name");
    const nameVal = name.value.trim();
    const nameError = document.getElementById("error_applicant_name");

    const nameRegex = /^[A-Za-zА-Яа-яЁё'’\- ]{2,50}$/;

    if (!nameVal) {
      nameError.textContent = "Пожалуйста, укажите ваше имя.";
      name.classList.add("invalid");
      valid = false;
    } else if (!nameRegex.test(nameVal)) {
      nameError.textContent =
        "Имя может содержать только буквы, пробелы, дефисы и апострофы.";
      name.classList.add("invalid");
      valid = false;
    }

    // --- Телефон ---
    const phone = document.getElementById("phone_number");
    const phoneVal = phone.value.trim();
    const phoneError = document.getElementById("error_phone_number");

    const phoneRegex = /^\+?[0-9 ]{7,20}$/;

    if (!phoneVal) {
      phoneError.textContent = "Пожалуйста, введите номер телефона.";
      phone.classList.add("invalid");
      valid = false;
    } else {
      const digitsOnly = phoneVal.replace(/\D/g, "");

      if (!phoneRegex.test(phoneVal)) {
        phoneError.textContent = "Пожалуйста, введите номер телефона.";
        phone.classList.add("invalid");
        valid = false;
      } else if (digitsOnly.length < 7) {
        phoneError.textContent = "Номер телефона должен содержать минимум 7 цифр.";
        phone.classList.add("invalid");
        valid = false;
      }
    }

    // --- Возраст ---
    const age = document.getElementById("applicant_age");
    const ageVal = Number(age.value);
    const ageError = document.getElementById("error_applicant_age");

    if (!age.value) {
      ageError.textContent = "Пожалуйста, укажите возраст.";
      age.classList.add("invalid");
      valid = false;
    } else if (ageVal < 6 || ageVal > 99) {
      ageError.textContent = "Возраст должен быть в пределах от 6 до 99 лет.";
      age.classList.add("invalid");
      valid = false;
    }

    // --- Формат обучения ---
    const classFormat = form.querySelectorAll(
      "input[name='preferred_class_format']:checked"
    );
    const classFormatError = document.getElementById("error_preferred_class_format");

    if (classFormat.length === 0) {
      classFormatError.textContent =
        "Пожалуйста, выберите хотя бы один формат обучения.";
      valid = false;
    }

    // --- Тип урока ---
    const studyMode = form.querySelectorAll(
      "input[name='preferred_study_mode']:checked"
    );
    const studyModeError = document.getElementById("error_preferred_study_mode");

    if (studyMode.length === 0) {
      studyModeError.textContent = "Пожалуйста, выберите хотя бы один тип урока.";
      valid = false;
    }

    // --- Расписание ---
    const schedule = form.querySelectorAll("input[name='schedule']:checked");
    const scheduleError = document.getElementById("error_schedule");

    if (schedule.length === 0) {
      scheduleError.textContent = "Пожалуйста, выберите подходящее время.";
      valid = false;
    }

    submitBtn.disabled = !valid;
    return valid;
  }

  form.addEventListener("input", validateForm);
  form.addEventListener("change", validateForm);

  // ==================== Загрузка заявки при редактировании ====================

  if (editId) {
    loadExistingApplication(editId);
  }

  async function loadExistingApplication(id) {
    try {
      const res = await fetch(`/api/applications/${id}`);
      if (!res.ok) throw new Error("Ошибка при получении заявки");

      const data = await res.json();

      document.getElementById("applicant_name").value = data.applicant_name || "";
      document.getElementById("phone_number").value = data.phone_number || "";
      document.getElementById("applicant_age").value = data.applicant_age || "";

      data.preferred_class_format?.forEach((val) => {
        const el = form.querySelector(
          `input[name="preferred_class_format"][value="${val}"]`
        );
        if (el) el.checked = true;
      });

      data.preferred_study_mode?.forEach((val) => {
        const el = form.querySelector(
          `input[name="preferred_study_mode"][value="${val}"]`
        );
        if (el) el.checked = true;
      });

      if (data.level) {
        const el = form.querySelector(`input[name="level"][value="${data.level}"]`);
        if (el) el.checked = true;
      }

      if (data.reference_source) {
        const el = form.querySelector(
          `input[name="reference_source"][value="${data.reference_source}"]`
        );
        if (el) el.checked = true;
      }

      data.previous_experience?.forEach((val) => {
        const el = form.querySelector(
          `input[name="previous_experience"][value="${val}"]`
        );
        if (el) el.checked = true;
      });

      if (typeof data.need_ielts === "boolean") {
        const el = form.querySelector(
          `input[name="need_ielts"][value="${data.need_ielts}"]`
        );
        if (el) el.checked = true;
      }

      if (typeof data.studied_at_lanex === "boolean") {
        const el = form.querySelector(
          `input[name="studied_at_lanex"][value="${data.studied_at_lanex}"]`
        );
        if (el) el.checked = true;
      }

      if (Array.isArray(data.possible_scheduling)) {
        data.possible_scheduling.forEach((slot) => {
          slot.times?.forEach((time) => {
            const input = form.querySelector(
              `input[name="schedule"][data-day="${slot.day}"][value="${time}"]`
            );
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

  cancelBtn?.addEventListener("click", () => {
    if (tg?.close) tg.close();
    else window.close();
  });

  // ==================== Отправка формы ====================

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (submitBtn.disabled) return;

    const fd = new FormData(form);

    const checkedSlots = form.querySelectorAll('input[name="schedule"]:checked');
    const grouped = {};

    checkedSlots.forEach((el) => {
      const { day } = el.dataset;
      if (!grouped[day]) grouped[day] = [];
      grouped[day].push(el.value);
    });

    const possible_scheduling = Object.entries(grouped).map(([day, times]) => ({
      day,
      times,
    }));

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

  // ==================== Отправка данных на сервер ====================

  async function submitForm(payload) {
    const url = editId ? `/api/applications/${editId}` : `/api/applications`;
    const method = editId ? "PUT" : "POST";

    const loader = document.getElementById("loader");

    loader?.classList.add("active");
    submitBtn.disabled = true;

    try {
      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await response.json().catch(() => null);

      if (response.ok) {
        modal && (modal.style.display = "flex");
        form.reset();
        submitBtn.disabled = true;
      } else {
        console.error("Server returned error:", response.status, result);
        alert("❌ Ошибка: " + (result?.detail || response.statusText || "Попробуйте позже"));
      }

    } catch (err) {
      console.error("Fetch error:", err);
      alert("⚠️ Не удалось связаться с сервером");
    } finally {
      loader?.classList.remove("active");
      submitBtn.disabled = false;
    }
  }

  // ==================== Модальное окно ====================

  okBtn?.addEventListener("click", () => {
    modal && (modal.style.display = "none");

    if (tg?.close) tg.close();
    else window.close();
  });

  validateForm();
});
