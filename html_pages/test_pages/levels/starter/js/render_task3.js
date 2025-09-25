import { task3Data } from "./task3_data.js";

export function renderTask3() {
  const container = document.getElementById("task3");

  task3Data.forEach((q, index) => {
    const qDiv = document.createElement("div");
    qDiv.className = "question";

    // Вопрос
    const questionP = document.createElement("p");
    questionP.className = "task-question";
    questionP.innerHTML = `<span class="num">${index + 1}.</span> ${q}`;
    qDiv.appendChild(questionP);

    // Поле для ответа
    const input = document.createElement("textarea");
    input.name = `t3q${index + 1}`;
    input.rows = 3;
    input.className = "task-textarea";
    qDiv.appendChild(input);

    container.appendChild(qDiv);
  });
}

