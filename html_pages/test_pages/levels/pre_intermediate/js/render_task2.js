import { task2Data } from "./task2_data.js";

export function renderTask2() {
  const container = document.getElementById("task2");

  task2Data.forEach((block, blockIndex) => {
    const blockDiv = document.createElement("div");
    blockDiv.className = "audio-block";

    // Заголовок блока
    const title = document.createElement("h4");
    title.textContent = block.title;
    blockDiv.appendChild(title);

    // Аудио
    const audioElem = document.createElement("audio");
    audioElem.className = "plyr";
    audioElem.src = block.audio;
    audioElem.controls = true;
    audioElem.dataset.index = blockIndex + 1; // сохраняем индекс
    blockDiv.appendChild(audioElem);

    // Вопросы
    block.questions.forEach((q) => {
      const qDiv = document.createElement("div");
      qDiv.className = "question";
      qDiv.dataset.qnum = q.qnum;

      const p = document.createElement("p");
      p.className = "task-question";
      p.innerHTML = `<span class="num">${q.qnum}.</span> ${q.question}`;
      qDiv.appendChild(p);

      if (q.type === "mcq") {
        q.options.forEach((opt, i) => {
          const label = document.createElement("label");
          label.className = "option";

          const input = document.createElement("input");
          input.type = "radio";
          input.name = `t2q${q.qnum}`;
          input.value = String.fromCharCode(65 + i);

          label.appendChild(input);
          label.appendChild(
            document.createTextNode(` ${String.fromCharCode(65 + i)}) ${opt}`)
          );
          qDiv.appendChild(label);
        });
      } else if (q.type === "truefalse") {
        ["True", "False"].forEach((val) => {
          const label = document.createElement("label");
          label.className = "option";

          const input = document.createElement("input");
          input.type = "radio";
          input.name = `t2q${q.qnum}`;
          input.value = val;

          label.appendChild(input);
          label.appendChild(document.createTextNode(` ${val}`));
          qDiv.appendChild(label);
        });
      } else if (q.type === "input") {
        const input = document.createElement("input");
        input.type = "text";
        input.name = `t2q${q.qnum}`;
        input.className = "open-input";
        qDiv.appendChild(input);
      } else if (q.type === "matching") {
        const select = document.createElement("select");
        select.name = `t2q${q.qnum}`;
        select.className = "matching-select";

        // первая пустая опция (чтобы не было выбрано по умолчанию)
        const emptyOpt = document.createElement("option");
        emptyOpt.value = "";
        emptyOpt.textContent = "-- choose --";
        select.appendChild(emptyOpt);

        q.options.forEach((opt) => {
          const option = document.createElement("option");
          const code = opt.split(".")[0].trim(); // "1", "2", "3"
          option.value = code; // вот сюда идёт ключ
          option.textContent = opt;
          select.appendChild(option);
        });

        qDiv.appendChild(select);
      }

      blockDiv.appendChild(qDiv);
    });

    container.appendChild(blockDiv);
  });

  // --- инициализация Plyr для всех плееров
  const players = Plyr.setup(".plyr", {
    controls: ["play", "progress", "current-time", "duration", "mute", "volume"]
  });

  // --- вешаем обработчики для логики "только 1 раз прослушать"
  players.forEach((player) => {
    const index = player.media.dataset.index;
    const storageKey = `pre_intermediate_task2_played_${index}`;

    const alreadyPlayed = sessionStorage.getItem(storageKey) === "true";
    if (alreadyPlayed) {
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
        const locked = document.createElement("div");
        locked.className = "audio-locked";
        locked.textContent = "Аудио уже прослушано";
        player.elements.container.replaceWith(locked);
      });
    }
  });
}
