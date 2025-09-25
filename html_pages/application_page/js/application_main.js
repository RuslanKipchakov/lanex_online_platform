document.addEventListener("DOMContentLoaded", () => {
  const tg = window.Telegram?.WebApp;
  if (tg && typeof tg.expand === "function") tg.expand();

  const form = document.getElementById("applicationForm");
  const submitBtn = document.getElementById("submitBtn");
  const cancelBtn = document.getElementById("cancelBtn");
  const modal = document.getElementById("successModal");
  const okBtn = document.getElementById("okBtn");
  const scheduleGrid = document.querySelector(".schedule-grid");

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

    // собираем и группируем расписание по дням
    const checkedSlots = Array.from(form.querySelectorAll('input[name="schedule"]:checked'));
    const grouped = {};
    checkedSlots.forEach(el => {
      const day = el.dataset.day;   // "Пн", "Вт" ...
      const time = el.value;        // "08:00"
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
    };

    try {
      const res = await fetch("/api/applications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const resJson = await res.json().catch(() => null);

      if (res.ok) {
        if (modal) modal.style.display = "flex";
        form.reset();
        submitBtn.disabled = true;
      } else {
        console.error("Server returned error:", res.status, resJson);
        alert("❌ Ошибка: " + (resJson?.detail || res.statusText || "Попробуйте позже"));
      }
    } catch (err) {
      console.error("Fetch error:", err);
      alert("⚠️ Не удалось связаться с сервером");
    }
  });

  // ==================== Модальное окно ====================
  if (okBtn) okBtn.addEventListener("click", () => {
    if (modal) modal.style.display = "none";
    if (tg && typeof tg.close === "function") tg.close();
    else window.close();
  });

  // ==================== Инициализация ====================
  validateForm();
});
