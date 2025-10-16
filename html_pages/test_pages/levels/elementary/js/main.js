// Импорт рендер-функций
import { renderTask1 } from "./render_task1.js";
import { renderTask2 } from "./render_task2.js";
import { renderTask3 } from "./render_task3.js";
import { renderTask4 } from "./render_task4.js";

// Импорт данных для теста
import { task1Data } from "./task1_data.js";
import { task2Data } from "./task2_data.js";
import { task3Data } from "./task3_data.js";
import { task4Data } from "./task4_data.js";

// Импорт движка теста
import { initTest } from "../../../common/js/test_engine.js";

// Рендерим все задания на страницу
renderTask1();
renderTask2();
renderTask3();
renderTask4();

// Инициализируем движок теста
const state = initTest("Elementary", {
  task1: task1Data,
  task2: task2Data,
  task3: task3Data,
  task4: task4Data,
});
