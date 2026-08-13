// Privacy-friendly analytics by Plausible
(function () {
  window.plausible = window.plausible || function () { (plausible.q = plausible.q || []).push(arguments); };
  plausible.init = plausible.init || function (i) { plausible.o = i || {}; };
  plausible.init();
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://plausible.io/js/pa-TtuS6vKapJ9f6oV--djoe.js";
  document.head.appendChild(s);
})();

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

  // "Latest from each section" strip (index.html only)
  var latestGrid = document.getElementById("latest-grid");
  if (latestGrid) initLatest(latestGrid);

  // "Is Your AI Covered?" self-check (insurance-coverage.html only)
  var quiz = document.getElementById("ai-coverage-quiz");
  if (quiz) initQuiz(quiz);
});

// Pull each section page's own "Latest" teaser onto the homepage, so the
// front page updates itself whenever a section page is updated. Each tile
// keeps a static fallback link if the fetch or parse doesn't succeed.
function initLatest(grid) {
  var items = Array.prototype.slice.call(grid.querySelectorAll(".latest-item"));
  items.forEach(function (item) {
    var page = item.getAttribute("data-section");
    if (!page) return;
    fetch(page, { credentials: "same-origin" })
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.text();
      })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, "text/html");
        var teaser = doc.querySelector(".post-teaser");
        if (!teaser) return;
        var titleLink = teaser.querySelector("h3 a");
        if (!titleLink || !titleLink.getAttribute("href")) return;

        var metaEl = teaser.querySelector(".post-meta");
        var body = null;
        var paras = teaser.querySelectorAll("p");
        for (var i = 0; i < paras.length; i++) {
          var p = paras[i];
          if (p.classList.contains("post-meta")) continue;
          if (p.querySelector("a") && /read the full post/i.test(p.textContent)) continue;
          body = p;
          break;
        }

        renderLatestItem(item, {
          eyebrow: item.getAttribute("data-eyebrow") || "",
          meta: metaEl ? metaEl.textContent.trim() : "",
          title: titleLink.textContent.trim(),
          href: titleLink.getAttribute("href"),
          teaser: body ? body.textContent.trim() : ""
        });
      })
      .catch(function () {
        // Leave the static fallback content already in the tile.
      });
  });
}

function renderLatestItem(item, data) {
  item.innerHTML = "";

  var eyebrow = document.createElement("div");
  eyebrow.className = "eyebrow";
  eyebrow.textContent = data.eyebrow;
  item.appendChild(eyebrow);

  if (data.meta) {
    var meta = document.createElement("p");
    meta.className = "post-meta";
    meta.textContent = data.meta;
    item.appendChild(meta);
  }

  var h3 = document.createElement("h3");
  var titleLink = document.createElement("a");
  titleLink.href = data.href;
  titleLink.textContent = data.title;
  h3.appendChild(titleLink);
  item.appendChild(h3);

  if (data.teaser) {
    var teaser = document.createElement("p");
    teaser.className = "teaser";
    teaser.textContent = data.teaser;
    item.appendChild(teaser);
  }

  var more = document.createElement("a");
  more.className = "read-more";
  more.href = data.href;
  more.innerHTML = "Read the full post &rarr;";
  item.appendChild(more);
}

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
