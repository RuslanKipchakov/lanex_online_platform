import { task4Data } from "./task4_data.js";

export function renderTask4() {
  const container = document.getElementById("task4");

  // Инструкция
  const instruction = document.createElement("div");
  instruction.className = "task-instruction";
  instruction.innerHTML = task4Data.instruction.replace(/\n/g, "<br>");
  container.appendChild(instruction);

  // Поле ввода
  const textarea = document.createElement("textarea");
  textarea.name = "task4_answer";
  textarea.rows = 8;
  textarea.placeholder = "Write your text here (40–60 words)...";
  textarea.className = "writing-textarea";
  container.appendChild(textarea);
}
