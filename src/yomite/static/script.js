const container = document.getElementById("grab");
const grabbedImage = document.getElementById("grabbed");
const adjustedImage = document.getElementById("adjusted");
const autoRefresh = document.getElementById("autoRefresh");
function refreshImage(img) {
    img.src = img.src.replace(/#.*$/, "") + "#" + new Date().getTime();
}
autoRefresh.addEventListener("click", () => {
    const checked = !autoRefresh.checked;
    if (checked) refresh();
    container.setAttribute("contenteditable", checked);
})
function refresh() {
    refreshImage(grabbedImage);
    refreshImage(adjustedImage);
    fetch("/text")
        .then(response => response
            .text()
            .then(grab => {
                if (container.innerText != grab) {
                    container.innerText = grab;
                }
            }));
}
setInterval(() => {
    if (autoRefresh.checked) refresh();
}, 250);

const reselectArea = document.getElementById("reselectArea");
reselectArea.addEventListener("click", () => {
    fetch("/reselect-area").then(() => {});
});