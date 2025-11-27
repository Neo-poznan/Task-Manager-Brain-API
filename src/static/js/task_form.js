let container = document.getElementById('rendering-content-container');
let textarea = document.getElementById('description-id-for-label');
let renderingContentElement = document.getElementById('rendering-content');
textarea.onblur = (event) => {
    renderMarkdownInTextarea(event.target.value);
}

renderingContentElement.onclick = (event) => {
    renderingContentElement.style.display = 'none';
    textarea.style.display = 'block';
    textarea.focus();
}

function renderMarkdownInTextarea (textareaValue) {
    textarea.style.display = 'none';
    renderingContentElement.style.display = 'block'
    if ( !textareaValue ) {
        renderingContentElement.innerHTML = '<p id="placeholder">Описание... (можно Markdown)</p>';
    }
    else {
        renderingContentElement.innerHTML = marked.parse(textareaValue);
    }
}

renderMarkdownInTextarea(textarea.value);

function autoResize() {
    textarea.style.height = '300px';
    textarea.style.height = textarea.scrollHeight + 'px';
}

if (textarea.attachEvent) {
    textarea.attachEvent('oninput', autoResize); // Для устаревших версий браузеров
} else {
    textarea.addEventListener('input', autoResize);
}

