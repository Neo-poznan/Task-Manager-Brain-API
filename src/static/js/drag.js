let dragged;


// перетаскивание элементов
document.addEventListener("dragstart", function(event) {
    dragged = event.target;
    event.dataTransfer.setData('text/plain', null);

});

document.addEventListener("dragover", function(event) {
    event.preventDefault();
    let target = getClosestTask(event.target);
    if (target) {
        target.style.border = "4px dashed gray";
    }
});

document.addEventListener("dragleave", function(event) {
    let target = getClosestTask(event.target);
    if (target) {
        target.style.border = "1px solid #ccc";
    }
    
});

document.addEventListener("drop", function(event) {
    event.preventDefault();
    let target = getClosestTask(event.target);
    if (target) {
        target.style.border = "1px solid #ccc";
        taskItems = Array.from(document.getElementsByClassName('task-item')).map(task => task.id)
        targetPosition = taskItems.indexOf(target.id);
        draggedPosition = taskItems.indexOf(dragged.id);

        if (targetPosition - 1 == draggedPosition) {
            target.parentNode.insertBefore(dragged, target.nextSibling);
        }
        else {
            target.parentNode.insertBefore(dragged, target);
        }
        
        sendTaskOrderToServer();        
    }

});

function getClosestTask(el) {
    if (el.className === 'task-item') {
        return el;
    } 
}

// отправляет на сервер данные о текущем расположении элементов

function sendTaskOrderToServer() {
    let tasks = Array.from(document.getElementsByClassName('task-item'));
    let taskId = tasks.map(task => task.id.replace('task', ''));
    console.log(taskId)
    

    fetch(ordersUpdateUrl, {
        method: 'PUT',
        headers: {
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({order: taskId}),
    }).then(response => {
        if (response.ok) {
            console.log('OK')
        }
    });
}