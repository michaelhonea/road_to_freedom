const form = document.getElementById("askForm");
const out = document.getElementById("out");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = form.querySelector("button");
  btn.disabled = true;
  out.hidden = false;
  out.textContent = "Looking through the lessons...";
  try {
    const res = await fetch("/api/ask", { method: "POST", body: new FormData(form) });
    const data = await res.json();
    out.textContent = data.answer;
    if (data.sources && data.sources.length) {
      const src = document.createElement("div");
      src.className = "small";
      src.style.marginTop = "0.8rem";
      src.textContent = "From: " + data.sources.join(" | ");
      out.appendChild(src);
    }
  } catch (err) {
    out.textContent = "Something went wrong. Please try again.";
  } finally {
    btn.disabled = false;
  }
});
