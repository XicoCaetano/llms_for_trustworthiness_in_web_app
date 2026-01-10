function setupCollapsibles() {
  const collapsibles = document.querySelectorAll(".collapsible-header");
  collapsibles.forEach((coll) => {
    coll.addEventListener("click", function () {
      this.classList.toggle("active");
      const content = this.nextElementSibling;
      if (content.style.maxHeight) {
        content.style.maxHeight = null;
      } else {
        content.style.maxHeight = content.scrollHeight + "px";
      }
    });
  });
}

function toggleComparison() {
  const section = document.getElementById("comparisonSection");
  section.style.display = document.getElementById("toggleComparison").checked
    ? "block"
    : "none";
}

function toggle1() {
  const section = document.getElementById("score1Results");
  section.style.display = document.getElementById("toggle1").checked
    ? "block"
    : "none";
}