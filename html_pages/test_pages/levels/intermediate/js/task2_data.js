// ========== Task 2 (Intermediate) ==========

// Общие варианты для matching-dragdrop
const productivityOptions = [
  "1. Avoid task switching",
  "2. Improve focus and creativity",
  "3. Limit distractions",
  "4. Reduce interruptions",
  "5. Stay focused"
];

export const task2Data = [
  {
    audio: "audio/intermediate_task_2_1.mp3",
    title: "Listening Track 1: A University Lecture on Sleep",
    instruction: "Choose the best option.",
    questions: [
      {
        qnum: 1,
        question: "What is the main focus of the lecture?",
        type: "mcq",
        options: [
          "How to avoid using phones at night",
          "The physical benefits of exercise",
          "The importance of sleep for memory and health",
          "Differences between deep and light sleep"
        ]
      },
      {
        qnum: 2,
        question: "According to the lecture, what happens during deep sleep?",
        type: "mcq",
        options: [
          "The body increases its energy levels",
          "The brain processes and stores memories",
          "People usually wake up during it",
          "Dreams become more vivid"
        ]
      },
      {
        qnum: 3,
        question: "Why do screens at night reduce sleep quality?",
        type: "mcq",
        options: [
          "They make people more alert",
          "They increase stress levels",
          "They prevent the body from feeling tired",
          "They suppress melatonin production"
        ]
      },
      {
        qnum: 4,
        question: "What can be inferred about students and sleep?",
        type: "mcq",
        options: [
          "Students tend to oversleep before exams",
          "Lack of sleep doesn't affect academic performance",
          "Sleeping helps students retain information",
          "Most students don’t need sleep to perform well"
        ]
      },
      {
        qnum: 5,
        question: "What is the speaker’s attitude toward sleep?",
        type: "mcq",
        options: [
          "Sleep is a luxury for some people",
          "Sleep is not as important as studying",
          "Sleep is essential for well-being",
          "Sleep is only useful for physical recovery"
        ]
      }
    ]
  },
  {
    audio: "audio/intermediate_task_2_2.mp3",
    title: "Listening Track 2: A Dialogue About a Volunteering Trip",
    instruction: "Fill the sentences. Write no more than 2 words.",
    questions: [
      {
        qnum: 6,
        question: "Jen will work in a ______ in Nepal.",
        type: "input"
      },
      {
        qnum: 7,
        question: "One of her tasks will be to help ______ classrooms.",
        type: "input"
      },
      {
        qnum: 8,
        question: "Volunteers will stay with local ______.",
        type: "input"
      },
      {
        qnum: 9,
        question: "Jen only had to pay for her ______.",
        type: "input"
      },
      {
        qnum: 10,
        question: "Tom says he might join the program ______.",
        type: "input"
      }
    ]
  },
  {
    audio: "audio/intermediate_task_2_3.mp3",
    title: "Listening Track 3: A Podcast About Personal Productivity",
    instruction: "Match a piece of advice with the right purpose.",
    questions: [
      { qnum: 11, question: "Time-blocking", type: "matching-dragdrop" },
      { qnum: 12, question: "Taking breaks", type: "matching-dragdrop" },
      { qnum: 13, question: "Turning off notifications", type: "matching-dragdrop" },
      { qnum: 14, question: "Blocking social media", type: "matching-dragdrop" },
      { qnum: 15, question: "Quiet environment", type: "matching-dragdrop" }
    ],
    sharedOptions: productivityOptions   // <--- ссылка на общий список
  }
];
