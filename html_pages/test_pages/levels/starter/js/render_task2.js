import { task2Data } from "./task2_data.js";

export function renderTask2() {
  const container = document.getElementById("task2");

  task2Data.forEach((item, index) => {
    const qDiv = document.createElement("div");
    qDiv.className = "question";
    qDiv.dataset.qnum = index + 1;

    // Вопрос с аудио
    const questionP = document.createElement("p");
    questionP.className = "task-question";
    questionP.innerHTML = `<span class="num">${index + 1}.</span>`;
    qDiv.appendChild(questionP);

    const storageKey = `starter_task2_played_${index + 1}`;

    const audioElem = document.createElement("audio");
    audioElem.className = "plyr"; // 👈 чтобы Plyr подхватил
    audioElem.src = item.audio;
    audioElem.preload = "none";
    audioElem.controls = true;
    audioElem.dataset.index = index + 1; // сохраняем индекс
    questionP.appendChild(audioElem);

    // Блок с вариантами ответов
    const optionsDiv = document.createElement("div");
    optionsDiv.className = "task2-options";
    optionsDiv.style.display = "none";

    item.options.forEach((opt, i) => {
      const label = document.createElement("label");
      label.className = "option";

      const input = document.createElement("input");
      input.type = "radio";
      input.name = `t2q${index + 1}`;
      input.value = String.fromCharCode(65 + i);

      label.appendChild(input);
      label.appendChild(document.createTextNode(` ${String.fromCharCode(65 + i)}) ${opt}`));
      optionsDiv.appendChild(label);
    });

    qDiv.appendChild(optionsDiv);
    container.appendChild(qDiv);
  });

  // --- инициализация Plyr
  const players = Plyr.setup('.plyr', {
  controls: [
    'play',        // кнопка play/pause
    'progress',    // прогресс-бар
    'current-time',
    'duration',
    'mute',
    'volume'
    // 👆 всё, что оставляем
    // 'settings' и 'speed' НЕ добавляем
  ]
  });

  // --- обработчики для каждого плеера
  players.forEach((player) => {
    const index = player.media.dataset.index;
    const storageKey = `starter_task2_played_${index}`;

    const qDiv = player.media.closest(".question");
    const optionsDiv = qDiv.querySelector(".task2-options");

    const alreadyPlayed = sessionStorage.getItem(storageKey) === "true";
    if (alreadyPlayed) {
      optionsDiv.style.display = "block";
      const locked = document.createElement("div");
      locked.className = "audio-locked";
      locked.textContent = "Аудио уже прослушано";
      player.elements.container.replaceWith(locked);
    } else {
      player.on("play", () => {
        if (sessionStorage.getItem(storageKey) === "true") {
          player.pause();
          alert("Вы можете прослушать это аудио только один раз.");
        }
      });

      player.on("ended", () => {
        sessionStorage.setItem(storageKey, "true");
        optionsDiv.style.display = "block";
        const locked = document.createElement("div");
        locked.className = "audio-locked";
        locked.textContent = "Аудио уже прослушано";
        player.elements.container.replaceWith(locked);
      });
    }
  });
}
