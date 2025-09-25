import { task4Data } from "./task4_data.js";

export function renderTask4() {
  const container = document.getElementById("task4");

  // Инструкция
  const instruction = document.createElement("div");
  instruction.className = "task-instruction";
  instruction.innerHTML = task4Data.instruction;
  container.appendChild(instruction);

  // Поле ввода
  const textarea = document.createElement("textarea");
  textarea.name = "task4_answer";
  textarea.rows = 10;
  textarea.placeholder = "Write your letter here (70–90 words)...";
  textarea.className = "writing-textarea";
  container.appendChild(textarea);
}
