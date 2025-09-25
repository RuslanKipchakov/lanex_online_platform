import { task3Data } from "./task3_data.js";

export function renderTask3() {
  const container = document.getElementById("task3");

  // Текст для чтения
  const passageDiv = document.createElement("div");
  passageDiv.className = "reading-passage";

  const passageTitle = document.createElement("h4");
  passageTitle.textContent = "Reading Passage";
  passageDiv.appendChild(passageTitle);

  const passageP = document.createElement("p");
  passageP.textContent = task3Data.passage.trim();
  passageDiv.appendChild(passageP);

  container.appendChild(passageDiv);

  // Вопросы
  task3Data.questions.forEach((q) => {
    const qDiv = document.createElement("div");
    qDiv.className = "question";
    qDiv.dataset.qnum = q.qnum;

    const p = document.createElement("p");
    p.className = "task-question";
    p.innerHTML = `<span class="num">${q.qnum}.</span> ${q.question}`;
    qDiv.appendChild(p);

    q.options.forEach((opt, i) => {
      const label = document.createElement("label");
      label.className = "option";

      const input = document.createElement("input");
      input.type = "radio";
      input.name = `t3q${q.qnum}`;
      input.value = String.fromCharCode(65 + i);

      label.appendChild(input);
      label.appendChild(document.createTextNode(` ${String.fromCharCode(65 + i)}) ${opt}`));
      qDiv.appendChild(label);
    });

    container.appendChild(qDiv);
  });
}
