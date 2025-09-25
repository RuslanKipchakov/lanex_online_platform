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

    // Инструкция
    if (block.instruction) {
      const instr = document.createElement("p");
      instr.className = "task-instruction";
      instr.textContent = block.instruction;
      blockDiv.appendChild(instr);
    }

    // Аудио
    const audioElem = document.createElement("audio");
    audioElem.className = "plyr";
    audioElem.src = block.audio;
    audioElem.controls = true;
    audioElem.dataset.index = blockIndex + 1;
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

        const emptyOpt = document.createElement("option");
        emptyOpt.value = "";
        emptyOpt.textContent = "-- choose --";
        select.appendChild(emptyOpt);

        q.options.forEach((opt) => {
          const option = document.createElement("option");
          const code = opt.split(".")[0].trim();
          option.value = code;
          option.textContent = opt;
          select.appendChild(option);
        });

        qDiv.appendChild(select);
      } else if (q.type === "matching-dragdrop") {
        // общий блок с вариантами
        if (!blockDiv.querySelector(".dragdrop-shared")) {
          const dragdropShared = document.createElement("div");
          dragdropShared.className = "dragdrop-shared";

          const optionsList = document.createElement("div");
          optionsList.className = "dragdrop-options";

          const opts = block.sharedOptions || q.options;
          opts.forEach((opt) => {
            const item = document.createElement("div");
            item.className = "drag-item";
            item.draggable = true;
            item.textContent = opt;
            item.dataset.value = opt.split(".")[0].trim();
            optionsList.appendChild(item);
          });

          dragdropShared.appendChild(optionsList);
          blockDiv.appendChild(dragdropShared);
        }

        // drop-зона
        const dropZone = document.createElement("div");
        dropZone.className = "drop-zone";
        dropZone.dataset.target = `t2q${q.qnum}`;
        dropZone.textContent = "Drag your answer here";
        qDiv.appendChild(dropZone);
      }

      blockDiv.appendChild(qDiv);
    });

    container.appendChild(blockDiv);
  });

  // инициализация Plyr
  const players = Plyr.setup(".plyr", {
    controls: ["play", "progress", "current-time", "duration", "mute", "volume"]
  });

  // логика "только 1 раз прослушать"
  players.forEach((player) => {
    const index = player.media.dataset.index;
    const storageKey = `intermediate_task2_played_${index}`;

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

  // --- Drag&Drop + Tap-to-Select логика с чипами ---
  let selectedItem = null;
  const dragItems = document.querySelectorAll(".drag-item");
  const dropZones = document.querySelectorAll(".drop-zone");

  // dragstart: кладем данные
  dragItems.forEach((item) => {
    item.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", item.dataset.value);
      e.dataTransfer.setData("text/label", item.textContent);
    });

    // Tap-выбор
    item.addEventListener("click", () => {
      dragItems.forEach((i) => i.classList.remove("selected"));
      item.classList.add("selected");
      selectedItem = item;
    });
  });

  // drop-зоны
  dropZones.forEach((zone) => {
    // dragover
    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("drag-over");
    });

    zone.addEventListener("dragleave", () => {
      zone.classList.remove("drag-over");
    });

    // drop
    zone.addEventListener("drop", (e) => {
      e.preventDefault();
      zone.classList.remove("drag-over");
      const value = e.dataTransfer.getData("text/plain");
      const label = e.dataTransfer.getData("text/label");

      zone.innerHTML = "";

      const chip = document.createElement("div");
      chip.className = "chip-answer";
      chip.textContent = label;

      const hidden = document.createElement("input");
      hidden.type = "hidden";
      hidden.name = zone.dataset.target;
      hidden.value = value;

      zone.appendChild(chip);
      zone.appendChild(hidden);
    });

    // tap
    zone.addEventListener("click", () => {
      if (selectedItem) {
        zone.innerHTML = "";

        const chip = document.createElement("div");
        chip.className = "chip-answer";
        chip.textContent = selectedItem.textContent;

        const hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = zone.dataset.target;
        hidden.value = selectedItem.dataset.value;

        zone.appendChild(chip);
        zone.appendChild(hidden);

        selectedItem.classList.remove("selected");
        selectedItem = null;
      }
    });
  });
}
