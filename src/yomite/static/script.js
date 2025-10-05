const container = document.getElementById("grab");
const autoRefresh = document.getElementById("autoRefresh");
autoRefresh.addEventListener("click", () => {
    const checked = !autoRefresh.checked;
    if (checked) refresh();
    container.setAttribute("contenteditable", checked);
})
function refresh() {
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