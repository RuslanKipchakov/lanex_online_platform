// Функция для рендеринга Task 1 на страницу (Pre-Intermediate)
import { task1Data } from "./task1_data.js";

export function renderTask1() {
  const container = document.getElementById("task1");

  task1Data.forEach((q, index) => {
    const qDiv = document.createElement("div");
    qDiv.className = "question";

    // Добавляем data-атрибут для связи с результатами проверки
    qDiv.dataset.qnum = index + 1;

    // Вопрос
    const questionP = document.createElement("p");
    questionP.className = "task-question";
    questionP.innerHTML = `<span class="num">${index + 1}.</span> ${q.question}`;
    qDiv.appendChild(questionP);

    // Варианты ответов
    q.options.forEach((opt, i) => {
      const label = document.createElement("label");
      label.className = "option";

      const input = document.createElement("input");
      input.type = "radio";
      input.name = `t1q${index + 1}`;
      input.value = String.fromCharCode(65 + i);

      label.appendChild(input);
      label.appendChild(document.createTextNode(` ${String.fromCharCode(65 + i)}) ${opt}`));
      qDiv.appendChild(label);
    });

    container.appendChild(qDiv);
  });
}
