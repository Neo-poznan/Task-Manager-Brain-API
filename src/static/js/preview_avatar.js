document.getElementById('file-input').onchange = function () {
    let src = URL.createObjectURL(this.files[0]);
    document.getElementById('preview-avatar-image').src = src;
    document.getElementById('preview-avatar-alt').style.display = 'none';
}