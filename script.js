// aiimplementation.online — shared site behavior

document.addEventListener("DOMContentLoaded", function () {
  // Mobile nav toggle
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector("nav.main-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      nav.classList.toggle("open");
    });
  }

  // "Is Your AI Covered?" self-check (insurance-coverage.html only)
  var quiz = document.getElementById("ai-coverage-quiz");
  if (quiz) initQuiz(quiz);
});

function initQuiz(root) {
  var questions = Array.prototype.slice.call(root.querySelectorAll(".quiz-question"));
  var progressEl = root.querySelector(".quiz-progress");
  var resultEl = root.querySelector(".quiz-result");
  var answers = {};

  function showQuestion(index) {
    questions.forEach(function (q, i) {
      q.classList.toggle("active", i === index);
    });
    if (progressEl) {
      progressEl.textContent = "Question " + (index + 1) + " of " + questions.length;
    }
  }

  questions.forEach(function (q, index) {
    var buttons = q.querySelectorAll(".quiz-options button");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        answers[q.dataset.key] = btn.dataset.value;
        if (index + 1 < questions.length) {
          showQuestion(index + 1);
        } else {
          showResult();
        }
      });
    });
  });

  function showResult() {
    questions.forEach(function (q) { q.classList.remove("active"); });
    if (progressEl) progressEl.textContent = "";
    resultEl.classList.add("active");

    var flags = 0;
    if (answers.usesAI === "yes") flags++;
    if (answers.knowsExclusion !== "yes") flags++;
    if (answers.vendorIndemnity !== "yes") flags++;
    if (answers.policyResponds !== "yes") flags++;
    if (answers.pastLoss === "yes") flags += 2;

    var riskLine, riskDetail;
    if (flags >= 4) {
      riskLine = "Your exposure here is likely real, and likely unpriced.";
      riskDetail = "Based on your answers, you're running AI in ways that could trigger a claim, without a confirmed answer from your carrier on whether it's covered. That combination is exactly the gap the July 2026 ISO endorsements created.";
    } else if (flags >= 2) {
      riskLine = "There's a real open question here, worth closing before renewal.";
      riskDetail = "You've got at least one piece of this unconfirmed. That's normal, most organizations do, but it's worth resolving on paper rather than assuming it's fine.";
    } else {
      riskLine = "You're in better shape than most, but get it in writing anyway.";
      riskDetail = "Your answers suggest you've already asked most of the right questions. The one thing worth doing regardless: get the confirmation in writing, not just in memory.";
    }

    root.querySelector(".risk-line").textContent = riskLine;
    root.querySelector(".risk-detail").textContent = riskDetail;

    var emailBody = "Subject: AI exclusion and coverage confirmation\n\n" +
      "Hi [Broker name],\n\n" +
      "I need three things confirmed in writing for our file:\n\n" +
      "1. Has our carrier filed any AI exclusion endorsement (ISO CG 40 47, CG 40 48, or CG 35 08, or an equivalent) in the states where we operate?\n\n" +
      "2. Does our current general liability / professional liability program respond to a claim arising from an AI monitoring, alerting, or documentation failure?\n\n" +
      "3. If an AI system fails and someone is harmed as a result, which policy responds, and under what trigger?\n\n" +
      "Please reply on paper rather than by phone. I'd like this on file before our next renewal.\n\n" +
      "Thanks,\n[Your name]";

    var draftEl = root.querySelector(".email-draft");
    draftEl.textContent = emailBody;

    var copyBtn = root.querySelector(".copy-btn");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        navigator.clipboard.writeText(emailBody).then(function () {
          copyBtn.textContent = "Copied";
          setTimeout(function () { copyBtn.textContent = "Copy this email"; }, 2000);
        });
      });
    }

    var restartLink = root.querySelector(".restart-link");
    if (restartLink) {
      restartLink.addEventListener("click", function (e) {
        e.preventDefault();
        answers = {};
        resultEl.classList.remove("active");
        showQuestion(0);
      });
    }
  }

  showQuestion(0);
}
