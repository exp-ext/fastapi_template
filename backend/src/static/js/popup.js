document.addEventListener("DOMContentLoaded", function() {
  const popup = document.getElementById("popup");
  const closeButton = document.getElementById("close-popup");

  popup.style.display = "flex";

  closeButton.addEventListener("click", function() {
    popup.style.display = "none";
  });
});